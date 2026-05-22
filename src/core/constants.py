"""信号类型、策略类型、交易动作等枚举常量"""

from enum import Enum


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SignalStrength(Enum):
    STRONG = 3
    MEDIUM = 2
    WEAK = 1


class StrategyType(Enum):
    TECH_INDICATOR = "tech_indicator"
    MEAN_REVERSION = "mean_reversion"
    VOLUME_PRICE = "volume_price"
    TREND_FOLLOWING = "trend_following"
    FUSION = "fusion"


class TradeAction(Enum):
    OPEN_LONG = "open_long"
    CLOSE_LONG = "close_long"


class BacktestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationMethod(Enum):
    GRID_SEARCH = "grid_search"
    GENETIC = "genetic"


class OptimizationMetric(Enum):
    WIN_RATE = "win_rate"
    SHARPE_RATIO = "sharpe_ratio"
    TOTAL_RETURN = "total_return"
    PROFIT_LOSS_RATIO = "profit_loss_ratio"
    COMPOSITE_SCORE = "composite_score"


# A股交易规则常量
COMMISSION_RATE = 0.0003       # 佣金率万三
STAMP_TAX_RATE = 0.001        # 印花税千一（仅卖出）
MIN_COMMISSION = 5.0           # 最低佣金5元
MIN_LOT_SIZE = 100             # 最小交易单位100股
LIMIT_UP_THRESHOLD = 0.10      # 涨停阈值10%
LIMIT_DOWN_THRESHOLD = -0.10   # 跌停阈值-10%
ST_LIMIT_UP = 0.05             # ST股涨停5%
ST_LIMIT_DOWN = -0.05          # ST股跌停-5%
BOARD_LIMIT_UP = 0.20          # 创业板/科创板涨停20%
BOARD_LIMIT_DOWN = -0.20       # 创业板/科创板跌停-20%

# 策略类型显示名称映射
STRATEGY_DISPLAY_MAP = {
    StrategyType.TECH_INDICATOR: "技术指标",
    StrategyType.MEAN_REVERSION: "均值回归",
    StrategyType.VOLUME_PRICE: "量价分析",
    StrategyType.TREND_FOLLOWING: "趋势跟踪",
    StrategyType.FUSION: "融合策略",
}

# 策略类型反向映射（从显示名称到类型）
STRATEGY_REVERSE_MAP = {v: k for k, v in STRATEGY_DISPLAY_MAP.items()}

# 优化方法显示名称映射
OPTIMIZATION_METHOD_DISPLAY = {
    OptimizationMethod.GRID_SEARCH: "网格搜索",
    OptimizationMethod.GENETIC: "遗传算法",
}

# 优化目标显示名称映射
OPTIMIZATION_METRIC_DISPLAY = {
    OptimizationMetric.WIN_RATE: "胜率",
    OptimizationMetric.SHARPE_RATIO: "夏普比率",
    OptimizationMetric.TOTAL_RETURN: "总收益率",
    OptimizationMetric.PROFIT_LOSS_RATIO: "盈亏比",
    OptimizationMetric.COMPOSITE_SCORE: "综合得分",
}