"""主窗口：QSplitter+QTabWidget布局"""

import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QTabWidget, QTextEdit,
    QWidget, QVBoxLayout, QStatusBar, QAction, QMenuBar,
)
from PyQt5.QtCore import Qt

from src.core.config import Config
from src.core.constants import StrategyType
from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.data_layer.data_fetcher import DataFetcher
from src.data_layer.data_manager import DataManager
from src.data_layer.stock_info import StockInfo
from src.strategy_engine.strategy_factory import StrategyFactory
from src.strategy_engine.strategy_fusion import StrategyFusionEngine
from src.backtest_engine.trade_simulator import TradeSimulator
from src.backtest_engine.backtest_runner import BacktestRunner
from src.optimizer.grid_search import GridSearchOptimizer
from src.optimizer.genetic_optimizer import GeneticOptimizer
from src.signal_output.signal_generator import SignalGenerator
from src.signal_output.signal_persistence import SignalPersistence

from src.ui.kline_widget import KlineWidget
from src.ui.chart_toolbar import ChartToolbar
from src.ui.panels.stock_select_panel import StockSelectPanel
from src.ui.panels.strategy_config_panel import StrategyConfigPanel
from src.ui.panels.backtest_panel import BacktestPanel
from src.ui.panels.signal_panel import SignalPanel
from src.ui.panels.optimizer_panel import OptimizerPanel
from src.ui.panels.data_manage_panel import DataManagePanel
from src.ui.styles.dark_theme import DARK_THEME_STYLE
from src.ui.styles.light_theme import LIGHT_THEME_STYLE

logger = setup_logger("main_window")


