"""趋势跟踪策略：均线趋势+动量确认"""

import pandas as pd
from typing import Any, Dict, List, Tuple

from src.core.constants import SignalType, SignalStrength, StrategyType
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.signal import Signal
from src.strategy_engine.indicator_calculator import IndicatorCalculator


class TrendFollowingStrategy(BaseStrategy):
    """趋势跟踪策略：均线多头/空头排列+价格突破+动量确认"""

    def __init__(self, params: Dict[str, Any] = None) -> None:
        default = self.get_default_params()
        super().__init__(params or default)
        self.name = "趋势跟踪策略"
        self.strategy_type = StrategyType.TREND_FOLLOWING
        self._calc = IndicatorCalculator()

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "fast_ma": 5, "slow_ma": 20, "trend_ma": 60,
            "momentum_period": 10, "atr_period": 14,
        }

    def get_param_ranges(self) -> Dict[str, Tuple[float, float, float]]:
        return {
            "fast_ma": (3, 10, 1), "slow_ma": (15, 30, 5), "trend_ma": (40, 80, 10),
            "momentum_period": (5, 15, 5), "atr_period": (10, 20, 5),
        }

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        df_ind = self._calc.calc_all_indicators(df, self.params)
        signals = []

        fast_ma_key = f"ma_{self.params.get('fast_ma', 5)}"
        slow_ma_key = f"ma_{self.params.get('slow_ma', 20)}"
        trend_ma_key = f"ma_{self.params.get('trend_ma', 60)}"
        momentum_period = self.params.get("momentum_period", 10)

        for i in range(momentum_period + 1, len(df_ind)):
            row = df_ind.iloc[i]
            prev = df_ind.iloc[i - 1]

            if fast_ma_key not in row or slow_ma_key not in row or trend_ma_key not in row:
                continue

            fast_ma = row[fast_ma_key]
            slow_ma = row[slow_ma_key]
            trend_ma = row[trend_ma_key]
            prev_fast = prev[fast_ma_key]
            prev_slow = prev[slow_ma_key]

            # 动量：N日收益率
            momentum = (row["close"] - df_ind.iloc[i - momentum_period]["close"]) / df_ind.iloc[i - momentum_period]["close"]

            # ATR止损参考
            atr_val = row.get("atr", 0)

            indicators = {
                "fast_ma": fast_ma, "slow_ma": slow_ma, "trend_ma": trend_ma,
                "momentum": momentum, "atr": atr_val,
            }

            # 买入：快线上穿慢线（金叉）+ 趋势向上 + 动量>0
            golden_cross = prev_fast <= prev_slow and fast_ma > slow_ma
            trend_up = row["close"] > trend_ma
            if golden_cross and trend_up and momentum > 0:
                strength = SignalStrength.STRONG if momentum > 0.05 else SignalStrength.MEDIUM
                confidence = min(0.3 + abs(momentum) * 5, 0.85)
                buy_target = row["close"] + atr_val * 2 if atr_val > 0 else None
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.BUY, strategy_type=self.strategy_type,
                    strength=strength, price=row["close"],
                    confidence=confidence,
                    description=f"趋势金叉买入(动量={momentum:.2%})",
                    indicators=indicators,
                ))

            # 卖出：快线下穿慢线（死叉）+ 趋势向下 + 动量<0
            death_cross = prev_fast >= prev_slow and fast_ma < slow_ma
            trend_down = row["close"] < trend_ma
            if death_cross and trend_down and momentum < 0:
                strength = SignalStrength.STRONG if momentum < -0.05 else SignalStrength.MEDIUM
                confidence = min(0.3 + abs(momentum) * 5, 0.85)
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.SELL, strategy_type=self.strategy_type,
                    strength=strength, price=row["close"],
                    confidence=confidence,
                    description=f"趋势死叉卖出(动量={momentum:.2%})",
                    indicators=indicators,
                ))

        return signals