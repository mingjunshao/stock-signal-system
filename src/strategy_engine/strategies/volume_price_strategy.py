"""量价分析策略：成交量异动+价格形态+OBV趋势"""

import pandas as pd
from typing import Any, Dict, List, Tuple

from src.core.constants import SignalType, SignalStrength, StrategyType
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.signal import Signal
from src.strategy_engine.indicator_calculator import IndicatorCalculator


class VolumePriceStrategy(BaseStrategy):
    """量价分析策略：量比异动+价格突破+OBV趋势确认"""

    def __init__(self, params: Dict[str, Any] = None) -> None:
        default = self.get_default_params()
        super().__init__(params or default)
        self.name = "量价分析策略"
        self.strategy_type = StrategyType.VOLUME_PRICE
        self._calc = IndicatorCalculator()

    def get_default_params(self) -> Dict[str, Any]:
        return {
            "volume_ratio_threshold": 2.0, "volume_ma_period": 5,
            "price_change_threshold": 0.03, "obv_trend_period": 10,
        }

    def get_param_ranges(self) -> Dict[str, Tuple[float, float, float]]:
        return {
            "volume_ratio_threshold": (1.5, 3.0, 0.5),
            "volume_ma_period": (3, 10, 1),
            "price_change_threshold": (0.02, 0.05, 0.01),
            "obv_trend_period": (5, 15, 5),
        }

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        df_ind = self._calc.calc_all_indicators(df, self.params)
        signals = []

        vol_threshold = self.params.get("volume_ratio_threshold", 2.0)
        price_threshold = self.params.get("price_change_threshold", 0.03)
        obv_period = self.params.get("obv_trend_period", 10)

        for i in range(obv_period + 1, len(df_ind)):
            row = df_ind.iloc[i]
            prev = df_ind.iloc[i - 1]

            if "volume_ratio" not in row or "obv" not in row:
                continue

            vol_ratio = row["volume_ratio"]
            price_change = (row["close"] - prev["close"]) / prev["close"] if prev["close"] > 0 else 0

            # OBV趋势判断
            obv_recent = df_ind["obv"].iloc[i - obv_period:i + 1]
            obv_trend_up = obv_recent.iloc[-1] > obv_recent.iloc[0] and obv_recent.diff().mean() > 0
            obv_trend_down = obv_recent.iloc[-1] < obv_recent.iloc[0] and obv_recent.diff().mean() < 0

            indicators = {
                "volume_ratio": vol_ratio,
                "price_change": price_change,
                "obv_trend": "up" if obv_trend_up else ("down" if obv_trend_down else "flat"),
            }

            # 买入：放量+价格上涨+OBV上升趋势
            if vol_ratio > vol_threshold and price_change > price_threshold and obv_trend_up:
                strength = SignalStrength.STRONG if vol_ratio > vol_threshold * 1.5 else SignalStrength.MEDIUM
                confidence = min(vol_ratio / vol_threshold * 0.5, 0.85)
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.BUY, strategy_type=self.strategy_type,
                    strength=strength, price=row["close"],
                    confidence=confidence,
                    description=f"放量上涨买入(量比={vol_ratio:.1f})",
                    indicators=indicators,
                ))

            # 卖出：放量+价格下跌+OBV下降趋势
            elif vol_ratio > vol_threshold and price_change < -price_threshold and obv_trend_down:
                strength = SignalStrength.STRONG if vol_ratio > vol_threshold * 1.5 else SignalStrength.MEDIUM
                confidence = min(vol_ratio / vol_threshold * 0.5, 0.85)
                signals.append(Signal(
                    date=row["date"], symbol=row.get("symbol", ""),
                    signal_type=SignalType.SELL, strategy_type=self.strategy_type,
                    strength=strength, price=row["close"],
                    confidence=confidence,
                    description=f"放量下跌卖出(量比={vol_ratio:.1f})",
                    indicators=indicators,
                ))

        return signals