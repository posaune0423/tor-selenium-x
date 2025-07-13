#!/usr/bin/env python3
"""
Tests for X scraper functionality
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from selenium.common.exceptions import NoSuchElementException

from src.models import Tweet, UserProfile
from src.x_scraper import XScraper

# Test constants
TEST_TBB_PATH = "/fake/tor/browser/path"
TEST_EMAIL = "test@example.com"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"
TEST_2FA_CODE = "123456"


class TestXScraper:
    """Test cases for XScraper class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = XScraper(
            tbb_path=TEST_TBB_PATH,
            email=TEST_EMAIL,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
        )

    def _create_mock_driver(self) -> Mock:
        """Create a mock driver for testing"""
        return Mock()

    def test_init(self):
        """Test XScraper initialization"""
        assert self.scraper.tbb_path == TEST_TBB_PATH
        assert self.scraper.headless is True
        assert self.scraper.email == TEST_EMAIL
        assert self.scraper.username == TEST_USERNAME
        assert self.scraper.password == TEST_PASSWORD
        assert self.scraper.driver is None
        # Check cookie manager is initialized
        assert self.scraper.cookie_manager is not None
        assert self.scraper.cookie_manager.user_identifier == TEST_EMAIL

    def test_init_without_credentials(self):
        """Test XScraper initialization without credentials"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        assert scraper.tbb_path == TEST_TBB_PATH
        assert scraper.headless is True
        assert scraper.email is None
        assert scraper.username is None
        assert scraper.password is None

    @patch("src.x_scraper.verify_tor_connection", return_value=True)
    @patch("src.x_scraper.create_tor_browser_driver")
    def test_start_success(self, mock_create_driver, mock_verify_tor):
        """Test successful start with Tor verification"""
        mock_driver = self._create_mock_driver()
        mock_create_driver.return_value = mock_driver

        result = self.scraper.start()
        assert result is True
        assert self.scraper.driver == mock_driver
        mock_create_driver.assert_called_once_with(
            TEST_TBB_PATH,
            headless=True,
        )
        mock_verify_tor.assert_called_once_with(mock_driver)

    @patch("src.x_scraper.verify_tor_connection", return_value=False)
    @patch("src.x_scraper.create_tor_browser_driver")
    def test_start_tor_verification_failure(self, mock_create_driver, mock_verify_tor):
        """Test start with driver creation success but Tor verification failure"""
        mock_driver = self._create_mock_driver()
        mock_create_driver.return_value = mock_driver

        result = self.scraper.start()
        assert result is False
        assert self.scraper.driver == mock_driver
        mock_create_driver.assert_called_once()
        mock_verify_tor.assert_called_once_with(mock_driver)

    @patch("src.utils.create_tor_browser_driver")
    def test_start_driver_creation_failure(self, mock_create_driver):
        """Test start when driver creation fails"""
        mock_create_driver.side_effect = Exception("Driver creation failed")

        result = self.scraper.start()
        assert result is False
        assert self.scraper.driver is None

    @patch("src.utils.verify_tor_connection")
    @patch("src.utils.create_tor_browser_driver")
    def test_start_connection_exception(self, mock_create_driver, mock_verify_tor):
        """Test start failure when Tor verification raises an exception"""
        mock_driver = self._create_mock_driver()
        mock_create_driver.return_value = mock_driver
        mock_verify_tor.side_effect = Exception("Network error")

        result = self.scraper.start()
        assert result is False

    def test_login_no_driver(self):
        """Test login without driver initialized"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH, email=TEST_EMAIL, password=TEST_PASSWORD)
        result = scraper.login()
        assert result is False

    @pytest.mark.parametrize(
        "email,username,password,expected",
        [
            (None, None, TEST_PASSWORD, False),  # No email or username
            (TEST_EMAIL, None, None, False),  # No password
            (None, TEST_USERNAME, None, False),  # No password
        ],
    )
    def test_login_missing_credentials(self, email, username, password, expected):
        """Test login with missing credentials"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH, email=email, username=username, password=password)
        scraper.driver = self._create_mock_driver()

        result = scraper.login()
        assert result is expected

    def _setup_mock_element(self, mock_driver, selector_patterns, element_mock=None):
        """Helper to set up mock element finding"""
        if element_mock is None:
            element_mock = Mock()

        def mock_find_element(by, value):
            for pattern in selector_patterns:
                if pattern in value:
                    return element_mock
            raise NoSuchElementException()

        mock_driver.find_element.side_effect = mock_find_element
        return element_mock

    @patch("src.x_scraper.time.sleep")
    def test_input_username_success(self, mock_sleep):
        """Test successful username input"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH, email=TEST_EMAIL, password=TEST_PASSWORD)
        mock_driver = self._create_mock_driver()
        scraper.driver = mock_driver

        # Setup mock element for username field
        mock_username_field = Mock()
        mock_driver.find_element.return_value = mock_username_field

        result = scraper._input_username()

        assert result is True
        mock_username_field.clear.assert_called_once()
        mock_username_field.send_keys.assert_called()

    def test_input_username_no_driver(self):
        """Test username input without driver"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH, email=TEST_EMAIL)
        result = scraper._input_username()
        assert result is False

    def test_input_username_no_identifier(self):
        """Test username input without email or username"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        scraper.driver = self._create_mock_driver()
        result = scraper._input_username()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_input_password_success(self, mock_sleep):
        """Test successful password input"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH, password=TEST_PASSWORD)
        mock_driver = self._create_mock_driver()
        scraper.driver = mock_driver

        # Setup mock elements
        mock_password_field = Mock()
        mock_login_button = Mock()

        def mock_find_element(by, value):
            if "password" in value:
                return mock_password_field
            elif "Log in" in value or "submit" in value:
                return mock_login_button
            else:
                raise NoSuchElementException()

        mock_driver.find_element.side_effect = mock_find_element

        result = scraper._input_password()

        assert result is True
        mock_password_field.clear.assert_called_once()

    def test_input_password_no_driver(self):
        """Test password input without driver"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        result = scraper._input_password()
        assert result is False

    def test_input_password_no_password(self):
        """Test password input without password set"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH, email=TEST_EMAIL)
        scraper.driver = self._create_mock_driver()
        result = scraper._input_password()
        assert result is False

    @patch("builtins.input", return_value=TEST_2FA_CODE)
    @patch("src.x_scraper.time.sleep")
    def test_handle_2fa_with_code(self, mock_sleep, mock_input):
        """Test 2FA handling with valid code"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        mock_driver = self._create_mock_driver()
        scraper.driver = mock_driver

        # Setup mock 2FA field and page_source
        mock_2fa_field = Mock()
        mock_driver.find_element.return_value = mock_2fa_field
        mock_driver.page_source = "2FA verification code"
        mock_driver.current_url = "https://x.com/home"

        result = scraper._handle_2fa()

        assert result is True
        mock_input.assert_called_once()
        mock_2fa_field.clear.assert_called_once()

    @patch("builtins.input", return_value="")
    @patch("src.x_scraper.time.sleep")
    def test_handle_2fa_no_code(self, mock_sleep, mock_input):
        """Test 2FA handling with empty code"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        mock_driver = self._create_mock_driver()
        scraper.driver = mock_driver

        # Setup mock to find no 2FA field
        mock_driver.find_element.side_effect = NoSuchElementException()
        mock_driver.page_source = "no 2FA required"

        result = scraper._handle_2fa()

        assert result is True  # No 2FA field found, so returns True
        mock_input.assert_not_called()  # input should not be called if no 2FA field

    @patch("builtins.input", return_value="")
    @patch("src.x_scraper.time.sleep")
    def test_handle_2fa_empty_code(self, mock_sleep, mock_input):
        """Test 2FA handling with empty code when 2FA field is found"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        mock_driver = self._create_mock_driver()
        scraper.driver = mock_driver

        # Setup mock 2FA field and page_source
        mock_2fa_field = Mock()
        mock_driver.find_element.return_value = mock_2fa_field
        mock_driver.page_source = "2FA verification code"

        result = scraper._handle_2fa()

        assert result is False  # Empty code should return False
        mock_input.assert_called_once()

    def test_handle_2fa_no_driver(self):
        """Test 2FA handling without driver"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)
        result = scraper._handle_2fa()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_verify_login_with_auth_token(self, mock_sleep):
        """Test login verification with auth token"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)

        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [{"name": "auth_token", "value": "test_token"}]
        scraper.driver = mock_driver

        result = scraper._verify_login()
        assert result is True

    @patch("src.x_scraper.time.sleep")
    def test_verify_login_without_auth_token(self, mock_sleep):
        """Test login verification without auth token"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)

        mock_driver = Mock()
        mock_driver.get_cookies.return_value = []
        mock_driver.current_url = "https://twitter.com/login"
        scraper.driver = mock_driver

        result = scraper._verify_login()
        assert result is False

    def test_verify_login_no_driver(self):
        """Test login verification without driver"""
        scraper = XScraper(tbb_path=TEST_TBB_PATH)

        result = scraper._verify_login()
        assert result is False

    def test_navigate_to_x_no_driver(self):
        """Test navigation without driver"""
        result = self.scraper.navigate_to_x()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_navigate_to_x_success(self, mock_sleep):
        """Test successful navigation to X"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        result = self.scraper.navigate_to_x()
        assert result is True
        mock_driver.get.assert_called_once_with("https://x.com")

    def test_search_tweets_no_driver(self):
        """Test search tweets without driver"""
        result = self.scraper.search_tweets("test query")
        assert result == []

    def test_get_user_profile_no_driver(self):
        """Test get user profile without driver"""
        result = self.scraper.get_user_profile("testuser")
        assert result is None

    def test_close(self):
        """Test browser close"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        self.scraper.close()
        mock_driver.quit.assert_called_once()

    def test_context_manager(self):
        """Test context manager functionality"""
        with XScraper(tbb_path=TEST_TBB_PATH) as scraper:
            assert isinstance(scraper, XScraper)
        # close() should be called automatically

    def test_take_screenshot_no_driver(self):
        """Test screenshot without driver"""
        result = self.scraper.take_screenshot()
        assert result is None

    def test_take_screenshot_success(self):
        """Test successful screenshot using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            # Mock file stats
            mock_stat.return_value.st_size = 12345

            result = self.scraper.take_screenshot("test_screenshot")
            # Check that a path is returned (actual path will be data/screenshots/test_screenshot.png)
            assert result is not None
            assert "test_screenshot.png" in result

    def test_take_screenshot_with_timestamp(self):
        """Test screenshot with timestamp using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            # Mock file stats
            mock_stat.return_value.st_size = 12345

            result = self.scraper.take_screenshot()
            # Check that a path is returned with timestamp
            assert result is not None
            assert "screenshot_" in result
            assert ".png" in result

    def test_take_screenshot_adds_png_extension(self):
        """Test screenshot adds .png extension using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            # Mock file stats
            mock_stat.return_value.st_size = 12345

            result = self.scraper.take_screenshot("test_screenshot")
            assert result is not None
            assert "test_screenshot.png" in result

    def test_take_screenshot_preserves_png_extension(self):
        """Test screenshot preserves existing .png extension using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            # Mock file stats
            mock_stat.return_value.st_size = 12345

            result = self.scraper.take_screenshot("test_screenshot.png")
            assert result is not None
            assert "test_screenshot.png" in result

    def test_take_screenshot_failure(self):
        """Test screenshot failure using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = False
        self.scraper.driver = mock_driver

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=True):
            result = self.scraper.take_screenshot("test_screenshot")
            assert result is None

    def test_take_screenshot_exception_handling(self):
        """Test take_screenshot exception handling"""
        mock_driver = Mock()
        mock_driver.save_screenshot.side_effect = Exception("Screenshot failed")
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot("test.png")
        assert result is None

    def test_save_session_cookies_success(self):
        """Test successful cookie saving"""
        mock_driver = Mock()
        mock_cookies = [
            {"name": "auth_token", "value": "abc123", "domain": ".twitter.com"},
            {"name": "ct0", "value": "def456", "domain": ".twitter.com"},
            {"name": "random_cookie", "value": "xyz789", "domain": ".example.com"},
        ]
        mock_driver.get_cookies.return_value = mock_cookies
        self.scraper.driver = mock_driver

        # Mock the cookie manager's save_cookies method
        with patch.object(self.scraper.cookie_manager, "save_cookies", return_value=True) as mock_save:
            self.scraper._save_session_cookies()
            mock_save.assert_called_once_with(mock_cookies)

    def test_save_session_cookies_no_driver(self):
        """Test cookie saving without driver"""
        self.scraper.driver = None

        # Should not raise exception
        self.scraper._save_session_cookies()

    def test_try_cookie_login_success(self):
        """Test successful cookie-based login"""
        mock_driver = Mock()
        mock_cookies = [
            {"name": "auth_token", "value": "abc123", "domain": ".twitter.com", "path": "/"},
        ]
        self.scraper.driver = mock_driver

        # Mock cookie manager methods
        with (
            patch.object(self.scraper.cookie_manager, "has_valid_cookies", return_value=True),
            patch.object(self.scraper.cookie_manager, "load_cookies", return_value=mock_cookies),
            patch.object(self.scraper, "_apply_cookies_to_session", return_value=True),
        ):
            result = self.scraper._try_cookie_login()

        assert result is True

    def test_try_cookie_login_no_cookies(self):
        """Test cookie login with no saved cookies"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        # Mock cookie manager to return no valid cookies
        with patch.object(self.scraper.cookie_manager, "has_valid_cookies", return_value=False):
            result = self.scraper._try_cookie_login()

        assert result is False

    def test_try_cookie_login_expired_cookies(self):
        """Test cookie login with expired cookies"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        # Mock cookie manager to return no valid cookies (expired)
        with patch.object(self.scraper.cookie_manager, "has_valid_cookies", return_value=False):
            result = self.scraper._try_cookie_login()

        assert result is False

    def test_clear_saved_cookies_success(self):
        """Test successful cookie clearing"""
        # Mock cookie manager's clear_cookies method
        with patch.object(self.scraper.cookie_manager, "clear_cookies", return_value=True) as mock_clear:
            result = self.scraper.clear_saved_cookies()

        assert result is True
        mock_clear.assert_called_once()

    @patch.object(Path, "exists")
    def test_clear_saved_cookies_no_file(self, mock_exists):
        """Test cookie clearing when no file exists"""
        mock_exists.return_value = False

        result = self.scraper.clear_saved_cookies()

        assert result is True

    def test_logout_no_driver(self):
        """Test logout without driver"""
        self.scraper.driver = None

        result = self.scraper.logout()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_logout_success(self, mock_sleep):
        """Test successful logout"""
        mock_driver = Mock()
        mock_logout_button = Mock()
        mock_driver.find_element.return_value = mock_logout_button
        self.scraper.driver = mock_driver

        with patch.object(self.scraper, "clear_saved_cookies", return_value=True):
            result = self.scraper.logout()

        assert result is True
        mock_driver.get.assert_called_with("https://twitter.com/logout")
        mock_logout_button.click.assert_called_once()
        mock_driver.delete_all_cookies.assert_called_once()

    def test_is_logged_in_no_driver(self):
        """Test login status check without driver"""
        self.scraper.driver = None

        result = self.scraper.is_logged_in()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_is_logged_in_true(self, mock_sleep):
        """Test login status check when logged in"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        with patch.object(self.scraper, "_verify_login", return_value=True):
            result = self.scraper.is_logged_in()

        assert result is True
        mock_driver.get.assert_called_with("https://twitter.com/home")

    @patch("src.x_scraper.time.sleep")
    @patch.object(XScraper, "_try_cookie_login")
    @patch.object(XScraper, "_verify_login")
    @patch.object(XScraper, "_save_session_cookies")
    def test_login_with_cookie_success(self, mock_save_cookies, mock_verify, mock_cookie_login, mock_sleep):
        """Test login using saved cookies"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver
        mock_cookie_login.return_value = True

        result = self.scraper.login()

        assert result is True
        mock_cookie_login.assert_called_once()
        # Should not call manual login methods when cookie login succeeds
        mock_verify.assert_not_called()
        mock_save_cookies.assert_not_called()

    def test_take_debug_screenshot_file_creation(self):
        """Test that debug screenshot creates all expected files"""
        from pathlib import Path

        # Create a mock that actually creates a file
        def mock_save_screenshot(file_path):
            # Create a minimal PNG file for testing
            png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Simple PNG header + data
            Path(file_path).write_bytes(png_header)
            return True

        mock_driver = Mock()
        mock_driver.current_url = "https://x.com/test"
        mock_driver.title = "Test Page"
        mock_driver.get_window_size.return_value = {"width": 1920, "height": 1080}
        mock_driver.page_source = "<html><head><title>Test</title></head><body>Test content</body></html>"
        mock_driver.save_screenshot.side_effect = mock_save_screenshot

        # Create scraper instance
        scraper = XScraper(tbb_path="/opt/torbrowser", headless=True)
        scraper.driver = mock_driver

        # Take debug screenshot
        description = "test_file_creation"
        scraper.take_debug_snapshot(description)

        # Check that debug directory was created
        import time

        from src.constants import SCREENSHOTS_DIR

        timestamp_pattern = time.strftime("%Y%m%d_%H%M")  # Pattern matching for timestamp
        debug_dir = SCREENSHOTS_DIR / "debug"
        debug_dirs = list(debug_dir.glob(f"{timestamp_pattern}*{description}"))

        assert len(debug_dirs) > 0, f"Debug directory not found matching pattern: {timestamp_pattern}*{description}"
        debug_dir = debug_dirs[0]

        # Verify all expected files exist
        screenshot_file = debug_dir / "screenshot.png"
        html_file = debug_dir / "page_source.html"
        metadata_file = debug_dir / "metadata.txt"

        assert screenshot_file.exists(), f"Screenshot PNG file not created: {screenshot_file}"
        assert html_file.exists(), f"Page source HTML file not created: {html_file}"
        assert metadata_file.exists(), f"Metadata txt file not created: {metadata_file}"

        # Verify file contents are not empty
        assert screenshot_file.stat().st_size > 0, "Screenshot file is empty"
        assert html_file.stat().st_size > 0, "HTML file is empty"
        assert metadata_file.stat().st_size > 0, "Metadata file is empty"

        # Verify HTML content
        html_content = html_file.read_text(encoding="utf-8")
        assert "<html>" in html_content, "HTML file does not contain valid HTML content"
        assert "Test content" in html_content, "HTML file does not contain expected page content"

        # Verify metadata content
        metadata_content = metadata_file.read_text(encoding="utf-8")
        assert "Debug Snapshot Metadata" in metadata_content, "Metadata file missing header"
        assert description in metadata_content, "Metadata file missing description"
        assert "https://x.com/test" in metadata_content, "Metadata file missing URL"
        assert "Files Created:" in metadata_content, "Metadata file missing files created info"
        assert "page_source.html" in metadata_content, "Metadata file missing HTML file info"

        # Clean up - remove test files
        import shutil

        shutil.rmtree(debug_dir)