class MainWindow(QMainWindow):
    """主窗口：左侧股票选择 + 右侧Tab面板 + 底部日志"""

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._current_symbol = ""

        # 保存worker引用，防止被垃圾回收
        self._worker = None

        # 初始化核心组件
        self._init_components()

        # 构建UI
        self._init_ui()
        self._connect_signals()

        # 应用主题
        self._apply_theme()

        logger.info("主窗口初始化完成")

    def _init_components(self) -> None:
        """初始化所有核心业务组件"""
        db_path = self._config.get_db_path()
        self._db = DatabaseManager(db_path)
        self._db.init_tables()

        self._fetcher = DataFetcher()
        self._data_mgr = DataManager(self._db, self._fetcher)
        self._stock_info = StockInfo(self._db, self._fetcher)

        # 创建策略
        strategies = StrategyFactory.create_all()
        weights = {
            k: v for k, v in self._config.fusion.get("weights", {}).items()
        }
        # 将字符串key转为StrategyType
        weight_map = {}
        for k, v in weights.items():
            stype = getattr(StrategyType, k.upper(), StrategyType.TECH_INDICATOR)
            weight_map[stype] = v

        self._fusion = StrategyFusionEngine(strategies, weight_map)
        self._simulator = TradeSimulator(
            initial_capital=self._config.backtest.get("initial_capital", 100000),
        )
        self._runner = BacktestRunner(self._data_mgr, self._simulator)
        self._grid_optimizer = GridSearchOptimizer(self._runner)
        self._genetic_optimizer = GeneticOptimizer(self._runner)
        self._signal_gen = SignalGenerator(self._fusion, self._data_mgr)
        self._persistence = SignalPersistence(self._db)
        
        # 进度对话框
        from src.ui.progress_dialog import ProgressDialog
        self._progress_dialog = ProgressDialog(self)
        self._progress_dialog.cancelled.connect(self._on_cancel_worker)

    def _init_ui(self) -> None:
        """构建UI布局"""
        ui_config = self._config.ui
        self.setWindowTitle("A股日线高抛低吸交易信号系统")
        self.resize(ui_config.get("window_width", 1400),
                    ui_config.get("window_height", 900))

        # 主分割器：左侧面板 + 右侧Tab
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：股票选择面板
        self._stock_panel = StockSelectPanel(self._data_mgr, self._stock_info)
        self._stock_panel.setMaximumWidth(ui_config.get("sidebar_width", 200))
        splitter.addWidget(self._stock_panel)

        # 右侧：Tab面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Tab页
        self._tabs = QTabWidget()

        # Tab1: K线图+信号
        kline_tab = QWidget()
        kline_tab_layout = QVBoxLayout(kline_tab)
        self._kline = KlineWidget()
        self._toolbar = ChartToolbar(self._kline)
        kline_tab_layout.addWidget(self._toolbar)
        kline_tab_layout.addWidget(self._kline)
        self._tabs.addTab(kline_tab, "K线图信号")

        # Tab2: 策略配置
        self._strategy_panel = StrategyConfigPanel(self._config)
        self._tabs.addTab(self._strategy_panel, "策略配置")

        # Tab3: 回测
        self._backtest_panel = BacktestPanel()
        self._tabs.addTab(self._backtest_panel, "回测")

        # Tab4: 参数优化
        self._optimizer_panel = OptimizerPanel()
        self._tabs.addTab(self._optimizer_panel, "参数优化")

        # Tab5: 信号展示
        self._signal_panel = SignalPanel()
        self._tabs.addTab(self._signal_panel, "信号")

        # Tab6: 数据管理
        self._data_panel = DataManagePanel(self._data_mgr, self._stock_info)
        self._tabs.addTab(self._data_panel, "数据管理")

        right_layout.addWidget(self._tabs)
        splitter.addWidget(right_widget)

        # 设置分割比例
        splitter.setSizes([200, 1200])

        # 主分割器：内容 + 日志
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(splitter)

        # 底部日志面板
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(ui_config.get("log_panel_height", 150))
        main_splitter.addWidget(self._log_text)

        main_splitter.setSizes([750, 150])

        self.setCentralWidget(main_splitter)

        # 状态栏
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")

    def _connect_signals(self) -> None:
        """连接所有信号"""
        self._stock_panel.stock_selected.connect(self._on_stock_selected)
        self._backtest_panel._start_btn.clicked.connect(self._on_start_backtest)
        self._backtest_panel.show_trades_on_chart.connect(self._on_show_trades_on_chart)
        self._backtest_panel.load_history_requested.connect(self._on_load_history_backtests)
        self._backtest_panel.history_record_selected.connect(self._on_history_backtest_selected)
        self._backtest_panel.delete_record_requested.connect(self._on_delete_backtest_record)
        self._optimizer_panel._start_btn.clicked.connect(self._on_start_optimize)
        self._optimizer_panel.apply_params.connect(self._on_apply_optimized_params)
        self._optimizer_panel.load_history_requested.connect(self._on_load_history_results)
        self._optimizer_panel.delete_record_requested.connect(self._on_delete_optimization_record)
        self._signal_panel._generate_btn.clicked.connect(self._on_generate_signals)
        self._signal_panel.show_on_chart.connect(self._on_show_signals_on_chart)
        self._signal_panel.load_history_signals.connect(self._on_load_history_signals)
        self._signal_panel.delete_signals_requested.connect(self._on_delete_signals)
        self._strategy_panel.config_applied.connect(self._on_config_applied)
        self._strategy_panel.save_config.connect(self._on_save_strategy_config)
        self._strategy_panel.load_config.connect(self._on_load_strategy_config)

    def _apply_theme(self) -> None:
        theme = self._config.ui.get("theme", "dark")
        if theme == "dark":
            self.setStyleSheet(DARK_THEME_STYLE)
        else:
            self.setStyleSheet(LIGHT_THEME_STYLE)
            
    def _show_progress(self, status_text, show_cancel=True):
        """显示进度对话框"""
        self._progress_dialog.set_status(status_text)
        self._progress_dialog.set_progress(0, None)
        self._progress_dialog.show_cancel_button(show_cancel)
        self._progress_dialog.show()
        
    def _hide_progress(self):
        """隐藏进度对话框"""
        self._progress_dialog.hide()
        
    def _on_cancel_worker(self):
        """取消工作线程"""
        if self._worker:
            self._worker.stop()
            self._log_text.append("任务已取消")
            self._hide_progress()

    def _on_stock_selected(self, symbol: str) -> None:
        """股票选中事件"""
        self._current_symbol = symbol
        self._statusbar.showMessage(f"当前股票: {symbol}")

        # 同步股票代码到优化面板和回测面板
        if hasattr(self._optimizer_panel, "_symbol_input"):
            self._optimizer_panel._symbol_input.setText(symbol)
        if hasattr(self._backtest_panel, "_symbol_input"):
            self._backtest_panel._symbol_input.setText(symbol)

        # 获取股票信息
        stock_info = self._stock_info.get_info(symbol)
        name = stock_info.get("name", "") if stock_info else ""

        # 获取数据并显示K线图（带技术指标）
        from datetime import datetime
        end_date = datetime.now().strftime("%Y-%m-%d")
        df = self._data_mgr.get_data_with_indicators(symbol, "2020-01-01", end_date)
        if not df.empty:
            self._kline.set_data(df, symbol=symbol, name=name)

    def _on_start_backtest(self) -> None:
        """开始回测"""
        config = self._backtest_panel.get_config()
        symbol = config["symbol"] or self._current_symbol
        if not symbol:
            return

        from src.ui.workers.workers import BacktestWorker, FusionBacktestWorker

        strategy_name = config["strategy"]
        if strategy_name == "融合策略":
            self._worker = FusionBacktestWorker(
                self._runner, symbol, self._fusion,
                config["start_date"], config["end_date"]
            )
        else:
            stype_map = {
                "技术指标": StrategyType.TECH_INDICATOR,
                "均值回归": StrategyType.MEAN_REVERSION,
                "量价分析": StrategyType.VOLUME_PRICE,
                "趋势跟踪": StrategyType.TREND_FOLLOWING,
            }
            stype = stype_map.get(strategy_name, StrategyType.TECH_INDICATOR)
            strategy = StrategyFactory.create(stype)
            self._worker = BacktestWorker(
                self._runner, symbol, strategy,
                config["start_date"], config["end_date"]
            )

        self._worker.log_signal.connect(self._log_text.append)
        self._worker.log_signal.connect(self._progress_dialog.set_status)
        self._worker.finished_signal.connect(self._on_backtest_finished)
        self._worker.start()
        self._show_progress(f"正在回测 {symbol}...", show_cancel=True)

    def _on_backtest_finished(self, success, result) -> None:
        """回测完成"""
        self._hide_progress()
        if success and result:
            self._backtest_panel.set_result(result)
            self._persistence.save_backtest_result(result)
            self._statusbar.showMessage(
                f"回测完成: 胜率={result.win_rate:.2%}, 夏普={result.sharpe_ratio:.2f}"
            )

    def _on_start_optimize(self) -> None:
        """开始优化"""
        config = self._optimizer_panel.get_config()
        symbol = config["symbol"] or self._current_symbol
        if not symbol:
            return

        from src.ui.workers.workers import OptimizerWorker
        from src.optimizer.param_space import ParamSpace

        stype_map = {
            "技术指标": StrategyType.TECH_INDICATOR,
            "均值回归": StrategyType.MEAN_REVERSION,
            "量价分析": StrategyType.VOLUME_PRICE,
            "趋势跟踪": StrategyType.TREND_FOLLOWING,
        }
        stype = stype_map.get(config["strategy"], StrategyType.TECH_INDICATOR)
        strategy = StrategyFactory.create(stype)
        param_space = ParamSpace(stype, strategy.get_param_ranges())

        metric_map = {
            "夏普比率": "sharpe_ratio",
            "胜率": "win_rate",
            "总收益率": "total_return",
            "盈亏比": "profit_loss_ratio",
        }
        metric = metric_map.get(config["metric"], "sharpe_ratio")

        if config["method"] == "网格搜索":
            optimizer = self._grid_optimizer
            kwargs = {}
        else:
            optimizer = self._genetic_optimizer
            kwargs = {
                "population_size": config["population_size"],
                "generations": config["generations"],
            }

        self._worker = OptimizerWorker(
            optimizer, symbol, strategy, param_space,
            "2020-01-01", "2025-12-31", metric, **kwargs
        )
        self._worker.log_signal.connect(self._log_text.append)
        self._worker.log_signal.connect(self._progress_dialog.set_status)
        self._worker.finished_signal.connect(self._on_optimize_finished)
        self._worker.start()
        self._show_progress(f"正在优化 {symbol} 策略参数...", show_cancel=True)

    def _on_optimize_finished(self, success, result) -> None:
        """优化完成"""
        self._hide_progress()
        if success and result:
            self._optimizer_panel.set_result(result)
            # 获取股票名称
            symbol_name = None
            try:
                stock_info = self._stock_info.get_info(result.symbol)
                if stock_info:
                    symbol_name = stock_info.get('name')
            except Exception as e:
                logger.warning(f"获取股票名称失败: {e}")
            # 保存优化结果，包含股票名称
            self._persistence.save_optimization_result(result, symbol_name)
            self._statusbar.showMessage(f"优化完成: 最佳指标值={result.best_metric_value:.4f}")

    def _on_apply_optimized_params(self, params: dict) -> None:
        """应用优化后的参数"""
        config = self._optimizer_panel.get_config()
        strategy_type = config.get("strategy", "")
        # 应用参数到策略配置面板
        self._strategy_panel.apply_params(params, strategy_type)
        # 自动切换到策略配置标签页
        self._tabs.setCurrentWidget(self._strategy_panel)
        self._statusbar.showMessage("已应用优化后的参数")

    def _on_load_history_results(self, symbol: str, strategy: str) -> None:
        """加载历史优化结果"""
        # 转换策略类型名称
        strategy_map = {
            "技术指标": "tech_indicator",
            "均值回归": "mean_reversion", 
            "量价分析": "volume_price",
            "趋势跟踪": "trend_following"
        }
        strategy_type = strategy_map.get(strategy)
        
        # 获取历史结果
        results = self._persistence.get_optimization_results(symbol, strategy_type)
        self._optimizer_panel.set_history_results(results)
        count = len(results)
        self._statusbar.showMessage(f"已加载 {count} 条历史优化结果")

    def _on_generate_signals(self) -> None:
        """生成信号"""
        if not self._current_symbol:
            return

        from src.ui.workers.workers import SignalWorker
        from datetime import datetime

        self._worker = SignalWorker(
            self._signal_gen, self._current_symbol,
            "2020-01-01", datetime.now().strftime("%Y-%m-%d")
        )
        self._worker.log_signal.connect(self._log_text.append)
        self._worker.log_signal.connect(self._progress_dialog.set_status)
        self._worker.finished_signal.connect(self._on_signals_generated)
        self._worker.start()
        self._show_progress(f"正在生成 {self._current_symbol} 的交易信号...", show_cancel=True)

    def _on_signals_generated(self, success, signals) -> None:
        """信号生成完成"""
        self._hide_progress()
        if success and signals:
            self._signal_panel.set_signals(signals, self._current_symbol)
            self._persistence.save_signals(signals)

    def _on_show_signals_on_chart(self, signals) -> None:
        """将信号标注到K线图"""
        if not self._current_symbol:
            return
        from datetime import datetime
        # 获取带指标的数据，确保显示效果一致
        df = self._data_mgr.get_data_with_indicators(
            self._current_symbol, "2020-01-01", datetime.now().strftime("%Y-%m-%d")
        )
        if not df.empty:
            # 获取股票名称
            stock_info = self._stock_info.get_info(self._current_symbol)
            name = stock_info.get("name", "") if stock_info else ""
            self._kline.set_data(df, signals, self._current_symbol, name)

    def _on_load_history_signals(self, symbol: str) -> None:
        """加载历史信号"""
        from datetime import datetime
        signals = self._persistence.load_fused_signals(
            symbol, "2020-01-01", datetime.now().strftime("%Y-%m-%d")
        )
        self._signal_panel.set_signals(signals, symbol)
        self._statusbar.showMessage(f"已加载 {len(signals)} 条历史信号")

    def _on_show_trades_on_chart(self, trades: list, symbol: str) -> None:
        """将回测交易记录标注到K线图"""
        if not symbol:
            symbol = self._current_symbol
        if not symbol:
            return
        
        from datetime import datetime
        # 获取带指标的数据
        df = self._data_mgr.get_data_with_indicators(
            symbol, "2020-01-01", datetime.now().strftime("%Y-%m-%d")
        )
        if df.empty:
            return
        
        # 获取股票名称
        stock_info = self._stock_info.get_info(symbol)
        name = stock_info.get("name", "") if stock_info else ""
        
        # 切换到K线图标签页
        self._tabs.setCurrentIndex(0)
        
        # 显示K线图并标注交易
        self._kline.set_data(df, signals=[], symbol=symbol, name=name, trades=trades)
        self._statusbar.showMessage(f"已在K线图上标注 {len(trades)} 笔交易")

    def _on_config_applied(self, config_dict) -> None:
        """策略配置应用"""
        # 更新策略参数
        for strategy in self._fusion.strategies:
            stype = strategy.strategy_type.value
            for key, value in config_dict.items():
                if key.startswith(f"{stype}_") and not key.endswith("_enabled"):
                    param_name = key.replace(f"{stype}_", "")
                    strategy.update_params({param_name: value})

        # 更新融合权重
        for key, value in config_dict.items():
            if key.startswith("fusion_"):
                wname = key.replace("fusion_", "")
                for stype in StrategyType:
                    if stype.value == wname:
                        self._fusion.weights[stype] = value
        
        self._statusbar.showMessage("策略配置已应用")
    
    def _on_save_strategy_config(self) -> None:
        """保存策略配置到数据库"""
        config_dict = self._strategy_panel.get_current_config()
        self._persistence.save_strategy_config(config_dict, self._current_symbol)
        self._statusbar.showMessage("策略配置已保存到数据库")
    
    def _on_load_strategy_config(self) -> None:
        """从数据库加载策略配置"""
        config_dict = self._persistence.load_strategy_config(self._current_symbol)
        if config_dict:
            self._strategy_panel.load_config_from_dict(config_dict)
            # 同时应用到策略
            self._on_config_applied(config_dict)
            self._statusbar.showMessage("策略配置已从数据库加载")
        else:
            self._statusbar.showMessage("数据库中没有找到保存的配置")
    
    def _on_load_history_backtests(self, symbol: str) -> None:
        """加载历史回测记录"""
        if not symbol:
            symbol = self._current_symbol
        if not symbol:
            self._statusbar.showMessage("请先选择或输入股票代码")
            return
        
        records = self._persistence.load_backtest_results(symbol)
        self._backtest_panel.set_history_records(records)
        self._statusbar.showMessage(f"已加载 {len(records)} 条历史回测记录")
    
    def _on_history_backtest_selected(self, record: dict) -> None:
        """历史回测记录被选中"""
        # 从数据库记录重建 BacktestResult 对象
        result = self._persistence.load_backtest_result_object(record)
        self._backtest_panel.set_result(result)
        self._statusbar.showMessage("已加载历史回测结果")
    
    def _on_delete_backtest_record(self, record_id: int) -> None:
        """删除回测记录"""
        try:
            count = self._persistence.delete_backtest_result(record_id)
            self._statusbar.showMessage(f"已删除 {count} 条回测记录")
        except Exception as e:
            self._statusbar.showMessage(f"删除回测记录失败: {e}")
    
    def _on_delete_optimization_record(self, record_id: int) -> None:
        """删除优化记录"""
        try:
            count = self._persistence.delete_optimization_result(record_id)
            self._statusbar.showMessage(f"已删除 {count} 条优化记录")
        except Exception as e:
            self._statusbar.showMessage(f"删除优化记录失败: {e}")
    
    def _on_delete_signals(self, symbol: str) -> None:
        """删除信号记录"""
        try:
            count = self._persistence.delete_signals_by_symbol(symbol)
            self._statusbar.showMessage(f"已删除 {count} 条信号记录")
        except Exception as e:
            self._statusbar.showMessage(f"删除信号记录失败: {e}")

    def closeEvent(self, event) -> None:
        self._db.close()
        event.accept()