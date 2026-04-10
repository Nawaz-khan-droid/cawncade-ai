import logging
import sys
from datetime import datetime


def setup_logger(name: str = "cawncade", level: str = "INFO") -> logging.Logger:
    """Configure and return a structured logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(handler)
    return logger


# Shared logger instance
log = setup_logger()
