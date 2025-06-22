#!/usr/bin/env python3
"""
Utility functions for X scraper
"""

import re
import sys
import time
from datetime import UTC, datetime
from typing import Final
from urllib.parse import urlparse

from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# Constants
DEFAULT_LOG_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
DEFAULT_LOG_LEVEL: Final[str] = "INFO"


def configure_logging(
    level: str | None = None,
    format_string: str = DEFAULT_LOG_FORMAT,
    remove_default: bool = True,
) -> None:
    """
    Configure loguru logger with specified settings.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses LOG_LEVEL environment variable or default.
        format_string: Log format string
        remove_default: Whether to remove default logger configuration
    """
    import os

    if level is None:
        level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    if remove_default:
        logger.remove()

    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
    )


def setup_file_logging(
    log_file: str = "logs/app.log",
    level: str = "DEBUG",
    rotation: str = "10 MB",
    retention: str = "1 week",
) -> None:
    """
    Add file logging to the configured logger.

    Args:
        log_file: Path to log file
        level: Log level for file logging
        rotation: When to rotate log files
        retention: How long to keep old log files
    """
    from pathlib import Path

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        level=level,
        rotation=rotation,
        retention=retention,
        format=DEFAULT_LOG_FORMAT,
    )


def wait_for_element(driver: WebDriver, by: str, value: str, timeout: int = 10, poll_frequency: float = 0.5) -> bool:
    """
    Wait for an element to be present on the page.

    Args:
        driver: WebDriver instance
        by: Locator strategy (By.ID, By.CLASS_NAME, etc.)
        value: Locator value
        timeout: Maximum wait time in seconds
        poll_frequency: Polling frequency in seconds

    Returns:
        True if element is found, False otherwise
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency).until(ec.presence_of_element_located((by, value)))  # type: ignore
        return True
    except TimeoutException:
        logger.warning(f"Element not found: {by}={value} within {timeout}s")
        return False


def wait_for_clickable(driver: WebDriver, by: str, value: str, timeout: int = 10, poll_frequency: float = 0.5) -> bool:
    """
    Wait for an element to be clickable.

    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value
        timeout: Maximum wait time in seconds
        poll_frequency: Polling frequency in seconds

    Returns:
        True if element is clickable, False otherwise
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency).until(ec.element_to_be_clickable((by, value)))  # type: ignore
        return True
    except TimeoutException:
        logger.warning(f"Element not clickable: {by}={value} within {timeout}s")
        return False


def safe_click(driver: WebDriver, by: str, value: str, timeout: int = 10) -> bool:
    """
    Safely click an element with error handling.

    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value
        timeout: Maximum wait time in seconds

    Returns:
        True if click was successful, False otherwise
    """
    try:
        if not wait_for_clickable(driver, by, value, timeout):
            return False

        element = driver.find_element(by, value)  # type: ignore
        element.click()
        return True

    except Exception as e:
        logger.error(f"Error clicking element {by}={value}: {e}")
        return False


def safe_send_keys(
    driver: WebDriver, by: str, value: str, text: str, timeout: int = 10, clear_first: bool = True
) -> bool:
    """
    Safely send keys to an element with error handling.

    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value
        text: Text to send
        timeout: Maximum wait time in seconds
        clear_first: Whether to clear the field first

    Returns:
        True if successful, False otherwise
    """
    try:
        if not wait_for_element(driver, by, value, timeout):
            return False

        element = driver.find_element(by, value)  # type: ignore
        if clear_first:
            element.clear()
        element.send_keys(text)
        return True

    except Exception as e:
        logger.error(f"Error sending keys to element {by}={value}: {e}")
        return False


def get_text_safe(driver: WebDriver, by: str, value: str) -> str | None:
    """
    Safely get text from an element.

    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value

    Returns:
        Element text if found, None otherwise
    """
    try:
        element = driver.find_element(by, value)  # type: ignore
        return element.text.strip()
    except NoSuchElementException:
        return None
    except Exception as e:
        logger.error(f"Error getting text from element {by}={value}: {e}")
        return None


def get_attribute_safe(driver: WebDriver, by: str, value: str, attribute: str) -> str | None:
    """
    Safely get attribute from an element.

    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value
        attribute: Attribute name

    Returns:
        Attribute value if found, None otherwise
    """
    try:
        element = driver.find_element(by, value)  # type: ignore
        return element.get_attribute(attribute)
    except NoSuchElementException:
        return None
    except Exception as e:
        logger.error(f"Error getting attribute {attribute} from element {by}={value}: {e}")
        return None


def scroll_to_element(driver: WebDriver, by: str, value: str) -> bool:
    """
    Scroll to an element on the page.

    Args:
        driver: WebDriver instance
        by: Locator strategy
        value: Locator value

    Returns:
        True if successful, False otherwise
    """
    try:
        element = driver.find_element(by, value)  # type: ignore
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        return True
    except Exception as e:
        logger.error(f"Error scrolling to element {by}={value}: {e}")
        return False


