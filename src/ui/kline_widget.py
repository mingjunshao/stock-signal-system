"""K线图组件：mplfinance嵌入PyQt5，A股红涨绿跌样式"""

import pandas as pd
from typing import Dict, List, Optional

import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

from src.core.constants import SignalType, SignalStrength
from src.strategy_engine.signal import FusedSignal
from src.core.logger import setup_logger

logger = setup_logger("kline_widget")

# A股红涨绿跌样式
_A_SHARE_STYLE = mpf.make_mpf_style(
    base_mpf_style="charles",
    marketcolors=mpf.make_marketcolors(
        up="red", down="green",
        edge="red", wick={"up": "red", "down": "green"},
        volume={"up": "red", "down": "green"},
    ),
    gridstyle="--",
    y_on_right=False,
)


class KlineWidget(QWidget):
    """mplfinance嵌入PyQt5的K线图组件"""

    # 信号用于数据提示
    data_hovered = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._df: pd.DataFrame = pd.DataFrame()
        self._signals: List[FusedSignal] = []
        self._trades: List = []  # 回测交易记录
        self._visible_range = 120
        self._offset = 0
        self._show_volume = True
        self._indicators: Dict[str, bool] = {
            "MACD": False, "KDJ": False, "RSI": False, "BOLL": False,
        }
        self._symbol: str = ""
        self._name: str = ""
        
        # 设置focus策略，让键盘事件能收到
        self.setFocusPolicy(Qt.StrongFocus)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部标题栏
        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(10, 5, 10, 5)
        
        self._title_label = QLabel("等待选择股票...")
        self._title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #000000;
                background-color: #f0f0f0;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #000000;
                background-color: #e0e0e0;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        
        self._header_layout.addWidget(self._title_label)
        self._header_layout.addStretch()
        self._header_layout.addWidget(self._info_label)
        
        self._layout.addLayout(self._header_layout, stretch=1)  # 标题栏只占很小比例
        self._canvas_container = QWidget()
        self._canvas_layout = QVBoxLayout(self._canvas_container)
        self._canvas_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._canvas_container, stretch=20)  # K线图占主要空间
        self._canvas = None
        self._update_chart()

    def set_data(self, df: pd.DataFrame,
                 signals: Optional[List[FusedSignal]] = None,
                 symbol: str = "",
                 name: str = "",
                 trades: Optional[List] = None) -> None:
        """设置K线数据和信号标注"""
        self._df = df.copy()
        self._signals = signals or []
        self._trades = trades or []
        self._symbol = symbol
        self._name = name
        self._offset = 0
        self._visible_range = min(120, len(df))
        
        # 更新标题
        if symbol and name:
            self._title_label.setText(f"{name} ({symbol})")
        elif symbol:
            self._title_label.setText(symbol)
        
        self._update_chart()

    def keyPressEvent(self, event):
        """处理键盘事件"""
        key = event.key()
        if key == Qt.Key_Up:
            self.zoom_in()
        elif key == Qt.Key_Down:
            self.zoom_out()
        elif key == Qt.Key_Left:
            self.scroll_left()
        elif key == Qt.Key_Right:
            self.scroll_right()
        elif key == Qt.Key_Escape:
            self.reset_zoom()
        else:
            super().keyPressEvent(event)

    def _update_chart(self) -> None:
        """刷新图表（内部方法）"""
        # 先移除旧的canvas
        if self._canvas:
            self._canvas_layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
            self._canvas = None

        if self._df.empty:
            return

        # 截取可见范围数据
        start = max(0, len(self._df) - self._visible_range - self._offset)
        end = max(0, len(self._df) - self._offset)
        visible_df = self._df.iloc[start:end].copy()

        if visible_df.empty:
            return

        # 准备mplfinance数据格式
        plot_df = visible_df.copy()
        if "date" in plot_df.columns:
            plot_df["Date"] = pd.to_datetime(plot_df["date"])
            plot_df = plot_df.set_index("Date")
        else:
            plot_df.index = pd.to_datetime(plot_df.index)

        # 确保必要列存在
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in plot_df.columns:
                logger.warning(f"数据缺少必要列: {col}")
                return

        import numpy as np
        
        # 构建附加图层
        add_plots = []

        # 信号标注
        buy_prices = [np.nan] * len(visible_df)
        sell_prices = [np.nan] * len(visible_df)
        
        # 回测交易记录标注
        entry_prices = [np.nan] * len(visible_df)  # 入场（红色圆圈）
        exit_prices = [np.nan] * len(visible_df)   # 出场（绿色方块）
        
        date_col = "date" if "date" in visible_df.columns else None
        if date_col:
            # 创建日期到索引的映射，兼容不同格式的日期
            date_to_idx = {}
            for i, d in enumerate(visible_df["date"]):
                # 标准化日期格式用于匹配
                date_str = str(d)
                date_to_idx[date_str] = i
                # 也尝试不带时间的格式
                if " " in date_str:
                    date_to_idx[date_str.split(" ")[0]] = i
            
            # 处理信号标注
            if self._signals:
                for sig in self._signals:
                    sig_date = str(sig.date)
                    matched_idx = None
                    
                    # 尝试精确匹配
                    if sig_date in date_to_idx:
                        matched_idx = date_to_idx[sig_date]
                    else:
                        # 尝试只匹配日期部分
                        if " " in sig_date:
                            sig_date_only = sig_date.split(" ")[0]
                            if sig_date_only in date_to_idx:
                                matched_idx = date_to_idx[sig_date_only]
                    
                    if matched_idx is not None:
                        idx = matched_idx
                        if sig.signal_type == SignalType.BUY:
                            buy_prices[idx] = sig.price
                            logger.debug(f"匹配到买入信号: {sig.date} at idx {idx}")
                        elif sig.signal_type == SignalType.SELL:
                            sell_prices[idx] = sig.price
                            logger.debug(f"匹配到卖出信号: {sig.date} at idx {idx}")
            
            # 处理回测交易记录标注
            if self._trades:
                for trade in self._trades:
                    # 入场点
                    entry_date = str(trade.entry_date)
                    entry_idx = None
                    if entry_date in date_to_idx:
                        entry_idx = date_to_idx[entry_date]
                    elif " " in entry_date and entry_date.split(" ")[0] in date_to_idx:
                        entry_idx = date_to_idx[entry_date.split(" ")[0]]
                    
                    if entry_idx is not None:
                        entry_prices[entry_idx] = trade.entry_price
                        logger.debug(f"匹配到入场交易: {trade.entry_date} at idx {entry_idx}")
                    
                    # 出场点（处理未平仓的情况）
                    exit_date = str(trade.exit_date)
                    # 移除"(未平仓)"标记以匹配日期
                    if "(未平仓)" in exit_date:
                        exit_date = exit_date.replace("(未平仓)", "")
                    
                    exit_idx = None
                    if exit_date in date_to_idx:
                        exit_idx = date_to_idx[exit_date]
                    elif " " in exit_date and exit_date.split(" ")[0] in date_to_idx:
                        exit_idx = date_to_idx[exit_date.split(" ")[0]]
                    
                    if exit_idx is not None:
                        exit_prices[exit_idx] = trade.exit_price
                        logger.debug(f"匹配到出场交易: {trade.exit_date} at idx {exit_idx}")
        
        # 添加信号标注
        has_buy_signals = not all(np.isnan(p) for p in buy_prices)
        has_sell_signals = not all(np.isnan(p) for p in sell_prices)
        has_entry_trades = not all(np.isnan(p) for p in entry_prices)
        has_exit_trades = not all(np.isnan(p) for p in exit_prices)
        
        if has_buy_signals:
            add_plots.append(mpf.make_addplot(
                buy_prices, type="scatter", markersize=80,
                marker="^", color="red", secondary_y=False,
            ))

        if has_sell_signals:
            add_plots.append(mpf.make_addplot(
                sell_prices, type="scatter", markersize=80,
                marker="v", color="green", secondary_y=False,
            ))
        
        # 添加回测交易标注（用不同形状区分）
        if has_entry_trades:
            add_plots.append(mpf.make_addplot(
                entry_prices, type="scatter", markersize=120,
                marker="o", color="#FF6B6B", secondary_y=False,
            ))

        if has_exit_trades:
            add_plots.append(mpf.make_addplot(
                exit_prices, type="scatter", markersize=120,
                marker="s", color="#4ECDC4", secondary_y=False,
            ))

        # 技术指标图层
        if self._indicators.get("BOLL") and "boll_upper" in visible_df.columns:
            add_plots.extend([
                mpf.make_addplot(visible_df["boll_upper"], color="orange", width=0.7),
                mpf.make_addplot(visible_df["boll_mid"], color="blue", width=0.7),
                mpf.make_addplot(visible_df["boll_lower"], color="orange", width=0.7),
            ])

        if self._indicators.get("MACD") and "macd_dif" in visible_df.columns:
            add_plots.extend([
                mpf.make_addplot(visible_df["macd_dif"], panel=2, color="blue", width=0.7),
                mpf.make_addplot(visible_df["macd_dea"], panel=2, color="orange", width=0.7),
                mpf.make_addplot(visible_df["macd_hist"], type="bar", panel=2, color="dimgray"),
            ])

        if self._indicators.get("KDJ") and "K" in visible_df.columns:
            add_plots.extend([
                mpf.make_addplot(visible_df["K"], panel=3, color="yellow", width=0.7),
                mpf.make_addplot(visible_df["D"], panel=3, color="purple", width=0.7),
                mpf.make_addplot(visible_df["J"], panel=3, color="cyan", width=0.7),
            ])

        if self._indicators.get("RSI") and "rsi_6" in visible_df.columns:
            add_plots.extend([
                mpf.make_addplot(visible_df["rsi_6"], panel=4, color="red", width=0.7),
                mpf.make_addplot(visible_df["rsi_12"], panel=4, color="green", width=0.7),
                mpf.make_addplot(visible_df["rsi_24"], panel=4, color="blue", width=0.7),
            ])

        # 绘制K线图
        try:
            plot_kwargs = {
                "type": "candle",
                "style": _A_SHARE_STYLE,
                "volume": self._show_volume,
                "figsize": (12, 8),
                "warn_too_much_data": max(len(plot_df) + 1, 10000),
            }
            if add_plots:
                plot_kwargs["addplot"] = add_plots
            
            # 使用 mplfinance 直接绘图
            fig, axes = mpf.plot(
                plot_df,
                **plot_kwargs,
                returnfig=True
            )
            
            # 创建新的 canvas
            self._canvas = FigureCanvas(fig)
            self._canvas_layout.addWidget(self._canvas)
            
            # 连接鼠标事件
            self._canvas.mpl_connect('button_press_event', self._on_mouse_click)
            self._canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
            
        except Exception as e:
            logger.error(f"绘制K线图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _on_mouse_click(self, event):
        """鼠标点击事件 - 显示焦点数据"""
        if not event.inaxes or len(self._df) == 0:
            return
            
        # 获取点击位置的索引
        if event.xdata:
            try:
                # 截取当前可见范围
                start = max(0, len(self._df) - self._visible_range - self._offset)
                end = max(0, len(self._df) - self._offset)
                visible_df = self._df.iloc[start:end].copy()
                
                # 找到最接近的索引
                idx = round(event.xdata)
                if 0 <= idx < len(visible_df):
                    row = visible_df.iloc[idx]
                    self._show_data_info(row)
            except Exception as e:
                logger.error(f"点击数据获取失败: {e}")

    def _on_mouse_move(self, event):
        """鼠标移动事件 - 可以更新提示"""
        pass

    def _show_data_info(self, row):
        """显示焦点位置的数据"""
        info_text = []
        if "date" in row:
            info_text.append(f"日期: {row['date']}")
        if "open" in row:
            info_text.append(f"开: {row['open']:.2f}")
        if "high" in row:
            info_text.append(f"高: {row['high']:.2f}")
        if "low" in row:
            info_text.append(f"低: {row['low']:.2f}")
        if "close" in row:
            info_text.append(f"收: {row['close']:.2f}")
        if "volume" in row:
            vol = row['volume'] / 10000 if row['volume'] > 10000 else row['volume']
            unit = "万" if row['volume'] > 10000 else ""
            info_text.append(f"量: {vol:.2f}{unit}")
            
        self._info_label.setText(" | ".join(info_text))

    def update_chart(self) -> None:
        """刷新图表（公开方法）"""
        self._update_chart()

    def zoom_in(self) -> None:
        self._visible_range = max(30, self._visible_range - 15)
        self._update_chart()

    def zoom_out(self) -> None:
        self._visible_range = min(len(self._df), self._visible_range + 15)
        self._update_chart()

    def reset_zoom(self) -> None:
        self._visible_range = min(120, len(self._df))
        self._offset = 0
        self._update_chart()

    def scroll_left(self) -> None:
        self._offset = min(len(self._df) - self._visible_range, self._offset + 5)
        self._update_chart()

    def scroll_right(self) -> None:
        self._offset = max(0, self._offset - 5)
        self._update_chart()

    def toggle_indicator(self, name: str, show: bool) -> None:
        self._indicators[name] = show
        self._update_chart()

    def toggle_volume(self, show: bool) -> None:
        self._show_volume = show
        self._update_chart()
