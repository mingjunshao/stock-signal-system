"""技术指标计算器：纯Python实现MACD/KDJ/RSI/BOLL/MA/VWAP/量比/OBV/支撑阻力/ATR"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Tuple


class IndicatorCalculator:
    """技术指标计算器，纯pandas实现"""

    def calc_ema(self, series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def calc_macd(self, df: pd.DataFrame,
                  fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        close = df["close"]
        ema_fast = self.calc_ema(close, fast)
        ema_slow = self.calc_ema(close, slow)
        dif = ema_fast - ema_slow
        dea = self.calc_ema(dif, signal)
        hist = 2 * (dif - dea)
        result = pd.DataFrame({
            "macd_dif": dif, "macd_dea": dea, "macd_hist": hist
        }, index=df.index)
        return result

    def calc_kdj(self, df: pd.DataFrame,
                 n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        low_n = df["low"].rolling(n).min()
        high_n = df["high"].rolling(n).max()
        rsv = (df["close"] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)

        k = rsv.ewm(com=m1 - 1, adjust=False).mean()
        d = k.ewm(com=m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d
        return pd.DataFrame({"K": k, "D": d, "J": j}, index=df.index)

    def calc_rsi(self, df: pd.DataFrame, periods: List[int] = [6, 12, 24]) -> pd.DataFrame:
        close = df["close"]
        result = {}
        for period in periods:
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = (-delta).where(delta < 0, 0.0)
            avg_gain = gain.rolling(period).mean()
            avg_loss = loss.rolling(period).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            result[f"rsi_{period}"] = rsi
        return pd.DataFrame(result, index=df.index)

    def calc_boll(self, df: pd.DataFrame,
                  period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        mid = df["close"].rolling(period).mean()
        std = df["close"].rolling(period).std()
        upper = mid + std_dev * std
        lower = mid - std_dev * std
        return pd.DataFrame({
            "boll_mid": mid, "boll_upper": upper, "boll_lower": lower
        }, index=df.index)

    def calc_ma(self, df: pd.DataFrame,
                periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        result = {}
        for p in periods:
            result[f"ma_{p}"] = df["close"].rolling(p).mean()
        return pd.DataFrame(result, index=df.index)

    def calc_vwap(self, df: pd.DataFrame) -> pd.Series:
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        cum_vol = df["volume"].cumsum()
        cum_tp_vol = (typical_price * df["volume"]).cumsum()
        return cum_tp_vol / cum_vol

    def calc_volume_ratio(self, df: pd.DataFrame, period: int = 5) -> pd.Series:
        avg_vol = df["volume"].rolling(period).mean()
        return df["volume"] / avg_vol

    def calc_obv(self, df: pd.DataFrame) -> pd.Series:
        direction = np.sign(df["close"].diff())
        direction.iloc[0] = 0
        return (direction * df["volume"]).cumsum()

    def calc_support_resistance(self, df: pd.DataFrame,
                                window: int = 20) -> Dict[str, float]:
        recent = df.tail(window)
        support = recent["low"].min()
        resistance = recent["high"].max()
        return {"support": support, "resistance": resistance}

    def calc_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift(1))
        low_close = abs(df["low"] - df["close"].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def calc_all_indicators(self, df: pd.DataFrame,
                            params: Dict[str, Any] = None) -> pd.DataFrame:
        """一次性计算所有常用指标并合并到DataFrame"""
        if params is None:
            params = {}

        result = df.copy()
        ic = self

        macd_params = {
            "fast": params.get("macd_fast", 12),
            "slow": params.get("macd_slow", 26),
            "signal": params.get("macd_signal", 9),
        }
        macd_df = ic.calc_macd(result, **macd_params)
        result = result.join(macd_df)

        kdj_params = {
            "n": params.get("kdj_n", 9),
            "m1": params.get("kdj_m1", 3),
            "m2": params.get("kdj_m2", 3),
        }
        kdj_df = ic.calc_kdj(result, **kdj_params)
        result = result.join(kdj_df)

        rsi_periods = params.get("rsi_periods", [6, 12, 24])
        rsi_df = ic.calc_rsi(result, rsi_periods)
        result = result.join(rsi_df)

        boll_params = {
            "period": params.get("boll_period", 20),
            "std_dev": params.get("boll_std", 2),
        }
        boll_df = ic.calc_boll(result, **boll_params)
        result = result.join(boll_df)

        ma_df = ic.calc_ma(result, [5, 10, 20, 60])
        result = result.join(ma_df)

        result["volume_ratio"] = ic.calc_volume_ratio(result, 5)
        result["obv"] = ic.calc_obv(result)
        result["atr"] = ic.calc_atr(result, params.get("atr_period", 14))
        result["vwap"] = ic.calc_vwap(result)

        return result