"""遗传算法优化器：使用DEAP库"""

import time
import random
from typing import Dict

from deap import base, creator, tools, algorithms

from src.core.logger import setup_logger
from src.strategy_engine.base_strategy import BaseStrategy
from src.backtest_engine.backtest_runner import BacktestRunner
from src.optimizer.param_space import ParamSpace
from src.optimizer.optimization_result import OptimizationResult

logger = setup_logger("genetic_optimizer")


class GeneticOptimizer:
    """遗传算法参数优化（DEAP实现）"""

    def __init__(self, backtest_runner: BacktestRunner) -> None:
        self._runner = backtest_runner

    def optimize(self, symbol: str, strategy: BaseStrategy,
                 param_space: ParamSpace,
                 start_date: str, end_date: str,
                 metric: str = "sharpe_ratio",
                 population_size: int = 50,
                 generations: int = 30,
                 crossover_rate: float = 0.7,
                 mutation_rate: float = 0.2) -> OptimizationResult:
        """遗传算法优化"""
        start_time = time.time()

        # 清理之前可能残留的creator类型
        if hasattr(creator, "FitnessMax"):
            del creator.FitnessMax
        if hasattr(creator, "Individual"):
            del creator.Individual

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        param_count = len(param_space.ranges)

        toolbox.register("attr_float", random.random)
        toolbox.register("individual", tools.initRepeat,
                         creator.Individual, toolbox.attr_float, n=param_count)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        def fitness_function(individual):
            params = param_space.decode_vector(individual)
            result = self._runner.run_backtest(
                symbol, strategy, start_date, end_date, params
            )
            metric_value = getattr(result, metric, 0)
            return (metric_value,)

        toolbox.register("evaluate", fitness_function)

        pop = toolbox.population(n=population_size)
        hof = tools.HallOfFame(1)

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", lambda x: sum(v[0] for v in x) / len(x))
        stats.register("max", lambda x: max(v[0] for v in x))

        logger.info(f"遗传算法开始: 群体={population_size}, 代数={generations}")

        algorithms.eaSimple(
            pop, toolbox,
            cxpb=crossover_rate, mutpb=mutation_rate,
            ngen=generations, stats=stats, halloffame=hof,
            verbose=False,
        )

        best_individual = hof[0]
        best_params = param_space.decode_vector(best_individual)
        best_metric = best_individual.fitness.values[0]

        elapsed = time.time() - start_time
        logger.info(f"遗传算法完成: 最优参数={best_params}, {metric}={best_metric:.4f}")

        return OptimizationResult(
            strategy_type=strategy.strategy_type,
            symbol=symbol,
            best_params=best_params,
            best_metric_value=best_metric,
            metric_name=metric,
            all_results=[],
            optimization_method="genetic",
            elapsed_time=elapsed,
        )