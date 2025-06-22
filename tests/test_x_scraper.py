#!/usr/bin/env python3
"""
Tests for X scraper functionality
"""

from unittest.mock import Mock, patch

from selenium.webdriver.common.keys import Keys

from src.models import Tweet, UserProfile
from src.x_scraper import XScraper


class TestXScraper:
    """Test XScraper class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = XScraper(
            tbb_path="/fake/tor/browser/path",
            headless=True,
        )

    def test_init(self):
        """Test XScraper initialization"""
        scraper = XScraper(
            tbb_path="/fake/path", headless=True, email="test@example.com", username="testuser", password="testpass"
        )
        assert scraper.tbb_path == "/fake/path"
        assert scraper.headless is True
        assert scraper.email == "test@example.com"
        assert scraper.username == "testuser"
        assert scraper.password == "testpass"
        assert scraper.driver is None

    def test_init_without_credentials(self):
        """Test XScraper initialization without credentials"""
        scraper = XScraper(tbb_path="/fake/path")

        assert scraper.email is None
        assert scraper.username is None
        assert scraper.password is None

    @patch("src.x_scraper.TorBrowserDriver")
    @patch("src.x_scraper.time.sleep")
    def test_start_success(self, mock_sleep, mock_driver_class):
        """Test successful start with two-step Tor verification"""
        mock_driver = Mock()
        # Mock the two-step verification process
        # First call to get() will be http://httpbin.org/ip
        # Second call to get() will be https://check.torproject.org/
        mock_driver.get.side_effect = [None, None]  # get() calls don't return values
        mock_driver.page_source = "origin"  # First check for basic connectivity

        # Create a side effect that changes page_source after each get() call
        def mock_get_side_effect(url):
            if "httpbin.org/ip" in url:
                mock_driver.page_source = '{"origin": "192.168.1.1"}'
            elif "check.torproject.org" in url:
                mock_driver.page_source = "Congratulations! This browser is configured to use Tor."

        mock_driver.get.side_effect = mock_get_side_effect
        mock_driver_class.return_value = mock_driver

        result = self.scraper.start()
        assert result is True
        assert self.scraper.driver == mock_driver
        # Verify both URLs were called
        assert mock_driver.get.call_count == 2

    @patch("src.x_scraper.TorBrowserDriver")
    @patch("src.x_scraper.time.sleep")
    def test_start_success_basic_connectivity_only(self, mock_sleep, mock_driver_class):
        """Test successful start with basic connectivity but Tor check page fails"""
        mock_driver = Mock()

        def mock_get_side_effect(url):
            if "httpbin.org/ip" in url:
                mock_driver.page_source = '{"origin": "192.168.1.1"}'
            elif "check.torproject.org" in url:
                mock_driver.page_source = "Some other content without Tor confirmation"

        mock_driver.get.side_effect = mock_get_side_effect
        mock_driver_class.return_value = mock_driver

        result = self.scraper.start()
        assert result is True  # Should still succeed with basic connectivity
        assert self.scraper.driver == mock_driver

    @patch("src.x_scraper.TorBrowserDriver")
    @patch("src.x_scraper.time.sleep")
    def test_start_failure_no_connectivity(self, mock_sleep, mock_driver_class):
        """Test start failure when no connectivity is detected"""
        mock_driver = Mock()

        def mock_get_side_effect(url):
            if "httpbin.org/ip" in url:
                mock_driver.page_source = "Connection failed - no response"  # No "origin" keyword

        mock_driver.get.side_effect = mock_get_side_effect
        mock_driver_class.return_value = mock_driver

        result = self.scraper.start()
        assert result is False

    @patch("src.x_scraper.os.path.exists")
    @patch("src.x_scraper.TorBrowserDriver")
    @patch("src.x_scraper.time.sleep")
    def test_start_docker_environment_detection(self, mock_sleep, mock_driver_class, mock_exists):
        """Test Docker environment detection"""
        mock_driver = Mock()
        mock_exists.return_value = True  # Mock /.dockerenv exists

        def mock_get_side_effect(url):
            if "httpbin.org/ip" in url:
                mock_driver.page_source = '{"origin": "192.168.1.1"}'
            elif "check.torproject.org" in url:
                mock_driver.page_source = "Congratulations! This browser is configured to use Tor."

        mock_driver.get.side_effect = mock_get_side_effect
        mock_driver_class.return_value = mock_driver

        result = self.scraper.start()
        assert result is True

    @patch("src.x_scraper.TorBrowserDriver")
    def test_start_failure(self, mock_driver_class):
        """Test start when driver creation fails"""
        mock_driver_class.side_effect = Exception("Driver creation failed")

        result = self.scraper.start()
        assert result is False
        assert self.scraper.driver is None

    @patch("src.x_scraper.TorBrowserDriver")
    @patch("src.x_scraper.time.sleep")
    def test_start_failure_connection_exception(self, mock_sleep, mock_driver_class):
        """Test start failure when connection raises an exception"""
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Network error")
        mock_driver_class.return_value = mock_driver

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
        scraper.driver = mock_driver

        result = scraper._handle_2fa()

        assert result is True
        mock_tfa_field.clear.assert_called_once()
        assert mock_tfa_field.send_keys.call_count == 2
        mock_tfa_field.send_keys.assert_any_call("123456")
        mock_tfa_field.send_keys.assert_any_call(Keys.RETURN)

    @patch("builtins.input", return_value="")
    @patch("src.x_scraper.time.sleep")
    def test_handle_2fa_no_code(self, mock_sleep, mock_input):
        """Test 2FA handling without code input"""
        scraper = XScraper(tbb_path="/fake/path")

        mock_driver = Mock()
        mock_tfa_field = Mock()
        mock_driver.find_element.return_value = mock_tfa_field
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
        mock_driver.get_cookies.return_value = [{"name": "other_cookie", "value": "test_value"}]
        mock_driver.current_url = "https://twitter.com/home"
        mock_driver.find_element.return_value = Mock()  # Found home page element
        scraper.driver = mock_driver

        result = scraper._verify_login()

        assert result is True

    def test_verify_login_no_driver(self):
        """Test login verification without driver"""
        scraper = XScraper(tbb_path="/fake/path")

        result = scraper._verify_login()
        assert result is False

    def test_navigate_to_x_no_driver(self):
        """Test navigating to X without driver"""
        result = self.scraper.navigate_to_x()
        assert result is False

    @patch("src.x_scraper.time.sleep")
    def test_navigate_to_x_success(self, mock_sleep):
        """Test successful navigation to X"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        result = self.scraper.navigate_to_x()
        assert result is True
        mock_driver.get.assert_called_with("https://x.com")

    def test_search_tweets_no_driver(self):
        """Test searching tweets without driver"""
        result = self.scraper.search_tweets("test query")
        assert result == []

    def test_get_user_profile_no_driver(self):
        """Test getting user profile without driver"""
        result = self.scraper.get_user_profile("testuser")
        assert result is None

    def test_close(self):
        """Test closing scraper"""
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        self.scraper.close()
        mock_driver.quit.assert_called_once()
        # Note: The current implementation doesn't set driver to None

    def test_context_manager(self):
        """Test using scraper as context manager"""
        with patch.object(self.scraper, "close") as mock_close:
            with self.scraper as scraper:
                assert scraper == self.scraper
            mock_close.assert_called_once()

    def test_take_screenshot_no_driver(self):
        """Test taking screenshot without driver"""
        result = self.scraper.take_screenshot()
        assert result is None

    @patch("pathlib.Path.mkdir")
    def test_take_screenshot_success(self, mock_mkdir):
        """Test successful screenshot capture"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot("test_screenshot")

        assert result is not None
        assert "test_screenshot.png" in result
        assert "reports/screenshots" in result
        mock_driver.save_screenshot.assert_called_once()
        mock_mkdir.assert_called_once()

    @patch("pathlib.Path.mkdir")
    def test_take_screenshot_with_timestamp(self, mock_mkdir):
        """Test screenshot with automatic timestamp filename"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot()

        assert result is not None
        assert "screenshot_" in result
        assert ".png" in result
        assert "reports/screenshots" in result
        mock_driver.save_screenshot.assert_called_once()

    @patch("pathlib.Path.mkdir")
    def test_take_screenshot_adds_png_extension(self, mock_mkdir):
        """Test that .png extension is added if not present"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot("test_without_extension")

        assert result is not None
        assert result.endswith("test_without_extension.png")
        mock_driver.save_screenshot.assert_called_once()

    @patch("pathlib.Path.mkdir")
    def test_take_screenshot_preserves_png_extension(self, mock_mkdir):
        """Test that existing .png extension is preserved"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot("test.png")

        assert result is not None
        assert result.endswith("test.png")
        # Should not become test.png.png
        assert not result.endswith("test.png.png")
        mock_driver.save_screenshot.assert_called_once()

    @patch("pathlib.Path.mkdir")
    def test_take_screenshot_failure(self, mock_mkdir):
        """Test screenshot failure handling"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = False
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot("failed_screenshot")

        assert result is None
        mock_driver.save_screenshot.assert_called_once()

    @patch("pathlib.Path.mkdir")
    def test_take_screenshot_exception_handling(self, mock_mkdir):
        """Test screenshot exception handling"""
        mock_driver = Mock()
        mock_driver.save_screenshot.side_effect = Exception("Screenshot failed")
        self.scraper.driver = mock_driver

        result = self.scraper.take_screenshot("exception_screenshot")

        assert result is None


class TestTweet:
    """Test Tweet model"""

    def test_tweet_creation(self):
        """Test creating a Tweet with default values"""
        tweet = Tweet()
        assert tweet.id is None
        assert tweet.text == ""
        assert tweet.author == ""
        assert tweet.timestamp is None
        assert tweet.likes == 0
        assert tweet.retweets == 0
        assert tweet.replies == 0

    def test_tweet_creation_with_values(self):
        """Test creating a Tweet with specific values"""
        tweet = Tweet(
            id="123456789",
            text="This is a test tweet",
            author="testuser",
            timestamp="2024-01-01T12:00:00Z",
            likes=42,
            retweets=10,
            replies=5,
        )
        assert tweet.id == "123456789"
        assert tweet.text == "This is a test tweet"
        assert tweet.author == "testuser"
        assert tweet.timestamp == "2024-01-01T12:00:00Z"
        assert tweet.likes == 42
        assert tweet.retweets == 10
        assert tweet.replies == 5


class TestUserProfile:
    """Test UserProfile model"""

    def test_profile_creation(self):
        """Test creating a UserProfile with default values"""
        profile = UserProfile()
        assert profile.username == ""
        assert profile.display_name == ""
        assert profile.bio == ""
        assert profile.location == ""
        assert profile.website is None
        assert profile.followers_count is None
        assert profile.following_count is None
        assert profile.verified is False

    def test_profile_creation_with_values(self):
        """Test creating a UserProfile with specific values"""
        profile = UserProfile(
            username="testuser",
            display_name="Test User",
            bio="This is a test bio",
            location="Test City",
            website="https://example.com",
            followers_count=1000,
            following_count=500,
            verified=True,
        )
        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.bio == "This is a test bio"
        assert profile.location == "Test City"
        assert profile.website == "https://example.com"
        assert profile.followers_count == 1000
        assert profile.following_count == 500
        assert profile.verified is True
