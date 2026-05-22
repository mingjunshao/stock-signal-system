"""回测面板：配置+结果展示+权益曲线"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDateEdit, QComboBox, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QLabel, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
)
from PyQt5.QtCore import pyqtSignal, QDate

from src.backtest_engine.backtest_result import BacktestResult


class BacktestPanel(QWidget):
    """回测配置与结果展示面板"""

    backtest_completed = pyqtSignal(BacktestResult)
    show_trades_on_chart = pyqtSignal(object, str)  # (trades, symbol)
    load_history_requested = pyqtSignal(str)  # (symbol)
    history_record_selected = pyqtSignal(object)  # (backtest_record)
    delete_record_requested = pyqtSignal(int)  # (record_id)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_result = None
        self._history_records = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 配置区
        config_group = QGroupBox("回测配置")
        config_layout = QFormLayout()

        self._symbol_input = QLineEdit()
        self._symbol_input.setPlaceholderText("股票代码，如 000001")
        config_layout.addRow("股票:", self._symbol_input)

        self._start_date = QDateEdit(QDate(2020, 1, 1))
        self._start_date.setCalendarPopup(True)
        config_layout.addRow("开始日期:", self._start_date)

        self._end_date = QDateEdit(QDate.currentDate())
        self._end_date.setCalendarPopup(True)
        config_layout.addRow("结束日期:", self._end_date)

        self._strategy_combo = QComboBox()
        self._strategy_combo.addItems(["融合策略", "技术指标", "均值回归", "量价分析", "趋势跟踪"])
        config_layout.addRow("策略:", self._strategy_combo)

        self._capital_spin = QDoubleSpinBox()
        self._capital_spin.setRange(10000, 10000000)
        self._capital_spin.setValue(100000)
        self._capital_spin.setSingleStep(10000)
        config_layout.addRow("初始资金:", self._capital_spin)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        # 开始按钮
        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton("开始回测")
        self._load_history_btn = QPushButton("加载历史回测")
        self._load_history_btn.clicked.connect(self._on_load_history)
        btn_layout.addWidget(self._start_btn)
        btn_layout.addWidget(self._load_history_btn)
        layout.addLayout(btn_layout)

        # 历史记录区
        history_group = QGroupBox("历史回测记录")
        history_layout = QVBoxLayout()

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(8)
        self._history_table.setHorizontalHeaderLabels([
            "时间", "策略", "开始日期", "结束日期",
            "交易次数", "胜率", "总收益", "夏普比率"
        ])
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._history_table.setMaximumHeight(200)
        self._history_table.itemSelectionChanged.connect(self._on_history_selected)
        history_layout.addWidget(self._history_table)
        
        # 历史记录操作按钮
        history_btn_layout = QHBoxLayout()
        self._delete_history_btn = QPushButton("删除选中记录")
        self._delete_history_btn.setEnabled(False)
        self._delete_history_btn.clicked.connect(self._on_delete_history)
        history_btn_layout.addWidget(self._delete_history_btn)
        history_layout.addLayout(history_btn_layout)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # 结果区
        result_group = QGroupBox("回测结果")
        result_layout = QVBoxLayout()

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMaximumHeight(250)
        result_layout.addWidget(self._result_text)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # 交易记录区
        trades_group = QGroupBox("交易记录")
        trades_layout = QVBoxLayout()

        self._trades_table = QTableWidget()
        self._trades_table.setColumnCount(7)
        self._trades_table.setHorizontalHeaderLabels([
            "入场日期", "入场价格", "出场日期", "出场价格",
            "盈亏(元)", "盈亏率", "持仓天数"
        ])
        self._trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._trades_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._trades_table.setSelectionBehavior(QTableWidget.SelectRows)
        trades_layout.addWidget(self._trades_table)

        # 交易记录操作按钮
        trades_btn_layout = QHBoxLayout()
        self._show_trades_btn = QPushButton("标注交易到K线图")
        self._show_trades_btn.setEnabled(False)
        self._show_trades_btn.clicked.connect(self._on_show_trades_on_chart)
        trades_btn_layout.addWidget(self._show_trades_btn)
        trades_layout.addLayout(trades_btn_layout)

        trades_group.setLayout(trades_layout)
        layout.addWidget(trades_group)

    def set_progress(self, value: int) -> None:
        self._progress.setValue(value)

    def set_result(self, result: BacktestResult) -> None:
        self._current_result = result
        from src.backtest_engine.performance_analyzer import PerformanceAnalyzer
        analyzer = PerformanceAnalyzer()
        self._result_text.setText(analyzer.generate_report(result))
        
        # 更新交易记录表格
        self._update_trades_table(result.trades)
        self._show_trades_btn.setEnabled(len(result.trades) > 0)

    def _update_trades_table(self, trades: list) -> None:
        """更新交易记录表格"""
        self._trades_table.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            # 入场日期
            self._trades_table.setItem(row, 0, QTableWidgetItem(trade.entry_date))
            # 入场价格
            self._trades_table.setItem(row, 1, QTableWidgetItem(f"{trade.entry_price:.2f}"))
            # 出场日期
            self._trades_table.setItem(row, 2, QTableWidgetItem(trade.exit_date))
            # 出场价格
            self._trades_table.setItem(row, 3, QTableWidgetItem(f"{trade.exit_price:.2f}"))
            # 盈亏
            profit_item = QTableWidgetItem(f"{trade.profit:.2f}")
            if trade.profit >= 0:
                profit_item.setForeground(self._trades_table.palette().link())  # 绿色
            else:
                profit_item.setForeground(self._trades_table.palette().highlight())  # 红色
            self._trades_table.setItem(row, 4, profit_item)
            # 盈亏率
            profit_rate_item = QTableWidgetItem(f"{trade.profit_rate:.2f}%")
            if trade.profit_rate >= 0:
                profit_rate_item.setForeground(self._trades_table.palette().link())
            else:
                profit_rate_item.setForeground(self._trades_table.palette().highlight())
            self._trades_table.setItem(row, 5, profit_rate_item)
            # 持仓天数
            self._trades_table.setItem(row, 6, QTableWidgetItem(str(trade.holding_days)))

    def _on_show_trades_on_chart(self) -> None:
        """将交易记录标注到K线图"""
        if self._current_result and self._current_result.trades:
            self.show_trades_on_chart.emit(
                self._current_result.trades,
                self._current_result.symbol
            )

    def get_config(self) -> dict:
        return {
            "symbol": self._symbol_input.text().strip(),
            "start_date": self._start_date.date().toString("yyyy-MM-dd"),
            "end_date": self._end_date.date().toString("yyyy-MM-dd"),
            "strategy": self._strategy_combo.currentText(),
            "initial_capital": self._capital_spin.value(),
        }
    
    def _on_load_history(self) -> None:
        """加载历史回测记录"""
        symbol = self._symbol_input.text().strip()
        if symbol:
            self.load_history_requested.emit(symbol)
    
    def set_history_records(self, records: list) -> None:
        """设置历史回测记录"""
        self._history_records = records
        self._update_history_table()
    
    def _update_history_table(self) -> None:
        """更新历史记录表格"""
        self._history_table.setRowCount(len(self._history_records))
        
        for row, record in enumerate(self._history_records):
            # 创建时间
            created_at = record.get("created_at", "")
            self._history_table.setItem(row, 0, QTableWidgetItem(str(created_at)))
            
            # 策略类型
            self._history_table.setItem(row, 1, QTableWidgetItem(str(record.get("strategy_type", ""))))
            
            # 开始日期
            self._history_table.setItem(row, 2, QTableWidgetItem(str(record.get("start_date", ""))))
            
            # 结束日期
            self._history_table.setItem(row, 3, QTableWidgetItem(str(record.get("end_date", ""))))
            
            # 交易次数
            self._history_table.setItem(row, 4, QTableWidgetItem(str(record.get("total_trades", 0))))
            
            # 胜率
            win_rate = record.get("win_rate", 0)
            win_rate_item = QTableWidgetItem(f"{win_rate:.2%}")
            self._history_table.setItem(row, 5, win_rate_item)
            
            # 总收益
            total_return = record.get("total_return", 0)
            return_item = QTableWidgetItem(f"{total_return:.2%}")
            if total_return >= 0:
                return_item.setForeground(self._history_table.palette().link())
            else:
                return_item.setForeground(self._history_table.palette().highlight())
            self._history_table.setItem(row, 6, return_item)
            
            # 夏普比率
            sharpe = record.get("sharpe_ratio", 0)
            self._history_table.setItem(row, 7, QTableWidgetItem(f"{sharpe:.2f}"))
    
    def _on_history_selected(self) -> None:
        """历史记录被选中"""
        selected_rows = self._history_table.selectionModel().selectedRows()
        self._delete_history_btn.setEnabled(len(selected_rows) > 0)
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self._history_records):
                record = self._history_records[row]
                self.history_record_selected.emit(record)
    
    def _on_delete_history(self) -> None:
        """删除选中的历史记录"""
        from PyQt5.QtWidgets import QMessageBox
        selected_rows = self._history_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self._history_records):
            record = self._history_records[row]
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除这条回测记录吗？\n股票: {record.get('symbol', '')}\n时间: {record.get('created_at', '')}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                record_id = record.get("id")
                if record_id is not None:
                    self.delete_record_requested.emit(record_id)
                    # 从内存中删除并刷新表格
                    self._history_records.pop(row)
                    self._update_history_table()