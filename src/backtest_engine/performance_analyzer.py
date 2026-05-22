"""绩效分析器：胜率、盈亏比、最大回撤、夏普比率、年化收益"""

import math
from typing import Dict, List, Tuple

from src.backtest_engine.backtest_result import TradeRecord, BacktestResult
from src.core.logger import setup_logger

logger = setup_logger("performance_analyzer")


class PerformanceAnalyzer:
    """绩效分析器"""

    def analyze(self, trades: List[TradeRecord],
                equity_curve: List[Tuple[str, float]]) -> Dict[str, float]:
        """计算所有绩效指标"""
        if not trades:
            return {}

        return {
            "win_rate": self.calc_win_rate(trades),
            "profit_loss_ratio": self.calc_profit_loss_ratio(trades),
            "max_drawdown": self.calc_max_drawdown(equity_curve)[0],
            "max_drawdown_duration": self.calc_max_drawdown(equity_curve)[1],
            "avg_profit_rate": self.calc_avg_profit_rate(trades),
            "total_return": self.calc_total_return(equity_curve),
            "annualized_return": self.calc_annualized_return(equity_curve),
            "sharpe_ratio": self.calc_sharpe_ratio(equity_curve),
        }

    def calc_win_rate(self, trades: List[TradeRecord]) -> float:
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t.profit > 0)
        return wins / len(trades)

    def calc_profit_loss_ratio(self, trades: List[TradeRecord]) -> float:
        wins = [t.profit_rate for t in trades if t.profit > 0]
        losses = [abs(t.profit_rate) for t in trades if t.profit <= 0]
        if not wins or not losses:
            return 0.0
        avg_win = sum(wins) / len(wins)
        avg_loss = sum(losses) / len(losses)
        return avg_win / avg_loss if avg_loss > 0 else 0.0

    def calc_max_drawdown(self, equity_curve: List[Tuple[str, float]]) -> Tuple[float, int]:
        if not equity_curve:
            return (0.0, 0)

        peak = equity_curve[0][1]
        max_dd = 0.0
        dd_duration = 0
        current_dd_duration = 0

        for i, (_, equity) in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                current_dd_duration = 0
            else:
                dd = (peak - equity) / peak
                current_dd_duration += 1
                if dd > max_dd:
                    max_dd = dd
                    dd_duration = current_dd_duration

        return (max_dd, dd_duration)

    def calc_sharpe_ratio(self, equity_curve: List[Tuple[str, float]],
                          risk_free_rate: float = 0.03) -> float:
        if len(equity_curve) < 2:
            return 0.0

        daily_returns = []
        for i in range(1, len(equity_curve)):
            prev = equity_curve[i - 1][1]
            curr = equity_curve[i][1]
            if prev > 0:
                daily_returns.append((curr - prev) / prev)

        if not daily_returns:
            return 0.0

        avg_return = sum(daily_returns) / len(daily_returns)
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns))

        if std_return == 0:
            return 0.0

        daily_rf = risk_free_rate / 252
        return (avg_return - daily_rf) / std_return * math.sqrt(252)

    def calc_annualized_return(self, equity_curve: List[Tuple[str, float]]) -> float:
        if len(equity_curve) < 2:
            return 0.0
        initial = equity_curve[0][1]
        final = equity_curve[-1][1]
        days = len(equity_curve)
        total_return = (final - initial) / initial
        return total_return * (252 / days)

    def calc_total_return(self, equity_curve: List[Tuple[str, float]]) -> float:
        if len(equity_curve) < 2:
            return 0.0
        initial = equity_curve[0][1]
        final = equity_curve[-1][1]
        return (final - initial) / initial

    def calc_avg_profit_rate(self, trades: List[TradeRecord]) -> float:
        if not trades:
            return 0.0
        return sum(t.profit_rate for t in trades) / len(trades)

    def generate_report(self, result: BacktestResult) -> str:
        """生成文本格式的回测报告"""
        lines = [
            f"=== 回测报告 ===",
            f"股票: {result.symbol}",
            f"策略: {result.strategy_type.value}",
            f"时间: {result.start_date} ~ {result.end_date}",
            f"参数: {result.params}",
            f"",
            f"总交易次数: {result.total_trades}",
            f"盈利次数: {result.win_trades}",
            f"亏损次数: {result.loss_trades}",
            f"胜率: {result.win_rate:.2%}",
            f"平均盈亏率: {result.avg_profit_rate:.2f}%",  # 直接显示百分比值
            f"盈亏比: {result.profit_loss_ratio:.2f}",
            f"最大回撤: {result.max_drawdown:.2%}",
            f"最大回撤持续: {result.max_drawdown_duration}天",
            f"总收益率: {result.total_return:.2%}",
            f"年化收益率: {result.annualized_return:.2%}",
            f"夏普比率: {result.sharpe_ratio:.2f}",
        ]
        return "\n".join(lines)