class TestTweet:
    """Test cases for Tweet model"""

    def test_tweet_creation(self):
        """Test tweet creation with default values"""
        tweet = Tweet()
        assert tweet.text == ""
        assert tweet.author == ""
        assert tweet.likes == 0
        assert tweet.retweets == 0
        assert tweet.replies == 0
        assert tweet.timestamp == ""

    def test_tweet_creation_with_values(self):
        """Test tweet creation with specific values"""
        tweet = Tweet(
            text="Test tweet content",
            author="testuser",
            likes=100,
            retweets=20,
            replies=5,
            timestamp="2023-01-01T00:00:00",
        )
        assert tweet.text == "Test tweet content"
        assert tweet.author == "testuser"
        assert tweet.likes == 100
        assert tweet.retweets == 20
        assert tweet.replies == 5
        assert tweet.timestamp == "2023-01-01T00:00:00"


class TestUserProfile:
    """Test cases for UserProfile model"""

    def test_profile_creation(self):
        """Test user profile creation with default values"""
        profile = UserProfile()
        assert profile.username == ""
        assert profile.display_name == ""
        assert profile.bio == ""
        assert profile.followers_count == 0
        assert profile.following_count == 0

    def test_profile_creation_with_values(self):
        """Test user profile creation with specific values"""
        profile = UserProfile(
            username="testuser",
            display_name="Test User",
            bio="Test bio description",
            followers_count=1000,
            following_count=500,
        )
        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.bio == "Test bio description"
        assert profile.followers_count == 1000
        assert profile.following_count == 500
