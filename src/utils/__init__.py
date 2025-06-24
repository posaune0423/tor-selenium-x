"""
Utility functions for X scraper - modularized package
"""

# Logger utilities
from .logger import configure_logging, setup_file_logging

# Selenium helper functions (used in tests)
from .selenium_helpers import (
    take_screenshot,
    wait_for_element,
)

# Text processing utilities (used in tests and potentially by x_scraper)
from .text_processing import (
    clean_text,
    create_safe_filename,
    extract_urls_from_text,
    format_timestamp,
    is_valid_url,
    parse_engagement_count,
)

# Tor utilities (used by x_scraper)
from .tor_helpers import (
    create_tor_browser_driver,
    verify_tor_connection,
)

# X (Twitter) specific helpers (used in tests)
from .x_helpers import (
    parse_x_url,
    validate_x_username,
)

__all__ = [
    "clean_text",
    "configure_logging",
    "create_safe_filename",
    "create_tor_browser_driver",
    "extract_urls_from_text",
    "format_timestamp",
    "is_valid_url",
    "parse_engagement_count",
    "parse_x_url",
    "setup_file_logging",
    "take_screenshot",
    "validate_x_username",
    "verify_tor_connection",
    "wait_for_element",
]
