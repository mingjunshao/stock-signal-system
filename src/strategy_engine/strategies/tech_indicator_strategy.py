"""技术指标组合策略：MACD/KDJ/RSI/BOLL多指标共振"""

import pandas as pd
from typing import Any, Dict, List, Tuple

from src.core.constants import SignalType, SignalStrength, StrategyType
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.signal import Signal
from src.strategy_engine.indicator_calculator import IndicatorCalculator


class TechIndicatorStrategy(BaseStrategy):
    """MACD/KDJ/RSI/BOLL组合策略，多指标共振产生信号"""

    def __init__(self, params: Dict[str, Any] = None) -> None:
        default = self.get_default_params()
        super().__init__(params or default)
        self.name = "技术指标组合策略"
        self.strategy_type = StrategyType.TECH_INDICATOR
        self._calc = IndicatorCalculator()

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
            "kdj_n": 9, "kdj_m1": 3, "kdj_m2": 3,
            "rsi_periods": [6, 12, 24],
            "rsi_buy_threshold": 30, "rsi_sell_threshold": 70,
            "boll_period": 20, "boll_std": 2,
        }

    def get_param_ranges(self) -> Dict[str, Tuple[float, float, float]]:
        return {
            "macd_fast": (8, 16, 2), "macd_slow": (20, 30, 2), "macd_signal": (7, 11, 2),
            "kdj_n": (5, 15, 2), "kdj_m1": (2, 5, 1), "kdj_m2": (2, 5, 1),
            "rsi_buy_threshold": (20, 40, 5), "rsi_sell_threshold": (60, 80, 5),
            "boll_period": (15, 25, 5), "boll_std": (1.5, 3.0, 0.5),
        }

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        df_with_ind = self._calc.calc_all_indicators(df, self.params)
        signals = []

        rsi_buy = self.params.get("rsi_buy_threshold", 30)
        rsi_sell = self.params.get("rsi_sell_threshold", 70)

        for i in range(1, len(df_with_ind)):
            row = df_with_ind.iloc[i]
            prev = df_with_ind.iloc[i - 1]

            buy_score = 0
            sell_score = 0
            indicators = {}

            # MACD判断
            if "macd_dif" in row and "macd_dea" in row:
                macd_cross_up = prev["macd_dif"] <= prev["macd_dea"] and row["macd_dif"] > row["macd_dea"]
                macd_cross_down = prev["macd_dif"] >= prev["macd_dea"] and row["macd_dif"] < row["macd_dea"]
                if macd_cross_up and row["macd_hist"] > 0:
                    buy_score += 1
                if macd_cross_down and row["macd_hist"] < 0:
                    sell_score += 1
                indicators["macd_dif"] = row["macd_dif"]
                indicators["macd_dea"] = row["macd_dea"]

            # KDJ判断
            if "K" in row and "D" in row and "J" in row:
                kdj_cross_up = prev["K"] <= prev["D"] and row["K"] > row["D"]
                kdj_cross_down = prev["K"] >= prev["D"] and row["K"] < row["D"]
                if kdj_cross_up and row["J"] < 80:
                    buy_score += 1
                if kdj_cross_down and row["J"] > 20:
                    sell_score += 1
                indicators["K"] = row["K"]
                indicators["D"] = row["D"]

            # RSI判断
            if "rsi_6" in row:
                if row["rsi_6"] < rsi_buy:
                    buy_score += 1
                if row["rsi_6"] > rsi_sell:
                    sell_score += 1
                indicators["rsi_6"] = row["rsi_6"]

            # BOLL判断
            if "boll_lower" in row and "boll_upper" in row:
                if row["close"] <= row["boll_lower"]:
                    buy_score += 1
                if row["close"] >= row["boll_upper"]:
                    sell_score += 1
                indicators["boll_upper"] = row["boll_upper"]
                indicators["boll_lower"] = row["boll_lower"]

            # 生成信号
            if buy_score >= 2:
                strength = SignalStrength.STRONG if buy_score >= 3 else SignalStrength.MEDIUM
                confidence = buy_score / 4.0
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.BUY, strategy_type=self.strategy_type,
                    strength=strength, price=row["close"],
                    confidence=confidence,
                    description=f"技术指标共振买入({buy_score}/4)",
                    indicators=indicators,
                ))
            elif sell_score >= 2:
                strength = SignalStrength.STRONG if sell_score >= 3 else SignalStrength.MEDIUM
                confidence = sell_score / 4.0
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.SELL, strategy_type=self.strategy_type,
                    strength=strength, price=row["close"],
                    confidence=confidence,
                    description=f"技术指标共振卖出({sell_score}/4)",
                    indicators=indicators,
                ))

        return signals