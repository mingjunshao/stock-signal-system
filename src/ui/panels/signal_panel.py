"""信号展示面板"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QComboBox, QHeaderView,
)
from PyQt5.QtCore import pyqtSignal, Qt

from src.strategy_engine.signal import FusedSignal
from src.core.constants import SignalType


class SignalPanel(QWidget):
    """信号展示面板"""

    show_on_chart = pyqtSignal(list)
    load_history_signals = pyqtSignal(str)  # 加载历史信号信号
    delete_signals_requested = pyqtSignal(str)  # 删除指定股票的所有信号

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._signals = []
        self._filtered_signals = []
        self._sort_order = Qt.DescendingOrder  # 默认降序
        self._sort_column = 1  # 默认按日期排序
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 当前信号摘要
        self._summary_label = QLabel("当前信号: 无")
        self._summary_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._summary_label)

        # 筛选区域
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("证券代码:"))
        self._symbol_filter = QLineEdit()
        self._symbol_filter.setPlaceholderText("输入证券代码筛选...")
        self._symbol_filter.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._symbol_filter)
        
        filter_layout.addWidget(QLabel("信号类型:"))
        self._type_filter = QComboBox()
        self._type_filter.addItem("全部", None)
        self._type_filter.addItem("买入", SignalType.BUY)
        self._type_filter.addItem("卖出", SignalType.SELL)
        self._type_filter.addItem("观望", SignalType.HOLD)
        self._type_filter.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._type_filter)
        
        layout.addLayout(filter_layout)

        # 信号历史列表
        self._signal_table = QTableWidget()
        self._signal_table.setColumnCount(7)
        self._signal_table.setHorizontalHeaderLabels(
            ["证券代码", "日期", "信号类型", "强度", "置信度", "价格", "描述"]
        )
        # 设置表头可点击排序
        self._signal_table.horizontalHeader().setSectionsClickable(True)
        self._signal_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        # 设置列宽自适应
        self._signal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self._signal_table)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self._generate_btn = QPushButton("生成信号")
        self._load_history_btn = QPushButton("加载历史")
        self._delete_signals_btn = QPushButton("删除历史信号")
        self._show_chart_btn = QPushButton("标注到K线图")
        btn_layout.addWidget(self._generate_btn)
        btn_layout.addWidget(self._load_history_btn)
        btn_layout.addWidget(self._delete_signals_btn)
        btn_layout.addWidget(self._show_chart_btn)
        layout.addLayout(btn_layout)

        self._show_chart_btn.clicked.connect(self._on_show_chart)
        self._load_history_btn.clicked.connect(self._on_load_history)
        self._delete_signals_btn.clicked.connect(self._on_delete_signals)

    def set_signals(self, signals: list, symbol: str = "") -> None:
        self._signals = signals
        self._current_symbol = symbol
        self._apply_filter()

    def _apply_filter(self) -> None:
        """应用筛选条件"""
        filtered = self._signals.copy()
        
        # 按信号类型筛选
        type_filter = self._type_filter.currentData()
        if type_filter is not None:
            filtered = [s for s in filtered if s.signal_type == type_filter]
        
        self._filtered_signals = filtered
        self._sort_and_display()

    def _sort_and_display(self) -> None:
        """排序并显示信号"""
        # 排序
        self._filtered_signals.sort(
            key=lambda x: self._get_sort_key(x),
            reverse=(self._sort_order == Qt.DescendingOrder)
        )
        
        # 显示
        self._signal_table.setRowCount(len(self._filtered_signals))
        
        for i, sig in enumerate(self._filtered_signals):
            self._signal_table.setItem(i, 0, QTableWidgetItem(getattr(sig, 'symbol', self._current_symbol)))
            self._signal_table.setItem(i, 1, QTableWidgetItem(sig.date))
            self._signal_table.setItem(i, 2, QTableWidgetItem(sig.signal_type.value))
            self._signal_table.setItem(i, 3, QTableWidgetItem(str(sig.strength.value)))
            self._signal_table.setItem(i, 4, QTableWidgetItem(f"{sig.confidence:.2f}"))
            self._signal_table.setItem(i, 5, QTableWidgetItem(f"{sig.price:.2f}"))
            self._signal_table.setItem(i, 6, QTableWidgetItem(sig.description))

        # 更新摘要
        if self._filtered_signals:
            latest = self._filtered_signals[0] if self._sort_order == Qt.DescendingOrder else self._filtered_signals[-1]
            self._summary_label.setText(
                f"最新信号: {latest.signal_type.value} | "
                f"强度: {latest.strength.value} | "
                f"置信度: {latest.confidence:.2f} | "
                f"价格: {latest.price:.2f}"
            )
        else:
            self._summary_label.setText("当前信号: 无")

    def _get_sort_key(self, signal):
        """获取排序键"""
        if self._sort_column == 0:
            return getattr(signal, 'symbol', '')
        elif self._sort_column == 1:
            return signal.date
        elif self._sort_column == 2:
            return signal.signal_type.value
        elif self._sort_column == 3:
            return signal.strength.value
        elif self._sort_column == 4:
            return signal.confidence
        elif self._sort_column == 5:
            return signal.price
        else:
            return signal.date

    def _on_header_clicked(self, column: int) -> None:
        """表头点击事件 - 切换排序"""
        if self._sort_column == column:
            # 同一列，切换顺序
            self._sort_order = Qt.AscendingOrder if self._sort_order == Qt.DescendingOrder else Qt.DescendingOrder
        else:
            # 不同列，默认降序
            self._sort_column = column
            self._sort_order = Qt.DescendingOrder
        
        # 更新表头显示排序指示
        header = self._signal_table.horizontalHeader()
        for i in range(header.count()):
            if i == self._sort_column:
                indicator = " ↓" if self._sort_order == Qt.DescendingOrder else " ↑"
                labels = ["证券代码", "日期", "信号类型", "强度", "置信度", "价格", "描述"]
                header.setSectionResizeMode(i, QHeaderView.Interactive)
            else:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        self._sort_and_display()

    def _on_show_chart(self) -> None:
        self.show_on_chart.emit(self._filtered_signals)

    def _on_load_history(self) -> None:
        """加载历史信号"""
        symbol = self._symbol_filter.text().strip()
        if not symbol and hasattr(self, '_current_symbol'):
            symbol = self._current_symbol
        if symbol:
            self.load_history_signals.emit(symbol)
    
    def _on_delete_signals(self) -> None:
        """删除历史信号"""
        from PyQt5.QtWidgets import QMessageBox
        symbol = self._symbol_filter.text().strip()
        if not symbol and hasattr(self, '_current_symbol'):
            symbol = self._current_symbol
        if not symbol:
            QMessageBox.warning(self, "提示", "请先选择或输入股票代码")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除股票 {symbol} 的所有历史信号吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.delete_signals_requested.emit(symbol)
            # 清空当前显示
            self.set_signals([])