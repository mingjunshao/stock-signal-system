"""日志管理：文件日志+控制台输出，支持自动项目目录识别和按日期分割"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime


# 全局日志目录（延迟初始化）
_global_log_dir: Optional[Path] = None
# 记录所有创建的 logger，以便之后统一添加文件处理器
_all_loggers: list[logging.Logger] = []


def set_global_log_dir(log_dir: Path) -> None:
    """设置全局日志目录，并给所有已有 logger 添加文件处理器

    Args:
        log_dir: 日志文件存放目录
    """
    global _global_log_dir
    _global_log_dir = log_dir

    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.log"

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 给所有已创建的 logger 添加文件处理器
    for logger in _all_loggers:
        has_file_handler = any(
            isinstance(handler, logging.FileHandler) for handler in logger.handlers)
        if not has_file_handler:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)


def get_global_log_dir() -> Optional[Path]:
    """获取全局日志目录

    Returns:
        日志目录 Path 对象，未设置时返回 None
    """
    return _global_log_dir


def setup_logger(name: str = "stock_signal",
                 log_dir: Optional[Path] = None,
                 level: int = logging.INFO) -> logging.Logger:
    """创建或获取 logger

    Args:
        name: logger 名称
        log_dir: 日志文件目录（可选，默认使用全局目录）
        level: 日志级别

    Returns:
        配置好的 logger 对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    # 文件输出（如果此时有可用的日志目录）
    effective_log_dir = log_dir or _global_log_dir
    if effective_log_dir:
        effective_log_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = effective_log_dir / f"{today}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    # 记录这个 logger，以便之后设置全局目录时补文件处理器
    if logger not in _all_loggers:
        _all_loggers.append(logger)

    return logger
