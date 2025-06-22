#!/usr/bin/env python3
"""
Text processing utilities for X scraper
"""

import re
from datetime import UTC, datetime
from urllib.parse import urlparse

from loguru import logger


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing line breaks.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Normalize line breaks and remove extra whitespace
    cleaned = re.sub(r"\s+", " ", text.strip())

    # Remove common Unicode characters that might cause issues
    cleaned = cleaned.replace("\u200b", "")  # Zero-width space
    cleaned = cleaned.replace("\u200c", "")  # Zero-width non-joiner
    cleaned = cleaned.replace("\u200d", "")  # Zero-width joiner
    cleaned = cleaned.replace("\ufeff", "")  # Byte order mark

    return cleaned


def extract_urls_from_text(text: str) -> list[str]:
    """
    Extract URLs from text using regex.

    Args:
        text: Text to extract URLs from

    Returns:
        List of found URLs
    """
    if not text:
        return []

    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?)]'
    urls = re.findall(url_pattern, text)
    return urls


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def format_timestamp(timestamp: int | float | str) -> str:
    """
    Format various timestamp formats to ISO string.

    Args:
        timestamp: Unix timestamp, ISO string, or other timestamp format

    Returns:
        ISO format timestamp string
    """
    try:
        if isinstance(timestamp, str):
            return _format_iso_timestamp(timestamp)
        elif isinstance(timestamp, int | float):
            return _format_unix_timestamp(timestamp)
        else:
            return datetime.now(UTC).isoformat()
    except Exception as e:
        logger.debug(f"Error formatting timestamp {timestamp}: {e}")
        return datetime.now(UTC).isoformat()


def _format_iso_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp string."""
    # If already ISO format, return as-is
    if "T" in timestamp_str and ("Z" in timestamp_str or "+" in timestamp_str):
        return timestamp_str
    # Otherwise return current time
    return datetime.now(UTC).isoformat()


def _format_unix_timestamp(timestamp: int | float) -> str:
    """Format Unix timestamp to ISO string."""
    return datetime.fromtimestamp(timestamp, UTC).isoformat()


def create_safe_filename(text: str, max_length: int = 200) -> str:
    """
    Create a safe filename from text.

    Args:
        text: Original text
        max_length: Maximum filename length

    Returns:
        Safe filename string
    """
    if not text:
        return "untitled"

    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", text)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip("._")

    # Limit length
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip("._")

    # Ensure it's not empty
    if not filename:
        filename = "untitled"

    return filename


def parse_engagement_count(text: str | None) -> int | None:
    """
    Parse engagement count text (e.g., "1.2K", "10M") to integer.

    Args:
        text: Count string to parse

    Returns:
        Parsed count as integer, None if parsing fails
    """
    if not text:
        return None

    # Clean and normalize the string
    text = text.strip().replace(",", "")
    if not text:
        return None

    try:
        # Convert to uppercase for case-insensitive matching
        upper_text = text.upper()

        # Extract numeric part
        num_str = ""
        for char in upper_text:
            if char.isdigit() or char == ".":
                num_str += char
            elif char in ["K", "M", "B"]:
                break

        if not num_str:
            return None

        num = float(num_str)

        # Apply multipliers based on suffix
        if "K" in upper_text:
            return int(num * 1000)
        elif "M" in upper_text:
            return int(num * 1000000)
        elif "B" in upper_text:
            return int(num * 1000000000)
        else:
            return int(num)

    except (ValueError, TypeError) as e:
        logger.debug(f"Failed to parse engagement count '{text}': {e}")
        return None
