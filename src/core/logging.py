"""
Logging configuration for the application.
"""

import logging
import sys

from src.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure application logging.

    Args:
        settings: Application settings containing log level
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("google.cloud").setLevel(logging.WARNING)
    logging.getLogger("firebase_admin").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.log_level}")
