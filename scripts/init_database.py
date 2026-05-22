"""数据库初始化脚本"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import Config
from src.core.database import DatabaseManager
from src.core.logger import setup_logger


def main():
    config = Config(str(project_root / "config.yaml"))
    logger = setup_logger("init_db", log_dir=project_root / "logs")

    db_path = config.get_db_path()
    logger.info(f"初始化数据库: {db_path}")

    db = DatabaseManager(db_path)
    db.init_tables()

    logger.info("数据库初始化完成")
    db.close()


if __name__ == "__main__":
    main()