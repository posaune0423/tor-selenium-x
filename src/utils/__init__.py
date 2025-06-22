"""
Utility functions for X scraper - modularized package
"""

# Logger utilities
# Anti-detection utilities
from .anti_detection import (
    add_anti_detection_measures,
    detect_and_handle_captcha,
    get_user_agent,
    safe_click_element,
)

# Cookie management
from .cookies import (
    are_cookies_expired,
    load_cookies_from_file,
    save_cookies_to_file,
)

# Utility decorators
from .decorators import retry_on_failure

# Human simulation utilities
from .human_simulation import (
    human_typing_delay,
    random_delay,
    simulate_human_click_delay,
)
from .logger import configure_logging, setup_file_logging

# Selector utilities
from .selectors import (
    extract_attribute_by_selectors,
    extract_attribute_from_driver_by_selectors,
    extract_count_by_selectors,
    extract_text_by_selectors,
    extract_text_from_driver_by_selectors,
    find_element_by_selectors,
    find_elements_by_selectors,
)

# Selenium helper functions
from .selenium_helpers import (
    get_attribute_safe,
    get_text_safe,
    safe_click,
    safe_send_keys,
    scroll_page,
    scroll_to_element,
    wait_for_clickable,
    wait_for_element,
    wait_for_element_clickable,
    wait_for_page_load,
)

# Text processing utilities
from .text_processing import (
    clean_text,
    create_safe_filename,
    extract_urls_from_text,
    format_timestamp,
    is_valid_url,
    parse_engagement_count,
)

# X (Twitter) specific helpers
from .x_helpers import (
    parse_x_url,
    validate_x_username,
)

__all__ = [
    "add_anti_detection_measures",
    "are_cookies_expired",
    "clean_text",
    "configure_logging",
    "create_safe_filename",
    "detect_and_handle_captcha",
    "extract_attribute_by_selectors",
    "extract_attribute_from_driver_by_selectors",
    "extract_count_by_selectors",
    "extract_text_by_selectors",
    "extract_text_from_driver_by_selectors",
    "extract_urls_from_text",
    "find_element_by_selectors",
    "find_elements_by_selectors",
    "format_timestamp",
    "get_attribute_safe",
    "get_text_safe",
    "get_user_agent",
    "human_typing_delay",
    "is_valid_url",
    "load_cookies_from_file",
    "parse_engagement_count",
    "parse_x_url",
    "random_delay",
    "retry_on_failure",
    "safe_click",
    "safe_click_element",
    "safe_send_keys",
    "save_cookies_to_file",
    "scroll_page",
    "scroll_to_element",
    "setup_file_logging",
    "simulate_human_click_delay",
    "validate_x_username",
    "wait_for_clickable",
    "wait_for_element",
    "wait_for_element_clickable",
    "wait_for_page_load",
]
