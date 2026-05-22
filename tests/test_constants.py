"""
测试常量定义模块
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core.constants import (
    SignalType,
    SignalStrength,
    StrategyType,
    TradeAction,
    STRATEGY_DISPLAY_MAP,
    STRATEGY_REVERSE_MAP,
    OPTIMIZATION_METHOD_DISPLAY,
    OPTIMIZATION_METRIC_DISPLAY,
)


def test_signal_type_enum():
    """测试信号类型枚举"""
    assert SignalType.BUY == "buy"
    assert SignalType.SELL == "sell"
    assert SignalType.HOLD == "hold"
    
    # 验证枚举值正确
    assert SignalType.BUY.value == "buy"
    assert SignalType.SELL.value == "sell"


def test_strategy_type_enum():
    """测试策略类型枚举"""
    assert StrategyType.TECH_INDICATOR == "tech_indicator"
    assert StrategyType.MEAN_REVERSION == "mean_reversion"
    assert StrategyType.VOLUME_PRICE == "volume_price"
    assert StrategyType.TREND_FOLLOWING == "trend_following"
    assert StrategyType.FUSION == "fusion"


def test_strategy_display_mapping():
    """测试策略显示名称映射"""
    assert STRATEGY_DISPLAY_MAP[StrategyType.TECH_INDICATOR] == "技术指标"
    assert STRATEGY_DISPLAY_MAP[StrategyType.MEAN_REVERSION] == "均值回归"
    
    # 反向映射测试
    assert STRATEGY_REVERSE_MAP["技术指标"] == StrategyType.TECH_INDICATOR
    assert STRATEGY_REVERSE_MAP["均值回归"] == StrategyType.MEAN_REVERSION


def test_optimization_display_mapping():
    """测试优化相关显示映射"""
    from src.core.constants import OptimizationMethod, OptimizationMetric
    
    assert OPTIMIZATION_METHOD_DISPLAY[OptimizationMethod.GRID_SEARCH] == "网格搜索"
    assert OPTIMIZATION_METHOD_DISPLAY[OptimizationMethod.GENETIC] == "遗传算法"
    
    assert OPTIMIZATION_METRIC_DISPLAY[OptimizationMetric.WIN_RATE] == "胜率"
    assert OPTIMIZATION_METRIC_DISPLAY[OptimizationMetric.SHARPE_RATIO] == "夏普比率"


if __name__ == "__main__":
    test_signal_type_enum()
    test_strategy_type_enum()
    test_strategy_display_mapping()
    test_optimization_display_mapping()
    print("✓ 所有常量测试通过！")
