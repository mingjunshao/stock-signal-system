#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行脚本（简化版）
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


print("=" * 60)
print("A股日线高抛低吸交易信号系统 - 测试套件")
print("=" * 60)


# 逐个测试模块
def test_constants():
    """测试常量模块"""
    print("\n[测试 1] 常量定义模块...")
    
    from src.core.constants import (
        SignalType, StrategyType,
        STRATEGY_DISPLAY_MAP, STRATEGY_REVERSE_MAP,
    )
    
    # 验证枚举
    assert SignalType.BUY.value == "buy"
    assert StrategyType.TECH_INDICATOR.value == "tech_indicator"
    
    # 验证映射
    assert STRATEGY_DISPLAY_MAP[StrategyType.TECH_INDICATOR] == "技术指标"
    assert STRATEGY_REVERSE_MAP["技术指标"] == StrategyType.TECH_INDICATOR
    
    print("  [OK] 常量测试通过")
    return True


def test_mean_reversion_strategy():
    """测试均值回归策略"""
    print("\n[测试 2] 均值回归策略...")
    
    from src.strategy_engine.strategies.mean_reversion_strategy import MeanReversionStrategy
    
    strategy = MeanReversionStrategy()
    
    # 验证默认参数
    assert strategy.strategy_type.value == "mean_reversion"
    assert strategy.params["deviation_threshold"] > 0
    assert strategy.params["deviation_threshold"] == 2.0, "默认阈值应该是2.0（表示2%）"
    
    # 验证参数更新
    strategy.params["deviation_threshold"] = 3.0
    assert strategy.params["deviation_threshold"] == 3.0
    
    print("  [OK] 均值回归策略测试通过")
    return True


def test_database():
    """测试数据库模块"""
    print("\n[测试 3] 数据库模块...")
    
    from src.core.database import DatabaseManager
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        db = DatabaseManager(db_path)
        db.init_tables()
        
        # 验证表存在
        assert db.table_exists("daily_kline")
        assert db.table_exists("backtest_results")
        assert db.table_exists("optimization_results")
        
        # 验证SQL注入防护
        try:
            db.insert_batch("invalid_table", [])
            assert False, "应该抛出异常"
        except ValueError as e:
            assert "Invalid table name" in str(e)
        
        db.close()
        print("  [OK] 数据库测试通过")
        return True
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


def test_performance_analyzer():
    """测试绩效分析模块"""
    print("\n[测试 4] 绩效分析模块...")
    
    from src.backtest_engine.performance_analyzer import PerformanceAnalyzer
    
    analyzer = PerformanceAnalyzer()
    
    # 测试空交易 - 返回空字典
    metrics = analyzer.analyze([], [])
    assert isinstance(metrics, dict)
    
    # 测试一些基本的计算方法
    assert analyzer.calc_win_rate([]) == 0.0
    assert analyzer.calc_avg_profit_rate([]) == 0.0
    assert analyzer.calc_total_return([]) == 0.0
    
    print("  [OK] 绩效分析测试通过")
    return True


# 运行所有测试
print("\n开始运行测试...\n")

results = []

results.append(("常量模块", test_constants()))
results.append(("均值回归策略", test_mean_reversion_strategy()))
results.append(("数据库模块", test_database()))
results.append(("绩效分析", test_performance_analyzer()))


print("\n" + "=" * 60)
print("测试汇总")
print("=" * 60)

for name, ok in results:
    status = "PASS" if ok else "FAIL"
    print(f"  {name}: {status}")

passed = sum(1 for name, ok in results if ok)
print(f"\n总计: {len(results)} 个, 通过: {passed} 个")

if passed == len(results):
    print("\n所有测试通过！")
else:
    print("\n部分测试失败，请检查")
