"""
测试绩效分析模块
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.backtest_engine.performance_analyzer import PerformanceAnalyzer
from src.backtest_engine.backtest_result import TradeRecord
from src.core.constants import SignalType


def test_empty_trades_analysis():
    """测试无交易时的分析"""
    analyzer = PerformanceAnalyzer()
    trades = []
    equity_curve = []
    
    metrics = analyzer.analyze(trades, equity_curve)
    
    assert metrics["total_trades"] == 0
    assert metrics["win_trades"] == 0
    assert metrics["loss_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["total_return"] == 0.0


def test_profitable_trades_analysis(sample_trade_records):
    """测试有交易的分析"""
    analyzer = PerformanceAnalyzer()
    
    # 构建 TradeRecord 对象
    trades = []
    for record in sample_trade_records:
        trades.append(TradeRecord(
            entry_date=record["entry_date"],
            entry_price=record["entry_price"],
            exit_date=record["exit_date"],
            exit_price=record["exit_price"],
            signal_type=SignalType.SELL,
            profit=record["profit"],
            profit_rate=record["profit_rate"],
            holding_days=record["holding_days"],
        ))
    
    # 创建简单的权益曲线
    equity_curve = [
        ("2020-01-01", 100000.0),
        ("2020-01-10", 100000.0),
        ("2020-01-20", 100950.0),
        ("2020-02-01", 100950.0),
        ("2020-02-15", 99900.0),
    ]
    
    metrics = analyzer.analyze(trades, equity_curve)
    
    # 验证基本指标
    assert metrics["total_trades"] == 2
    assert metrics["win_trades"] == 1
    assert metrics["loss_trades"] == 1
    assert metrics["win_rate"] == 0.5  # 1/2
    assert isinstance(metrics["avg_profit_rate"], float)
    
    # 验证报告生成
    report = analyzer.generate_report(metrics, trades)
    assert "回测报告" in report
    assert "胜率" in report
    assert "夏普比率" in report


def test_trade_statistics(sample_trade_records):
    """测试交易统计"""
    analyzer = PerformanceAnalyzer()
    
    trades = []
    for record in sample_trade_records:
        trades.append(TradeRecord(
            entry_date=record["entry_date"],
            entry_price=record["entry_price"],
            exit_date=record["exit_date"],
            exit_price=record["exit_price"],
            signal_type=SignalType.SELL,
            profit=record["profit"],
            profit_rate=record["profit_rate"],
            holding_days=record["holding_days"],
        ))
    
    # 验证统计计算
    win_trades = [t for t in trades if t.profit > 0]
    loss_trades = [t for t in trades if t.profit <= 0]
    
    assert len(win_trades) == 1
    assert len(loss_trades) == 1


if __name__ == "__main__":
    from conftest import sample_trade_records
    
    test_empty_trades_analysis()
    test_profitable_trades_analysis(sample_trade_records())
    test_trade_statistics(sample_trade_records())
    print("✓ 所有绩效分析测试通过！")