def scroll_page(driver: WebDriver, direction: str = "down", pixels: int = 500) -> None:
    """
    Scroll the page in the specified direction.

    Args:
        driver: WebDriver instance
        direction: "up" or "down"
        pixels: Number of pixels to scroll
    """
    if direction == "down":
        driver.execute_script(f"window.scrollBy(0, {pixels});")
    elif direction == "up":
        driver.execute_script(f"window.scrollBy(0, -{pixels});")


def wait_for_page_load(driver: WebDriver, timeout: int = 30) -> bool:
    """
    Wait for page to fully load.

    Args:
        driver: WebDriver instance
        timeout: Maximum wait time in seconds

    Returns:
        True if page loaded, False otherwise
    """
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        return True
    except TimeoutException:
        logger.warning(f"Page did not load within {timeout}s")
        return False


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Add a random delay to avoid detection.

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    import random

    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove non-printable characters first
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_urls_from_text(text: str) -> list[str]:
    """
    Extract URLs from text.

    Args:
        text: Input text

    Returns:
        List of URLs found in text
    """
    url_pattern = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
    return url_pattern.findall(text)


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
    Format timestamp to readable string.

    Args:
        timestamp: Unix timestamp or datetime string

    Returns:
        Formatted timestamp string
    """
    try:
        if isinstance(timestamp, str):
            return _format_iso_timestamp(timestamp)
        else:
            return _format_unix_timestamp(timestamp)
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {e}")
        return str(timestamp)


def _format_iso_timestamp(timestamp_str: str) -> str:
    """Format ISO datetime string."""
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _format_unix_timestamp(timestamp: int | float) -> str:
    """Format Unix timestamp."""
    dt = datetime.fromtimestamp(float(timestamp), tz=UTC)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_safe_filename(text: str, max_length: int = 200) -> str:
    """
    Create a safe filename from text.

    Args:
        text: Input text
        max_length: Maximum filename length

    Returns:
        Safe filename
    """
    # Replace unsafe characters
    safe_text = re.sub(r'[<>:"/\\|?*]', "_", text)

    # Remove extra whitespace and replace with underscores
    safe_text = re.sub(r"\s+", "_", safe_text)

    # Limit length
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]

    return safe_text.strip("_")


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to retry a function on failure.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Backoff multiplier

    Returns:
        Decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_retries:
                        raise

                    time.sleep(current_delay)
                    current_delay *= backoff_factor

        return wrapper

    return decorator


def get_user_agent() -> str:
    """
    Get a realistic user agent string.

    Returns:
        User agent string
    """
    return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def validate_x_username(username: str) -> bool:
    """
    Validate X (Twitter) username format.

    Args:
        username: Username to validate

    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False

    # Remove @ if present
    username = username.lstrip("@")

    # Check length (1-15 characters)
    if len(username) < 1 or len(username) > 15:
        return False

    # Check allowed characters (alphanumeric and underscore)
    return bool(re.match(r"^[a-zA-Z0-9_]+$", username))


def parse_x_url(url: str) -> dict[str, str | None]:
    """
    Parse X (Twitter) URL to extract components.

    Args:
        url: X URL to parse

    Returns:
        Dictionary with parsed components
    """
    result = {"username": None, "tweet_id": None, "url_type": None, "is_valid": False}

    try:
        parsed = urlparse(url)
        if not _is_valid_x_domain(parsed.netloc):
            return result

        path_parts = [p for p in parsed.path.split("/") if p]

        if not path_parts:
            return result

        # Extract username and determine URL type
        result["username"] = path_parts[0]
        result["is_valid"] = True
        result["url_type"] = _determine_url_type(path_parts)

        # Extract tweet ID if it's a tweet URL
        if result["url_type"] == "tweet" and len(path_parts) >= 3:
            result["tweet_id"] = path_parts[2]

    except Exception as e:
        logger.error(f"Error parsing X URL {url}: {e}")

    return result


def _is_valid_x_domain(netloc: str) -> bool:
    """Check if the netloc is a valid X domain."""
    return netloc in ["twitter.com", "x.com", "www.twitter.com", "www.x.com"]


def _determine_url_type(path_parts: list[str]) -> str:
    """Determine URL type based on path parts."""
    if len(path_parts) >= 2 and path_parts[1] == "status" and len(path_parts) >= 3:
        return "tweet"
    return "profile"


def find_element_by_selectors(driver: WebDriver, selectors: list[str], timeout: int = 5):
    """
    Try multiple CSS selectors and return the first found element.

    Args:
        driver: WebDriver instance
        selectors: List of CSS selectors to try
        timeout: Timeout for each selector attempt

    Returns:
        First found element or None
    """
    from selenium.webdriver.common.by import By

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.debug(f"Found element with selector: {selector}")
                return elements[0]
        except NoSuchElementException:
            continue
        except Exception as e:
            logger.debug(f"Error trying selector '{selector}': {e}")
            continue

    logger.debug(f"No elements found with any of the selectors: {selectors}")
    return None


