"""数据校验与清洗：缺失值、异常值处理"""

import pandas as pd
from src.core.logger import setup_logger

logger = setup_logger("data_validator")


class DataValidator:
    """数据校验与清洗器"""

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = self._remove_duplicates(df)
        df = self._fill_missing(df)
        df = self._remove_abnormal(df)
        df = self._validate_price_consistency(df)
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        if "date" in df.columns and "symbol" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["symbol", "date"], keep="last")
            if len(df) < before:
                logger.info(f"去除重复记录: {before - len(df)}条")
        return df

    def _fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        price_cols = ["open", "high", "low", "close"]
        for col in price_cols:
            if col in df.columns and df[col].isnull().any():
                cnt = df[col].isnull().sum()
                df[col] = df[col].ffill()
                logger.info(f"前向填充缺失值: {col}, {cnt}条")

        if "volume" in df.columns and df["volume"].isnull().any():
            df["volume"] = df["volume"].fillna(0)

        if "amount" in df.columns and df["amount"].isnull().any():
            df["amount"] = df["amount"].fillna(0)

        return df

    def _remove_abnormal(self, df: pd.DataFrame) -> pd.DataFrame:
        if "volume" in df.columns:
            df = df[df["volume"] >= 0]
        if "close" in df.columns:
            df = df[df["close"] > 0]
        return df

    def _validate_price_consistency(self, df: pd.DataFrame) -> pd.DataFrame:
        """确保 high >= max(open,close) 且 low <= min(open,close)"""
        if all(c in df.columns for c in ["open", "high", "low", "close"]):
            df["high"] = df[["open", "high", "close"]].max(axis=1)
            df["low"] = df[["open", "low", "close"]].min(axis=1)
        return df