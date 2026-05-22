"""进度对话框：用于长时间运行任务"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from src.core.logger import setup_logger

logger = setup_logger("progress_dialog")


class ProgressDialog(QDialog):
    """悬浮进度对话框"""
    
    # 取消按钮信号
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("请稍候...")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 状态标签
        self._status_label = QLabel("正在处理...")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)
        
        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # 无限进度
        self._progress_bar.setTextVisible(False)
        layout.addWidget(self._progress_bar)
        
        # 取消按钮
        button_layout = QHBoxLayout()
        self._cancel_button = QPushButton("取消")
        self._cancel_button.clicked.connect(self.cancelled.emit)
        button_layout.addStretch()
        button_layout.addWidget(self._cancel_button)
        
        layout.addLayout(button_layout)
        
    def set_status(self, text):
        """设置状态文本"""
        self._status_label.setText(text)
        
    def set_progress(self, value, max_value=None):
        """设置进度
        
        Args:
            value: 当前值
            max_value: 最大值（如果不指定，则使用无限进度）
        """
        if max_value is not None:
            self._progress_bar.setRange(0, max_value)
            self._progress_bar.setValue(value)
            self._progress_bar.setTextVisible(True)
        else:
            self._progress_bar.setRange(0, 0)
            self._progress_bar.setTextVisible(False)
            
    def show_cancel_button(self, show):
        """显示/隐藏取消按钮"""
        self._cancel_button.setVisible(show)
