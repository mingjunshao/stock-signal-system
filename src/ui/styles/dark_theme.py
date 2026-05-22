"""深色主题样式"""

DARK_THEME_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #45475a;
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
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 15px;
    min-height: 25px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 3px 8px;
    min-height: 22px;
}
QTableWidget {
    background-color: #1e1e2e;
    gridline-color: #45475a;
    border: 1px solid #45475a;
}
QTableWidget::item {
    padding: 3px;
}
QHeaderView::section {
    background-color: #313244;
    border: 1px solid #45475a;
    padding: 3px;
    font-weight: bold;
}
QTextEdit {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 4px;
}
QProgressBar {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #a6e3a1;
    border-radius: 3px;
}
QCheckBox {
    spacing: 5px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QTabWidget::pane {
    border: 1px solid #45475a;
}
QTabBar::tab {
    background-color: #313244;
    border: 1px solid #45475a;
    padding: 5px 10px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #45475a;
}
QListWidget {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 4px;
}
QListWidget::item {
    padding: 3px;
}
QListWidget::item:selected {
    background-color: #45475a;
}
QLabel {
    color: #cdd6f4;
}
QSplitter::handle {
    background-color: #45475a;
}
"""