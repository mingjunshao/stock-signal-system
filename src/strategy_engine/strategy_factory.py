"""策略工厂：动态注册和创建策略实例"""

from typing import Any, Dict, List, Type

from src.core.constants import StrategyType
from src.strategy_engine.base_strategy import BaseStrategy


class StrategyFactory:
    """策略工厂，注册+动态创建策略实例"""

    _registry: Dict[StrategyType, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, strategy_type: StrategyType,
                 strategy_class: Type[BaseStrategy]) -> None:
        cls._registry[strategy_type] = strategy_class

    @classmethod
    def create(cls, strategy_type: StrategyType,
               params: Dict[str, Any] = None) -> BaseStrategy:
        if strategy_type not in cls._registry:
            raise ValueError(f"未注册的策略类型: {strategy_type}")
        return cls._registry[strategy_type](params)

    @classmethod
    def create_all(cls, params_map: Dict[StrategyType, Dict[str, Any]] = None) -> List[BaseStrategy]:
        strategies = []
        for stype, sclass in cls._registry.items():
            params = params_map.get(stype) if params_map else None
            strategies.append(sclass(params))
        return strategies

    @classmethod
    def get_registered_types(cls) -> List[StrategyType]:
        return list(cls._registry.keys())


# 自动注册所有策略
from src.strategy_engine.strategies.tech_indicator_strategy import TechIndicatorStrategy
from src.strategy_engine.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategy_engine.strategies.volume_price_strategy import VolumePriceStrategy
from src.strategy_engine.strategies.trend_following_strategy import TrendFollowingStrategy

StrategyFactory.register(StrategyType.TECH_INDICATOR, TechIndicatorStrategy)
StrategyFactory.register(StrategyType.MEAN_REVERSION, MeanReversionStrategy)
StrategyFactory.register(StrategyType.VOLUME_PRICE, VolumePriceStrategy)
StrategyFactory.register(StrategyType.TREND_FOLLOWING, TrendFollowingStrategy)