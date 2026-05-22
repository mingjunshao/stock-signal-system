"""回测结果数据结构"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from src.core.constants import StrategyType, SignalType


@dataclass
class TradeRecord:
    """单次交易记录"""
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    signal_type: SignalType
    profit: float
    profit_rate: float
    holding_days: int


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str
    strategy_type: StrategyType
    params: Dict[str, Any]
    start_date: str
    end_date: str
    trades: List[TradeRecord] = field(default_factory=list)
    total_trades: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0
    avg_profit_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    equity_curve: List[Tuple[str, float]] = field(default_factory=list)