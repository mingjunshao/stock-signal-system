# A股日线高抛低吸交易信号系统

> A comprehensive A-share stock trading signal generation and backtesting system

## 📋 目录

- [系统概述](#系统概述)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [使用指南](#使用指南)
- [开发说明](#开发说明)
- [常见问题](#常见问题)
- [免责声明](#免责声明)

---

## 系统概述

本系统是一套完整的A股交易信号分析工具，提供从数据获取、策略生成、回测验证、参数优化到信号输出的全流程支持。

### 核心特性

- 📊 **多策略融合** - 4种独立策略加权投票，灵活配置权重
- 🔍 **完整回测引擎** - A股T+1、涨跌停、佣金印花税真实模拟
- ⚙️ **智能参数优化** - 网格搜索 + 遗传算法，自动寻找最优参数
- 📈 **K线图可视化** - 交互式K线，支持信号标注、缩放、移动
- 💾 **完善数据管理** - SQLite持久化，历史信号和回测结果可追溯
- 🎨 **友好界面** - PyQt5 UI，深色/浅色主题切换

### 技术栈

| 组件 | 技术 |
|------|------|
| 数据来源 | akshare (A股历史行情) |
| 回测引擎 | 自研TradeSimulator |
| 可视化 | matplotlib + mplfinance |
| UI框架 | PyQt5 |
| 数据库 | SQLite3 |

---

## 功能特性

### 数据层
- ✅ 多数据源自动切换（腾讯/新浪/东方财富）
- ✅ 智能缓存与增量更新
- ✅ 数据校验与清洗
- ✅ 完整股票信息维护

### 策略层
- 📐 技术指标策略（MACD、KDJ、RSI、BOLL）
- 📉 均值回归策略（均线偏离度）
- 💰 量价分析策略（OBV、量价背离）
- 📈 趋势跟踪策略（均线系统、动量、ATR）
- 🎯 融合策略（加权投票机制）

### 回测引擎
- 📊 真实交易模拟（T+1、涨停跌停、佣金）
- 📈 完整绩效分析（胜率、盈亏比、夏普率、最大回撤）
- 📉 权益曲线与交易记录
- 🔄 历史回测结果保存与对比

### 优化器
- 🎛️ 网格搜索优化
- 🧬 遗传算法优化
- 💾 优化结果存档与应用
- 📊 优化过程可视化

---

## 快速开始

### 环境要求

- Python >= 3.10
- Windows 10/11 (推荐) / Linux / macOS

### 安装步骤

1. **克隆/下载项目**
```bash
cd stock_signal_system
```

2. **创建虚拟环境 (推荐)**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **运行系统**
```bash
python main.py
```

### 首次运行

1. 点击左侧「加股票」添加您关注的股票（如 688258、000001）
2. 在「K线图信号」标签页查看信号
3. 在「回测」标签页进行历史回测
4. 在「参数优化」标签页优化策略参数

---

## 项目结构

```
stock_signal_system/
├── src/
│   ├── core/                    # 核心基础组件
│   │   ├── config.py           # 配置管理
│   │   ├── constants.py        # 常量定义
│   │   ├── database.py         # 数据库管理
│   │   └── logger.py           # 日志模块
│   ├── data_layer/             # 数据获取层
│   │   ├── data_fetcher.py     # 多源数据获取
│   │   ├── data_manager.py     # 数据管理与缓存
│   │   └── stock_info.py       # 股票信息管理
│   ├── strategy_engine/        # 策略引擎
│   │   ├── strategies/         # 策略实现
│   │   ├── strategy_fusion.py  # 策略融合
│   │   └── signal.py           # 信号定义
│   ├── backtest_engine/        # 回测引擎
│   │   ├── trade_simulator.py  # 交易模拟
│   │   ├── performance_analyzer.py
│   │   └── backtest_runner.py
│   ├── optimizer/              # 参数优化
│   ├── signal_output/          # 信号输出与保存
│   └── ui/                     # 用户界面
├── data/                       # 数据目录
├── logs/                       # 日志目录
├── tests/                      # 测试用例
├── config.yaml                 # 配置文件
├── requirements.txt            # 依赖列表
└── main.py                     # 入口文件
```

---

## 使用指南

详细使用说明请参考：[用户手册.md](./用户手册.md)

### 基本工作流

```
选择股票 → 获取数据 → 配置策略 → 生成信号 → 回测验证 → 优化参数 → 实际使用
```

### 常用快捷键

| 功能 | 快捷键 |
|------|--------|
| 刷新K线图 | F5 |
| 切换主题 | Ctrl+T |
| 放大K线 | ↑ |
| 缩小K线 | ↓ |
| 左移K线 | ← |
| 右移K线 | → |

---

## 开发说明

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_strategies/ -v

# 生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

### 添加新策略

1. 在 `src/strategy_engine/strategies/` 下创建策略类
2. 继承 `BaseStrategy`
3. 实现 `generate_signals(df)` 方法
4. 在 `StrategyFactory` 中注册

### 代码规范

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 模块顶部添加文档字符串
- 使用统一的日志格式

---

## 常见问题

### 数据获取失败？
- 检查网络连接
- 尝试切换数据源（系统会自动降级）
- 查看 `logs/` 目录下的错误日志

### 回测结果与预期不符？
- 检查策略参数配置
- 确认交易成本设置（佣金、印花税）
- 查看交易记录表格，逐笔分析

### 程序启动失败？
- 确认 Python 版本 >= 3.10
- 检查依赖是否完整安装：`pip list`
- 查看控制台错误提示

更多FAQ请参考：[用户手册.md](./用户手册.md)

---

## 更新日志

### v1.1.0 (2026-05-22)
- ✨ 新增历史回测记录查看与删除
- ✨ 新增策略配置保存与加载
- ✨ 新增历史信号删除功能
- 🔧 修正均值回归策略阈值逻辑
- 🔧 增强SQL注入防护
- 📝 完善项目文档和测试

### v1.0.0 (2026-05-20)
- 🎉 初始版本发布
- 完整的策略、回测、优化功能

---

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎！

---

## 许可证

© 2026 Stock Signal System. All rights reserved.

## 致谢

- [akshare](https://github.com/akfamily/akshare) - A股数据源
- [mplfinance](https://github.com/matplotlib/mplfinance) - K线图绘制
- PyQt5 - UI框架
