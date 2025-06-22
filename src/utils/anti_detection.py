#!/usr/bin/env python3
"""
Anti-detection utilities for X scraper
"""

import random
import time

from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def detect_and_handle_captcha(driver: WebDriver) -> bool:
    """
    Detect and alert about CAPTCHA presence.

    Args:
        driver: WebDriver instance

    Returns:
        True if no CAPTCHA detected, False if CAPTCHA found
    """
    try:
        # Common CAPTCHA selectors
        captcha_selectors = [
            "#challenge-running",  # X CAPTCHA
            ".captcha",
            "[data-testid='captcha']",
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            ".recaptcha",
            "#recaptcha",
            "[aria-label*='captcha']",
            "[aria-label*='Captcha']",
            ".arkose-challenge",  # Arkose Labs
            "#arkose-challenge",
            "[data-arkose]",
        ]

        for selector in captcha_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Check if element is visible
                    for element in elements:
                        if element.is_displayed():
                            logger.warning(f"CAPTCHA detected with selector: {selector}")
                            return False
            except Exception as e:
                logger.debug(f"Error checking CAPTCHA selector {selector}: {e}")
                continue

        # Check page source for CAPTCHA-related text
        page_source = driver.page_source.lower()
        captcha_keywords = [
            "captcha",
            "recaptcha",
            "i'm not a robot",
            "verify you are human",
            "prove you're not a robot",
            "security challenge",
            "arkose",
        ]

        for keyword in captcha_keywords:
            if keyword in page_source:
                logger.warning(f"CAPTCHA-related content detected: {keyword}")
                return False

        logger.debug("No CAPTCHA detected")
        return True

    except Exception as e:
        logger.error(f"Error during CAPTCHA detection: {e}")
        return False


def add_anti_detection_measures(driver: WebDriver) -> None:
    """
    Add anti-detection measures to the browser.

    Args:
        driver: WebDriver instance
    """
    try:
        logger.info("Applying anti-detection measures...")

        # Disable webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Override plugins length
        driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [{filename: "internal-pdf-viewer", description: "Portable Document Format"}]
            });
        """)

        # Override languages
        driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        # Override permissions API
        driver.execute_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        # Override Chrome runtime
        driver.execute_script("""
            window.chrome = {
                runtime: {}
            };
        """)

        # Remove selenium indicators
        driver.execute_script("""
            delete window.navigator.__proto__.webdriver;
            delete window.navigator.webdriver;
            delete window.webdriver;
        """)

        logger.debug("Anti-detection measures applied successfully")

    except Exception as e:
        logger.warning(f"Error applying anti-detection measures: {e}")


def get_user_agent() -> str:
    """
    Get a realistic user agent string.

    Returns:
        User agent string
    """
    user_agents = [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ),
    ]
    return random.choice(user_agents)


def safe_click_element(driver: WebDriver, element, max_retries: int = 3) -> bool:
    """
    Safely click an element with retries and error handling.

    Args:
        driver: WebDriver instance
        element: Element to click
        max_retries: Maximum number of retries

    Returns:
        True if click was successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

            # Wait a bit for scroll to complete
            time.sleep(0.5)

            # Check if element is clickable
            if not element.is_enabled() or not element.is_displayed():
                logger.debug(f"Element not clickable on attempt {attempt + 1}")
                time.sleep(1)
                continue

            # Try regular click first
            try:
                element.click()
                logger.debug("Element clicked successfully")
                return True
            except Exception as click_error:
                logger.debug(f"Regular click failed: {click_error}")

                # Try JavaScript click as fallback
                driver.execute_script("arguments[0].click();", element)
                logger.debug("Element clicked using JavaScript")
                return True

        except Exception as e:
            logger.debug(f"Click attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            continue

    logger.error(f"Failed to click element after {max_retries} attempts")
    return False
