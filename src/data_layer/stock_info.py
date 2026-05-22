"""股票基本信息查询和管理"""

from typing import Dict, List, Any
from datetime import datetime

from src.core.database import DatabaseManager
from src.data_layer.data_fetcher import DataFetcher
from src.core.logger import setup_logger

logger = setup_logger("stock_info")


class StockInfo:
    """股票信息查询和管理服务"""

    def __init__(self, db_manager: DatabaseManager, fetcher: DataFetcher) -> None:
        self._db = db_manager
        self._fetcher = fetcher

    def search(self, keyword: str) -> List[Dict[str, str]]:
        """搜索股票（本地数据库优先，再从akshare）"""
        rows = self._db.query(
            "SELECT symbol, name FROM stock_info WHERE symbol LIKE ? OR name LIKE ?",
            (f"%{keyword}%", f"%{keyword}%"),
        )
        if rows:
            return rows
        return self._fetcher.search_stock(keyword)

    def get_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票详细信息"""
        rows = self._db.query("SELECT * FROM stock_info WHERE symbol=?", (symbol,))
        if rows:
            return rows[0]
        return self._fetcher.fetch_stock_info(symbol)

    def get_all_stocks(self, market: str = "all") -> List[Dict[str, Any]]:
        """获取所有股票列表（从本地数据库）"""
        if market == "all":
            rows = self._db.query("SELECT * FROM stock_info ORDER BY symbol")
        elif market == "SH":
            rows = self._db.query(
                "SELECT * FROM stock_info WHERE symbol LIKE '6%' ORDER BY symbol"
            )
        else:
            rows = self._db.query(
                "SELECT * FROM stock_info WHERE symbol NOT LIKE '6%' ORDER BY symbol"
            )
        return rows

    def get_tracked_stocks(self) -> List[Dict[str, Any]]:
        """获取所有跟踪股票"""
        return self._db.query(
            "SELECT * FROM stock_info WHERE is_tracked=1 ORDER BY symbol"
        )

    def set_tracked(self, symbol: str, tracked: bool) -> int:
        """设置/取消跟踪股票"""
        return self._db.update(
            "stock_info",
            {"symbol": symbol},
            {"is_tracked": 1 if tracked else 0}
        )

    def refresh_stock_list(self) -> int:
        """全量刷新股票列表到数据库（从数据源）"""
        logger.info("开始刷新股票列表...")
        df = self._fetcher.fetch_stock_list()
        if df.empty:
            logger.warning("获取股票列表失败或为空")
            return 0
        
        # 确保 DataFrame 有必要的列
        required_cols = ["symbol", "name"]
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"数据缺少必要列: {col}")
                return 0

        records = df.to_dict("records")
        count = self._db.insert_batch("stock_info", records)
        logger.info(f"股票列表刷新完成，共更新/插入 {count} 条记录")
        return count

    def get_last_update_time(self) -> str:
        """获取最后一次更新股票列表的时间"""
        rows = self._db.query(
            "SELECT MAX(updated_at) as last_update FROM stock_info"
        )
        if rows and rows[0].get("last_update"):
            return rows[0]["last_update"]
        return "从未更新"
