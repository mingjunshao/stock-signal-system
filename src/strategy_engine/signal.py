"""信号数据结构定义"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.core.constants import SignalType, SignalStrength, StrategyType


@dataclass
class Signal:
    """单个策略产生的交易信号"""
    date: str
    symbol: str
    signal_type: SignalType
    strategy_type: StrategyType
    strength: SignalStrength
    price: float
    confidence: float
    description: str = ""
    indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class FusedSignal:
    """融合后的最终交易信号"""
    date: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    price: float
    confidence: float
    contributing_strategies: List[StrategyType] = field(default_factory=list)
    weights: Dict[StrategyType, float] = field(default_factory=dict)
    description: str = ""
    buy_price_target: Optional[float] = None
    sell_price_target: Optional[float] = None