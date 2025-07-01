#!/usr/bin/env python3
"""
Project-wide constants for X scraper
"""

from pathlib import Path
from typing import Final

# ======================================================================
# URL Constants
# ======================================================================

# X (Twitter) URLs
TWITTER_LOGIN_URL: Final[str] = "https://x.com/i/flow/login"
TWITTER_HOME_URL: Final[str] = "https://twitter.com"

# IP checking services
IP_CHECK_SERVICES: Final[list[str]] = [
    "http://httpbin.org/ip",
    "https://api.ipify.org?format=json",
    "https://ipapi.co/json/",
]

# Tor verification services
TOR_CHECK_SERVICES: Final[list[str]] = [
    "https://check.torproject.org/",
    "https://check.torproject.org/api/ip",
]

# ======================================================================
# Timing Constants (seconds)
# ======================================================================

# Basic wait times
WAIT_SHORT: Final[int] = 2
WAIT_MEDIUM: Final[int] = 3
WAIT_LONG: Final[int] = 5
WAIT_EXTRA_LONG: Final[int] = 10

# Specific operation timeouts
LOGIN_PAGE_LOAD_TIMEOUT: Final[int] = 5
TOR_CHECK_TIMEOUT: Final[int] = 5
ELEMENT_WAIT_TIMEOUT: Final[int] = 10
SCREENSHOT_DELAY: Final[int] = 1

# ======================================================================
# Path Constants
# ======================================================================

# Default Tor Browser paths
DEFAULT_TBB_PATH_MACOS: Final[str] = "/Applications/Tor Browser.app/Contents/MacOS/tor-browser"
DEFAULT_TBB_PATH_DOCKER: Final[str] = "/opt/torbrowser"

# Docker detection file
DOCKER_ENV_FILE: Final[str] = "/.dockerenv"

# Data directories
DATA_DIR: Final[Path] = Path("data")
SCRAPING_RESULTS_DIR: Final[Path] = DATA_DIR / "scraping_results"
SCREENSHOTS_DIR: Final[Path] = DATA_DIR / "screenshots"
LOGS_DIR: Final[Path] = DATA_DIR / "logs"

# ======================================================================
# Scraping Constants
# ======================================================================

# Default scraping limits
DEFAULT_MAX_TWEETS: Final[int] = 10
DEFAULT_MAX_PROFILES: Final[int] = 5

# File extensions
JSON_EXTENSION: Final[str] = ".json"
PNG_EXTENSION: Final[str] = ".png"
HTML_EXTENSION: Final[str] = ".html"
TXT_EXTENSION: Final[str] = ".txt"

# Cookie file name
COOKIE_FILE_NAME: Final[str] = "x_cookies.json"

# ======================================================================
# Browser Configuration
# ======================================================================

# Default browser settings
DEFAULT_HEADLESS: Final[bool] = True
DEFAULT_WINDOW_SIZE: Final[tuple[int, int]] = (1920, 1080)

# ======================================================================
# Network Configuration
# ======================================================================

# Default Tor ports
DEFAULT_SOCKS_PORT: Final[int] = 9150
DEFAULT_CONTROL_PORT: Final[int] = 9151

# ======================================================================
# Debug and Logging
# ======================================================================

# Log file name patterns
LOG_FILE_PATTERN: Final[str] = "scraper_{time}.log"
DEBUG_SCREENSHOT_PREFIX: Final[str] = "debug_"

# Debug contexts
DEBUG_CONTEXTS: Final[dict[str, str]] = {
    "INITIAL_LOGIN": "initial_login_page",
    "AFTER_USERNAME": "after_username_input",
    "AFTER_PASSWORD": "after_password_input",
    "CAPTCHA_DETECTED": "captcha_detected",
    "LOGIN_SUCCESS": "login_success",
    "LOGIN_FAILED": "login_failed",
}

# ======================================================================
# Element Selectors (commonly used)
# ======================================================================

# Login form selectors
LOGIN_SELECTORS: Final[dict[str, list[str]]] = {
    "username": [
        'input[name="text"]',
        'input[autocomplete="username"]',
        'input[data-testid="ocfEnterTextTextInput"]',
        'input[placeholder*="phone"]',
        'input[placeholder*="email"]',
        'input[placeholder*="username"]',
    ],
    "password": [
        'input[name="password"]',
        'input[type="password"]',
        'input[data-testid="ocfEnterTextTextInput"]',
    ],
    "login_button": [
        'div[data-testid="LoginForm_Login_Button"]',
        'button[type="submit"]',
        'div[role="button"]:has-text("Log in")',
        'div[role="button"]:has-text("Next")',
    ],
}

# ======================================================================
# Error Messages and Patterns
# ======================================================================

# Common error patterns
ERROR_PATTERNS: Final[dict[str, list[str]]] = {
    "captcha": [
        "recaptcha",
        "arkose",
        "funcaptcha",
        "hcaptcha",
    ],
    "login_failed": [
        "wrong password",
        "incorrect password",
        "authentication failed",
        "login failed",
    ],
    "rate_limited": [
        "rate limit",
        "too many requests",
        "try again later",
    ],
}

# ======================================================================
# Tor Verification
# ======================================================================

# Tor verification indicators
TOR_VERIFICATION_INDICATORS: Final[list[str]] = [
    "congratulations",
    "you are using tor",
    "using tor",
    "this browser is configured to use tor",
    '"IsTor":true',
    '"istory":true',
]

# ======================================================================
# Environment Variables
# ======================================================================

# Environment variable names
ENV_VARS: Final[dict[str, str]] = {
    "TBB_PATH": "TBB_PATH",
    "TBSELENIUM_TBB_PATH": "TBSELENIUM_TBB_PATH",
    "DOCKER_ENV": "DOCKER_ENV",
    "X_EMAIL": "X_EMAIL",
    "X_USERNAME": "X_USERNAME",
    "X_PASSWORD": "X_PASSWORD",
    "HEADLESS": "HEADLESS",
    "LOG_LEVEL": "LOG_LEVEL",
}
