#!/usr/bin/env python3
"""
Decorator utilities for X scraper
"""

import time
from functools import wraps

from loguru import logger


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor by which delay increases after each failure

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            return None  # This should never be reached

        return wrapper

    return decorator
