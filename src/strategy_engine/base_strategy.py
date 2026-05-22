"""策略抽象基类：所有策略必须继承"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.core.constants import StrategyType
from src.strategy_engine.signal import Signal


class BaseStrategy(ABC):
    """策略基类，定义统一接口"""

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.name: str = ""
        self.strategy_type: StrategyType = StrategyType.TECH_INDICATOR

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """根据行情数据生成交易信号"""

    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """返回策略默认参数"""

    @abstractmethod
    def get_param_ranges(self) -> Dict[str, Tuple[float, float, float]]:
        """返回参数优化范围 (min, max, step)"""

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """校验参数合法性"""
        ranges = self.get_param_ranges()
        for key, (min_val, max_val, _) in ranges.items():
            if key in params:
                val = params[key]
                if isinstance(val, (int, float)) and (val < min_val or val > max_val):
                    return False
        return True

    def update_params(self, params: Dict[str, Any]) -> None:
        """更新策略参数"""
        self.params.update(params)