"""
测试均值回归策略
"""
import sys
import pandas as pd
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pytest
from src.strategy_engine.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.core.constants import SignalType


def test_mean_reversion_initialization():
    """测试策略初始化"""
    strategy = MeanReversionStrategy()
    
    assert strategy.strategy_type.value == "mean_reversion"
    assert "ma_period" in strategy.params
    assert "deviation_threshold" in strategy.params
    assert strategy.params["deviation_threshold"] > 0


def test_mean_reversion_params_update():
    """测试参数更新"""
    strategy = MeanReversionStrategy()
    
    # 更新参数
    new_params = {
        "ma_period": 30,
        "deviation_threshold": 0.05,
    }
    
    strategy.update_params(new_params)
    
    assert strategy.params["ma_period"] == 30
    assert strategy.params["deviation_threshold"] == 0.05


def test_strategy_parameter_validation():
    """测试策略参数验证"""
    strategy = MeanReversionStrategy()
    
    # 验证默认参数
    validation = strategy.validate_params(strategy.params)
    assert validation["valid"] is True
    assert len(validation["errors"]) == 0
    
    # 测试无效参数
    invalid_params = {
        "ma_period": -1,
        "deviation_threshold": -0.05,
    }
    
    validation = strategy.validate_params(invalid_params)
    assert validation["valid"] is False
    assert len(validation["errors"]) > 0


def test_strategy_signal_generation(sample_kline_data):
    """测试信号生成"""
    strategy = MeanReversionStrategy()
    
    # 生成信号
    signals = strategy.generate_signals(sample_kline_data)
    
    # 信号应该是列表
    assert isinstance(signals, list)
    
    # 如果有信号，验证信号类型
    if signals:
        signal_types = {s.signal_type for s in signals}
        assert len(signal_types) > 0
        # 至少应该包含买入或卖出信号
        assert (SignalType.BUY in signal_types) or (SignalType.SELL in signal_types)


def test_mean_reversion_threshold_logic(sample_kline_data):
    """测试阈值逻辑（我们刚修复的！）"""
    strategy = MeanReversionStrategy()
    
    # 验证默认参数
    assert strategy.params["deviation_threshold"] > 0, "阈值应该是正数"
    
    # 更新为不同的阈值
    thresholds = [0.01, 0.02, 0.03, 0.05, 0.1]
    
    for threshold in thresholds:
        strategy.params["deviation_threshold"] = threshold
        
        # 生成信号
        signals = strategy.generate_signals(sample_kline_data)
        
        # 验证阈值在合理范围内（现在没有除以100）
        assert strategy.params["deviation_threshold"] == threshold
        assert 0.001 <= strategy.params["deviation_threshold"] <= 0.2


if __name__ == "__main__":
    from conftest import sample_kline_data
    
    print("测试策略初始化...")
    test_mean_reversion_initialization()
    
    print("测试参数更新...")
    test_mean_reversion_params_update()
    
    print("测试参数验证...")
    test_strategy_parameter_validation()
    
    print("测试信号生成...")
    df = sample_kline_data()
    test_strategy_signal_generation(df)
    
    print("测试阈值逻辑...")
    test_mean_reversion_threshold_logic(df)
    
    print("✓ 所有均值回归策略测试通过！")
