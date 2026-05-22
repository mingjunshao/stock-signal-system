"""akshare数据获取器：A股日线行情、股票列表、搜索

数据源优先级:
  历史日线: 腾讯(stock_zh_a_hist_tx) > 新浪(stock_zh_a_daily) > 东方财富(stock_zh_a_hist)
  股票列表/搜索: 交易所(stock_info_a_code_name/sz/sh) > 新浪(stock_zh_a_spot) > 东方财富(stock_zh_a_spot_em)
"""

import akshare as ak
import pandas as pd
import time
from typing import Any, Dict, List, Optional

from src.core.logger import setup_logger

logger = setup_logger("data_fetcher")


class DataFetcher:
    """基于akshare的A股行情数据获取器，多数据源自动切换"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._stock_list_cache: Optional[pd.DataFrame] = None

    @staticmethod
    def _symbol_to_tx(symbol: str) -> str:
        if symbol.startswith("sz") or symbol.startswith("sh"):
            return symbol
        prefix = "sh" if symbol.startswith("6") else "sz"
        return f"{prefix}{symbol}"

    @staticmethod
    def _symbol_to_sina(symbol: str) -> str:
        if symbol.startswith("sh") or symbol.startswith("sz"):
            return symbol
        prefix = "sh" if symbol.startswith("6") else "sz"
        return f"{prefix}{symbol}"

    @staticmethod
    def _strip_symbol(symbol: str) -> str:
        return symbol.replace("sz", "").replace("sh", "")

    def _retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"尝试 {attempt + 1}/{self.max_retries} 失败: {e}, "
                        f"等待 {self.retry_delay}秒后重试..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    raise

    # ── 历史日线数据 ──────────────────────────────────────────────

    def fetch_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指定股票日线数据，按数据源优先级依次尝试"""
        logger.info(f"获取日线数据: {symbol}, {start_date} ~ {end_date}")
        pure_symbol = self._strip_symbol(symbol)
        start = start_date.replace("-", "")
        end = end_date.replace("-", "")

        sources = [
            ("腾讯", self._fetch_daily_tx, pure_symbol, start, end),
            ("新浪", self._fetch_daily_sina, pure_symbol, start, end),
            ("东方财富", self._fetch_daily_em, pure_symbol, start, end),
        ]

        for name, func, *args in sources:
            try:
                raw_df = self._retry(func, *args)
                if raw_df is not None and not raw_df.empty:
                    logger.info(f"通过 [{name}] 成功获取日线数据")
                    return self._normalize_data(raw_df, pure_symbol)
            except Exception as e:
                logger.warning(f"[{name}] 获取日线数据失败: {e}")

        logger.error(f"所有数据源均失败: {symbol}")
        return pd.DataFrame()

    def _fetch_daily_tx(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        tx_symbol = self._symbol_to_tx(symbol)
        return ak.stock_zh_a_hist_tx(
            symbol=tx_symbol,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )

    def _fetch_daily_sina(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        sina_symbol = self._symbol_to_sina(symbol)
        return ak.stock_zh_a_daily(
            symbol=sina_symbol,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )

    def _fetch_daily_em(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )

    def fetch_daily_data_incremental(self, symbol: str, last_date: str) -> pd.DataFrame:
        """增量获取：从last_date之后到最新"""
        from datetime import datetime
        pure_symbol = self._strip_symbol(symbol)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = last_date.replace("-", "")

        sources = [
            ("腾讯", self._fetch_daily_tx, pure_symbol, start_date, end_date),
            ("新浪", self._fetch_daily_sina, pure_symbol, start_date, end_date),
            ("东方财富", self._fetch_daily_em, pure_symbol, start_date, end_date),
        ]

        for name, func, *args in sources:
            try:
                raw_df = self._retry(func, *args)
                if raw_df is not None and not raw_df.empty:
                    date_col = "日期" if "日期" in raw_df.columns else "date"
                    if date_col in raw_df.columns:
                        raw_df = raw_df[raw_df[date_col].astype(str) > last_date]
                    logger.info(f"通过 [{name}] 成功获取增量数据")
                    return self._normalize_data(raw_df, pure_symbol)
            except Exception as e:
                logger.warning(f"[{name}] 增量获取失败: {e}")

        logger.error(f"增量获取所有数据源均失败: {symbol}")
        return pd.DataFrame()

    # ── 股票列表 / 搜索 / 信息 ────────────────────────────────────

    def _get_stock_list_df(self) -> Optional[pd.DataFrame]:
        """获取完整股票列表(带缓存)，按数据源优先级尝试

        优先使用交易所官方接口(稳定)，其次实时行情接口(数据更丰富)
        """
        if self._stock_list_cache is not None:
            return self._stock_list_cache

        sources = [
            ("交易所", self._fetch_stock_list_exchange),
            ("新浪", self._fetch_spot_sina),
            ("东方财富", self._fetch_spot_em),
        ]
        for name, func in sources:
            try:
                df = self._retry(func)
                if df is not None and not df.empty:
                    logger.info(f"通过 [{name}] 获取股票列表成功")
                    self._stock_list_cache = df
                    return df
            except Exception as e:
                logger.warning(f"[{name}] 获取股票列表失败: {e}")
        return None

    def _fetch_stock_list_exchange(self) -> pd.DataFrame:
        """交易所官方接口: stock_info_a_code_name + stock_info_sz/sh_name_code"""
        dfs = []
        try:
            df_simple = ak.stock_info_a_code_name()
            if not df_simple.empty:
                result = pd.DataFrame()
                result["code"] = df_simple["code"].astype(str)
                result["name"] = df_simple["name"].astype(str)
                dfs.append(result)
        except Exception as e:
            logger.warning(f"stock_info_a_code_name 失败: {e}")

        try:
            df_sz = ak.stock_info_sz_name_code(symbol="A股列表")
            if not df_sz.empty:
                sz_result = pd.DataFrame()
                sz_result["code"] = df_sz["A股代码"].astype(str)
                sz_result["name"] = df_sz["A股简称"].astype(str)
                sz_result["industry"] = df_sz["所属行业"].astype(str)
                dfs.append(sz_result)
        except Exception as e:
            logger.warning(f"stock_info_sz_name_code 失败: {e}")

        try:
            df_sh = ak.stock_info_sh_name_code()
            if not df_sh.empty:
                sh_result = pd.DataFrame()
                sh_result["code"] = df_sh["证券代码"].astype(str)
                sh_result["name"] = df_sh["证券简称"].astype(str)
                dfs.append(sh_result)
        except Exception as e:
            logger.warning(f"stock_info_sh_name_code 失败: {e}")

        if not dfs:
            raise RuntimeError("交易所接口均失败")

        merged = pd.concat(dfs, ignore_index=True)
        merged = merged.drop_duplicates(subset=["code"], keep="last")
        return merged

    def _fetch_spot_sina(self) -> pd.DataFrame:
        return ak.stock_zh_a_spot()

    def _fetch_spot_em(self) -> pd.DataFrame:
        return ak.stock_zh_a_spot_em()

    def fetch_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            df = self._get_stock_list_df()
            if df is None:
                return self._get_default_stock_list()

            code_col = self._detect_col(df, ["代码", "code", "symbol"])
            name_col = self._detect_col(df, ["名称", "name", "A股简称", "证券简称"])

            result = pd.DataFrame()
            result["symbol"] = df[code_col].astype(str).str.strip()
            result["name"] = df[name_col].astype(str).str.strip()
            result["market"] = result["symbol"].apply(
                lambda x: "SH" if x.startswith("6") else "SZ"
            )
            if market != "all":
                prefix = "6" if market == "SH" else "0"
                result = result[result["symbol"].str.startswith(prefix)]
            return result
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return self._get_default_stock_list()

    def fetch_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        pure_symbol = self._strip_symbol(symbol)
        try:
            df = self._get_stock_list_df()
            if df is None:
                return self._get_default_stock_info(pure_symbol)

            code_col = self._detect_col(df, ["代码", "code", "symbol"])
            name_col = self._detect_col(df, ["名称", "name", "A股简称", "证券简称"])
            industry_col = self._detect_col(df, ["行业", "所属行业"], optional=True)

            row = df[df[code_col].astype(str).str.strip() == pure_symbol]
            if row.empty:
                return self._get_default_stock_info(pure_symbol)
            row = row.iloc[0]
            return {
                "symbol": pure_symbol,
                "name": str(row.get(name_col, "")).strip(),
                "market": "SH" if pure_symbol.startswith("6") else "SZ",
                "industry": str(row.get(industry_col, "")).strip() if industry_col else "",
            }
        except Exception as e:
            logger.error(f"获取股票信息失败: {symbol}, {e}")
            return self._get_default_stock_info(pure_symbol)

    def search_stock(self, keyword: str) -> List[Dict[str, str]]:
        """按关键字搜索股票（代码或名称模糊匹配）"""
        try:
            df = self._get_stock_list_df()
            if df is None:
                return self._get_default_search_results(keyword)

            code_col = self._detect_col(df, ["代码", "code", "symbol"])
            name_col = self._detect_col(df, ["名称", "name", "A股简称", "证券简称"])

            mask = (
                df[code_col].astype(str).str.contains(keyword, na=False)
                | df[name_col].astype(str).str.contains(keyword, na=False)
            )
            matched = df[mask]
            return [
                {"symbol": str(row[code_col]).strip(), "name": str(row[name_col]).strip()}
                for _, row in matched.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索股票失败: {keyword}, {e}")
            return self._get_default_search_results(keyword)

    # ── 工具方法 ──────────────────────────────────────────────────

    @staticmethod
    def _detect_col(df: pd.DataFrame, candidates: List[str], optional: bool = False) -> Optional[str]:
        for col in candidates:
            if col in df.columns:
                return col
        if optional:
            return None
        return candidates[0]

    def _get_default_stock_list(self) -> pd.DataFrame:
        default_stocks = [
            {"symbol": "000001", "name": "平安银行", "market": "SZ"},
            {"symbol": "000002", "name": "万科A", "market": "SZ"},
            {"symbol": "600000", "name": "浦发银行", "market": "SH"},
            {"symbol": "600036", "name": "招商银行", "market": "SH"},
            {"symbol": "600519", "name": "贵州茅台", "market": "SH"},
        ]
        return pd.DataFrame(default_stocks)

    def _get_default_stock_info(self, symbol: str) -> Dict[str, Any]:
        default_names = {
            "000001": "平安银行",
            "000002": "万科A",
            "600000": "浦发银行",
            "600036": "招商银行",
            "600519": "贵州茅台",
        }
        return {
            "symbol": symbol,
            "name": default_names.get(symbol, symbol),
            "market": "SH" if symbol.startswith("6") else "SZ",
            "industry": "",
        }

    def _get_default_search_results(self, keyword: str) -> List[Dict[str, str]]:
        default_stocks = [
            {"symbol": "000001", "name": "平安银行"},
            {"symbol": "000002", "name": "万科A"},
            {"symbol": "600000", "name": "浦发银行"},
            {"symbol": "600036", "name": "招商银行"},
            {"symbol": "600519", "name": "贵州茅台"},
        ]
        results = []
        for stock in default_stocks:
            if keyword.lower() in stock["symbol"].lower() or keyword.lower() in stock["name"].lower():
                results.append(stock)
        return results if results else default_stocks[:3]

    def _normalize_data(self, raw_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """标准化akshare数据为统一格式，兼容多数据源列名

        各数据源列名差异:
          腾讯: date, open, close, high, low, amount(成交量/手)
          新浪: date, open, high, low, close, volume(股), amount(元), turnover
          东方财富: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 换手率

        统一输出: volume=成交量(股), amount=成交额(元)
        """
        if raw_df.empty:
            return raw_df

        column_map = {
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "换手率": "turnover",
        }
        df = raw_df.rename(columns=column_map)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        for col in ["open", "high", "low", "close", "volume", "amount", "turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        has_volume = "volume" in df.columns
        has_amount = "amount" in df.columns

        if not has_volume and has_amount:
            # 腾讯源: amount=成交量(手)，volume=股数，amount*100=股数
            df["volume"] = df["amount"] * 100  # 手数转股数(1手=100股)
            df["amount"] = df["volume"] * df["close"]  # 计算成交额=股数*收盘价
        elif has_volume and not has_amount:
            # 有成交量无成交额，计算成交额
            df["amount"] = df["volume"] * df["close"]

        df["symbol"] = symbol
        df = df.sort_values("date").reset_index(drop=True)

        keep_cols = ["symbol", "date", "open", "high", "low", "close",
                      "volume", "amount", "turnover"]
        df = df[[c for c in keep_cols if c in df.columns]]
        return df
