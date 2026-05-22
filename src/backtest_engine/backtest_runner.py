"""回测执行器：协调策略→信号→模拟→分析"""

import pandas as pd
from typing import Dict, List, Optional

from src.core.constants import StrategyType
from src.core.logger import setup_logger
from src.data_layer.data_manager import DataManager
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.strategy_fusion import StrategyFusionEngine
from src.strategy_engine.signal import FusedSignal
from src.backtest_engine.backtest_result import BacktestResult, TradeRecord
from src.backtest_engine.trade_simulator import TradeSimulator
from src.backtest_engine.performance_analyzer import PerformanceAnalyzer

logger = setup_logger("backtest_runner")


class BacktestRunner:
    """回测执行器，协调策略→信号→模拟→绩效分析"""

    def __init__(self, data_manager: DataManager,
                 simulator: TradeSimulator) -> None:
        self._data_mgr = data_manager
        self._simulator = simulator
        self._analyzer = PerformanceAnalyzer()
    
    def _build_backtest_result(self, symbol: str, strategy_type: StrategyType,
                               params: Dict, start_date: str, end_date: str,
                               trades: List[TradeRecord],
                               equity_curve: List) -> BacktestResult:
        """构建回测结果对象"""
        metrics = self._analyzer.analyze(trades, equity_curve)
        return BacktestResult(
            symbol=symbol,
            strategy_type=strategy_type,
            params=params,
            start_date=start_date,
            end_date=end_date,
            trades=trades,
            total_trades=len(trades),
            win_trades=sum(1 for t in trades if t.profit > 0),
            loss_trades=sum(1 for t in trades if t.profit <= 0),
            win_rate=metrics.get("win_rate", 0),
            avg_profit_rate=metrics.get("avg_profit_rate", 0),
            profit_loss_ratio=metrics.get("profit_loss_ratio", 0),
            max_drawdown=metrics.get("max_drawdown", 0),
            max_drawdown_duration=metrics.get("max_drawdown_duration", 0),
            total_return=metrics.get("total_return", 0),
            annualized_return=metrics.get("annualized_return", 0),
            sharpe_ratio=metrics.get("sharpe_ratio", 0),
            equity_curve=equity_curve,
        )

    def run_backtest(self, symbol: str, strategy: BaseStrategy,
                     start_date: str, end_date: str,
                     params: Optional[Dict] = None) -> BacktestResult:
        """单策略回测"""
        if params:
            strategy.update_params(params)

        # 获取数据
        df = self._data_mgr.fetch_full_data(symbol, start_date, end_date)
        if df.empty:
            logger.error(f"回测数据获取失败: {symbol}")
            return BacktestResult(
                symbol=symbol, strategy_type=strategy.strategy_type,
                params=strategy.params, start_date=start_date, end_date=end_date,
            )

        # 生成信号
        signals = strategy.generate_signals(df)

        # 将Signal转换为FusedSignal（单策略回测时直接使用）
        fused_signals = [
            FusedSignal(
                date=s.date, symbol=s.symbol,
                signal_type=s.signal_type, strength=s.strength,
                price=s.price, confidence=s.confidence,
                contributing_strategies=[s.strategy_type],
                description=s.description,
            ) for s in signals
        ]

        # 模拟交易
        trades = self._simulator.simulate_trades(fused_signals, df)
        equity_curve = self._simulator.get_equity_curve(trades, df)

        # 构建结果
        result = self._build_backtest_result(
            symbol, strategy.strategy_type, strategy.params,
            start_date, end_date, trades, equity_curve
        )

        logger.info(f"回测完成: {symbol}, 胜率={result.win_rate:.2%}, 夏普={result.sharpe_ratio:.2f}")
        return result

    def run_fusion_backtest(self, symbol: str,
                            fusion_engine: StrategyFusionEngine,
                            start_date: str, end_date: str) -> BacktestResult:
        """融合策略回测"""
        df = self._data_mgr.fetch_full_data(symbol, start_date, end_date)
        if df.empty:
            return BacktestResult(
                symbol=symbol, strategy_type=StrategyType.FUSION,
                params={}, start_date=start_date, end_date=end_date,
            )

        # 各策略生成信号
        all_signals: Dict[StrategyType, list] = {}
        for strategy in fusion_engine.strategies:
            sigs = strategy.generate_signals(df)
            all_signals[strategy.strategy_type] = sigs

        # 融合信号
        fused_signals = fusion_engine.fuse_signals(all_signals, df)

        # 模拟交易
        trades = self._simulator.simulate_trades(fused_signals, df)
        equity_curve = self._simulator.get_equity_curve(trades, df)

        result = self._build_backtest_result(
            symbol, StrategyType.FUSION, {"weights": fusion_engine.get_weights()},
            start_date, end_date, trades, equity_curve
        )

        logger.info(f"融合回测完成: {symbol}, 胜率={result.win_rate:.2%}")
        return result