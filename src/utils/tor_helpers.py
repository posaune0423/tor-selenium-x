"""
Tor browser and connection utilities for the X scraper
"""

import ipaddress
import json
import os
import re
import time
from typing import Any

from loguru import logger
from selenium.webdriver.remote.webdriver import WebDriver
from tbselenium.tbdriver import TorBrowserDriver

from src.constants import (
    DEFAULT_TBB_PATH_DOCKER,
    DOCKER_ENV_FILE,
    ENV_VARS,
    IP_CHECK_SERVICES,
    TOR_CHECK_SERVICES,
    TOR_CHECK_TIMEOUT,
    TOR_VERIFICATION_INDICATORS,
    WAIT_MEDIUM,
)


def create_tor_browser_driver(tbb_path: str, headless: bool = True, **kwargs: Any) -> TorBrowserDriver:
    """
    Create and configure a Tor Browser driver

    Args:
        tbb_path: Path to Tor Browser directory
        headless: Run in headless mode
        **kwargs: Additional arguments for TorBrowserDriver

    Returns:
        TorBrowserDriver: Configured Tor Browser driver
    """
    # Check if we're running in Docker
    is_docker = os.path.exists(DOCKER_ENV_FILE) or os.environ.get(ENV_VARS["DOCKER_ENV"], "false").lower() == "true"

    if is_docker:
        logger.info("🐳 Running in Docker environment - using external Tor service")
        # Use Docker-specific TBB path from environment variable or default
        docker_tbb_path = os.environ.get(ENV_VARS["TBB_PATH"], DEFAULT_TBB_PATH_DOCKER)
        logger.info(f"Using Docker TBB path: {docker_tbb_path}")
        actual_tbb_path = docker_tbb_path
    else:
        # Use the provided path for non-Docker environments
        actual_tbb_path = tbb_path

    logger.debug(f"Initializing TorBrowserDriver with path: {actual_tbb_path}")

    # Initialize tbselenium with the appropriate path
    driver = TorBrowserDriver(actual_tbb_path, headless=headless, tbb_logfile_path="/dev/null", **kwargs)

    return driver


def verify_tor_connection(driver: WebDriver) -> bool:
    """
    Verify that the connection is actually going through Tor

    Args:
        driver: WebDriver instance to test

    Returns:
        bool: True if Tor connection is verified, False otherwise
    """
    if not driver:
        logger.error("Driver not initialized")
        return False

    logger.info("🔍 Verifying Tor connection...")

    # Step 1: Get IP address through Tor
    tor_ip = get_tor_ip(driver)
    if not tor_ip:
        logger.error("❌ Failed to get IP address through Tor")
        return False

    logger.info(f"🌐 Current IP address (via Tor): {tor_ip}")

    # Step 2: Check against known Tor exit nodes (simplified check)
    is_tor_verified = check_tor_status(driver)

    if is_tor_verified:
        logger.success(f"✅ Tor connection verified! IP: {tor_ip}")
        return True
    else:
        logger.error(f"❌ Tor connection not verified. IP: {tor_ip}")
        return False


def get_tor_ip(driver: WebDriver) -> str | None:
    """
    Get current IP address through Tor connection

    Args:
        driver: WebDriver instance to use

    Returns:
        str | None: IP address if successful, None if failed
    """
    if not driver:
        return None

    # Use IP checking services from constants
    for service in IP_CHECK_SERVICES:
        try:
            logger.debug(f"Checking IP via: {service}")
            driver.get(service)
            time.sleep(WAIT_MEDIUM)

            page_source = driver.page_source

            # Extract IP from different response formats
            ip = _extract_ip_from_response(service, page_source)
            if ip:
                return ip

        except Exception as e:
            logger.debug(f"Failed to get IP from {service}: {e}")
            continue

    logger.warning("❌ Could not retrieve IP address from any service")
    return None


def _extract_ip_from_response(service: str, page_source: str) -> str | None:
    """
    Extract IP address from service response

    Args:
        service: Service URL that was queried
        page_source: HTML/JSON response from service

    Returns:
        str | None: Extracted IP address or None if not found
    """
    # Extract IP from different response formats
    if "httpbin.org" in service:
        # httpbin.org returns JSON with "origin" field
        ip = _extract_ip_from_json(page_source, "origin")
        if ip:
            return ip

    elif "ipify.org" in service:
        # ipify returns JSON with "ip" field
        ip = _extract_ip_from_json(page_source, "ip")
        if ip:
            return ip

    elif "ipapi.co" in service:
        # ipapi.co returns JSON with "ip" field
        ip = _extract_ip_from_json(page_source, "ip")
        if ip:
            return ip

    # Generic regex fallback for any numeric IP
    return _extract_ip_with_regex(page_source)


def _extract_ip_from_json(page_source: str, field_name: str) -> str | None:
    """
    Extract IP address from JSON response

    Args:
        page_source: JSON response as string
        field_name: Field name containing IP address

    Returns:
        str | None: Extracted IP address or None if not found
    """
    try:
        data = json.loads(page_source)
        ip = data.get(field_name, "").strip()
        if ip and is_valid_ip(ip):
            return ip
    except (json.JSONDecodeError, KeyError):
        # Try regex fallback
        ip_match = re.search(rf'"{field_name}":\s*"([^"]+)"', page_source)
        if ip_match:
            ip = ip_match.group(1).strip()
            if is_valid_ip(ip):
                return ip

    return None


def _extract_ip_with_regex(page_source: str) -> str | None:
    """
    Extract IP address using regex patterns

    Args:
        page_source: HTML/text response

    Returns:
        str | None: Extracted IP address or None if not found
    """
    ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    ip_matches = re.findall(ip_pattern, page_source)

    for ip in ip_matches:
        if is_valid_ip(ip) and not is_private_ip(ip):
            logger.debug(f"Found IP via regex: {ip}")
            return ip

    return None


def check_tor_status(driver: WebDriver) -> bool:
    """
    Check if connection is going through Tor using official Tor check services

    Args:
        driver: WebDriver instance to use

    Returns:
        bool: True if Tor is confirmed, False otherwise
    """
    if not driver:
        return False

    # Use Tor verification services from constants
    for service in TOR_CHECK_SERVICES:
        try:
            logger.debug(f"Checking Tor status via: {service}")
            driver.get(service)
            time.sleep(TOR_CHECK_TIMEOUT)

            page_source = driver.page_source.lower()

            # Check for positive Tor indicators from constants
            for indicator in TOR_VERIFICATION_INDICATORS:
                if indicator in page_source:
                    logger.debug(f"Found Tor indicator: {indicator}")
                    return True

        except Exception as e:
            logger.debug(f"Error checking Tor status via {service}: {e}")
            continue

    logger.debug("No Tor indicators found in any service")
    return False


def is_valid_ip(ip: str) -> bool:
    """
    Check if string is a valid IP address

    Args:
        ip: IP address string to validate

    Returns:
        bool: True if valid IP, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """
    Check if IP address is private/local

    Args:
        ip: IP address string to check

    Returns:
        bool: True if private IP, False otherwise
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except ValueError:
        return False
