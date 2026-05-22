"""网格搜索优化器"""

import time
from typing import Dict, Optional

from src.core.constants import StrategyType
from src.core.logger import setup_logger
from src.strategy_engine.base_strategy import BaseStrategy
from src.backtest_engine.backtest_runner import BacktestRunner
from src.optimizer.param_space import ParamSpace
from src.optimizer.optimization_result import OptimizationResult

logger = setup_logger("grid_search")


class GridSearchOptimizer:
    """网格搜索参数优化"""

    def __init__(self, backtest_runner: BacktestRunner) -> None:
        self._runner = backtest_runner

    def optimize(self, symbol: str, strategy: BaseStrategy,
                 param_space: ParamSpace,
                 start_date: str, end_date: str,
                 metric: str = "sharpe_ratio",
                 max_combinations: int = 500) -> OptimizationResult:
        """网格搜索所有参数组合"""
        start_time = time.time()

        grid_points = param_space.get_grid_points()
        if len(grid_points) > max_combinations:
            logger.warning(f"参数组合过多({len(grid_points)}), 限制为{max_combinations}")
            grid_points = grid_points[:max_combinations]

        all_results = []
        best_metric = float("-inf")
        best_params = {}

        for i, params in enumerate(grid_points):
            logger.info(f"网格搜索进度: {i + 1}/{len(grid_points)}")

            result = self._runner.run_backtest(
                symbol, strategy, start_date, end_date, params
            )

            metric_value = getattr(result, metric, 0)
            all_results.append({
                "params": params,
                "metric_value": metric_value,
                "win_rate": result.win_rate,
                "sharpe_ratio": result.sharpe_ratio,
                "total_return": result.total_return,
            })

            if metric_value > best_metric:
                best_metric = metric_value
                best_params = params

        elapsed = time.time() - start_time
        logger.info(f"网格搜索完成: 最优参数={best_params}, {metric}={best_metric:.4f}")

        return OptimizationResult(
            strategy_type=strategy.strategy_type,
            symbol=symbol,
            best_params=best_params,
            best_metric_value=best_metric,
            metric_name=metric,
            all_results=all_results,
            optimization_method="grid_search",
            elapsed_time=elapsed,
        )