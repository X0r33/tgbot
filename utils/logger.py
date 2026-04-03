# utils/logger.py — логування у файл та консоль

import logging
import sys
from config import LOG_PATH


def setup_logger() -> logging.Logger:
    """Налаштовує та повертає логер."""
    logger = logging.getLogger("filebot")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Файловий хендлер
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    # Консольний хендлер
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


logger = setup_logger()
