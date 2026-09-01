"""统一日志基础设施：文件 + 可选控制台双输出，级别可调，幂等初始化。

入口调用一次 setup_logging()，其余模块用 get_logger(__name__) 取日志器。

级别：环境变量 SB_LOG_LEVEL（DEBUG/INFO/WARNING/ERROR），默认 INFO。
日志文件：<src 上级>/logs/translation_<时间戳>.log；该目录不可写时回退到用户主目录。
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

_initialized = False
_log_file_path = None

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"


def _default_log_dir():
    import sys
    if getattr(sys, "frozen", False):
        # 打包后（onefile 下 __file__ 指向临时目录），日志写到 exe 同级
        return Path(sys.executable).resolve().parent / "logs"
    return Path(__file__).resolve().parent / "logs"


def _make_log_dir(log_dir):
    """确保日志目录可用；目标目录不可写时回退到用户主目录。"""
    for candidate in (Path(log_dir), Path.home() / ".starbound_tools_logs"):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            continue
    return Path(log_dir)  # 都失败则原样返回，交由 FileHandler 报错


def setup_logging(log_dir=None, level=None, console=True):
    """幂等初始化根日志器，返回 (logger, 日志文件路径)。"""
    global _initialized, _log_file_path
    if _initialized:
        return logging.getLogger(), _log_file_path

    if level is None:
        level = os.environ.get("SB_LOG_LEVEL", "INFO").upper()
    numeric = _LOG_LEVELS.get(level, logging.INFO)

    if log_dir is None:
        log_dir = _default_log_dir()
    log_dir = _make_log_dir(log_dir)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file_path = log_dir / f"translation_{ts}.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # 根级别放开，由各 handler 控制
    formatter = logging.Formatter(_FORMAT)

    fh = logging.FileHandler(_log_file_path, encoding="utf-8")
    fh.setLevel(numeric)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    if console:
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(numeric)
        sh.setFormatter(formatter)
        root.addHandler(sh)

    _initialized = True
    return root, _log_file_path


def get_logger(name=None):
    """获取日志器；未初始化时自动以仅文件模式初始化。"""
    if not _initialized:
        setup_logging(console=False)
    return logging.getLogger(name)


def get_log_file_path():
    """返回当前日志文件路径（未初始化则为 None）。"""
    return _log_file_path
