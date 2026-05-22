"""参数优化面板"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QProgressBar, QTextEdit,
    QGroupBox, QSpinBox, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter,
)
from PyQt5.QtCore import pyqtSignal, Qt

from src.optimizer.optimization_result import OptimizationResult


class OptimizerPanel(QWidget):
    """参数优化配置与结果展示面板"""

    optimization_completed = pyqtSignal(OptimizationResult)
    apply_params = pyqtSignal(dict)
    load_history_requested = pyqtSignal(str, str)
    delete_record_requested = pyqtSignal(int)  # (record_id)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_result = None
        self._history_results = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 配置区
        config_group = QGroupBox("优化配置")
        config_layout = QFormLayout()

        self._symbol_input = QLineEdit()
        self._symbol_input.setPlaceholderText("股票代码")
        config_layout.addRow("股票:", self._symbol_input)

        self._strategy_combo = QComboBox()
        self._strategy_combo.addItems(["技术指标", "均值回归", "量价分析", "趋势跟踪"])
        config_layout.addRow("策略:", self._strategy_combo)

        self._method_combo = QComboBox()
        self._method_combo.addItems(["网格搜索", "遗传算法"])
        config_layout.addRow("方法:", self._method_combo)

        self._metric_combo = QComboBox()
        self._metric_combo.addItems(["夏普比率", "胜率", "总收益率", "盈亏比"])
        config_layout.addRow("目标:", self._metric_combo)

        self._pop_spin = QSpinBox()
        self._pop_spin.setRange(10, 200)
        self._pop_spin.setValue(50)
        config_layout.addRow("群体大小:", self._pop_spin)

        self._gen_spin = QSpinBox()
        self._gen_spin.setRange(5, 100)
        self._gen_spin.setValue(30)
        config_layout.addRow("迭代次数:", self._gen_spin)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 进度条
        self._progress = QProgressBar()
        layout.addWidget(self._progress)

        # 按钮区
        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton("开始优化")
        btn_layout.addWidget(self._start_btn)
        self._load_history_btn = QPushButton("加载历史")
        self._load_history_btn.clicked.connect(self._on_load_history)
        btn_layout.addWidget(self._load_history_btn)
        self._apply_btn = QPushButton("应用参数")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply_params)
        btn_layout.addWidget(self._apply_btn)
        layout.addLayout(btn_layout)

        # 使用分割器分割历史结果和详细结果
        splitter = QSplitter(Qt.Vertical)

        # 历史结果列表
        history_group = QGroupBox("历史优化结果")
        history_layout = QVBoxLayout(history_group)
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(6)
        self._history_table.setHorizontalHeaderLabels([
            "股票代码", "股票名称", "策略", "优化方式", "优化目标", "创建时间"
        ])
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.itemSelectionChanged.connect(self._on_history_selection_changed)
        history_layout.addWidget(self._history_table)
        
        # 历史记录操作按钮
        history_btn_layout = QHBoxLayout()
        self._delete_history_btn = QPushButton("删除选中记录")
        self._delete_history_btn.setEnabled(False)
        self._delete_history_btn.clicked.connect(self._on_delete_history)
        history_btn_layout.addWidget(self._delete_history_btn)
        history_layout.addLayout(history_btn_layout)
        
        splitter.addWidget(history_group)

        # 结果详情
        result_group = QGroupBox("优化结果详情")
        result_layout = QVBoxLayout(result_group)
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        result_layout.addWidget(self._result_text)
        splitter.addWidget(result_group)

        splitter.setSizes([300, 400])
        layout.addWidget(splitter)

    def _on_apply_params(self) -> None:
        """应用参数按钮点击"""
        if self._current_result:
            self.apply_params.emit(self._current_result.best_params)

    def _on_load_history(self) -> None:
        """加载历史优化结果"""
        symbol = self._symbol_input.text().strip()
        strategy = self._strategy_combo.currentText()
        self.load_history_requested.emit(symbol, strategy)

    def _on_history_selection_changed(self) -> None:
        """历史结果选择改变"""
        selected_rows = self._history_table.selectionModel().selectedRows()
        self._delete_history_btn.setEnabled(len(selected_rows) > 0)
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self._history_results):
                result = self._history_results[row]
                self._display_history_result(result)
    
    def _on_delete_history(self) -> None:
        """删除选中的历史记录"""
        from PyQt5.QtWidgets import QMessageBox
        selected_rows = self._history_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self._history_results):
            record = self._history_results[row]
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除这条优化记录吗？\n股票: {record.get('symbol', '')}\n时间: {record.get('created_at', '')}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                record_id = record.get("id")
                if record_id is not None:
                    self.delete_record_requested.emit(record_id)
                    # 从内存中删除并刷新表格
                    self._history_results.pop(row)
                    self.set_history_results(self._history_results)

    def _display_history_result(self, result: dict) -> None:
        """显示历史结果详情"""
        best_params = result.get("best_params", {})
        text = (
            f"=== 历史优化结果 ===\n"
            f"股票代码: {result.get('symbol', '')}\n"
            f"股票名称: {result.get('symbol_name', '')}\n"
            f"策略: {result.get('strategy_type', '')}\n"
            f"优化方式: {result.get('optimization_method', '')}\n"
            f"优化目标: {result.get('metric_name', '')}\n"
            f"最优指标值: {result.get('best_metric_value', 0):.4f}\n"
            f"耗时: {result.get('elapsed_time', 0):.1f}秒\n"
            f"创建时间: {result.get('created_at', '')}\n"
            f"最优参数:\n"
        )
        for key, value in best_params.items():
            text += f"  {key}: {value}\n"
        self._result_text.setText(text)
        self._apply_btn.setEnabled(True)
        # 创建一个模拟的result对象用于应用参数
        class MockResult:
            def __init__(self, params):
                self.best_params = params
        self._current_result = MockResult(best_params)

    def set_history_results(self, results: list) -> None:
        """设置历史优化结果列表
        
        Args:
            results: 历史结果列表，每个结果是字典
        """
        self._history_results = results
        self._history_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            self._history_table.setItem(row, 0, QTableWidgetItem(str(result.get('symbol', ''))))
            self._history_table.setItem(row, 1, QTableWidgetItem(str(result.get('symbol_name', ''))))
            self._history_table.setItem(row, 2, QTableWidgetItem(str(result.get('strategy_type', ''))))
            self._history_table.setItem(row, 3, QTableWidgetItem(str(result.get('optimization_method', ''))))
            self._history_table.setItem(row, 4, QTableWidgetItem(str(result.get('metric_name', ''))))
            self._history_table.setItem(row, 5, QTableWidgetItem(str(result.get('created_at', ''))))

    def set_progress(self, value: int) -> None:
        self._progress.setValue(value)

    def set_result(self, result: OptimizationResult) -> None:
        self._current_result = result
        text = (
            f"=== 优化结果 ===\n"
            f"策略: {result.strategy_type.value}\n"
            f"方法: {result.optimization_method}\n"
            f"目标指标: {result.metric_name}\n"
            f"最优参数: {result.best_params}\n"
            f"最优指标值: {result.best_metric_value:.4f}\n"
            f"耗时: {result.elapsed_time:.1f}秒\n"
        )
        self._result_text.setText(text)
        self._apply_btn.setEnabled(True)

    def get_config(self) -> dict:
        return {
            "symbol": self._symbol_input.text().strip(),
            "strategy": self._strategy_combo.currentText(),
            "method": self._method_combo.currentText(),
            "metric": self._metric_combo.currentText(),
            "population_size": self._pop_spin.value(),
            "generations": self._gen_spin.value(),
        }