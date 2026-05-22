"""A股日线高抛低吸交易信号系统 - 入口"""

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import Config
from src.core.logger import setup_logger
from src.ui.main_window import MainWindow


def main():
    config_path = project_root / "config.yaml"
    config = Config(str(config_path))

    # 设置全局日志目录，这样所有模块的 logger 都能写入文件
    log_dir = project_root / "logs"
    from src.core.logger import set_global_log_dir
    set_global_log_dir(log_dir)

    # 主 logger 也用这个目录
    logger = setup_logger("stock_signal", log_dir=log_dir)

    app = QApplication(sys.argv)
    app.setApplicationName("A股交易信号系统")

    window = MainWindow(config)
    window.show()

    logger.info("系统启动")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()