"""信号报告生成器"""

from pathlib import Path
from typing import List

from src.backtest_engine.backtest_result import BacktestResult
from src.backtest_engine.performance_analyzer import PerformanceAnalyzer
from src.strategy_engine.signal import FusedSignal
from src.core.constants import SignalType

_analyzer = PerformanceAnalyzer()


def generate_signal_report(signals: List[FusedSignal], symbol: str) -> str:
    """生成信号报告"""
    buy_count = sum(1 for s in signals if s.signal_type == SignalType.BUY)
    sell_count = sum(1 for s in signals if s.signal_type == SignalType.SELL)
    hold_count = sum(1 for s in signals if s.signal_type == SignalType.HOLD)

    lines = [
        f"=== 信号报告 ===",
        f"股票: {symbol}",
        f"信号总数: {len(signals)}",
        f"买入信号: {buy_count}",
        f"卖出信号: {sell_count}",
        f"持有信号: {hold_count}",
        f"",
        f"--- 信号明细 ---",
    ]

    for sig in signals[-20:]:  # 最近20条
        lines.append(
            f"{sig.date} | {sig.signal_type.value} | "
            f"强度={sig.strength.value} | 置信度={sig.confidence:.2f} | "
            f"价格={sig.price:.2f} | {sig.description}"
        )

    return "\n".join(lines)


def generate_backtest_report(result: BacktestResult) -> str:
    """生成回测报告"""
    return _analyzer.generate_report(result)


def save_report(content: str, output_dir: Path, filename: str) -> Path:
    """保存报告到文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath