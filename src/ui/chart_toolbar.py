"""图表工具栏：缩放、十字线、指标切换、信号显示"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QCheckBox, QComboBox, QLabel,
)
from PyQt5.QtCore import pyqtSignal

from src.ui.kline_widget import KlineWidget


class ChartToolbar(QWidget):
    """K线图控制工具栏"""

    zoom_in_signal = pyqtSignal()
    zoom_out_signal = pyqtSignal()
    reset_zoom_signal = pyqtSignal()
    scroll_left_signal = pyqtSignal()
    scroll_right_signal = pyqtSignal()
    indicator_toggled = pyqtSignal(str, bool)
    volume_toggled = pyqtSignal(bool)
    signal_filter_changed = pyqtSignal(str)

    def __init__(self, kline_widget: KlineWidget,
                 parent: QWidget = None) -> None:
        super().__init__(parent)
        self._kline = kline_widget
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 缩放按钮
        self._btn_zoom_in = QPushButton("放大")
        self._btn_zoom_out = QPushButton("缩小")
        self._btn_reset = QPushButton("重置")
        self._btn_left = QPushButton("←")
        self._btn_right = QPushButton("→")

        for btn in [self._btn_zoom_in, self._btn_zoom_out,
                    self._btn_reset, self._btn_left, self._btn_right]:
            btn.setFixedWidth(50)
            layout.addWidget(btn)

        layout.addWidget(self._separator())

        # 指标复选框
        self._chk_macd = QCheckBox("MACD")
        self._chk_kdj = QCheckBox("KDJ")
        self._chk_rsi = QCheckBox("RSI")
        self._chk_boll = QCheckBox("BOLL")
        self._chk_volume = QCheckBox("成交量")
        self._chk_volume.setChecked(True)

        for chk in [self._chk_macd, self._chk_kdj, self._chk_rsi,
                    self._chk_boll, self._chk_volume]:
            layout.addWidget(chk)

        layout.addWidget(self._separator())

        # 信号过滤
        self._cmb_signal = QComboBox()
        self._cmb_signal.addItems(["全部信号", "仅买入", "仅卖出", "隐藏信号"])
        layout.addWidget(QLabel("信号:"))
        layout.addWidget(self._cmb_signal)

        layout.addStretch()

    def _separator(self) -> QLabel:
        sep = QLabel("|")
        sep.setFixedWidth(10)
        return sep

    def _connect_signals(self) -> None:
        self._btn_zoom_in.clicked.connect(self._kline.zoom_in)
        self._btn_zoom_out.clicked.connect(self._kline.zoom_out)
        self._btn_reset.clicked.connect(self._kline.reset_zoom)
        self._btn_left.clicked.connect(self._kline.scroll_left)
        self._btn_right.clicked.connect(self._kline.scroll_right)

        for chk, name in [(self._chk_macd, "MACD"), (self._chk_kdj, "KDJ"),
                          (self._chk_rsi, "RSI"), (self._chk_boll, "BOLL")]:
            chk.stateChanged.connect(
                lambda state, n=name: self._kline.toggle_indicator(n, state == 2)
            )

        self._chk_volume.stateChanged.connect(
            lambda state: self._kline.toggle_volume(state == 2)
        )

        self._cmb_signal.currentTextChanged.connect(self.signal_filter_changed)