import logging
import sys
from datetime import datetime


def setup_logger(name: str = "cawncade", level: str = None) -> logging.Logger:
    """
    Configure and return a structured logger instance.
    Level is read from settings.LOG_LEVEL (HF Variable: LOG_LEVEL).
    Falls back to INFO if not set or invalid.
    """
    if level is None:
        try:
            from app.config.settings import get_settings
            _settings = get_settings()
            level = getattr(_settings, "LOG_LEVEL", "INFO") or "INFO"
        except Exception:
            level = "INFO"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Ensure sys.stdout handles UTF-8 encoding safely on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(handler)
    return logger


# Shared logger instance — reads LOG_LEVEL from HF Variables automatically
log = setup_logger()
