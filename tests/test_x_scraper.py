#!/usr/bin/env python3
"""
Tests for X scraper functionality
"""

from unittest.mock import Mock, patch

from selenium.webdriver.common.keys import Keys

from src.models import Tweet, UserProfile
from src.x_scraper import XScraper


class TestXScraper:
    """Test cases for XScraper class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = XScraper(
            tbb_path="/fake/tor/browser/path",
            email="test@example.com",
            username="testuser",
            password="testpass",
        )

    def test_init(self):
        """Test XScraper initialization"""
        assert self.scraper.tbb_path == "/fake/tor/browser/path"
        assert self.scraper.headless is True
        assert self.scraper.email == "test@example.com"
        assert self.scraper.username == "testuser"
        assert self.scraper.password == "testpass"
        assert self.scraper.driver is None

    def test_init_without_credentials(self):
        """Test XScraper initialization without credentials"""
        scraper = XScraper(tbb_path="/fake/path")
        assert scraper.tbb_path == "/fake/path"
        assert scraper.headless is True
        assert scraper.email is None
        assert scraper.username is None
        assert scraper.password is None

    @patch("src.x_scraper.verify_tor_connection", return_value=True)
    @patch("src.x_scraper.create_tor_browser_driver")
    def test_start_success(self, mock_create_driver, mock_verify_tor):
        """Test successful start with Tor verification"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver

        result = self.scraper.start()
        assert result is True
        assert self.scraper.driver == mock_driver
        mock_create_driver.assert_called_once_with(
            "/fake/tor/browser/path",
            headless=True,
        )
        mock_verify_tor.assert_called_once_with(mock_driver)

    @patch("src.x_scraper.verify_tor_connection", return_value=False)
    @patch("src.x_scraper.create_tor_browser_driver")
    def test_start_success_basic_connectivity_only(self, mock_create_driver, mock_verify_tor):
        """Test start with driver creation success but Tor verification failure"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver

        result = self.scraper.start()
        assert result is False  # Should fail because Tor verification fails
        assert self.scraper.driver == mock_driver  # Driver should be set even if verification fails
        mock_create_driver.assert_called_once()
        mock_verify_tor.assert_called_once_with(mock_driver)

    @patch("src.x_scraper.verify_tor_connection", return_value=False)
    @patch("src.x_scraper.create_tor_browser_driver")
    def test_start_failure_no_connectivity(self, mock_create_driver, mock_verify_tor):
        """Test start failure when Tor verification fails"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver

        result = self.scraper.start()
        assert result is False
        assert self.scraper.driver == mock_driver  # Driver should be set even if verification fails
        mock_create_driver.assert_called_once()
        mock_verify_tor.assert_called_once_with(mock_driver)

    @patch("src.x_scraper.verify_tor_connection", return_value=True)
    @patch("src.x_scraper.create_tor_browser_driver")
    def test_start_docker_environment_detection(self, mock_create_driver, mock_verify_tor):
        """Test Docker environment detection (handled by tor_helpers)"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver

        result = self.scraper.start()
        assert result is True
        mock_create_driver.assert_called_once()
        mock_verify_tor.assert_called_once_with(mock_driver)

    @patch("src.utils.create_tor_browser_driver")
    def test_start_failure(self, mock_create_driver):
        """Test start when driver creation fails"""
        mock_create_driver.side_effect = Exception("Driver creation failed")

        result = self.scraper.start()
        assert result is False
        assert self.scraper.driver is None

    @patch("src.utils.verify_tor_connection")
    @patch("src.utils.create_tor_browser_driver")
    def test_start_failure_connection_exception(self, mock_create_driver, mock_verify_tor):
        """Test start failure when Tor verification raises an exception"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver
        mock_verify_tor.side_effect = Exception("Network error")

        result = self.scraper.start()
        assert result is False

    def test_login_no_driver(self):
        """Test login without driver initialized"""
        scraper = XScraper(tbb_path="/fake/path", email="test@example.com", password="pass")
        result = scraper.login()

        assert result is False

    def test_login_no_credentials(self):
        """Test login without credentials"""
        scraper = XScraper(tbb_path="/fake/path")
        scraper.driver = Mock()

        result = scraper.login()
        assert result is False

    def test_login_no_password(self):
        """Test login without password"""
        scraper = XScraper(tbb_path="/fake/path", email="test@example.com")
        scraper.driver = Mock()

        result = scraper.login()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_input_username_success(self, mock_sleep):
        """Test successful username input"""
        scraper = XScraper(tbb_path="/fake/path", email="test@example.com", password="pass")

        mock_driver = Mock()
        mock_username_field = Mock()
        mock_driver.find_element.return_value = mock_username_field
        scraper.driver = mock_driver

        result = scraper._input_username()

        assert result is True
        mock_username_field.clear.assert_called_once()
        mock_username_field.send_keys.assert_called()

    def test_input_username_no_driver(self):
        """Test username input without driver"""
        scraper = XScraper(tbb_path="/fake/path", email="test@example.com")

        result = scraper._input_username()
        assert result is False

    def test_input_username_no_identifier(self):
        """Test username input without email or username"""
        scraper = XScraper(tbb_path="/fake/path")
        scraper.driver = Mock()

        result = scraper._input_username()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_input_password_success(self, mock_sleep):
        """Test successful password input"""
        scraper = XScraper(tbb_path="/fake/path", password="testpass")

        mock_driver = Mock()
        mock_password_field = Mock()
        mock_driver.find_element.return_value = mock_password_field
        scraper.driver = mock_driver

        result = scraper._input_password()

        assert result is True
        mock_password_field.clear.assert_called_once()
        assert mock_password_field.send_keys.call_count == 2
        mock_password_field.send_keys.assert_any_call("testpass")
        mock_password_field.send_keys.assert_any_call(Keys.RETURN)

    def test_input_password_no_driver(self):
        """Test password input without driver"""
        scraper = XScraper(tbb_path="/fake/path", password="testpass")

        result = scraper._input_password()
        assert result is False

    def test_input_password_no_password(self):
        """Test password input without password"""
        scraper = XScraper(tbb_path="/fake/path")
        scraper.driver = Mock()

        result = scraper._input_password()
        assert result is False

    @patch("builtins.input", return_value="123456")
    @patch("src.x_scraper.time.sleep")
    def test_handle_2fa_with_code(self, mock_sleep, mock_input):
        """Test 2FA handling with code input"""
        scraper = XScraper(tbb_path="/fake/path")

        mock_driver = Mock()
        mock_tfa_field = Mock()
        mock_driver.find_element.return_value = mock_tfa_field
        mock_driver.page_source = "Email verification code required"
        mock_driver.current_url = "https://twitter.com/home"
        scraper.driver = mock_driver

        result = scraper._handle_2fa()

        assert result is True
        # Check that the code was entered character by character
        assert mock_tfa_field.send_keys.call_count == 7  # 6 chars + RETURN

    @patch("builtins.input", return_value="")
    @patch("src.x_scraper.time.sleep")
    def test_handle_2fa_no_code(self, mock_sleep, mock_input):
        """Test 2FA handling without code input"""
        scraper = XScraper(tbb_path="/fake/path")

        mock_driver = Mock()
        mock_tfa_field = Mock()
        mock_driver.find_element.return_value = mock_tfa_field
        mock_driver.page_source = "Email verification"
        scraper.driver = mock_driver

        result = scraper._handle_2fa()
        assert result is False

    def test_handle_2fa_no_driver(self):
        """Test 2FA handling without driver"""
        scraper = XScraper(tbb_path="/fake/path")

        result = scraper._handle_2fa()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_verify_login_with_auth_token(self, mock_sleep):
        """Test login verification with auth token"""
        scraper = XScraper(tbb_path="/fake/path")

        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [{"name": "auth_token", "value": "test_token"}]
        scraper.driver = mock_driver

        result = scraper._verify_login()
        assert result is True

    @patch("src.x_scraper.time.sleep")
    def test_verify_login_without_auth_token(self, mock_sleep):
        """Test login verification without auth token"""
        scraper = XScraper(tbb_path="/fake/path")

        mock_driver = Mock()
        mock_driver.get_cookies.return_value = []
        mock_driver.current_url = "https://twitter.com/login"
        scraper.driver = mock_driver

        result = scraper._verify_login()
        assert result is False

    def test_verify_login_no_driver(self):
        """Test login verification without driver"""
        scraper = XScraper(tbb_path="/fake/path")

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
        with XScraper(tbb_path="/fake/path") as scraper:
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

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=True):
            result = self.scraper.take_screenshot("test_screenshot")
            # Check that a path is returned (actual path will be reports/screenshots/test_screenshot.png)
            assert result is not None
            assert "test_screenshot.png" in result

    def test_take_screenshot_with_timestamp(self):
        """Test screenshot with timestamp using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=True):
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

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=True):
            result = self.scraper.take_screenshot("test_screenshot")
            assert result is not None
            assert "test_screenshot.png" in result

    def test_take_screenshot_preserves_png_extension(self):
        """Test screenshot preserves existing .png extension using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=True):
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
        """Test screenshot exception handling using utils"""
        mock_driver = Mock()
        mock_driver.save_screenshot.side_effect = Exception("Screenshot error")
        self.scraper.driver = mock_driver

        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=True):
            result = self.scraper.take_screenshot("test_screenshot")
            assert result is None


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
