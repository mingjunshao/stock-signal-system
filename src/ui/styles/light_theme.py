"""浅色主题样式"""

LIGHT_THEME_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}
QWidget {
    background-color: #f5f5f5;
    color: #333333;
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px 15px;
    min-height: 25px;
}
QPushButton:hover {
    background-color: #e8e8e8;
}
QPushButton:pressed {
    background-color: #d0d0d0;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 3px 8px;
    min-height: 22px;
}
QTableWidget {
    background-color: #ffffff;
    gridline-color: #cccccc;
    border: 1px solid #cccccc;
}
QTableWidget::item {
    padding: 3px;
}
QHeaderView::section {
    background-color: #e8e8e8;
    border: 1px solid #cccccc;
    padding: 3px;
    font-weight: bold;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
}
QProgressBar {
    background-color: #e8e8e8;
    border: 1px solid #cccccc;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #4caf50;
    border-radius: 3px;
}
QTabWidget::pane {
    border: 1px solid #cccccc;
}
QTabBar::tab {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    padding: 5px 10px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #e8e8e8;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #e8e8e8;
}
"""