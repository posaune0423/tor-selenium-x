#!/usr/bin/env python3
"""
Utility functions for X scraper
"""

import re
import time
from datetime import datetime
from urllib.parse import urlparse

from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def wait_for_element(driver: WebDriver, by: By, value: str, timeout: int = 10, poll_frequency: float = 0.5) -> bool:
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


def wait_for_clickable(driver: WebDriver, by: By, value: str, timeout: int = 10, poll_frequency: float = 0.5) -> bool:
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


def safe_click(driver: WebDriver, by: By, value: str, timeout: int = 10) -> bool:
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
        if wait_for_clickable(driver, by, value, timeout):
            element = driver.find_element(by, value)  # type: ignore
            element.click()
            return True
        return False
    except Exception as e:
        logger.error(f"Error clicking element {by}={value}: {e}")
        return False


def safe_send_keys(
    driver: WebDriver, by: By, value: str, text: str, timeout: int = 10, clear_first: bool = True
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
        if wait_for_element(driver, by, value, timeout):
            element = driver.find_element(by, value)  # type: ignore
            if clear_first:
                element.clear()
            element.send_keys(text)
            return True
        return False
    except Exception as e:
        logger.error(f"Error sending keys to element {by}={value}: {e}")
        return False


def get_text_safe(driver: WebDriver, by: By, value: str) -> str | None:
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


def get_attribute_safe(driver: WebDriver, by: By, value: str, attribute: str) -> str | None:
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


def scroll_to_element(driver: WebDriver, by: By, value: str) -> bool:
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

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove non-printable characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

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
            # Try to parse as datetime string
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Assume unix timestamp
            dt = datetime.fromtimestamp(float(timestamp))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {e}")
        return str(timestamp)


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


def retry_on_failure(
    func, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function on failure.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Backoff multiplier
        exceptions: Exceptions to catch

    Returns:
        Decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
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
        if parsed.netloc not in ["twitter.com", "x.com", "www.twitter.com", "www.x.com"]:
            return result

        path_parts = [p for p in parsed.path.split("/") if p]

        if len(path_parts) >= 1:
            result["username"] = path_parts[0]
            result["is_valid"] = True

            if len(path_parts) >= 2:
                if path_parts[1] == "status" and len(path_parts) >= 3:
                    result["tweet_id"] = path_parts[2]
                    result["url_type"] = "tweet"
                else:
                    result["url_type"] = "profile"
            else:
                result["url_type"] = "profile"

    except Exception as e:
        logger.error(f"Error parsing X URL {url}: {e}")

    return result
