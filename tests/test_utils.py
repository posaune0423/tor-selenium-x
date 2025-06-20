#!/usr/bin/env python3
"""
Unit tests for utility functions
"""

from unittest.mock import Mock, patch

import pytest

from src.utils import (
    clean_text,
    create_safe_filename,
    extract_urls_from_text,
    format_timestamp,
    is_valid_url,
    parse_x_url,
    validate_x_username,
)


class TestTextUtils:
    """Test text utility functions"""

    def test_clean_text_removes_extra_whitespace(self):
        """Test that clean_text removes extra whitespace"""
        assert clean_text("hello    world  \n\t  test") == "hello world test"
        assert clean_text("  leading and trailing  ") == "leading and trailing"
        assert clean_text("") == ""
        assert clean_text("normal text") == "normal text"

    def test_clean_text_removes_non_printable(self):
        """Test that clean_text removes non-printable characters"""
        text_with_nonprintable = "hello\x00\x1f\x7fworld"
        assert clean_text(text_with_nonprintable) == "helloworld"

    def test_create_safe_filename(self):
        """Test safe filename creation"""
        assert create_safe_filename("hello world") == "hello_world"
        assert create_safe_filename("file<>name") == "file__name"
        assert create_safe_filename('file"name') == "file_name"
        assert create_safe_filename("file/name") == "file_name"
        assert create_safe_filename("file|name") == "file_name"

        # Test length limiting
        long_text = "a" * 300
        result = create_safe_filename(long_text, max_length=50)
        assert len(result) <= 50

    def test_extract_urls_from_text(self):
        """Test URL extraction from text"""
        text = "Check out https://example.com and http://test.org for more info"
        urls = extract_urls_from_text(text)
        assert "https://example.com" in urls
        assert "http://test.org" in urls
        assert len(urls) == 2

        # Test with no URLs
        text_no_urls = "This text has no URLs"
        assert extract_urls_from_text(text_no_urls) == []


class TestUrlValidation:
    """Test URL validation functions"""

    def test_is_valid_url(self):
        """Test URL validation"""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://test.org") is True
        assert is_valid_url("ftp://files.example.com") is True

        assert is_valid_url("not-a-url") is False
        assert is_valid_url("") is False
        assert is_valid_url("example.com") is False  # Missing scheme

    def test_parse_x_url(self):
        """Test X URL parsing"""
        # Test profile URL
        profile_url = "https://x.com/username"
        result = parse_x_url(profile_url)
        assert result["username"] == "username"
        assert result["url_type"] == "profile"
        assert result["is_valid"] is True
        assert result["tweet_id"] is None

        # Test tweet URL
        tweet_url = "https://x.com/username/status/1234567890"
        result = parse_x_url(tweet_url)
        assert result["username"] == "username"
        assert result["tweet_id"] == "1234567890"
        assert result["url_type"] == "tweet"
        assert result["is_valid"] is True

        # Test twitter.com domain
        twitter_url = "https://twitter.com/username"
        result = parse_x_url(twitter_url)
        assert result["username"] == "username"
        assert result["is_valid"] is True

        # Test invalid URL
        invalid_url = "https://facebook.com/username"
        result = parse_x_url(invalid_url)
        assert result["is_valid"] is False


class TestXValidation:
    """Test X-specific validation functions"""

    def test_validate_x_username(self):
        """Test X username validation"""
        # Valid usernames
        assert validate_x_username("username") is True
        assert validate_x_username("user_name") is True
        assert validate_x_username("user123") is True
        assert validate_x_username("123user") is True
        assert validate_x_username("_user") is True
        assert validate_x_username("@username") is True  # Should strip @

        # Invalid usernames
        assert validate_x_username("") is False
        assert validate_x_username("a" * 16) is False  # Too long
        assert validate_x_username("user-name") is False  # Hyphen not allowed
        assert validate_x_username("user.name") is False  # Dot not allowed
        assert validate_x_username("user name") is False  # Space not allowed
        assert validate_x_username("user@name") is False  # @ in middle not allowed


class TestTimestampFormatting:
    """Test timestamp formatting functions"""

    def test_format_timestamp_unix(self):
        """Test formatting Unix timestamps"""
        # Test with integer timestamp
        timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
        result = format_timestamp(timestamp)
        assert "2022-01-01" in result
        assert "00:00:00" in result

    def test_format_timestamp_string(self):
        """Test formatting ISO string timestamps"""
        # Test with ISO string
        iso_string = "2022-01-01T00:00:00Z"
        result = format_timestamp(iso_string)
        assert "2022-01-01" in result
        assert "00:00:00" in result

    def test_format_timestamp_invalid(self):
        """Test formatting invalid timestamps"""
        # Should return the original value as string
        invalid_timestamp = "invalid"
        result = format_timestamp(invalid_timestamp)
        assert result == "invalid"


class TestSeleniumHelpers:
    """Test selenium helper functions"""

    @patch("src.utils.WebDriverWait")
    @patch("src.utils.EC")
    def test_wait_for_element_success(self, mock_ec, mock_wait):
        """Test successful element waiting"""
        from selenium.webdriver.common.by import By

        from src.utils import wait_for_element

        # Mock successful wait
        mock_driver = Mock()
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True

        result = wait_for_element(mock_driver, By.ID, "test-id")
        assert result is True
        mock_wait.assert_called_once()

    @patch("src.utils.WebDriverWait")
    def test_wait_for_element_timeout(self, mock_wait):
        """Test element waiting timeout"""
        from selenium.webdriver.common.by import By

        from src.utils import TimeoutException, wait_for_element

        # Mock timeout
        mock_driver = Mock()
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException("Timeout")

        result = wait_for_element(mock_driver, By.ID, "test-id")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
