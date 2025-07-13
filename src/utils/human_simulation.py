#!/usr/bin/env python3
"""
Human simulation utilities for X scraper
"""

import random
import time

from loguru import logger


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Random delay to simulate human behavior.

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Random delay: {delay:.2f}s")
    time.sleep(delay)


def human_typing_delay(text: str, base_delay: float = 0.1, variance: float = 0.05) -> None:
    """
    Simulate human typing delay based on text length.

    Args:
        text: Text that was typed
        base_delay: Base delay per character
        variance: Random variance in delay
    """
    if not text:
        return

    char_count = len(text)

    # Calculate delay: base time per character + random variance
    total_delay = char_count * base_delay
    variance_delay = random.uniform(-variance, variance) * char_count
    final_delay = max(0.01, total_delay + variance_delay)  # Minimum 0.01s

    logger.debug(f"Human typing delay for {char_count} chars: {final_delay:.3f}s")
    time.sleep(final_delay)


def simulate_human_click_delay() -> None:
    """Simulate human click delay - brief pause before clicking."""
    delay = random.uniform(0.1, 0.3)
    logger.debug(f"Human click delay: {delay:.3f}s")
    time.sleep(delay)
