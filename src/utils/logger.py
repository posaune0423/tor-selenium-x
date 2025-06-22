#!/usr/bin/env python3
"""
Logger configuration utilities for X scraper
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Final

from loguru import logger

# Constants
DEFAULT_LOG_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
LOG_DIR: Final[Path] = Path("reports/logs")


def configure_logging(
    level: str | None = None,
    format_string: str = DEFAULT_LOG_FORMAT,
    remove_default: bool = True,
    enable_file_logging: bool = True,
) -> None:
    """
    Configure loguru logger with specified settings.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses LOG_LEVEL environment variable or default.
        format_string: Log format string
        remove_default: Whether to remove default logger configuration
        enable_file_logging: Whether to enable file logging
    """
    import os

    if level is None:
        level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    if remove_default:
        logger.remove()

    # Console logging
    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
    )

    # File logging with timestamp-based filename
    if enable_file_logging:
        setup_file_logging(level=level)


def setup_file_logging(
    level: str = "DEBUG",
    rotation: str = "10 MB",
    retention: str = "1 week",
) -> None:
    """
    Add file logging to the configured logger with timestamp-based naming.

    Args:
        level: Log level for file logging
        rotation: When to rotate log files
        retention: How long to keep old log files
    """
    # Create logs directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamp-based log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"x_scraper_{timestamp}.log"

    logger.add(
        str(log_file),
        level=level,
        rotation=rotation,
        retention=retention,
        format=DEFAULT_LOG_FORMAT,
        enqueue=True,  # Make logging thread-safe
        diagnose=True,  # Show variable values in exception traceback
    )

    # Also add a latest.log symlink for easy access
    latest_log = LOG_DIR / "latest.log"
    try:
        if latest_log.exists():
            latest_log.unlink()
        latest_log.symlink_to(log_file.name)
    except (OSError, NotImplementedError):
        # Symlinks might not be supported on all platforms
        pass

    logger.info(f"File logging enabled: {log_file}")


def get_log_files() -> list[Path]:
    """
    Get list of all log files in the logs directory.

    Returns:
        List of log file paths
    """
    if not LOG_DIR.exists():
        return []

    return sorted(LOG_DIR.glob("*.log"))


def cleanup_old_logs(keep_count: int = 10) -> None:
    """
    Clean up old log files, keeping only the most recent ones.

    Args:
        keep_count: Number of log files to keep
    """
    log_files = get_log_files()
    if len(log_files) <= keep_count:
        return

    # Keep the most recent files
    files_to_remove = log_files[:-keep_count]
    for log_file in files_to_remove:
        try:
            log_file.unlink()
            logger.debug(f"Removed old log file: {log_file}")
        except OSError as e:
            logger.warning(f"Failed to remove log file {log_file}: {e}")
