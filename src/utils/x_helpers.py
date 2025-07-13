#!/usr/bin/env python3
"""
X (Twitter) specific helper utilities for X scraper
"""

import re
from urllib.parse import urlparse

from loguru import logger


def validate_x_username(username: str) -> bool:
    """
    Validate X (Twitter) username format.

    Args:
        username: Username to validate (without @)

    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False

    # Remove @ if present
    username = username.lstrip("@")

    # X username requirements:
    # - 1-15 characters
    # - Only letters, numbers, and underscores
    # - Cannot be only numbers
    if not (1 <= len(username) <= 15):
        return False

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False

    # Cannot be only numbers
    return not username.isdigit()


def parse_x_url(url: str) -> dict[str, str | None]:
    """
    Parse X (Twitter) URL and extract relevant information.

    Args:
        url: X URL to parse

    Returns:
        Dictionary with parsed information
    """
    result = {
        "type": None,
        "username": None,
        "tweet_id": None,
        "is_valid": False,
        "original_url": url,
    }

    try:
        parsed = urlparse(url)

        if not _is_valid_x_domain(parsed.netloc):
            logger.debug(f"Invalid X domain: {parsed.netloc}")
            return result

        path_parts = [part for part in parsed.path.split("/") if part]

        if not path_parts:
            result["type"] = "home"
            result["is_valid"] = True
            return result

        # Determine URL type based on path
        result["type"] = _determine_url_type(path_parts)

        # Extract username from first path component
        if path_parts[0] not in ["i", "search", "settings", "messages", "notifications"]:
            username = path_parts[0]
            if validate_x_username(username):
                result["username"] = username

        # Extract tweet ID if this is a tweet URL
        if len(path_parts) >= 3 and path_parts[1] == "status":
            tweet_id = path_parts[2]
            if tweet_id.isdigit():
                result["tweet_id"] = tweet_id

        result["is_valid"] = True
        logger.debug(f"Parsed X URL: {result}")
        return result

    except Exception as e:
        logger.error(f"Error parsing X URL {url}: {e}")
        return result


def _is_valid_x_domain(netloc: str) -> bool:
    """Check if domain is a valid X domain."""
    valid_domains = ["x.com", "twitter.com", "mobile.x.com", "mobile.twitter.com"]
    return netloc.lower() in valid_domains


def _determine_url_type(path_parts: list[str]) -> str:
    """Determine URL type based on path components."""
    if not path_parts:
        return "home"

    first_part = path_parts[0].lower()

    if first_part == "search":
        return "search"
    elif first_part == "i":
        return "internal"
    elif first_part == "settings":
        return "settings"
    elif first_part == "messages":
        return "messages"
    elif first_part == "notifications":
        return "notifications"
    elif len(path_parts) >= 2 and path_parts[1] == "status":
        return "tweet"
    elif len(path_parts) >= 2 and path_parts[1] == "following":
        return "following"
    elif len(path_parts) >= 2 and path_parts[1] == "followers":
        return "followers"
    else:
        return "profile"
