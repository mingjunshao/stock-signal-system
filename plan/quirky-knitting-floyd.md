# A股日线高抛低吸交易信号系统 - 实现计划

## Context

用户需要一个A股日线级别的交易信号系统，核心目标是：获取指定个股历史数据 → 回归测试 → 寻找最优交易参数 → 输出高抛低吸信号 → 分析交易成功率。采用多策略融合（技术指标+均值回归+量价分析+趋势跟踪），使用Python+PyQt5+mplfinance+SQLite+akshare实现。

---

## 项目结构

```
d:/claudeproject/stock_signal_system/
├── main.py                    # 入口
├── config.yaml                # 全局配置
├── requirements.txt           # 依赖
├── data/                      # SQLite数据库+缓存
├── output/                    # 回测结果+信号报告
├── logs/
├── src/
│   ├── core/                  # config, logger, database, constants
│   ├── data_layer/            # data_fetcher, data_manager, data_validator, stock_info
│   ├── strategy_engine/       # base_strategy, signal, indicator_calculator
│   │   └ategies/              # 4个具体策略实现
│   │   └── strategy_fusion, strategy_factory
│   ├── backtest_engine/       # backtest_runner, trade_simulator, performance_analyzer, backtest_result
│   ├── optimizer/             # grid_search, genetic_optimizer, param_space, optimization_result
│   ├── signal_output/         # signal_generator, signal_persistence, signal_report
│   ├── ui/                    # main_window, kline_widget, chart_toolbar
│   │   ├── panels/            # 6个功能面板
│   │   ├── dialogs/           # 3个对话框
│   │   ├── workers/           # 4个后台线程
│   │   └── styles/            # 深色/浅色主题
├── tests/
└── scripts/                   # 初始化脚本
```

---

## 实现步骤（按优先级分7个Phase）

### Phase 1: 基础框架
1. 创建项目目录结构
2. `src/core/config.py` - YAML配置管理（参考financereportV2模式）
3. `src/core/logger.py` - 日志管理
4. `src/core/database.py` - SQLite连接池+建表+CRUD
5. `src/core/constants.py` - SignalType/StrategyType等枚举
6. `config.yaml` - 默认配置（数据源、策略参数、回测参数、UI参数）
7. `requirements.txt` - akshare, mplfinance, matplotlib, deap, pyyaml
8. `main.py` + `MainWindow` 骨架

### Phase 2: 数据层
9. `src/data_layer/data_fetcher.py` - akshare获取A股日线数据，标准化列名
10. `src/data_layer/data_validator.py` - 缺失值/异常值清洗
11. `src/data_layer/data_manager.py` - 缓存调度+增量更新+数据库读写
12. `src/data_layer/stock_info.py` - 股票列表+搜索
13. `src/ui/panels/stock_select_panel.py` - 股票选择面板
14. `src/ui/workers/data_fetch_worker.py` - 后台数据获取线程

### Phase 3: 策略引擎
15. `src/strategy_engine/signal.py` - Signal + FusedSignal 数据结构
16. `src/strategy_engine/base_strategy.py` - 策略抽象基类
17. `src/strategy_engine/indicator_calculator.py` - 纯Python实现MACD/KDJ/RSI/BOLL/MA/VWAP/量比/OBV/支撑阻力/ATR
18. `src/strategy_engine/strategies/tech_indicator_strategy.py` - 技术指标组合策略
19. `src/strategy_engine/strategies/mean_reversion_strategy.py` - 均值回归策略
20. `src/strategy_engine/strategies/volume_price_strategy.py` - 量价分析策略
21. `src/strategy_engine/strategies/trend_following_strategy.py` - 趋势跟踪策略
22. `src/strategy_engine/strategy_fusion.py` - 加权投票融合引擎
23. `src/strategy_engine/strategy_factory.py` - 策略注册+动态创建

### Phase 4: K线图UI
24. `src/ui/kline_widget.py` - mplfinance嵌入PyQt5（FigureCanvasQTAgg），A股红涨绿跌样式
25. `src/ui/chart_toolbar.py` - 缩放/十字线/指标切换/信号显示/时间范围
26. 信号标注：买入↑红色三角、卖出↓绿色三角，强度用大小区分
27. 十字线追踪：鼠标移动显示日期/价格/成交量
28. `src/ui/panels/strategy_config_panel.py` - 策略参数配置面板

