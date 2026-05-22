"""均值回归策略：基于支撑阻力位和均线偏离回归"""

import pandas as pd
from typing import Any, Dict, List, Tuple

from src.core.constants import SignalType, SignalStrength, StrategyType
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.signal import Signal
from src.strategy_engine.indicator_calculator import IndicatorCalculator


class MeanReversionStrategy(BaseStrategy):
    """均值回归策略：价格偏离均线后回归+支撑阻力位"""

    def __init__(self, params: Dict[str, Any] = None) -> None:
        default = self.get_default_params()
        super().__init__(params or default)
        self.name = "均值回归策略"
        self.strategy_type = StrategyType.MEAN_REVERSION
        self._calc = IndicatorCalculator()

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "ma_period": 20, "deviation_threshold": 2.0,
            "support_lookback": 20, "resistance_lookback": 20,
            "reversion_speed": 0.5,
        }

    def get_param_ranges(self) -> Dict[str, Tuple[float, float, float]]:
        return {
            "ma_period": (10, 30, 5),
            "deviation_threshold": (1.5, 3.0, 0.5),
            "support_lookback": (10, 30, 5),
            "resistance_lookback": (10, 30, 5),
            "reversion_speed": (0.3, 0.8, 0.1),
        }

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        df_ind = self._calc.calc_all_indicators(df, self.params)
        signals = []

        ma_period = self.params.get("ma_period", 20)
        deviation_threshold = self.params.get("deviation_threshold", 2.0)
        reversion_speed = self.params.get("reversion_speed", 0.5)

        for i in range(ma_period, len(df_ind)):
            row = df_ind.iloc[i]
            prev = df_ind.iloc[i - 1]

            if "boll_mid" not in row or "boll_upper" not in row or "boll_lower" not in row:
                continue

            ma_val = row["boll_mid"]
            close = row["close"]
            deviation = (close - ma_val) / ma_val if ma_val > 0 else 0

            # 支撑阻力位
            sr = self._calc.calc_support_resistance(
                df_ind.iloc[:i + 1],
                self.params.get("support_lookback", 20)
            )

            indicators = {
                "deviation": deviation,
                "ma_value": ma_val,
                "support": sr["support"],
                "resistance": sr["resistance"],
            }

            # 买入：价格偏离均线向下超过阈值，且开始回归（前一日偏离更大）
            prev_deviation = (prev["close"] - prev["boll_mid"]) / prev["boll_mid"] if prev["boll_mid"] > 0 else 0
            if deviation < -deviation_threshold and prev_deviation < deviation:
                # 价格接近支撑位，回归信号更强
                near_support = abs(close - sr["support"]) / sr["support"] < 0.02 if sr["support"] > 0 else False
                strength = SignalStrength.STRONG if near_support else SignalStrength.MEDIUM
                confidence = min(abs(deviation) * 10 * reversion_speed, 0.9)
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.BUY, strategy_type=self.strategy_type,
                    strength=strength, price=close,
                    confidence=confidence,
                    description=f"均值回归买入(偏离={deviation:.2%})",
                    indicators=indicators,
                ))

            # 卖出：价格偏离均线向上超过阈值，且开始回归
            elif deviation > deviation_threshold and prev_deviation > deviation:
                near_resistance = abs(close - sr["resistance"]) / sr["resistance"] < 0.02 if sr["resistance"] > 0 else False
                strength = SignalStrength.STRONG if near_resistance else SignalStrength.MEDIUM
                confidence = min(abs(deviation) * 10 * reversion_speed, 0.9)
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.SELL, strategy_type=self.strategy_type,
                    strength=strength, price=close,
                    confidence=confidence,
                    description=f"均值回归卖出(偏离={deviation:.2%})",
                    indicators=indicators,
                ))

        return signals