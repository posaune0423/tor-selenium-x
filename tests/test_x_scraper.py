#!/usr/bin/env python3
"""
Integration tests for X scraper
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models import Tweet, UserProfile
from src.x_scraper import XScraper


class TestXScraper:
    """Test X scraper functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.tbb_path = "/fake/tor/browser/path"
        self.scraper = XScraper(tbb_path=self.tbb_path, headless=True)

    def test_init(self):
        """Test scraper initialization"""
        assert self.scraper.tbb_path == Path(self.tbb_path).resolve()
        assert self.scraper.headless is True
        assert self.scraper.driver is None
        assert self.scraper.tor_process is None

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

        # Mock check_tor_connection
        with patch.object(self.scraper, "_check_tor_connection", return_value=True):
            result = self.scraper.start()

        assert result is True
        assert self.scraper.driver == mock_driver
        assert self.scraper.tor_process == mock_tor_process
        mock_launch_tor.assert_called_once()
        mock_driver_class.assert_called_once()

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

        # Mock check_tor_connection to fail
        with patch.object(self.scraper, "_check_tor_connection", return_value=False):
            result = self.scraper.start()

        assert result is False

    def test_check_tor_connection_no_driver(self):
        """Test Tor connection check without driver"""
        result = self.scraper._check_tor_connection()
        assert result is False

    def test_check_tor_connection_success(self):
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

            result = self.scraper._check_tor_connection()

        assert result is True
        mock_driver.get.assert_called_once_with("https://check.torproject.org")

    def test_search_tweets_no_driver(self):
        """Test search tweets without driver"""
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

        # Mock the _check_element_exists method to return True for main content
        with patch.object(self.scraper, "_check_element_exists", return_value=True), \
             patch.object(self.scraper, "_extract_tweet_data", side_effect=[mock_tweet1, mock_tweet2]), \
             patch.object(self.scraper, "_collect_tweets_from_search", return_value=[mock_tweet1, mock_tweet2]):

            result = self.scraper.search_tweets("test query", max_tweets=2)

        assert len(result) == 2
        assert result[0].text == "Test tweet 1"
        assert result[1].text == "Test tweet 2"
        mock_driver.get.assert_called_once()

    def test_get_user_profile_invalid_username(self):
        """Test getting profile with invalid username"""
        result = self.scraper.get_user_profile("invalid-username")
        assert result is None

    def test_get_user_profile_no_driver(self):
        """Test getting profile without driver"""
        result = self.scraper.get_user_profile("validuser")
        assert result is None

    @patch("src.x_scraper.WebDriverWait")
    def test_get_user_profile_success(self, mock_wait):
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

        with patch.object(self.scraper, "_extract_profile_data", return_value=mock_profile):
            result = self.scraper.get_user_profile("testuser")

        assert result is not None
        assert result.username == "testuser"
        assert result.display_name == "Test User"
        mock_driver.get.assert_called_once()


class TestTweet:
    """Test Tweet data class"""

    def test_tweet_creation(self):
        """Test tweet creation with default values"""
        tweet = Tweet()
        assert tweet.id is None
        assert tweet.text == ""
        assert tweet.author == ""
        assert tweet.timestamp is None
        assert tweet.likes == 0
        assert tweet.retweets == 0
        assert tweet.replies == 0
        assert tweet.url is None

    def test_tweet_creation_with_values(self):
        """Test tweet creation with custom values"""
        tweet = Tweet(
            id="123456789",
            text="Test tweet",
            author="testuser",
            timestamp="2023-01-01T00:00:00Z",
            likes=10,
            retweets=5,
            replies=3,
            url="https://x.com/testuser/status/123456789",
        )

        assert tweet.id == "123456789"
        assert tweet.text == "Test tweet"
        assert tweet.author == "testuser"
        assert tweet.timestamp == "2023-01-01T00:00:00Z"
        assert tweet.likes == 10
        assert tweet.retweets == 5
        assert tweet.replies == 3
        assert tweet.url == "https://x.com/testuser/status/123456789"


class TestUserProfile:
    """Test UserProfile data class"""

    def test_profile_creation(self):
        """Test profile creation with default values"""
        profile = UserProfile()
        assert profile.username == ""
        assert profile.display_name == ""
        assert profile.bio == ""
        assert profile.followers_count is None
        assert profile.following_count is None

    def test_profile_creation_with_values(self):
        """Test profile creation with custom values"""
        profile = UserProfile(
            username="testuser",
            display_name="Test User",
            bio="This is a test bio",
            followers_count=1000,
            following_count=500,
        )

        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.bio == "This is a test bio"
        assert profile.followers_count == 1000
        assert profile.following_count == 500


class TestCountParsing:
    """Test count parsing functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = XScraper("/fake/path")

    def test_parse_count_normal_numbers(self):
        """Test parsing normal numbers"""
        assert self.scraper._parse_count("100") == 100
        assert self.scraper._parse_count("1,234") == 1234
        assert self.scraper._parse_count("0") == 0

    def test_parse_count_with_suffixes(self):
        """Test parsing numbers with K, M, B suffixes"""
        assert self.scraper._parse_count("1K") == 1000
        assert self.scraper._parse_count("1.5K") == 1500
        assert self.scraper._parse_count("2M") == 2000000
        assert self.scraper._parse_count("1.2M") == 1200000
        assert self.scraper._parse_count("1B") == 1000000000
        assert self.scraper._parse_count("2.5B") == 2500000000

    def test_parse_count_invalid_input(self):
        """Test parsing invalid input"""
        assert self.scraper._parse_count("") == 0
        assert self.scraper._parse_count("invalid") == 0
        assert self.scraper._parse_count("K") == 0
        assert self.scraper._parse_count(None) == 0


if __name__ == "__main__":
    pytest.main([__file__])
