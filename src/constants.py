#!/usr/bin/env python3
"""
Project-wide constants for X scraper
"""

import os
from pathlib import Path
from typing import Final

# ======================================================================
# URL Constants
# ======================================================================

# X (Twitter) URLs
TWITTER_LOGIN_URL: Final[str] = "https://x.com/i/flow/login"
TWITTER_HOME_URL: Final[str] = "https://x.com"

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


# Docker detection
def is_docker_environment() -> bool:
    """Check if running in Docker environment"""
    return os.path.exists("/.dockerenv") or os.environ.get("DOCKER_ENV") == "true"


# Docker detection file
DOCKER_ENV_FILE: Final[str] = "/.dockerenv"

# Default Tor Browser paths
DEFAULT_TBB_PATH_MACOS: Final[str] = "/Applications/Tor Browser.app/Contents/MacOS/tor-browser"
DEFAULT_TBB_PATH_DOCKER: Final[str] = "/opt/torbrowser"


# Base data directory - unified for Docker and local environments
def get_data_dir() -> Path:
    """Get appropriate data directory based on environment"""
    if is_docker_environment():
        # In Docker, use /app/data which is mounted from host's ./data
        return Path("/app/data")
    else:
        # Local development
        return Path("data")


DATA_DIR: Final[Path] = get_data_dir()


# Ensure data directories exist - シンプル化版
def ensure_data_directories() -> None:
    """Ensure all required data directories exist - シンプル化版"""
    directories = [
        DATA_DIR,
        SCRAPING_RESULTS_DIR,  # 全てのJSONデータ
        SCREENSHOTS_DIR,  # スクリーンショット
        LOGS_DIR,  # ログファイル
        COOKIES_DIR,  # クッキー
    ]

    import contextlib

    for directory in directories:
        with contextlib.suppress(Exception):
            directory.mkdir(parents=True, exist_ok=True)


# Data directories with unified paths - シンプル化版
SCRAPING_RESULTS_DIR: Final[Path] = DATA_DIR / "scraping_results"
SCREENSHOTS_DIR: Final[Path] = DATA_DIR / "screenshots"
LOGS_DIR: Final[Path] = DATA_DIR / "logs"
COOKIES_DIR: Final[Path] = DATA_DIR / "cookies"

# シンプル化されたディレクトリ構造(詳細な分類は削除)
JSON_DATA_DIR: Final[Path] = SCRAPING_RESULTS_DIR  # 全てのJSONデータを統一保存

# Initialize directories on import
ensure_data_directories()

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

# Cookie management
DEFAULT_COOKIE_FILE_NAME: Final[str] = "session_cookies.json"
COOKIE_BACKUP_SUFFIX: Final[str] = "_backup"
COOKIE_EXPIRY_BUFFER_MINUTES: Final[int] = 5

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
# (Unused constants removed for cleaner codebase)

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
