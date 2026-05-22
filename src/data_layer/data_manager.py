"""数据管理器：缓存调度、增量更新、数据库读写

核心策略:
  - 优先使用数据库中已有数据
  - 仅在数据库无数据时才从数据源获取
  - 获取后立即入库，供后续使用
  - 支持增量更新（只获取缺失部分）
  - 数据完整性由 update_stock_data() 主动维护
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.data_layer.data_fetcher import DataFetcher
from src.data_layer.data_validator import DataValidator
from src.strategy_engine.indicator_calculator import IndicatorCalculator

logger = setup_logger("data_manager")


class DataManager:
    """数据管理：数据库优先+多源获取+增量更新"""

    def __init__(self, db_manager: DatabaseManager, fetcher: DataFetcher) -> None:
        self._db = db_manager
        self._fetcher = fetcher
        self._validator = DataValidator()
        self._indicator_calc = IndicatorCalculator()

    def ensure_data_available(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """确保指定范围数据可用

        策略:
          1. 先查数据库，如果返回了数据就直接使用
          2. 如果数据库无数据，从数据源获取并入库
          3. 如需更新到最新，先调用 update_stock_data()
        """
        db_df = self.get_daily_data(symbol, start_date, end_date)
        if not db_df.empty:
            logger.info(f"使用数据库缓存: {symbol}, {len(db_df)}条")
            return db_df

        logger.info(f"从数据源获取: {symbol}, {start_date} ~ {end_date}")
        new_df = self._fetcher.fetch_daily_data(symbol, start_date, end_date)
        if not new_df.empty:
            new_df = self._validator.validate(new_df)
            self.save_daily_data(symbol, new_df)
        return self.get_daily_data(symbol, start_date, end_date)

    def fetch_full_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取完整范围数据，自动增量补充缺失部分

        与 ensure_data_available 不同，此方法会检查数据库数据是否
        覆盖了请求的日期范围，如有缺失则增量补充。
        适用于回测等需要完整数据的场景。
        """
        db_df = self.get_daily_data(symbol, start_date, end_date)
        if not db_df.empty:
            db_range = self._get_db_date_range(symbol)
            if db_range is not None:
                db_start, db_end = db_range
                today = datetime.now().strftime("%Y-%m-%d")
                effective_end = min(end_date, today)
                need_suffix = effective_end > db_end

                if not need_suffix:
                    logger.info(f"使用数据库缓存(完整): {symbol}, {len(db_df)}条")
                    return db_df

                logger.info(f"增量补充尾部: {symbol}, {db_end} ~ {effective_end}")
                new_df = self._fetcher.fetch_daily_data_incremental(symbol, db_end)
                if not new_df.empty:
                    new_df = self._validator.validate(new_df)
                    self.save_daily_data(symbol, new_df)

                return self.get_daily_data(symbol, start_date, end_date)

        logger.info(f"从数据源获取: {symbol}, {start_date} ~ {end_date}")
        new_df = self._fetcher.fetch_daily_data(symbol, start_date, end_date)
        if not new_df.empty:
            new_df = self._validator.validate(new_df)
            self.save_daily_data(symbol, new_df)
        return self.get_daily_data(symbol, start_date, end_date)

    def _get_db_date_range(self, symbol: str) -> Optional[tuple]:
        """查询数据库中该股票的数据日期范围 (最早, 最新)"""
        rows = self._db.query(
            "SELECT MIN(date) as min_date, MAX(date) as max_date FROM daily_kline WHERE symbol=?",
            (symbol,),
        )
        if rows and rows[0]["min_date"] and rows[0]["max_date"]:
            return (rows[0]["min_date"], rows[0]["max_date"])
        return None

    def update_stock_data(self, symbol: str) -> None:
        """增量更新单只股票数据到最新"""
        db_range = self._get_db_date_range(symbol)
        if db_range:
            _, db_end = db_range
            new_df = self._fetcher.fetch_daily_data_incremental(symbol, db_end)
        else:
            new_df = self._fetcher.fetch_daily_data(
                symbol, "2020-01-01", datetime.now().strftime("%Y-%m-%d")
            )
        if not new_df.empty:
            new_df = self._validator.validate(new_df)
            self.save_daily_data(symbol, new_df)
            logger.info(f"更新完成: {symbol}, 新增{len(new_df)}条")

    def update_all_stocks(self) -> None:
        """更新所有跟踪股票"""
        tracked = self.get_tracked_stocks()
        for stock in tracked:
            self.update_stock_data(stock["symbol"])

    def get_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从数据库查询日线数据"""
        rows = self._db.query(
            "SELECT * FROM daily_kline WHERE symbol=? AND date BETWEEN ? AND ? ORDER BY date",
            (symbol, start_date, end_date),
        )
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        drop_cols = ["id", "created_at"]
        df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")
        for col in ["open", "high", "low", "close", "volume", "amount", "turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def get_latest_date(self, symbol: str) -> Optional[str]:
        """查询数据库中该股票最新日期"""
        rows = self._db.query(
            "SELECT MAX(date) as latest FROM daily_kline WHERE symbol=?",
            (symbol,),
        )
        return rows[0]["latest"] if rows and rows[0]["latest"] else None

    def save_daily_data(self, symbol: str, df: pd.DataFrame) -> int:
        """保存日线数据到数据库（INSERT OR REPLACE 去重）"""
        if df.empty:
            return 0
        records = df.to_dict("records")
        count = self._db.insert_batch("daily_kline", records)
        logger.info(f"入库: {symbol}, {count}条")
        return count

    def get_tracked_stocks(self) -> List[Dict[str, str]]:
        """获取跟踪股票列表"""
        return self._db.query("SELECT symbol, name FROM stock_info WHERE is_tracked=1")

    def add_tracked_stock(self, symbol: str, name: str) -> None:
        """添加跟踪股票"""
        self._db.insert_batch("stock_info", [
            {"symbol": symbol, "name": name, "is_tracked": 1}
        ])

    def remove_tracked_stock(self, symbol: str) -> None:
        """移除跟踪股票"""
        self._db.update("stock_info", {"symbol": symbol}, {"is_tracked": 0})

    def get_data_with_indicators(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取带技术指标的数据"""
        df = self.ensure_data_available(symbol, start_date, end_date)
        if df.empty:
            return df
        return self._indicator_calc.calc_all_indicators(df)