### Phase 5: 回测引擎
29. `src/backtest_engine/backtest_result.py` - TradeRecord + BacktestResult 数据结构
30. `src/backtest_engine/trade_simulator.py` - 模拟交易（A股T+1、佣金+印花税千一、涨跌停处理、最小100股）
31. `src/backtest_engine/performance_analyzer.py` - 胜率/盈亏比/最大回撤/夏普比率/年化收益
32. `src/backtest_engine/backtest_runner.py` - 协调策略→信号→模拟→分析
33. `src/ui/panels/backtest_panel.py` - 回测配置+结果展示+权益曲线
34. `src/ui/workers/backtest_worker.py` - 后台回测线程

### Phase 6: 参数优化
35. `src/optimizer/param_space.py` - 参数范围定义+网格点生成+编码/解码
36. `src/optimizer/grid_search.py` - 网格搜索（支持多进程并行）
37. `src/optimizer/genetic_optimizer.py` - DEAP遗传算法（锦标赛选择+两点交叉+高斯变异+精英保留）
38. `src/optimizer/optimization_result.py` - 优化结果数据结构
39. `src/ui/panels/optimizer_panel.py` - 优化配置+结果展示+参数-绩效散点图
40. `src/ui/workers/optimizer_worker.py` - 后台优化线程

### Phase 7: 信号输出与集成
41. `src/signal_output/signal_generator.py` - 协调策略→融合→最终信号
42. `src/signal_output/signal_persistence.py` - 信号/回测/优化结果写入SQLite
43. `src/signal_output/signal_report.py` - 文本报告生成
44. `src/ui/panels/signal_panel.py` - 信号展示面板
45. `src/ui/panels/data_manage_panel.py` - 数据管理面板
46. 全流程集成测试

---

## SQLite表结构（7张表）

1. **daily_kline** - 日线行情（symbol, date, open, high, low, close, volume, amount, turnover, adj_close）
2. **stock_info** - 股票基本信息（symbol, name, market, industry, is_tracked）
3. **strategy_params** - 策略参数（strategy_type, symbol, params_json, is_optimized）
4. **fusion_weights** - 融合权重（symbol, 4策略权重, buy/sell阈值）
5. **signal_records** - 信号记录（symbol, date, signal_type, strength, price, confidence, contributing_json）
6. **backtest_results** - 回测结果（symbol, strategy_type, params_json, 胜率/盈亏比/回撤/夏普等, trades_json）
7. **optimization_results** - 优化结果（symbol, strategy_type, method, best_params_json, best_metric_value）

---

## 策略融合算法

加权投票融合：
- 每日收集4策略信号
- buy_score = Σ(weight_i × confidence_i × strength_i) for BUY信号
- sell_score = Σ(weight_i × confidence_i × strength_i) for SELL信号
- net_score = buy_score - sell_score
- net_score ≥ buy_threshold(0.6) → BUY
- net_score ≤ sell_threshold(-0.6) → SELL
- else → HOLD
- 融合置信度 = |net_score| / Σ(weights)
- 3策略以上达成一致 → STRONG，2策略 → MEDIUM，1策略 → WEAK

---

## 关键技术决策

1. **K线图嵌入**: FigureCanvasQTAgg + mplfinance自定义style（A股红涨绿跌）
2. **技术指标**: 纯Python实现（pandas计算），不依赖TA-Lib（避免Windows编译问题）
3. **数据源**: akshare免费A股日线数据
4. **遗传算法**: DEAP库实现
5. **A股交易规则**: T+1、佣金万三+印花税千一（卖出）、最小100股、涨跌停信号失效处理

---

## 验证方式

1. 安装依赖: `pip install akshare mplfinance matplotlib deap pyyaml`
2. 运行 `python main.py` 启动GUI
3. 选择股票（如000001平安银行），获取历史数据
4. 配置策略参数，生成信号，查看K线图标注
5. 执行回测，验证胜率/盈亏比等指标
6. 执行参数优化，验证最优参数搜索
7. 查看SQLite数据库中持久化的信号和回测结果