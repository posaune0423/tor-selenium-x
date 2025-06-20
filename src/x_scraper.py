#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser with tbselenium
"""

import json
import time
from pathlib import Path

import tbselenium.common as tb_common
from loguru import logger
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import launch_tbb_tor_with_stem

from src.models import Tweet, UserProfile
from src.utils import (
    clean_text,
    get_user_agent,
    random_delay,
    validate_x_username,
)


class XScraper:
    """X (Twitter) scraper using Tor Browser"""

    def __init__(
        self,
        tbb_path: str,
        headless: bool = True,
        use_stem: bool = True,
        socks_port: int = 9150,
        control_port: int = 9151,
        data_dir: str | None = None,
    ):
        """
        Initialize X scraper.

        Args:
            tbb_path: Path to Tor Browser directory
            headless: Whether to run in headless mode
            use_stem: Whether to use Stem to manage Tor process
            socks_port: SOCKS proxy port
            control_port: Tor control port
            data_dir: Directory to store data files
        """
        self.tbb_path = Path(tbb_path).resolve()
        self.headless = headless
        self.use_stem = use_stem
        self.socks_port = socks_port
        self.control_port = control_port

        # Data directory setup
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path.cwd() / "data"
        self.data_dir.mkdir(exist_ok=True)

        # Driver and process management
        self.driver: TorBrowserDriver | None = None
        self.tor_process = None

        # Session state
        self.is_logged_in = False
        self.current_user = None

        logger.info(f"Initialized X scraper with TBB path: {self.tbb_path}")

    def start(self) -> bool:
        """
        Start the Tor Browser and connect to Tor network.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Start Tor process if using Stem
            if self.use_stem:
                logger.info("Starting Tor process with Stem...")
                self.tor_process = launch_tbb_tor_with_stem(tbb_path=str(self.tbb_path))
                time.sleep(3)  # Wait for Tor to start

            # Configure Tor Browser driver
            logger.info("Starting Tor Browser...")
            tor_cfg = tb_common.USE_STEM if self.use_stem else tb_common.USE_RUNNING_TOR

            # Additional options for headless mode
            pref_dict = {}
            if self.headless:
                # Set headless preference
                pref_dict["general.useragent.override"] = get_user_agent()

            # Initialize driver
            self.driver = TorBrowserDriver(
                tbb_path=str(self.tbb_path),
                tor_cfg=tor_cfg,
                socks_port=self.socks_port,
                control_port=self.control_port,
                headless=self.headless,
                pref_dict=pref_dict,
            )

            # Check Tor connection
            if self._check_tor_connection():
                logger.success("Successfully connected to Tor network")
                return True
            else:
                logger.error("Failed to connect to Tor network")
                return False

        except Exception as e:
            logger.error(f"Error starting X scraper: {e}")
            return False

    def _check_tor_connection(self) -> bool:
        """
        Check if Tor connection is working.

        Returns:
            True if connected, False otherwise
        """
        if not self.driver:
            return False

        try:
            logger.info("Checking Tor connection...")
            self.driver.get("https://check.torproject.org")

            # Wait for page to load
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.TAG_NAME, "body")))

            # Check if we're using Tor
            if "congratulations" in self.driver.title.lower():
                # Try to extract IP address
                try:
                    ip_element = self.driver.find_element(By.TAG_NAME, "strong")
                    ip_address = ip_element.text
                    logger.info(f"Connected via Tor - IP: {ip_address}")
                except NoSuchElementException:
                    logger.info("Connected via Tor - IP extraction failed")
                return True
            else:
                logger.warning("Not connected via Tor")
                return False

        except Exception as e:
            logger.error(f"Error checking Tor connection: {e}")
            return False

    def navigate_to_x(self) -> bool:
        """
        Navigate to X (Twitter) homepage.

        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            logger.info("Navigating to X.com...")
            self.driver.get("https://x.com")

            # Wait for page to load
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.TAG_NAME, "body")))

            # Add random delay
            random_delay(2, 4)

            logger.success("Successfully navigated to X.com")
            return True

        except Exception as e:
            logger.error(f"Error navigating to X: {e}")
            return False

    def search_tweets(self, query: str, max_tweets: int = 20) -> list[Tweet]:
        """
        Search for tweets using the search function.

        Args:
            query: Search query
            max_tweets: Maximum number of tweets to collect

        Returns:
            List of Tweet objects
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return []

        tweets = []

        try:
            # Navigate to search
            search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
            logger.info(f"Searching for: {query}")
            self.driver.get(search_url)

            # Wait for search results to load
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']"))
            )

            random_delay(3, 5)

            # Scroll and collect tweets
            collected = 0
            scroll_attempts = 0
            max_scroll_attempts = 10

            while collected < max_tweets and scroll_attempts < max_scroll_attempts:
                # Find tweet elements
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")

                for element in tweet_elements[collected:]:
                    if collected >= max_tweets:
                        break

                    tweet = self._extract_tweet_data(element)
                    if tweet and tweet.text:  # Only add tweets with content
                        tweets.append(tweet)
                        collected += 1

                if collected < max_tweets:
                    # Scroll down to load more tweets
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    random_delay(2, 4)
                    scroll_attempts += 1

            logger.success(f"Collected {len(tweets)} tweets for query: {query}")
            return tweets

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return tweets

    def get_user_profile(self, username: str) -> UserProfile | None:
        """
        Get user profile information.

        Args:
            username: X username (without @)

        Returns:
            UserProfile object or None
        """
        if not validate_x_username(username):
            logger.error(f"Invalid username: {username}")
            return None

        if not self.driver:
            logger.error("Driver not initialized")
            return None

        try:
            # Navigate to user profile
            profile_url = f"https://x.com/{username}"
            logger.info(f"Getting profile for: @{username}")
            self.driver.get(profile_url)

            # Wait for profile to load
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']"))
            )

            random_delay(3, 5)

            # Extract profile data
            profile = self._extract_profile_data(username)

            if profile.username:
                logger.success(f"Successfully extracted profile for @{username}")
            else:
                logger.warning(f"Profile data extraction incomplete for @{username}")

            return profile

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    def get_user_tweets(self, username: str, max_tweets: int = 20) -> list[Tweet]:
        """
        Get tweets from a specific user.

        Args:
            username: X username (without @)
            max_tweets: Maximum number of tweets to collect

        Returns:
            List of Tweet objects
        """
        if not validate_x_username(username):
            logger.error(f"Invalid username: {username}")
            return []

        if not self.driver:
            logger.error("Driver not initialized")
            return []

        tweets = []

        try:
            # Navigate to user's tweets
            profile_url = f"https://x.com/{username}"
            logger.info(f"Getting tweets from: @{username}")
            self.driver.get(profile_url)

            # Wait for tweets to load
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']"))
            )

            random_delay(3, 5)

            # Scroll and collect tweets
            collected = 0
            scroll_attempts = 0
            max_scroll_attempts = 10

            while collected < max_tweets and scroll_attempts < max_scroll_attempts:
                # Find tweet elements
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")

                for element in tweet_elements[collected:]:
                    if collected >= max_tweets:
                        break

                    tweet = self._extract_tweet_data(element)
                    if tweet and tweet.text and tweet.author.lower() == username.lower():
                        tweets.append(tweet)
                        collected += 1

                if collected < max_tweets:
                    # Scroll down to load more tweets
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    random_delay(2, 4)
                    scroll_attempts += 1

            logger.success(f"Collected {len(tweets)} tweets from @{username}")
            return tweets

        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            return tweets

    def _extract_tweet_data(self, element) -> Tweet | None:
        """
        Extract tweet data from a tweet element.

        Args:
            element: Tweet element from Selenium

        Returns:
            Tweet object or None
        """
        try:
            tweet = Tweet()

            # Extract text content
            try:
                text_element = element.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']")
                tweet.text = clean_text(text_element.text)
            except NoSuchElementException:
                # Some tweets might not have text (e.g., pure media tweets)
                pass

            # Extract author
            try:
                author_element = element.find_element(By.CSS_SELECTOR, "[data-testid='User-Name'] a")
                author_href = author_element.get_attribute("href")
                if author_href:
                    tweet.author = author_href.split("/")[-1]
            except NoSuchElementException:
                pass

            # Extract engagement metrics
            try:
                # Likes
                like_element = element.find_element(By.CSS_SELECTOR, "[data-testid='like'] span")
                tweet.likes = self._parse_count(like_element.text)
            except NoSuchElementException:
                pass

            try:
                # Retweets
                retweet_element = element.find_element(By.CSS_SELECTOR, "[data-testid='retweet'] span")
                tweet.retweets = self._parse_count(retweet_element.text)
            except NoSuchElementException:
                pass

            try:
                # Replies
                reply_element = element.find_element(By.CSS_SELECTOR, "[data-testid='reply'] span")
                tweet.replies = self._parse_count(reply_element.text)
            except NoSuchElementException:
                pass

            # Extract timestamp and URL
            try:
                time_element = element.find_element(By.CSS_SELECTOR, "time")
                tweet.timestamp = time_element.get_attribute("datetime")

                # Try to get tweet URL from time element's parent link
                time_link = time_element.find_element(By.XPATH, "..")
                tweet_url = time_link.get_attribute("href")
                if tweet_url:
                    tweet.url = tweet_url
                    # Extract tweet ID from URL
                    url_parts = tweet_url.split("/")
                    if "status" in url_parts:
                        status_index = url_parts.index("status")
                        if status_index + 1 < len(url_parts):
                            tweet.id = url_parts[status_index + 1]

            except NoSuchElementException:
                pass

            return tweet if tweet.text or tweet.author else None

        except Exception as e:
            logger.error(f"Error extracting tweet data: {e}")
            return None

    def _extract_profile_data(self, username: str) -> UserProfile:
        """
        Extract user profile data from profile page.

        Args:
            username: Username to extract data for

        Returns:
            UserProfile object
        """
        profile = UserProfile(username=username)

        try:
            # Extract display name
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserName'] span")  # type: ignore
                profile.display_name = clean_text(name_element.text)
            except NoSuchElementException:
                pass

            # Extract bio
            try:
                bio_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserDescription']")  # type: ignore
                profile.bio = clean_text(bio_element.text)
            except NoSuchElementException:
                pass

            # Extract follower/following counts
            try:
                stats_elements = self.driver.find_elements(  # type: ignore
                    By.CSS_SELECTOR, "[href$='/following'] span, [href$='/verified_followers'] span"
                )
                for element in stats_elements:
                    text = element.text.lower()
                    if "following" in text:
                        profile.following_count = self._parse_count(text.replace("following", "").strip())
                    elif "followers" in text:
                        profile.followers_count = self._parse_count(text.replace("followers", "").strip())
            except NoSuchElementException:
                pass

            # Extract location
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserLocation']")  # type: ignore
                profile.location = clean_text(location_element.text)
            except NoSuchElementException:
                pass

            # Extract website
            try:
                website_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserUrl'] a")  # type: ignore
                profile.website = website_element.get_attribute("href")
            except NoSuchElementException:
                pass

        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")

        return profile

    def _parse_count(self, count_str: str | None) -> int:
        """
        Parse count string (e.g., "1.2K", "10M") to integer.

        Args:
            count_str: Count string to parse (can be None)

        Returns:
            Parsed count as integer
        """
        if not count_str:
            return 0

        count_str = count_str.strip().upper()

        try:
            if "K" in count_str:
                return int(float(count_str.replace("K", "")) * 1000)
            elif "M" in count_str:
                return int(float(count_str.replace("M", "")) * 1000000)
            elif "B" in count_str:
                return int(float(count_str.replace("B", "")) * 1000000000)
            else:
                # Try to parse as regular number
                return int(count_str.replace(",", ""))
        except (ValueError, TypeError):
            return 0

    def save_tweets_to_json(self, tweets: list[Tweet], filename: str) -> bool:
        """
        Save tweets to JSON file.

        Args:
            tweets: List of Tweet objects
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self.data_dir / filename

            # Convert tweets to dictionaries
            tweets_data = []
            for tweet in tweets:
                tweet_dict = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "author": tweet.author,
                    "timestamp": tweet.timestamp,
                    "likes": tweet.likes,
                    "retweets": tweet.retweets,
                    "replies": tweet.replies,
                    "url": tweet.url,
                    "media_urls": tweet.media_urls,
                    "hashtags": tweet.hashtags,
                    "mentions": tweet.mentions,
                }
                tweets_data.append(tweet_dict)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(tweets_data, f, indent=2, ensure_ascii=False)

            logger.success(f"Saved {len(tweets)} tweets to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving tweets to JSON: {e}")
            return False

    def save_profile_to_json(self, profile: UserProfile, filename: str) -> bool:
        """
        Save user profile to JSON file.

        Args:
            profile: UserProfile object
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self.data_dir / filename

            profile_dict = {
                "username": profile.username,
                "display_name": profile.display_name,
                "bio": profile.bio,
                "location": profile.location,
                "website": profile.website,
                "followers_count": profile.followers_count,
                "following_count": profile.following_count,
                "tweets_count": profile.tweets_count,
                "verified": profile.verified,
                "profile_image_url": profile.profile_image_url,
                "banner_image_url": profile.banner_image_url,
                "joined_date": profile.joined_date,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False)

            logger.success(f"Saved profile to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving profile to JSON: {e}")
            return False

    def close(self) -> None:
        """Close the driver and clean up resources."""
        try:
            if self.driver:
                logger.info("Closing Tor Browser...")
                self.driver.quit()
                self.driver = None

            if self.tor_process:
                logger.info("Stopping Tor process...")
                self.tor_process.kill()
                self.tor_process = None

            logger.success("X scraper closed successfully")

        except Exception as e:
            logger.error(f"Error closing X scraper: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
