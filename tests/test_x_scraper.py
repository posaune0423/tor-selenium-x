#!/usr/bin/env python3
"""
Tests for X scraper functionality
"""

from unittest.mock import Mock, patch

import pytest

from src.models import Tweet, UserProfile
from src.x_scraper import XScraper


class TestXScraper:
    """Test XScraper class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = XScraper(
            tbb_path="/fake/tor/browser/path",
            headless=True,
            use_stem=False,
        )

    @patch("src.x_scraper.launch_tbb_tor_with_stem")
    @patch("src.x_scraper.TorBrowserDriver")
    def test_init(self, mock_driver_class, mock_launch_tor):
        """Test scraper initialization"""
        scraper = XScraper(
            tbb_path="/test/path",
            headless=False,
            use_stem=True,
            socks_port=9050,
            control_port=9051,
        )
        assert scraper.tbb_path.name == "path"
        assert not scraper.headless
        assert scraper.use_stem
        assert scraper.socks_port == 9050
        assert scraper.control_port == 9051

    @patch("src.x_scraper.launch_tbb_tor_with_stem")
    @patch("src.x_scraper.TorBrowserDriver")
    def test_start_success(self, mock_driver_class, mock_launch_tor):
        """Test successful scraper start"""
        # Mock Tor process
        mock_tor_process = Mock()
        mock_launch_tor.return_value = mock_tor_process

        # Mock driver
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver

        # Mock check_tor method
        with patch.object(self.scraper, "_check_tor", return_value=True):
            result = self.scraper.start()
            assert result is True

    @patch("src.x_scraper.launch_tbb_tor_with_stem")
    @patch("src.x_scraper.TorBrowserDriver")
    def test_start_tor_connection_fails(self, mock_driver_class, mock_launch_tor):
        """Test scraper start when Tor connection fails"""
        # Mock Tor process
        mock_tor_process = Mock()
        mock_launch_tor.return_value = mock_tor_process

        # Mock driver
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver

        # Mock check_tor to fail
        with patch.object(self.scraper, "_check_tor", return_value=False):
            result = self.scraper.start()
            assert result is False

    def test_check_tor_no_driver(self):
        """Test Tor connection check without driver"""
        result = self.scraper._check_tor()
        assert result is False

    def test_check_tor_success(self):
        """Test successful Tor connection check"""
        # Mock driver
        mock_driver = Mock()
        mock_driver.title = "Congratulations. This browser is configured to use Tor."
        mock_driver.page_source = "Congratulations! This browser is configured to use Tor."
        self.scraper.driver = mock_driver

        # Mock WebDriverWait
        with patch("src.x_scraper.WebDriverWait") as mock_wait:
            mock_wait_instance = Mock()
            mock_wait.return_value = mock_wait_instance

            result = self.scraper._check_tor()
            assert result is True

    def test_search_tweets_no_driver(self):
        """Test tweet search without driver"""
        result = self.scraper.search_tweets("test query")
        assert result == []

    @patch("src.x_scraper.WebDriverWait")
    @patch("src.x_scraper.time.sleep")
    @patch("src.x_scraper.random_delay")
    def test_search_tweets_success(self, mock_random_delay, mock_sleep, mock_wait):
        """Test successful tweet search"""
        # Mock driver
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        # Mock driver properties and methods
        mock_driver.current_url = "https://x.com/search?q=testquery&src=typed_query&f=live"
        mock_driver.title = "Search Results"
        mock_driver.page_source = "<html><body>Mock page</body></html>"

        # Mock tweet elements
        mock_element1 = Mock()
        mock_element2 = Mock()
        mock_driver.find_elements.return_value = [mock_element1, mock_element2]

        # Mock WebDriverWait
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance

        # Mock tweet extraction
        mock_tweet1 = Tweet(text="Test tweet 1", author="user1")
        mock_tweet2 = Tweet(text="Test tweet 2", author="user2")

        # Mock the methods that exist in the implementation
        with (
            patch.object(self.scraper, "_go_to_search", return_value=True),
            patch.object(self.scraper, "_collect_tweets", return_value=[mock_tweet1, mock_tweet2]),
        ):
            result = self.scraper.search_tweets("test query", max_tweets=2)
            assert len(result) == 2
            assert result[0].text == "Test tweet 1"
            assert result[1].text == "Test tweet 2"

    def test_get_profile_invalid_username(self):
        """Test getting profile with invalid username"""
        result = self.scraper.get_profile("invalid-username")
        assert result is None

    def test_get_profile_no_driver(self):
        """Test getting profile without driver"""
        result = self.scraper.get_profile("validuser")
        assert result is None

    @patch("src.x_scraper.WebDriverWait")
    def test_get_profile_success(self, mock_wait):
        """Test successful profile retrieval"""
        # Mock driver
        mock_driver = Mock()
        self.scraper.driver = mock_driver

        # Mock WebDriverWait
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance

        # Mock profile extraction
        mock_profile = UserProfile(
            username="testuser", display_name="Test User", bio="Test bio", followers_count=1000, following_count=500
        )

        with patch.object(self.scraper, "_extract_profile", return_value=mock_profile):
            result = self.scraper.get_profile("testuser")
            assert result is not None
            assert result.username == "testuser"
            assert result.display_name == "Test User"


class TestTweet:
    """Test Tweet model"""

    def test_tweet_creation(self):
        """Test Tweet creation with defaults"""
        tweet = Tweet()
        assert tweet.text == ""
        assert tweet.author == ""
        assert tweet.likes == 0
        assert tweet.retweets == 0
        assert tweet.replies == 0

    def test_tweet_creation_with_values(self):
        """Test Tweet creation with values"""
        tweet = Tweet(
            text="Test tweet", author="testuser", likes=10, retweets=5, replies=2, url="https://x.com/test/123"
        )
        assert tweet.text == "Test tweet"
        assert tweet.author == "testuser"
        assert tweet.likes == 10
        assert tweet.retweets == 5
        assert tweet.replies == 2
        assert tweet.url == "https://x.com/test/123"


class TestUserProfile:
    """Test UserProfile model"""

    def test_profile_creation(self):
        """Test UserProfile creation with defaults"""
        profile = UserProfile(username="testuser")
        assert profile.username == "testuser"
        assert profile.display_name == ""
        assert profile.bio == ""
        assert profile.followers_count is None
        assert profile.following_count is None

    def test_profile_creation_with_values(self):
        """Test UserProfile creation with values"""
        profile = UserProfile(
            username="testuser",
            display_name="Test User",
            bio="Test bio",
            followers_count=1000,
            following_count=500,
            location="Test City",
            website="https://test.com",
        )
        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.bio == "Test bio"
        assert profile.followers_count == 1000
        assert profile.following_count == 500
        assert profile.location == "Test City"
        assert profile.website == "https://test.com"


class TestCountParsing:
    """Test count parsing functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = XScraper(tbb_path="/fake/path", headless=True)

    def test_parse_count_normal_numbers(self):
        """Test parsing normal numbers"""
        assert self.scraper._parse_count("123") == 123
        assert self.scraper._parse_count("1,234") == 1234
        assert self.scraper._parse_count("12,345") == 12345

    def test_parse_count_with_suffixes(self):
        """Test parsing numbers with suffixes"""
        assert self.scraper._parse_count("1.2K") == 1200
        assert self.scraper._parse_count("5.5K") == 5500
        assert self.scraper._parse_count("1.5M") == 1500000
        assert self.scraper._parse_count("2.3B") == 2300000000

    def test_parse_count_invalid_input(self):
        """Test parsing invalid input"""
        assert self.scraper._parse_count("") == 0
        assert self.scraper._parse_count(None) == 0
        assert self.scraper._parse_count("invalid") == 0
        assert self.scraper._parse_count("abc123") == 0


if __name__ == "__main__":
    pytest.main([__file__])
