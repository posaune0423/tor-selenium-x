#!/usr/bin/env python3
"""
Selector utilities for X scraper
"""

from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def find_element_by_selectors(driver: WebDriver, selectors: list[str], timeout: int = 5):
    """
    Try to find an element using multiple selectors.

    Args:
        driver: WebDriver instance
        selectors: List of CSS selectors to try
        timeout: Timeout for each selector attempt

    Returns:
        Element if found, None otherwise
    """
    for selector in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
            logger.debug(f"Element found with selector: {selector}")
            return element
        except TimeoutException:
            logger.debug(f"Element not found with selector: {selector}")
            continue
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")
            continue

    logger.debug("Element not found with any selector")
    return None


def find_elements_by_selectors(driver: WebDriver, selectors: list[str]) -> list:
    """
    Try to find elements using multiple selectors.

    Args:
        driver: WebDriver instance
        selectors: List of CSS selectors to try

    Returns:
        List of elements (may be empty)
    """
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                return elements
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")
            continue

    logger.debug("No elements found with any selector")
    return []


def extract_text_by_selectors(element, selectors: list[str]) -> str:
    """
    Extract text from an element using multiple selectors.

    Args:
        element: Parent element to search within
        selectors: List of CSS selectors to try

    Returns:
        Extracted text or empty string
    """
    for selector in selectors:
        try:
            sub_elements = element.find_elements(By.CSS_SELECTOR, selector)
            if sub_elements:
                text_parts = []
                for sub_element in sub_elements:
                    text = sub_element.text.strip()
                    if text:
                        text_parts.append(text)

                if text_parts:
                    result = " ".join(text_parts)
                    logger.debug(f"Text extracted with selector '{selector}': {result[:50]}...")
                    return result
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            continue

    # Fallback: try to get text from the element itself
    try:
        text = element.text.strip()
        if text:
            logger.debug(f"Text extracted from element directly: {text[:50]}...")
            return text
    except Exception as e:
        logger.debug(f"Error extracting text from element directly: {e}")

    return ""


def extract_count_by_selectors(element, selectors: list[str], parse_count_func) -> int:
    """
    Extract count from an element using multiple selectors.

    Args:
        element: Parent element to search within
        selectors: List of CSS selectors to try
        parse_count_func: Function to parse count string

    Returns:
        Parsed count as integer
    """
    for selector in selectors:
        try:
            sub_elements = element.find_elements(By.CSS_SELECTOR, selector)
            for sub_element in sub_elements:
                text = sub_element.text.strip()
                if text and any(char.isdigit() for char in text):
                    count = parse_count_func(text)
                    if count is not None:
                        logger.debug(f"Count extracted with selector '{selector}': {text} -> {count}")
                        return count
        except Exception as e:
            logger.debug(f"Error extracting count with selector {selector}: {e}")
            continue

    return 0


def extract_attribute_by_selectors(element, selectors: list[str], attribute: str) -> str:
    """
    Extract attribute from an element using multiple selectors.

    Args:
        element: Parent element to search within
        selectors: List of CSS selectors to try
        attribute: Attribute name to extract

    Returns:
        Attribute value or empty string
    """
    for selector in selectors:
        try:
            sub_elements = element.find_elements(By.CSS_SELECTOR, selector)
            for sub_element in sub_elements:
                attr_value = sub_element.get_attribute(attribute)
                if attr_value:
                    logger.debug(f"Attribute '{attribute}' extracted with selector '{selector}': {attr_value}")
                    return attr_value
        except Exception as e:
            logger.debug(f"Error extracting attribute with selector {selector}: {e}")
            continue

    return ""


def extract_text_from_driver_by_selectors(driver: WebDriver | None, selectors: list[str]) -> str:
    """
    Extract text from driver using multiple selectors.

    Args:
        driver: WebDriver instance
        selectors: List of CSS selectors to try

    Returns:
        Extracted text or empty string
    """
    if not driver:
        return ""

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                text_parts = []
                for element in elements:
                    text = element.text.strip()
                    if text:
                        text_parts.append(text)

                if text_parts:
                    result = " ".join(text_parts)
                    logger.debug(f"Text extracted from driver with selector '{selector}': {result[:50]}...")
                    return result
        except Exception as e:
            logger.debug(f"Error extracting text from driver with selector {selector}: {e}")
            continue

    return ""


def extract_attribute_from_driver_by_selectors(driver: WebDriver | None, selectors: list[str], attribute: str) -> str:
    """
    Extract attribute from driver using multiple selectors.

    Args:
        driver: WebDriver instance
        selectors: List of CSS selectors to try
        attribute: Attribute name to extract

    Returns:
        Attribute value or empty string
    """
    if not driver:
        return ""

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                attr_value = element.get_attribute(attribute)
                if attr_value:
                    logger.debug(
                        f"Attribute '{attribute}' extracted from driver with selector '{selector}': {attr_value}"
                    )
                    return attr_value
        except Exception as e:
            logger.debug(f"Error extracting attribute from driver with selector {selector}: {e}")
            continue

    return ""
