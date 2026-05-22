"""数据管理面板"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox,
    QTabWidget, QCheckBox,
)
from PyQt5.QtCore import pyqtSignal

from src.data_layer.data_manager import DataManager
from src.data_layer.stock_info import StockInfo


class DataManagePanel(QWidget):
    """数据管理面板：获取、更新、统计、股票列表管理"""

    data_updated = pyqtSignal()

    def __init__(self, data_manager: DataManager, stock_info: StockInfo, parent=None) -> None:
        super().__init__(parent)
        self._data_mgr = data_manager
        self._stock_info = stock_info
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Tab 页面：股票列表管理
        self._tabs = QTabWidget()
        
        # Tab1：股票列表
        stock_tab = QWidget()
        stock_layout = QVBoxLayout(stock_tab)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self._refresh_stock_btn = QPushButton("刷新股票列表")
        self._refresh_stock_btn.clicked.connect(self._refresh_stock_list)
        self._market_combo = QComboBox()
        self._market_combo.addItems(["全部市场", "上海(SH)", "深圳(SZ)"])
        self._market_combo.currentIndexChanged.connect(self._filter_market_changed)
        btn_layout.addWidget(self._refresh_stock_btn)
        btn_layout.addWidget(self._market_combo)
        stock_layout.addLayout(btn_layout)
        
        # 股票列表表格
        self._stock_table = QTableWidget()
        self._stock_table.setColumnCount(6)
        self._stock_table.setHorizontalHeaderLabels(
            ["代码", "名称", "市场", "行业", "是否跟踪", "最后更新"]
        )
        self._stock_table.cellClicked.connect(self._on_stock_clicked)
        stock_layout.addWidget(self._stock_table)
        
        # 更新信息
        self._update_info = QLabel("股票列表: 未更新")
        stock_layout.addWidget(self._update_info)
        
        self._tabs.addTab(stock_tab, "股票列表")
        
        # Tab2：跟踪股票与数据管理
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        # 操作按钮
        data_btn_layout = QHBoxLayout()
        self._fetch_btn = QPushButton("获取数据")
        self._update_btn = QPushButton("更新所有")
        self._stats_btn = QPushButton("查看统计")
        data_btn_layout.addWidget(self._fetch_btn)
        data_btn_layout.addWidget(self._update_btn)
        data_btn_layout.addWidget(self._stats_btn)
        data_layout.addLayout(data_btn_layout)
        
        # 跟踪股票列表
        self._tracked_table = QTableWidget()
        self._tracked_table.setColumnCount(4)
        self._tracked_table.setHorizontalHeaderLabels(
            ["代码", "名称", "最新日期", "记录数"]
        )
        data_layout.addWidget(self._tracked_table)
        
        # 统计信息
        self._stats_label = QLabel("数据统计: 加载中...")
        data_layout.addWidget(self._stats_label)
        
        self._tabs.addTab(data_tab, "跟踪股票数据")
        
        layout.addWidget(self._tabs)

        self._stats_btn.clicked.connect(self._show_stats)
        self._update_btn.clicked.connect(self._update_all)
        
        # 初始化显示
        self._show_stock_list()
        self._show_stats()

    def _show_stock_list(self, market: str = "all") -> None:
        """显示股票列表"""
        if market == "全部市场":
            m = "all"
        elif market == "上海(SH)":
            m = "SH"
        else:
            m = "SZ"
            
        stocks = self._stock_info.get_all_stocks(m)
        self._stock_table.setRowCount(len(stocks))
        
        for i, stock in enumerate(stocks):
            symbol = str(stock.get("symbol", ""))
            self._stock_table.setItem(i, 0, QTableWidgetItem(symbol))
            self._stock_table.setItem(i, 1, QTableWidgetItem(str(stock.get("name", ""))))
            market_text = "SH" if str(stock.get("symbol", "")).startswith("6") else "SZ"
            self._stock_table.setItem(i, 2, QTableWidgetItem(market_text))
            self._stock_table.setItem(i, 3, QTableWidgetItem(str(stock.get("industry", ""))))
            
            # 跟踪复选框
            tracked = bool(stock.get("is_tracked", 0))
            checkbox = QCheckBox("")
            checkbox.setChecked(tracked)
            # 使用闭包捕获当前 symbol
            checkbox.stateChanged.connect(
                lambda s, sym=symbol: self._toggle_tracked(s, sym)
            )
            self._stock_table.setCellWidget(i, 4, checkbox)
            
            self._stock_table.setItem(i, 5, QTableWidgetItem(str(stock.get("updated_at", ""))))
        
        last_update = self._stock_info.get_last_update_time()
        self._update_info.setText(f"股票总数: {len(stocks)} | 最后更新: {last_update}")

    def _refresh_stock_list(self) -> None:
        """刷新股票列表"""
        count = self._stock_info.refresh_stock_list()
        if count > 0:
            self._show_stock_list(self._market_combo.currentText())
            self.data_updated.emit()

    def _toggle_tracked(self, state: int, symbol: str) -> None:
        """切换股票跟踪状态"""
        self._stock_info.set_tracked(symbol, state == 2)
        self._update_info.setText(f"股票 '{symbol}' 跟踪状态已更新")

    def _on_stock_clicked(self, row: int, col: int) -> None:
        """点击股票行点击事件"""
        pass

    def _filter_market_changed(self, index: int) -> None:
        """市场筛选变化"""
        self._show_stock_list(self._market_combo.currentText())

    def _show_stats(self) -> None:
        tracked = self._stock_info.get_tracked_stocks()
        self._tracked_table.setRowCount(len(tracked))
        for i, stock in enumerate(tracked):
            self._tracked_table.setItem(i, 0, QTableWidgetItem(stock["symbol"]))
            self._tracked_table.setItem(i, 1, QTableWidgetItem(stock["name"]))
            latest = self._data_mgr.get_latest_date(stock["symbol"])
            self._tracked_table.setItem(i, 2, QTableWidgetItem(latest or "无数据"))

        total = self._data_mgr._db.get_table_count("daily_kline")
        self._stats_label.setText(f"总记录数: {total}")

    def _update_all(self) -> None:
        self._data_mgr.update_all_stocks()
        self._show_stats()
        self.data_updated.emit()
