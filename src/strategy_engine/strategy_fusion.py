"""策略融合引擎：加权投票融合多策略信号"""

from typing import Dict, List

import pandas as pd

from src.core.constants import SignalType, SignalStrength, StrategyType
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.signal import Signal, FusedSignal


class StrategyFusionEngine:
    """加权投票融合引擎：多策略信号加权融合为最终信号"""

    def __init__(self, strategies: List[BaseStrategy],
                 weights: Dict[StrategyType, float] = None) -> None:
        self.strategies = strategies
        self.weights = weights or {
            StrategyType.TECH_INDICATOR: 0.25,
            StrategyType.MEAN_REVERSION: 0.25,
            StrategyType.VOLUME_PRICE: 0.25,
            StrategyType.TREND_FOLLOWING: 0.25,
        }
        self.buy_threshold = 0.6
        self.sell_threshold = -0.6

    def fuse_signals(self,
                     all_signals: Dict[StrategyType, List[Signal]],
                     df: pd.DataFrame) -> List[FusedSignal]:
        """融合算法：加权投票"""
        # 按日期分组所有信号
        date_signals: Dict[str, List[Signal]] = {}
        for stype, sigs in all_signals.items():
            for sig in sigs:
                if sig.date not in date_signals:
                    date_signals[sig.date] = []
                date_signals[sig.date].append(sig)

        fused = []
        for date, sigs in date_signals.items():
            # 查找当日价格
            price_row = df[df["date"] == date]
            price = price_row.iloc[0]["close"] if not price_row.empty else 0
            symbol = price_row.iloc[0].get("symbol", "") if not price_row.empty else ""

            buy_score = 0.0
            sell_score = 0.0
            contributing_buy: List[StrategyType] = []
            contributing_sell: List[StrategyType] = []
            used_weights: Dict[StrategyType, float] = {}

            for sig in sigs:
                weight = self.weights.get(sig.strategy_type, 0.25)
                score = weight * sig.confidence * sig.strength.value

                if sig.signal_type == SignalType.BUY:
                    buy_score += score
                    contributing_buy.append(sig.strategy_type)
                elif sig.signal_type == SignalType.SELL:
                    sell_score += score
                    contributing_sell.append(sig.strategy_type)

                used_weights[sig.strategy_type] = weight

            net_score = buy_score - sell_score
            total_weight = sum(self.weights.values())

            # 判断信号类型
            if net_score >= self.buy_threshold:
                signal_type = SignalType.BUY
                contributing = contributing_buy
                confidence = min(abs(net_score) / total_weight, 1.0)
            elif net_score <= self.sell_threshold:
                signal_type = SignalType.SELL
                contributing = contributing_sell
                confidence = min(abs(net_score) / total_weight, 1.0)
            else:
                signal_type = SignalType.HOLD
                contributing = contributing_buy + contributing_sell
                confidence = abs(net_score) / total_weight

            # 信号强度：根据达成一致的策略数量
            agree_count = len(contributing_buy) if signal_type == SignalType.BUY else len(contributing_sell)
            if agree_count >= 3:
                strength = SignalStrength.STRONG
            elif agree_count >= 2:
                strength = SignalStrength.MEDIUM
            else:
                strength = SignalStrength.WEAK

            desc_parts = [f"{sig.strategy_type.value}" for sig in sigs]
            description = f"融合信号({signal_type.value}): {', '.join(desc_parts)}"

            fused.append(FusedSignal(
                date=date, symbol=symbol,
                signal_type=signal_type, strength=strength,
                price=price, confidence=confidence,
                contributing_strategies=contributing,
                weights=used_weights,
                description=description,
            ))

        return fused

    def set_weights(self, weights: Dict[StrategyType, float]) -> None:
        self.weights = weights

    def get_weights(self) -> Dict[StrategyType, float]:
        return self.weights

    def auto_weight_by_backtest(self,
                                backtest_results: Dict[StrategyType, dict]) -> Dict[StrategyType, float]:
        """根据各策略回测胜率自动调整权重"""
        win_rates = {}
        for stype, result in backtest_results.items():
            win_rates[stype] = result.get("win_rate", 0.5)

        total_wr = sum(win_rates.values())
        if total_wr == 0:
            return self.weights

        new_weights = {}
        for stype, wr in win_rates.items():
            new_weights[stype] = wr / total_wr

        self.weights = new_weights
        return new_weights