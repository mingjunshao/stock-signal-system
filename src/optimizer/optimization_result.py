"""优化结果数据结构"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.constants import StrategyType


@dataclass
class OptimizationResult:
    """参数优化结果"""
    strategy_type: StrategyType
    symbol: str
    best_params: Dict[str, Any]
    best_metric_value: float
    metric_name: str
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    optimization_method: str = ""
    elapsed_time: float = 0.0