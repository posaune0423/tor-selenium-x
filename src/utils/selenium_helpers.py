#!/usr/bin/env python3
"""
Selenium helper utilities for X scraper
"""

from datetime import datetime
from pathlib import Path

from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


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
        return element.text
    except NoSuchElementException:
        logger.debug(f"Element not found for text extraction: {by}={value}")
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
        attribute: Attribute name to get

    Returns:
        Attribute value if found, None otherwise
    """
    try:
        element = driver.find_element(by, value)  # type: ignore
        return element.get_attribute(attribute)
    except NoSuchElementException:
        logger.debug(f"Element not found for attribute extraction: {by}={value}")
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
    Scroll the page by specified pixels.

    Args:
        driver: WebDriver instance
        direction: Scroll direction ("up" or "down")
        pixels: Number of pixels to scroll
    """
    scroll_pixels = pixels if direction == "down" else -pixels
    driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")


def wait_for_page_load(driver: WebDriver, timeout: int = 30) -> bool:
    """
    Wait for page to finish loading.

    Args:
        driver: WebDriver instance
        timeout: Maximum wait time in seconds

    Returns:
        True if page loaded, False if timeout
    """
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        return True
    except TimeoutException:
        logger.warning(f"Page load timeout after {timeout}s")
        return False


def wait_for_element_clickable(driver: WebDriver, selector: str, timeout: int = 30) -> bool:
    """
    Wait for element to be clickable using CSS selector.

    Args:
        driver: WebDriver instance
        selector: CSS selector
        timeout: Maximum wait time in seconds

    Returns:
        True if element is clickable, False otherwise
    """
    from selenium.webdriver.common.by import By

    try:
        WebDriverWait(driver, timeout).until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        return True
    except TimeoutException:
        logger.debug(f"Element not clickable within {timeout}s: {selector}")
        return False
    except Exception as e:
        logger.error(f"Error waiting for clickable element {selector}: {e}")
        return False


def take_screenshot(driver: WebDriver, filename: str | None = None, output_dir: str = "data/screenshots") -> str | None:
    """
    Take a screenshot of the current page with enhanced reliability

    Args:
        driver: WebDriver instance
        filename: Filename to save (without extension). If None, uses timestamp
        output_dir: Directory to save screenshots

    Returns:
        str | None: Path to saved screenshot file, None if failed
    """
    if not driver:
        logger.error("Driver not initialized - cannot take screenshot")
        return None

    try:
        # Create screenshot directory with detailed logging
        screenshot_dir = Path(output_dir)
        logger.info(f"📁 Creating screenshot directory: {screenshot_dir.absolute()}")

        try:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directory created/verified: {screenshot_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to create directory {screenshot_dir}: {e}")
            return None

        # Check directory permissions
        try:
            test_file = screenshot_dir / "test_write_permission.tmp"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            logger.info("✅ Directory write permission verified")
        except Exception as e:
            logger.error(f"❌ Directory write permission failed: {e}")
            return None

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}"

        # Sanitize filename and add .png extension if not present
        import re

        safe_filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        if not safe_filename.endswith(".png"):
            safe_filename = f"{safe_filename}.png"

        # Full path
        screenshot_path = screenshot_dir / safe_filename
        logger.info(f"📸 Taking screenshot: {screenshot_path.absolute()}")

        # Check driver state before screenshot
        try:
            current_url = driver.current_url
            page_title = driver.title or "No title"
            window_size = driver.get_window_size()
            logger.info(f"🌐 Page state - URL: {current_url}, Title: {page_title}, Size: {window_size}")
        except Exception as e:
            logger.warning(f"Failed to get page state: {e}")

        # Take screenshot with retry mechanism
        max_retries = 3
        screenshot_success = False

        for attempt in range(max_retries):
            try:
                logger.info(f"📸 Screenshot attempt {attempt + 1}/{max_retries}")
                screenshot_success = driver.save_screenshot(str(screenshot_path))

                if screenshot_success:
                    logger.info("✅ Driver save_screenshot() returned True")
                    break
                else:
                    logger.warning(f"⚠️ Driver save_screenshot() returned False on attempt {attempt + 1}")

            except Exception as e:
                logger.error(f"❌ Screenshot attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None

        # Verify file was actually created and has content
        if screenshot_path.exists():
            file_size = screenshot_path.stat().st_size
            if file_size > 0:
                logger.info(f"✅ Screenshot saved successfully: {screenshot_path} ({file_size:,} bytes)")

                # Additional verification - try to read the file
                try:
                    with open(screenshot_path, "rb") as f:
                        header = f.read(8)
                    # PNG files start with specific byte sequence
                    if header.startswith(b"\x89PNG\r\n\x1a\n"):
                        logger.info("✅ PNG file format verified")
                    else:
                        logger.warning("⚠️ File created but may not be valid PNG format")
                except Exception as e:
                    logger.warning(f"⚠️ Could not verify PNG format: {e}")

                return str(screenshot_path)
            else:
                logger.error(f"❌ Screenshot file created but empty: {screenshot_path}")
                # Try to remove empty file
                import contextlib

                with contextlib.suppress(Exception):
                    screenshot_path.unlink()
                return None
        else:
            logger.error(f"❌ Screenshot file not found after save: {screenshot_path}")
            return None

    except Exception as e:
        logger.error(f"❌ Unexpected error in take_screenshot: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return None
