"""策略参数配置面板"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
    QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox,
    QScrollArea, QFrame,
)
from PyQt5.QtCore import pyqtSignal, Qt

from src.core.config import Config
from src.core.constants import StrategyType


class StrategyConfigPanel(QWidget):
    """策略参数配置面板"""

    config_applied = pyqtSignal(dict)
    save_config = pyqtSignal()  # 保存配置到数据库
    load_config = pyqtSignal()  # 从数据库加载配置

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._param_widgets = {}
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)

        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        strategies = self._config.strategies
        for stype, sdata in strategies.items():
            group = QGroupBox(stype)
            group_layout = QVBoxLayout(group)

            # 启用复选框
            chk = QCheckBox("启用")
            chk.setChecked(sdata.get("enabled", True))
            group_layout.addWidget(chk)
            self._param_widgets[f"{stype}_enabled"] = chk

            # 参数编辑
            params = sdata.get("params", {})
            form = QFormLayout()
            for pname, pval in params.items():
                if isinstance(pval, (int, float)):
                    if isinstance(pval, int):
                        spin = QSpinBox()
                        spin.setRange(1, 200)
                        spin.setValue(pval)
                    else:
                        spin = QDoubleSpinBox()
                        spin.setRange(0.01, 100.0)
                        spin.setSingleStep(0.1)
                        spin.setValue(pval)
                    form.addRow(pname, spin)
                    self._param_widgets[f"{stype}_{pname}"] = spin
                elif isinstance(pval, list):
                    lbl = QLabel(str(pval))
                    form.addRow(pname, lbl)
            group_layout.addLayout(form)
            layout.addWidget(group)

        # 融合权重
        fusion_group = QGroupBox("融合权重")
        fusion_layout = QFormLayout()
        weights = self._config.fusion.get("weights", {})
        for wname, wval in weights.items():
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.05)
            spin.setValue(wval)
            fusion_layout.addRow(wname, spin)
            self._param_widgets[f"fusion_{wname}"] = spin
        fusion_group.setLayout(fusion_layout)
        layout.addWidget(fusion_group)

        # 添加弹性空间
        layout.addStretch()

        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # 按钮（放在滚动区域外，始终可见）
        btn_layout = QHBoxLayout()
        self._apply_btn = QPushButton("应用配置")
        self._save_btn = QPushButton("保存配置")
        self._load_btn = QPushButton("加载配置")
        self._reset_btn = QPushButton("重置默认")
        btn_layout.addWidget(self._apply_btn)
        btn_layout.addWidget(self._save_btn)
        btn_layout.addWidget(self._load_btn)
        btn_layout.addWidget(self._reset_btn)
        main_layout.addLayout(btn_layout)

        self._apply_btn.clicked.connect(self._apply_config)
        self._save_btn.clicked.connect(self._save_config)
        self._load_btn.clicked.connect(self._load_config)
        self._reset_btn.clicked.connect(self._reset_config)

    def apply_params(self, params: dict, strategy_type: str = None) -> None:
        """应用参数到面板
        
        Args:
            params: 参数字典
            strategy_type: 策略类型名称（可选，如"技术指标"或"tech_indicator"）
        """
        if strategy_type:
            # 策略类型映射：显示名 -> 配置名
            strategy_map = {
                "技术指标": "tech_indicator",
                "均值回归": "mean_reversion",
                "量价分析": "volume_price",
                "趋势跟踪": "trend_following"
            }
            
            # 确定目标策略类型
            target_strategy = None
            if strategy_type in self._config.strategies:
                # 已经是配置中使用的类型名称
                target_strategy = strategy_type
            elif strategy_type in strategy_map:
                # 是显示名称，转换为配置名称
                target_strategy = strategy_map[strategy_type]
            else:
                # 尝试反向查找
                for stype, display_name in strategy_map.items():
                    if display_name == strategy_type:
                        target_strategy = stype
                        break
            
            if target_strategy and target_strategy in self._config.strategies:
                # 应用该策略的参数
                for pname, pval in params.items():
                    key = f"{target_strategy}_{pname}"
                    if key in self._param_widgets:
                        widget = self._param_widgets[key]
                        if isinstance(widget, QSpinBox) and isinstance(pval, (int, float)):
                            widget.setValue(int(pval))
                        elif isinstance(widget, QDoubleSpinBox) and isinstance(pval, (int, float)):
                            widget.setValue(float(pval))
        else:
            # 没有指定策略，尝试自动匹配
            for key, pval in params.items():
                if key in self._param_widgets:
                    widget = self._param_widgets[key]
                    if isinstance(widget, QSpinBox) and isinstance(pval, (int, float)):
                        widget.setValue(int(pval))
                    elif isinstance(widget, QDoubleSpinBox) and isinstance(pval, (int, float)):
                        widget.setValue(float(pval))

    def _apply_config(self) -> None:
        config_dict = {}
        for key, widget in self._param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                config_dict[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                config_dict[key] = widget.isChecked()
        self.config_applied.emit(config_dict)
    
    def _save_config(self) -> None:
        """保存配置到数据库"""
        self.save_config.emit()
    
    def _load_config(self) -> None:
        """从数据库加载配置"""
        self.load_config.emit()
    
    def load_config_from_dict(self, config_dict: dict) -> None:
        """从字典加载配置到界面"""
        for key, value in config_dict.items():
            if key in self._param_widgets:
                widget = self._param_widgets[key]
                if isinstance(widget, QSpinBox) and isinstance(value, (int, float)):
                    widget.setValue(int(value))
                elif isinstance(widget, QDoubleSpinBox) and isinstance(value, (int, float)):
                    widget.setValue(float(value))
                elif isinstance(widget, QCheckBox) and isinstance(value, bool):
                    widget.setChecked(value)

    def _reset_config(self) -> None:
        self._config.reload()
        strategies = self._config.strategies
        for stype, sdata in strategies.items():
            self._param_widgets[f"{stype}_enabled"].setChecked(sdata.get("enabled", True))
            params = sdata.get("params", {})
            for pname, pval in params.items():
                key = f"{stype}_{pname}"
                if key in self._param_widgets and isinstance(pval, (int, float)):
                    self._param_widgets[key].setValue(pval)

    def get_current_config(self) -> dict:
        result = {}
        for key, widget in self._param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                result[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                result[key] = widget.isChecked()
        return result