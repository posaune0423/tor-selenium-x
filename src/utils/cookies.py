#!/usr/bin/env python3
"""
Cookie management utilities for X scraper
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger


def save_cookies_to_file(cookies: list[dict], filepath: str) -> bool:
    """
    Save cookies to a JSON file.

    Args:
        cookies: List of cookie dictionaries
        filepath: Path to save cookies

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        file_path = Path(filepath)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp for tracking
        cookie_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "cookies": cookies,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(cookies)} cookies to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Error saving cookies to {filepath}: {e}")
        return False


def load_cookies_from_file(filepath: str) -> list[dict]:
    """
    Load cookies from a JSON file.

    Args:
        filepath: Path to cookie file

    Returns:
        List of cookie dictionaries, empty list if error
    """
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            logger.debug(f"Cookie file does not exist: {filepath}")
            return []

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Handle both old format (direct list) and new format (with timestamp)
        if isinstance(data, list):
            cookies = data
        elif isinstance(data, dict) and "cookies" in data:
            cookies = data["cookies"]
        else:
            logger.warning(f"Invalid cookie file format: {filepath}")
            return []

        logger.info(f"Loaded {len(cookies)} cookies from {filepath}")
        return cookies

    except Exception as e:
        logger.error(f"Error loading cookies from {filepath}: {e}")
        return []


def are_cookies_expired(cookies: list[dict]) -> bool:
    """
    Check if cookies are expired or about to expire.

    Args:
        cookies: List of cookie dictionaries

    Returns:
        True if cookies are expired, False otherwise
    """
    if not cookies:
        return True

    try:
        current_time = datetime.now(UTC).timestamp()

        for cookie in cookies:
            expiry = cookie.get("expiry")
            if expiry is None:
                continue  # Session cookies don't expire

            # Check if cookie expires within next 5 minutes
            if expiry - current_time < 300:  # 5 minutes buffer
                logger.debug(f"Cookie '{cookie.get('name', 'unknown')}' expires soon")
                return True

        logger.debug("Cookies are still valid")
        return False

    except Exception as e:
        logger.warning(f"Error checking cookie expiry: {e}")
        return True  # Consider expired if we can't check
