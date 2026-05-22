"""股票选择面板：搜索、列表、跟踪管理"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QPushButton, QLabel, QListWidgetItem,
)
from PyQt5.QtCore import pyqtSignal, Qt

from src.data_layer.data_manager import DataManager
from src.data_layer.stock_info import StockInfo
from src.core.logger import setup_logger

logger = setup_logger("stock_select_panel")


class StockSelectPanel(QWidget):
    """左侧股票选择面板"""

    stock_selected = pyqtSignal(str)

    def __init__(self, data_manager: DataManager, stock_info: StockInfo,
                 parent=None) -> None:
        super().__init__(parent)
        self._data_mgr = data_manager
        self._stock_info = stock_info
        self._init_ui()
        self._load_tracked_stocks()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 搜索框
        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入代码或名称搜索...")
        self._search_btn = QPushButton("搜索")
        search_layout.addWidget(self._search_input)
        search_layout.addWidget(self._search_btn)
        layout.addLayout(search_layout)

        # 搜索结果列表
        self._search_list = QListWidget()
        self._search_list.setMaximumHeight(150)
        layout.addWidget(self._search_list)

        # 跟踪股票列表
        layout.addWidget(QLabel("跟踪股票:"))
        self._tracked_list = QListWidget()
        layout.addWidget(self._tracked_list)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("添加跟踪")
        self._remove_btn = QPushButton("移除跟踪")
        self._refresh_btn = QPushButton("刷新数据")
        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        btn_layout.addWidget(self._refresh_btn)
        layout.addLayout(btn_layout)

        # 信号连接
        self._search_btn.clicked.connect(self._do_search)
        self._search_input.returnPressed.connect(self._do_search)
        self._tracked_list.currentItemChanged.connect(self._on_tracked_selected)
        self._add_btn.clicked.connect(self._add_tracked)
        self._remove_btn.clicked.connect(self._remove_tracked)

    def _load_tracked_stocks(self) -> None:
        tracked = self._data_mgr.get_tracked_stocks()
        self._tracked_list.clear()
        for stock in tracked:
            item = QListWidgetItem(f"{stock['symbol']} - {stock['name']}")
            item.setData(Qt.UserRole, stock["symbol"])
            self._tracked_list.addItem(item)

    def _do_search(self) -> None:
        keyword = self._search_input.text().strip()
        if not keyword:
            return
        results = self._stock_info.search(keyword)
        self._search_list.clear()
        for r in results:
            item = QListWidgetItem(f"{r['symbol']} - {r['name']}")
            item.setData(Qt.UserRole, r["symbol"])
            self._search_list.addItem(item)

    def _on_tracked_selected(self, current, previous) -> None:
        if current:
            symbol = current.data(Qt.UserRole)
            self.stock_selected.emit(symbol)

    def _add_tracked(self) -> None:
        current = self._search_list.currentItem()
        if current:
            symbol = current.data(Qt.UserRole)
            text = current.text()
            name = text.split(" - ")[1] if " - " in text else symbol
            self._data_mgr.add_tracked_stock(symbol, name)
            self._load_tracked_stocks()

    def _remove_tracked(self) -> None:
        current = self._tracked_list.currentItem()
        if current:
            symbol = current.data(Qt.UserRole)
            self._data_mgr.remove_tracked_stock(symbol)
            self._load_tracked_stocks()