def find_elements_by_selectors(driver: WebDriver, selectors: list[str]) -> list:
    """
    Try multiple CSS selectors and return elements from the first successful selector.

    Args:
        driver: WebDriver instance
        selectors: List of CSS selectors to try

    Returns:
        List of elements from first successful selector, empty list if none found
    """
    from selenium.webdriver.common.by import By

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                return elements
        except Exception as e:
            logger.debug(f"Error trying selector '{selector}': {e}")
            continue

    logger.debug(f"No elements found with any of the selectors: {selectors}")
    return []


def extract_text_by_selectors(element, selectors: list[str]) -> str:
    """
    Extract text content using multiple CSS selectors.

    Args:
        element: Selenium WebElement to search within
        selectors: List of CSS selectors to try

    Returns:
        Cleaned text content or empty string
    """
    from selenium.webdriver.common.by import By

    for selector in selectors:
        try:
            text_elements = element.find_elements(By.CSS_SELECTOR, selector)
            if text_elements:
                text_parts = []
                for elem in text_elements:
                    text = elem.text.strip()
                    if text:
                        text_parts.append(text)

                if text_parts:
                    combined_text = " ".join(text_parts).strip()
                    if combined_text:
                        logger.debug(f"Found text with selector: {selector}")
                        return clean_text(combined_text)
        except Exception as e:
            logger.debug(f"Error extracting text with selector '{selector}': {e}")
            continue

    return ""


def extract_count_by_selectors(element, selectors: list[str], parse_count_func) -> int:
    """
    Extract numeric count using multiple CSS selectors.

    Args:
        element: Selenium WebElement to search within
        selectors: List of CSS selectors to try
        parse_count_func: Function to parse count string to integer

    Returns:
        Parsed count as integer, 0 if not found or parsing fails
    """
    from selenium.webdriver.common.by import By

    for selector in selectors:
        try:
            count_elements = element.find_elements(By.CSS_SELECTOR, selector)
            for count_elem in count_elements:
                count_text = count_elem.text.strip()
                if count_text and any(c.isdigit() for c in count_text):
                    count = parse_count_func(count_text)
                    if count is not None and count >= 0:
                        logger.debug(f"Found count {count} with selector: {selector}")
                        return count
        except Exception as e:
            logger.debug(f"Error extracting count with selector '{selector}': {e}")
            continue

    return 0


def extract_attribute_by_selectors(element, selectors: list[str], attribute: str) -> str:
    """
    Extract attribute value using multiple CSS selectors.

    Args:
        element: Selenium WebElement to search within
        selectors: List of CSS selectors to try
        attribute: Attribute name to extract

    Returns:
        Attribute value or empty string
    """
    from selenium.webdriver.common.by import By

    for selector in selectors:
        try:
            attr_elements = element.find_elements(By.CSS_SELECTOR, selector)
            for attr_elem in attr_elements:
                attr_value = attr_elem.get_attribute(attribute)
                if attr_value:
                    logger.debug(f"Found {attribute} attribute with selector: {selector}")
                    return attr_value.strip()
        except Exception as e:
            logger.debug(f"Error extracting {attribute} with selector '{selector}': {e}")
            continue

    return ""


def extract_text_from_driver_by_selectors(driver: WebDriver | None, selectors: list[str]) -> str:
    """
    Extract text content from driver using multiple CSS selectors.

    Args:
        driver: WebDriver instance (can be None)
        selectors: List of CSS selectors to try

    Returns:
        Cleaned text content or empty string
    """
    from selenium.webdriver.common.by import By

    if not driver:
        return ""

    for selector in selectors:
        try:
            text_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if text_elements:
                text_parts = []
                for elem in text_elements:
                    text = elem.text.strip()
                    if text:
                        text_parts.append(text)

                if text_parts:
                    combined_text = " ".join(text_parts).strip()
                    if combined_text:
                        logger.debug(f"Found text with selector: {selector}")
                        return clean_text(combined_text)
        except Exception as e:
            logger.debug(f"Error extracting text with selector '{selector}': {e}")
            continue

    return ""


def extract_attribute_from_driver_by_selectors(driver: WebDriver | None, selectors: list[str], attribute: str) -> str:
    """
    Extract attribute value from driver using multiple CSS selectors.

    Args:
        driver: WebDriver instance (can be None)
        selectors: List of CSS selectors to try
        attribute: Attribute name to extract

    Returns:
        Attribute value or empty string
    """
    from selenium.webdriver.common.by import By

    if not driver:
        return ""

    for selector in selectors:
        try:
            attr_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for attr_elem in attr_elements:
                attr_value = attr_elem.get_attribute(attribute)
                if attr_value:
                    logger.debug(f"Found {attribute} attribute with selector: {selector}")
                    return attr_value.strip()
        except Exception as e:
            logger.debug(f"Error extracting {attribute} with selector '{selector}': {e}")
            continue

    return ""
