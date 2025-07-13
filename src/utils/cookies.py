#!/usr/bin/env python3
"""
Cookie management utilities for X scraper - Enhanced cookie management system
"""

import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from src.constants import (
    COOKIE_BACKUP_SUFFIX,
    COOKIE_EXPIRY_BUFFER_MINUTES,
    COOKIES_DIR,
    DEFAULT_COOKIE_FILE_NAME,
)


class CookieManager:
    """Enhanced cookie management class for X scraper session persistence"""

    def __init__(self, user_identifier: str | None = None) -> None:
        """
        Initialize cookie manager

        Args:
            user_identifier: Unique identifier for user (email or username)
                           If None, uses default session file
        """
        self.cookies_dir = COOKIES_DIR
        self.user_identifier = user_identifier
        self.cookie_file = self._get_cookie_file_path()
        self.backup_file = self._get_backup_file_path()

        # Ensure cookies directory exists
        self._ensure_directory_exists()

    def _get_cookie_file_path(self) -> Path:
        """Get cookie file path based on user identifier"""
        if self.user_identifier:
            # Create user-specific cookie file
            safe_identifier = self._sanitize_filename(self.user_identifier)
            filename = f"{safe_identifier}_cookies.json"
        else:
            filename = DEFAULT_COOKIE_FILE_NAME

        return self.cookies_dir / filename

    def _get_backup_file_path(self) -> Path:
        """Get backup cookie file path"""
        stem = self.cookie_file.stem
        suffix = self.cookie_file.suffix
        backup_name = f"{stem}{COOKIE_BACKUP_SUFFIX}{suffix}"
        return self.cookies_dir / backup_name

    def _sanitize_filename(self, identifier: str) -> str:
        """
        Sanitize user identifier for safe filename

        Args:
            identifier: User identifier to sanitize

        Returns:
            str: Safe filename string
        """
        # Remove or replace unsafe characters
        safe_chars = []
        for char in identifier:
            if char.isalnum() or char in "-_.":
                safe_chars.append(char)
            elif char in "@+":
                safe_chars.append("_")

        return "".join(safe_chars)[:50]  # Limit length

    def _ensure_directory_exists(self) -> None:
        """Ensure cookies directory exists with proper permissions"""
        try:
            # Use the unified path from constants
            from src.constants import is_docker_environment

            # Create directory with appropriate permissions
            self.cookies_dir.mkdir(parents=True, exist_ok=True)

            # Docker environment debugging
            is_docker = is_docker_environment()
            logger.debug(f"🐳 Docker environment: {is_docker}")
            logger.debug(f"📁 Cookies directory: {self.cookies_dir.absolute()}")

            # Check directory permissions
            if self.cookies_dir.exists():
                try:
                    dir_stat = self.cookies_dir.stat()
                    logger.debug(f"📊 Directory owner: UID={dir_stat.st_uid}, GID={dir_stat.st_gid}")
                    logger.debug(f"📊 Directory permissions: {oct(dir_stat.st_mode)[-3:]}")
                except Exception as e:
                    logger.debug(f"Could not get directory stats: {e}")

                # Test write permissions
                test_file = self.cookies_dir / "test_write_permission.tmp"
                try:
                    test_file.write_text("permission_test", encoding="utf-8")
                    content = test_file.read_text(encoding="utf-8")
                    test_file.unlink()

                    if content == "permission_test":
                        logger.debug(f"✅ Cookies directory write permission verified: {self.cookies_dir}")
                    else:
                        logger.warning("⚠️ Write permission test failed: content mismatch")
                except Exception as e:
                    logger.warning(f"⚠️ Write permission test failed: {e}")
                    # Try to set proper permissions if possible
                    try:
                        import stat

                        self.cookies_dir.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
                        logger.debug("📝 Set directory permissions to 750")
                    except Exception as perm_e:
                        logger.debug(f"Could not set directory permissions: {perm_e}")

            logger.debug(f"✅ Cookies directory ensured: {self.cookies_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to create cookies directory: {e}")
            raise

    def save_cookies(self, cookies: list[dict[str, Any]]) -> bool:
        """
        Save cookies to file with backup and validation

        Args:
            cookies: List of cookie dictionaries from selenium

        Returns:
            bool: True if successful, False otherwise
        """
        if not cookies:
            logger.warning("No cookies to save")
            return False

        try:
            # Debug information for Docker troubleshooting
            is_docker = os.path.exists("/.dockerenv")
            logger.info(f"🐳 Docker environment: {is_docker}")
            logger.info(f"📁 Cookie directory: {self.cookies_dir.absolute()}")
            logger.info(f"📄 Cookie file: {self.cookie_file.absolute()}")
            logger.info(f"👤 Current user: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
            logger.info(f"👥 Current group: {os.getgid() if hasattr(os, 'getgid') else 'N/A'}")

            # Check directory permissions
            try:
                dir_stat = self.cookies_dir.stat()
                logger.info(f"📊 Directory owner: UID={dir_stat.st_uid}, GID={dir_stat.st_gid}")
                logger.info(f"📊 Directory permissions: {oct(dir_stat.st_mode)[-3:]}")
            except Exception as e:
                logger.warning(f"Cannot get directory stats: {e}")

            # Test write permissions with a temporary file
            test_file = self.cookies_dir / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logger.info("✅ Directory write permission: OK")
            except Exception as e:
                logger.error(f"❌ Directory write permission failed: {e}")
                logger.error(f"   Check if {self.cookies_dir} is writable by current user")
                return False

            # Create backup of existing cookies if they exist
            if self.cookie_file.exists():
                logger.info("Creating backup of existing cookies")
                self._create_backup()

            # Filter and clean cookies for X/Twitter
            cleaned_cookies = self._filter_important_cookies(cookies)

            if not cleaned_cookies:
                logger.warning("No important cookies found to save")
                return False

            # Prepare cookie data with metadata
            cookie_data = {
                "timestamp": datetime.now(UTC).isoformat(),
                "user_identifier": self.user_identifier,
                "cookie_count": len(cleaned_cookies),
                "cookies": cleaned_cookies,
            }

            # Save to file with detailed logging
            logger.info(f"📝 Writing {len(cleaned_cookies)} cookies to {self.cookie_file}")
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)

            # Verify file was created and has content
            if self.cookie_file.exists():
                file_size = self.cookie_file.stat().st_size
                if file_size > 0:
                    logger.info(f"✅ Cookie file saved successfully: {self.cookie_file} ({file_size} bytes)")

                    # Set appropriate permissions for cookie file (readable by owner only)
                    try:
                        os.chmod(self.cookie_file, 0o600)
                        logger.debug("Set cookie file permissions to 600 (owner read/write only)")
                    except Exception as e:
                        logger.warning(f"Failed to set cookie file permissions: {e}")

                    return True
                else:
                    logger.error(f"❌ Cookie file created but empty: {self.cookie_file}")
                    return False
            else:
                logger.error(f"❌ Cookie file was not created: {self.cookie_file}")
                return False

        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            logger.error(f"Cookie file path: {self.cookie_file}")
            logger.error(f"Cookies directory: {self.cookies_dir}")

            # Additional debugging information
            try:
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
            except Exception:
                pass

            # Restore backup if save failed
            self._restore_backup()
            return False

    def load_cookies(self) -> list[dict[str, Any]]:
        """
        Load cookies from file with validation

        Returns:
            list[dict[str, Any]]: List of cookie dictionaries, empty if error/expired
        """
        try:
            if not self.cookie_file.exists():
                logger.debug(f"Cookie file does not exist: {self.cookie_file}")
                return []

            with open(self.cookie_file, encoding="utf-8") as f:
                data = json.load(f)

            # Handle different data formats for backward compatibility
            cookies = self._extract_cookies_from_data(data)

            if not cookies:
                logger.debug("No cookies found in file")
                return []

            # Check if cookies are expired
            if self.are_cookies_expired(cookies):
                logger.info("Loaded cookies are expired, removing file")
                self._remove_expired_cookies()
                return []

            logger.info(f"Loaded {len(cookies)} valid cookies from {self.cookie_file}")
            return cookies

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return []

    def are_cookies_expired(self, cookies: list[dict[str, Any]] | None = None) -> bool:
        """
        Check if cookies are expired

        Args:
            cookies: Optional cookies to check. If None, loads from file

        Returns:
            bool: True if expired, False if valid
        """
        if cookies is None:
            # Try to load cookies from file
            if not self.cookie_file.exists():
                return True
            cookies = self.load_cookies()

        if not cookies:
            return True

        try:
            current_time = datetime.now(UTC).timestamp()
            buffer_seconds = COOKIE_EXPIRY_BUFFER_MINUTES * 60

            for cookie in cookies:
                expiry = cookie.get("expiry")
                if expiry is None:
                    continue  # Session cookies don't expire

                # Check if cookie expires within buffer time
                if expiry - current_time < buffer_seconds:
                    logger.debug(f"Cookie '{cookie.get('name', 'unknown')}' expires soon")
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking cookie expiry: {e}")
            return True

    def clear_cookies(self) -> bool:
        """
        Clear saved cookies and backup

        Returns:
            bool: True if successful
        """
        try:
            removed_files = []

            if self.cookie_file.exists():
                self.cookie_file.unlink()
                removed_files.append(str(self.cookie_file))

            if self.backup_file.exists():
                self.backup_file.unlink()
                removed_files.append(str(self.backup_file))

            if removed_files:
                logger.info(f"Cleared cookie files: {removed_files}")
            else:
                logger.info("No cookie files to clear")

            return True

        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
            return False

    def has_valid_cookies(self) -> bool:
        """
        Check if valid cookies exist

        Returns:
            bool: True if valid cookies exist
        """
        if not self.cookie_file.exists():
            return False

        cookies = self.load_cookies()
        return len(cookies) > 0 and not self.are_cookies_expired(cookies)

    def _filter_important_cookies(self, cookies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter important cookies for X/Twitter login persistence

        Args:
            cookies: Raw cookies from selenium

        Returns:
            list[dict[str, Any]]: Filtered important cookies
        """
        important_names = {
            "auth_token",
            "ct0",
            "twid",
            "personalization_id",
            "guest_id",
            "gt",
            "_twitter_sess",
            "kdt",
            "lang",
        }

        important_cookies = []

        for cookie in cookies:
            # Keep cookies that are X/Twitter related
            domain = cookie.get("domain", "")
            name = cookie.get("name", "")

            if (
                any(domain_part in domain for domain_part in [".twitter.com", ".x.com", "twitter.com", "x.com"])
                or name in important_names
            ):
                # Clean cookie data for JSON serialization
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ".twitter.com"),
                    "path": cookie.get("path", "/"),
                }

                # Add optional fields if present
                for field in ["secure", "httpOnly", "expiry", "sameSite"]:
                    if field in cookie:
                        clean_cookie[field] = cookie[field]

                important_cookies.append(clean_cookie)

        return important_cookies

    def _extract_cookies_from_data(self, data: Any) -> list[dict[str, Any]]:
        """
        Extract cookies from loaded data (handles different formats)

        Args:
            data: Loaded JSON data

        Returns:
            list[dict[str, Any]]: Extracted cookies
        """
        if isinstance(data, list):
            # Old format: direct list of cookies
            return data
        elif isinstance(data, dict):
            if "cookies" in data:
                # New format: data with metadata
                return data["cookies"]
            else:
                # Single cookie object
                return [data] if "name" in data and "value" in data else []
        else:
            logger.warning("Invalid cookie data format")
            return []

    def _create_backup(self) -> None:
        """Create backup of current cookie file"""
        try:
            if self.cookie_file.exists():
                shutil.copy2(self.cookie_file, self.backup_file)
                logger.debug(f"Created cookie backup: {self.backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create cookie backup: {e}")

    def _restore_backup(self) -> None:
        """Restore cookie file from backup"""
        try:
            if self.backup_file.exists():
                shutil.copy2(self.backup_file, self.cookie_file)
                logger.info(f"Restored cookies from backup: {self.backup_file}")
        except Exception as e:
            logger.warning(f"Failed to restore cookie backup: {e}")

    def _remove_expired_cookies(self) -> None:
        """Remove expired cookie files"""
        try:
            if self.cookie_file.exists():
                self.cookie_file.unlink()
                logger.info("Removed expired cookie file")
        except Exception as e:
            logger.warning(f"Failed to remove expired cookie file: {e}")


# Legacy functions for backward compatibility
def save_cookies_to_file(cookies: list[dict[str, Any]], filepath: str) -> bool:
    """
    Legacy function for saving cookies (deprecated - use CookieManager instead)

    Args:
        cookies: List of cookie dictionaries
        filepath: Path to save cookies

    Returns:
        bool: True if successful, False otherwise
    """
    logger.warning("save_cookies_to_file is deprecated. Use CookieManager.save_cookies() instead")
    try:
        # Create temporary cookie manager for this operation
        file_path = Path(filepath)
        temp_manager = CookieManager()
        temp_manager.cookie_file = file_path
        temp_manager._ensure_directory_exists()
        return temp_manager.save_cookies(cookies)
    except Exception as e:
        logger.error(f"Legacy save_cookies_to_file failed: {e}")
        return False


def load_cookies_from_file(filepath: str) -> list[dict[str, Any]]:
    """
    Legacy function for loading cookies (deprecated - use CookieManager instead)

    Args:
        filepath: Path to cookie file

    Returns:
        list[dict[str, Any]]: List of cookie dictionaries
    """
    logger.warning("load_cookies_from_file is deprecated. Use CookieManager.load_cookies() instead")
    try:
        # Create temporary cookie manager for this operation
        file_path = Path(filepath)
        temp_manager = CookieManager()
        temp_manager.cookie_file = file_path
        return temp_manager.load_cookies()
    except Exception as e:
        logger.error(f"Legacy load_cookies_from_file failed: {e}")
        return []


def are_cookies_expired(cookies: list[dict[str, Any]]) -> bool:
    """
    Legacy function for checking cookie expiry (deprecated - use CookieManager instead)

    Args:
        cookies: List of cookie dictionaries

    Returns:
        bool: True if expired, False if valid
    """
    logger.warning("are_cookies_expired is deprecated. Use CookieManager.are_cookies_expired() instead")
    try:
        temp_manager = CookieManager()
        return temp_manager.are_cookies_expired(cookies)
    except Exception as e:
        logger.error(f"Legacy are_cookies_expired failed: {e}")
        return True
