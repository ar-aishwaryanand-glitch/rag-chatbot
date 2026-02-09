"""Centralized logging configuration for RAG Agent."""

import logging
import os
import sys
from typing import Optional


def get_log_level() -> int:
    """Get log level from environment variable."""
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_str, logging.INFO)


def configure_logging(
    name: Optional[str] = None,
    level: Optional[int] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    Args:
        name: Logger name (uses module name if None)
        level: Log level (uses LOG_LEVEL env var if None)
        format_string: Custom format string (uses default if None)

    Returns:
        Configured logger instance
    """
    if level is None:
        level = get_log_level()

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure the root logger if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(format_string))
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

    # Get or create the named logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the standard configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return configure_logging(name)


# Pre-configure common loggers to reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
