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
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_ENV", "false").lower() == "true"

    if is_docker:
        logger.info("🐳 Running in Docker environment - using external Tor service")

    # Initialize tbselenium
    driver = TorBrowserDriver(tbb_path, headless=headless, tbb_logfile_path="/dev/null", **kwargs)

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

    # Try multiple IP checking services
    ip_services = [
        "http://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ipapi.co/json/",
    ]

    for service in ip_services:
        try:
            logger.debug(f"Checking IP via: {service}")
            driver.get(service)
            time.sleep(3)

            page_source = driver.page_source

            # Extract IP from different response formats
            if "httpbin.org" in service:
                # httpbin.org returns JSON with "origin" field
                try:
                    data = json.loads(page_source)
                    ip = data.get("origin", "").strip()
                    if ip and is_valid_ip(ip):
                        return ip
                except (json.JSONDecodeError, KeyError):
                    # Try regex fallback
                    ip_match = re.search(r'"origin":\s*"([^"]+)"', page_source)
                    if ip_match:
                        ip = ip_match.group(1).strip()
                        if is_valid_ip(ip):
                            return ip

            elif "ipify.org" in service:
                # ipify returns JSON with "ip" field
                try:
                    data = json.loads(page_source)
                    ip = data.get("ip", "").strip()
                    if ip and is_valid_ip(ip):
                        return ip
                except (json.JSONDecodeError, KeyError):
                    pass

            elif "ipapi.co" in service:
                # ipapi.co returns JSON with "ip" field
                try:
                    data = json.loads(page_source)
                    ip = data.get("ip", "").strip()
                    if ip and is_valid_ip(ip):
                        return ip
                except (json.JSONDecodeError, KeyError):
                    pass

            # Generic regex fallback for any numeric IP
            ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
            ip_matches = re.findall(ip_pattern, page_source)
            for ip in ip_matches:
                if is_valid_ip(ip) and not is_private_ip(ip):
                    logger.debug(f"Found IP via regex: {ip}")
                    return ip

        except Exception as e:
            logger.debug(f"Failed to get IP from {service}: {e}")
            continue

    logger.warning("❌ Could not retrieve IP address from any service")
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

    # Tor verification services
    tor_check_services = [
        "https://check.torproject.org/",
        "https://check.torproject.org/api/ip",
    ]

    for service in tor_check_services:
        try:
            logger.debug(f"Checking Tor status via: {service}")
            driver.get(service)
            time.sleep(5)  # Give more time for Tor check page to load

            page_source = driver.page_source.lower()

            # Check for positive Tor indicators
            tor_indicators = [
                "congratulations",
                "you are using tor",
                "using tor",
                "this browser is configured to use tor",
                '"IsTor":true',
                '"istory":true',
            ]

            for indicator in tor_indicators:
                if indicator in page_source:
                    logger.debug(f"✅ Tor confirmed by indicator: '{indicator}'")
                    return True

            # Log first 500 chars for debugging if no match found
            logger.debug(f"Page content (first 500 chars): {page_source[:500]}")

        except Exception as e:
            logger.debug(f"Failed to check Tor status via {service}: {e}")
            continue

    logger.warning("⚠️  Could not confirm Tor status from official services")
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
