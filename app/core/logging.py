from loguru import logger
import sys
from pathlib import Path

from app.core.config import config, BASE_DIR


def setup_logging():
    logger.remove()  # remove default logger

    log_cfg = config._config.get("logging", {})

    # Console sink
    logger.add(
        sys.stdout,
        level=log_cfg.get("level", "INFO"),
        format=log_cfg.get("format"),
        enqueue=True,
    )

    # File sink
    file_cfg = log_cfg.get("file", {})
    if file_cfg.get("enabled", False):
        log_path = BASE_DIR / file_cfg.get("path", "logs/app.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path),
            level=log_cfg.get("level", "INFO"),
            rotation=file_cfg.get("rotation", "10 MB"),
            retention=file_cfg.get("retention", "10 days"),
            enqueue=True,
        )

    logger.info("Logging initialized")


# expose singleton logger
log = logger
