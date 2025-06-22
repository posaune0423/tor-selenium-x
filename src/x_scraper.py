#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser with tbselenium
"""

import json
import random
import time
from datetime import datetime
from pathlib import Path

import tbselenium.common as tb_common
from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import launch_tbb_tor_with_stem

from src.models import SessionState, Tweet, UserProfile, XCredentials
from src.utils import (
    add_anti_detection_measures,
    are_cookies_expired,
    detect_and_handle_captcha,
    extract_attribute_from_driver_by_selectors,
    extract_count_by_selectors,
    extract_text_by_selectors,
    extract_text_from_driver_by_selectors,
    find_elements_by_selectors,
    get_user_agent,
    load_cookies_from_file,
    random_delay,
    safe_click_element,
    save_cookies_to_file,
    simulate_human_click_delay,
    validate_x_username,
)


class XScraper:
    """X (Twitter) scraper using Tor Browser with advanced login capabilities"""

    def __init__(
        self,
        tbb_path: str,
        headless: bool = True,
        use_stem: bool = True,
        socks_port: int = 9150,
        control_port: int = 9151,
        data_dir: str | None = None,
        credentials: XCredentials | None = None,
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
            credentials: X login credentials
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
            self.data_dir = Path.cwd() / "reports" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Driver and process management
        self.driver: TorBrowserDriver | None = None
        self.tor_process = None

        # Session state and credentials
        self.credentials = credentials
        self.session = SessionState()
        self.cookies_file = self.data_dir / "session_cookies.json"

        logger.info(f"Initialized X scraper with TBB path: {self.tbb_path}")

    def start(self) -> bool:
        """
        Start the Tor Browser and connect to Tor network.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._start_tor_process():
                return False

            if not self._initialize_driver():
                return False

            if not self._check_tor_connection():
                logger.error("Failed to connect to Tor network")
                return False

            # Apply anti-detection measures
            if self.driver:
                add_anti_detection_measures(self.driver)

            logger.success("Successfully connected to Tor network")
            return True

        except Exception as e:
            logger.error(f"Error starting X scraper: {e}")
            return False

    def login(self, credentials: XCredentials | None = None) -> bool:
        """
        Login to X with provided credentials.

        Args:
            credentials: Login credentials (uses instance credentials if not provided)

        Returns:
            True if login successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized. Call start() first.")
            return False

        # Use provided credentials or instance credentials
        creds = credentials or self.credentials
        if not creds:
            logger.error("No credentials provided for login")
            return False

        try:
            # Check if we have valid session cookies
            if self._try_restore_session():
                logger.success("Restored session from cookies")
                self.session.is_logged_in = True
                self.session.current_user = creds.username
                return True

            # Perform fresh login
            logger.info("Starting fresh login process")
            return self._perform_login(creds)

        except Exception as e:
            logger.error(f"Login process failed: {e}")
            return False

    def _try_restore_session(self) -> bool:
        """
        Try to restore session from saved cookies.

        Returns:
            True if session restored successfully, False otherwise
        """
        if not self.driver:
            return False

        try:
            # Load cookies from file
            cookies = load_cookies_from_file(str(self.cookies_file))
            if not cookies:
                logger.debug("No saved cookies found")
                return False

            # Check if cookies are expired
            if are_cookies_expired(cookies):
                logger.info("Saved cookies are expired")
                return False

            # Navigate to X homepage first
            logger.info("Attempting to restore session from cookies")
            self.driver.get("https://x.com")
            random_delay(2, 4)

            # Add cookies to driver
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")

            # Navigate to home to verify session
            self.driver.get("https://x.com/home")
            random_delay(3, 5)

            # Check if we're logged in by looking for login indicators
            if self._verify_login_status():
                self.session.session_cookies = cookies
                logger.success("Session successfully restored from cookies")
                return True
            else:
                logger.info("Cookie session invalid, fresh login required")
                return False

        except Exception as e:
            logger.warning(f"Failed to restore session: {e}")
            return False

    def _perform_login(self, credentials: XCredentials) -> bool:
        """
        Perform fresh login with credentials.

        Args:
            credentials: Login credentials

        Returns:
            True if login successful, False otherwise
        """
        if not self.driver:
            return False

        try:
            # Navigate to login page
            logger.info("Navigating to login page")
            self.driver.get("https://x.com/i/flow/login")
            random_delay(3, 5)

            # Handle email/username input
            if not self._handle_initial_input(credentials.email):
                return False

            # Handle potential username verification step
            if not self._handle_username_verification(credentials.username):
                return False

            # Handle password input
            if not self._handle_password_input(credentials.password):
                return False

            # Verify successful login
            if not self._verify_login_success():
                return False

            # Save session cookies for future use
            self._save_session_cookies()

            self.session.is_logged_in = True
            self.session.current_user = credentials.username
            self.session.login_timestamp = datetime.now().isoformat()

            logger.success(f"Successfully logged in as @{credentials.username}")
            return True

        except Exception as e:
            logger.error(f"Login process failed: {e}")
            return False

    def _handle_initial_input(self, email: str) -> bool:
        """Handle email/username input step."""
        if not self.driver:
            return False

        try:
            # Wait for and find email input
            logger.info("Looking for email/username input field")
            email_input = WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']"))
            )

            # Clear and enter email with human-like typing
            email_input.clear()
            random_delay(0.5, 1.5)

            # Type email character by character with human delays
            for char in email:
                email_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            random_delay(1, 2)

            # Find and click Next button
            next_button_selectors = [
                "//span[text()='Next']//ancestor::button",
                "[data-testid='LoginForm_Login_Button']",
                "button[role='button']:has-text('Next')",
                "div[role='button'] span:has-text('Next')",
            ]

            next_button = None
            for selector in next_button_selectors:
                try:
                    if selector.startswith("//"):
                        next_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if not next_button:
                logger.error("Could not find Next button")
                return False

            # Click Next button
            simulate_human_click_delay()
            safe_click_element(self.driver, next_button)

            logger.info("Email submitted successfully")
            random_delay(2, 4)
            return True

        except Exception as e:
            logger.error(f"Failed to handle email input: {e}")
            return False

    def _handle_username_verification(self, username: str) -> bool:
        """Handle optional username verification step."""
        if not self.driver:
            return False

        try:
            # Check if username verification step is present
            # Wait briefly to see if username input appears
            try:
                WebDriverWait(self.driver, 5).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']"))
                )

                # Check current URL to determine if this is username verification
                current_url = self.driver.current_url
                if "identifier" in current_url or "LoginForm" in self.driver.page_source:
                    logger.info("Username verification step detected")

                    username_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='text']")
                    username_input.clear()
                    random_delay(0.5, 1.0)

                    # Type username with human-like delays
                    for char in username:
                        username_input.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))

                    random_delay(1, 2)

                    # Find and click Next button
                    next_button = self.driver.find_element(By.XPATH, "//span[text()='Next']//ancestor::button")
                    safe_click_element(self.driver, next_button)

                    logger.info("Username verification completed")
                    random_delay(2, 4)

            except TimeoutException:
                # No username verification needed
                logger.debug("No username verification step detected")

            return True

        except Exception as e:
            logger.warning(f"Username verification step failed: {e}")
            # Don't fail completely, continue to password step
            return True

    def _handle_password_input(self, password: str) -> bool:
        """Handle password input step."""
        if not self.driver:
            return False

        try:
            logger.info("Looking for password input field")

            # Wait for password field to appear
            password_input = WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
            )

            # Clear and enter password
            password_input.clear()
            random_delay(0.5, 1.5)

            # Type password with human-like delays
            for char in password:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.12))

            random_delay(1, 2)

            # Submit password (Enter key or click login button)
            password_input.send_keys(Keys.RETURN)

            logger.info("Password submitted successfully")
            random_delay(3, 6)  # Wait for login processing

            return True

        except Exception as e:
            logger.error(f"Failed to handle password input: {e}")
            return False

    def _verify_login_status(self) -> bool:
        """Check if currently logged in."""
        if not self.driver:
            return False

        try:
            # Check for logged-in indicators
            logged_in_selectors = [
                "[data-testid='primaryColumn']",
                "[data-testid='AppTabBar_Home_Link']",
                "[data-testid='SideNav_AccountSwitcher_Button']",
            ]

            for selector in logged_in_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    return True
                except TimeoutException:
                    continue

            return False

        except Exception:
            return False

    def _verify_login_success(self) -> bool:
        """Verify that login was successful."""
        if not self.driver:
            return False

        try:
            logger.info("Verifying login success")

            # Check for CAPTCHA
            if not detect_and_handle_captcha(self.driver):
                logger.warning("CAPTCHA detected during login")
                return False

            # Wait for main timeline or home page
            timeline_selectors = [
                "[data-testid='primaryColumn']",
                "[data-testid='AppTabBar_Home_Link']",
                "main[role='main']",
            ]

            for selector in timeline_selectors:
                try:
                    WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.success("Login verification successful")
                    return True
                except TimeoutException:
                    continue

            logger.error("Login verification failed - could not find expected elements")
            return False

        except Exception as e:
            logger.error(f"Login verification failed: {e}")
            return False

    def _save_session_cookies(self) -> None:
        """Save current session cookies to file."""
        if not self.driver:
            return

        try:
            cookies = self.driver.get_cookies()
            if cookies:
                save_cookies_to_file(cookies, str(self.cookies_file))
                self.session.session_cookies = cookies
                logger.info(f"Saved {len(cookies)} session cookies")
            else:
                logger.warning("No cookies to save")

        except Exception as e:
            logger.error(f"Failed to save session cookies: {e}")

    def ensure_logged_in(self) -> bool:
        """
        Ensure user is logged in, attempt login if not.

        Returns:
            True if logged in, False otherwise
        """
        if self.session.is_logged_in and self._verify_login_status():
            logger.debug("Already logged in")
            return True

        if not self.credentials:
            logger.error("No credentials available for login")
            return False

        logger.info("Not logged in, attempting login")
        return self.login()

    def _start_tor_process(self) -> bool:
        """Start Tor process if using Stem."""
        if not self.use_stem:
            return True

        try:
            logger.info("Starting Tor process with Stem...")
            self.tor_process = launch_tbb_tor_with_stem(tbb_path=str(self.tbb_path))
            time.sleep(3)  # Wait for Tor to start
            return True
        except Exception as e:
            logger.error(f"Failed to start Tor process: {e}")
            return False

    def _initialize_driver(self) -> bool:
        """Initialize Tor Browser driver."""
        try:
            logger.info("Starting Tor Browser...")
            tor_cfg = tb_common.USE_STEM if self.use_stem else tb_common.USE_RUNNING_TOR

            # Additional options for headless mode and proxy
            pref_dict = {
                "network.proxy.type": 1,  # Manual proxy configuration
                "network.proxy.socks": "127.0.0.1",
                "network.proxy.socks_port": self.socks_port,
                "network.proxy.socks_version": 5,
                "network.proxy.socks_remote_dns": True,
            }

            if self.headless:
                pref_dict["general.useragent.override"] = get_user_agent()

            logger.info(f"Using SOCKS proxy on port {self.socks_port}")
            logger.info(f"Using control port {self.control_port}")

            # Initialize driver
            self.driver = TorBrowserDriver(
                tbb_path=str(self.tbb_path),
                tor_cfg=tor_cfg,
                socks_port=self.socks_port,
                control_port=self.control_port,
                headless=self.headless,
                pref_dict=pref_dict,
            )

            # Verify driver was created
            if not self.driver:
                logger.error("Driver initialization returned None")
                return False

            logger.info("TorBrowserDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
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
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()

            tor_indicators = [
                "congratulations" in page_title,
                "congratulations" in page_source,
                "using tor" in page_source,
            ]

            if any(tor_indicators):
                logger.info("Successfully connected via Tor")
                return True
            else:
                logger.warning("Tor connection verification failed")
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
        # Guard clauses for early exit
        if not query.strip():
            logger.error("Empty search query provided")
            return []

        if not self.driver:
            logger.error("Driver not initialized")
            return []

        # Remove spaces from query for better results
        clean_query = query.replace(" ", "")
        logger.info(f"Cleaned search query: '{query}' -> '{clean_query}'")

        if not self._navigate_to_search(clean_query):
            return []

        return self._collect_tweets_from_search(max_tweets)

    def _navigate_to_search(self, query: str) -> bool:
        """Navigate to search page and wait for results to load."""
        if not self.driver:
            return False

        try:
            search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
            logger.info(f"Searching for: {query}")
            self.driver.get(search_url)

            # Wait for search page to load - try multiple modern selectors
            logger.debug(f"Waiting for search page to load: {search_url}")

            # Modern X.com main content selectors (2024/2025)
            main_content_selectors = [
                "main[role='main']",  # Most common main element
                "div[data-testid='primaryColumn']",  # Legacy selector
                "section[role='region']",  # Content sections
                "div[dir='ltr']",  # Language direction container
                "div[aria-label*='Timeline']",  # Timeline container
                "div[aria-label*='Search']",  # Search results container
                "[role='main']",  # Generic main role
                "main",  # Basic main tag
            ]

            found_main_content = False
            for i, selector in enumerate(main_content_selectors):
                if self._check_element_exists(selector, timeout=10):
                    logger.debug(f"Found main content with selector[{i}]: {selector}")
                    found_main_content = True
                    break

            if not found_main_content:
                logger.warning("No main content elements found, trying extended wait...")
                # Extended wait for slow loading
                time.sleep(5)

                # Try again with more generic selectors
                generic_selectors = ["body", "div", "section", "article"]
                for selector in generic_selectors:
                    if self._check_element_exists(selector, timeout=5):
                        logger.debug(f"Found basic element: {selector}")
                        found_main_content = True
                        break

            if not found_main_content:
                logger.error("No main content elements found on search page")
                self._debug_page_state(f"Search page load failed for query: {query}")
                return False

            # Additional wait for dynamic content to load
            random_delay(3, 5)

            # Check if we actually got to a search page
            if "search" not in self.driver.current_url.lower():
                logger.warning(f"URL doesn't contain 'search': {self.driver.current_url}")
                self._debug_page_state("Search URL verification failed")
                return False

            logger.success(f"Successfully navigated to search page for: {query}")
            return True

        except Exception as e:
            logger.error(f"Error navigating to search: {e}")
            self._debug_page_state(f"Search navigation error for query: {query}")
            return False

    def _collect_tweets_from_search(self, max_tweets: int) -> list[Tweet]:
        """Collect tweets from search results."""
        if not self.driver:
            return []

        tweets = []
        collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 10

        try:
            while collected < max_tweets and scroll_attempts < max_scroll_attempts:
                # Modern X.com tweet selectors (2024/2025)
                tweet_selectors = [
                    "article[data-testid='tweet']",  # Primary tweet articles
                    "div[data-testid='tweet']",  # Alternative tweet containers
                    "article[role='article']",  # Generic article role
                    "div[data-testid='cellInnerDiv'] article",  # Nested tweet articles
                    "article",  # Basic article tags
                    "[data-testid='tweet']",  # Any element with tweet testid
                ]

                tweet_elements = find_elements_by_selectors(self.driver, tweet_selectors)

                if not tweet_elements:
                    logger.debug(f"No tweet elements found with any selector on attempt {scroll_attempts + 1}")
                    # Try to scroll and continue
                    self._scroll_for_more_content()
                    scroll_attempts += 1
                    continue

                logger.debug(f"Found {len(tweet_elements)} tweet elements")

                # Process new tweets
                for element in tweet_elements[collected:]:
                    if collected >= max_tweets:
                        break

                    tweet = self._extract_tweet_data(element)
                    if tweet and tweet.text:  # Only add tweets with content
                        tweets.append(tweet)
                        collected += 1
                        logger.debug(f"Collected tweet {collected}/{max_tweets}: {tweet.text[:50]}...")

                # Scroll for more tweets if needed
                if collected < max_tweets:
                    self._scroll_for_more_content()
                    scroll_attempts += 1
                    # Add extra delay between scrolls
                    random_delay(2, 4)

            logger.success(f"Collected {len(tweets)} tweets")
            return tweets

        except Exception as e:
            logger.error(f"Error collecting tweets: {e}")
            self._debug_page_state("Tweet collection error")
            return tweets

    def _scroll_for_more_content(self) -> None:
        """Scroll down to load more content."""
        if not self.driver:
            return
        self.driver.execute_script("window.scrollBy(0, 1000);")
        random_delay(2, 4)

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
            self._debug_page_state(f"Profile extraction error for {username}")
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
        # Guard clauses for early exit
        if not validate_x_username(username):
            logger.error(f"Invalid username: {username}")
            return []

        if not self.driver:
            logger.error("Driver not initialized")
            return []

        if not self._navigate_to_user_profile(username):
            return []

        return self._collect_user_tweets(username, max_tweets)

    def _navigate_to_user_profile(self, username: str) -> bool:
        """Navigate to user's profile page."""
        if not self.driver:
            return False

        try:
            profile_url = f"https://x.com/{username}"
            logger.info(f"Getting tweets from: @{username}")
            self.driver.get(profile_url)

            # Wait for tweets to load
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']"))
            )

            random_delay(3, 5)
            return True

        except Exception as e:
            logger.error(f"Error navigating to user profile: {e}")
            return False

    def _collect_user_tweets(self, username: str, max_tweets: int) -> list[Tweet]:
        """Collect tweets from user's profile page."""
        if not self.driver:
            return []

        tweets = []
        collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 10

        try:
            while collected < max_tweets and scroll_attempts < max_scroll_attempts:
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")

                for element in tweet_elements[collected:]:
                    if collected >= max_tweets:
                        break

                    tweet = self._extract_tweet_data(element)
                    if tweet and tweet.text and tweet.author.lower() == username.lower():
                        tweets.append(tweet)
                        collected += 1

                if collected < max_tweets:
                    self._scroll_for_more_content()
                    scroll_attempts += 1

            logger.success(f"Collected {len(tweets)} tweets from @{username}")
            return tweets

        except Exception as e:
            logger.error(f"Error collecting user tweets: {e}")
            return tweets

    def _extract_tweet_data(self, element) -> Tweet | None:
        """
        Extract tweet data from a tweet element.

        Args:
            element: Tweet element from Selenium

        Returns:
            Tweet object or None
        """
        if not element:
            return None

        tweet = Tweet()

        # Extract each piece of data using helper methods
        tweet.text = self._extract_tweet_text(element)
        tweet.author = self._extract_tweet_author(element)
        tweet.likes = self._extract_tweet_likes(element)
        tweet.retweets = self._extract_tweet_retweets(element)
        tweet.replies = self._extract_tweet_replies(element)

        # Extract timestamp and URL data
        self._extract_tweet_time_data(element, tweet)

        # Return tweet only if it has essential data
        if not tweet.text and not tweet.author:
            return None

        return tweet

    def _extract_tweet_text(self, element) -> str:
        """Extract tweet text content using TypeScript-style selectors."""
        try:
            # Define selectors in priority order
            selectors = [
                "[data-testid='tweetText'] span",  # Primary selector
                "[data-testid='tweetText']",  # Fallback 1
                "[lang] span",  # Language-specific spans
                "div[dir='auto'] span",  # Direction-specific spans
                "[role='presentation'] span",  # Presentation role spans
            ]

            return extract_text_by_selectors(element, selectors)

        except Exception as e:
            logger.debug(f"Error extracting tweet text: {e}")
            return ""

    def _extract_tweet_author(self, element) -> str:
        """Extract tweet author username."""
        try:
            author_element = element.find_element(By.CSS_SELECTOR, "[data-testid='User-Name'] a")
            author_href = author_element.get_attribute("href")
            if not author_href:
                return ""
            return author_href.split("/")[-1]
        except NoSuchElementException:
            return ""

    def _extract_tweet_likes(self, element) -> int:
        """Extract tweet likes count."""
        selectors = [
            "[data-testid='like'] span",
            "[data-testid='like']",
            "[aria-label*='like'] span",
            "button[data-testid='like'] span",
            "[role='button'][aria-label*='like'] span",
        ]

        return extract_count_by_selectors(element, selectors, self._parse_count)

    def _extract_tweet_retweets(self, element) -> int:
        """Extract tweet retweets count."""
        selectors = [
            "[data-testid='retweet'] span",
            "[data-testid='unretweet'] span",
            "[aria-label*='retweet'] span",
            "button[data-testid='retweet'] span",
            "[role='button'][aria-label*='retweet'] span",
        ]

        return extract_count_by_selectors(element, selectors, self._parse_count)

    def _extract_tweet_replies(self, element) -> int:
        """Extract tweet replies count."""
        selectors = [
            "[data-testid='reply'] span",
            "[aria-label*='repl'] span",
            "button[data-testid='reply'] span",
            "[role='button'][aria-label*='repl'] span",
        ]

        return extract_count_by_selectors(element, selectors, self._parse_count)

    def _extract_tweet_time_data(self, element, tweet: Tweet) -> None:
        """Extract timestamp and URL data for tweet."""
        try:
            time_element = element.find_element(By.CSS_SELECTOR, "time")
            tweet.timestamp = time_element.get_attribute("datetime") or ""

            # Extract tweet URL and ID
            time_link = time_element.find_element(By.XPATH, "..")
            tweet_url = time_link.get_attribute("href")
            if not tweet_url:
                return

            tweet.url = tweet_url
            self._extract_tweet_id_from_url(tweet_url, tweet)

        except NoSuchElementException:
            pass

    def _extract_tweet_id_from_url(self, tweet_url: str, tweet: Tweet) -> None:
        """Extract tweet ID from URL."""
        url_parts = tweet_url.split("/")
        if "status" not in url_parts:
            return

        status_index = url_parts.index("status")
        if status_index + 1 >= len(url_parts):
            return

        tweet.id = url_parts[status_index + 1]

    def _extract_profile_data(self, username: str) -> UserProfile:
        """
        Extract profile data from the current page.

        Args:
            username: Username for the profile

        Returns:
            UserProfile object
        """
        profile = UserProfile(username=username)

        # Add delay to ensure page is fully loaded
        random_delay(2, 4)

        # Wait for profile header to be loaded
        try:
            logger.debug("Waiting for profile header to load...")
            if self.driver:
                WebDriverWait(self.driver, 10).until(
                    ec.any_of(
                        ec.presence_of_element_located((By.CSS_SELECTOR, "h1[role='heading']")),
                        ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserName']")),
                        ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserProfileHeader_Items']")),
                    )
                )
                logger.debug("Profile header loaded successfully")
        except Exception as e:
            logger.warning(f"Profile header did not load as expected: {e}")

        # Extract each piece of profile data using helper methods
        profile.display_name = self._extract_profile_display_name()
        profile.bio = self._extract_profile_bio()
        profile.location = self._extract_profile_location()
        profile.website = self._extract_profile_website()

        # Extract follower/following counts
        self._extract_profile_stats(profile)

        return profile

    def _extract_profile_display_name(self) -> str:
        """Extract profile display name."""
        selectors = [
            "h1[role='heading'] span span",  # Primary selector for display name
            "[data-testid='UserName'] span",
            "[data-testid='UserProfileHeader_Items'] h1 span",
            "h1 span span",  # More generic selector
            "h1 div span",  # Alternative structure
        ]

        return extract_text_from_driver_by_selectors(self.driver, selectors)

    def _extract_profile_bio(self) -> str:
        """Extract profile bio/description."""
        # 最初にbio要素の存在を確認
        bio_container_selectors = [
            "[data-testid='UserDescription']",
            "div[data-testid='UserDescription']",
        ]

        # プロフィールヘッダー内でのみ検索するためのコンテナセレクタ
        profile_header_selectors = [
            "[data-testid='UserProfileHeader_Items']",
            "[data-testid='primaryColumn'] div:has([data-testid='UserName'])",
            "[data-testid='primaryColumn']",
        ]

        if not self.driver:
            return ""

        # まず、プロフィールヘッダー内でbio要素を探す
        for header_selector in profile_header_selectors:
            try:
                header_elements = self.driver.find_elements(By.CSS_SELECTOR, header_selector)
                if not header_elements:
                    continue

                for header_elem in header_elements:
                    # bio要素が存在するかチェック
                    for bio_selector in bio_container_selectors:
                        try:
                            bio_elements = header_elem.find_elements(By.CSS_SELECTOR, bio_selector)
                            if bio_elements:
                                # bio要素が見つかった場合、そのテキストを抽出
                                bio_text_selectors = ["span", "div span", "div"]
                                bio_text = extract_text_by_selectors(bio_elements[0], bio_text_selectors)
                                if bio_text:
                                    logger.debug(f"Found bio with selector: {header_selector} -> {bio_selector}")
                                    return bio_text
                        except Exception as e:
                            logger.debug(f"Error checking bio selector '{bio_selector}': {e}")
                            continue
            except Exception as e:
                logger.debug(f"Error with header selector '{header_selector}': {e}")
                continue

        # bio要素が見つからない場合は空文字列を返す(bioが設定されていない)
        logger.debug("No bio element found - user likely has no bio set")
        return ""

    def _extract_profile_location(self) -> str:
        """Extract profile location."""
        selectors = [
            "[data-testid='UserLocation'] span",
            "[data-testid='UserLocation']",
            "[data-testid='UserProfileHeader_Items'] span[data-testid='UserLocation']",
        ]

        return extract_text_from_driver_by_selectors(self.driver, selectors)

    def _extract_profile_website(self) -> str:
        """Extract profile website URL."""
        selectors = [
            "[data-testid='UserUrl'] a",
            "a[href*='http'][target='_blank']",
            "[data-testid='UserProfileHeader_Items'] a[href*='http']",
        ]

        return extract_attribute_from_driver_by_selectors(self.driver, selectors, "href")

    def _extract_profile_stats(self, profile: UserProfile) -> None:
        """Extract follower/following counts using modern X.com selectors."""
        if not self.driver:
            logger.warning("Driver not initialized, cannot extract profile stats")
            profile.following_count = 0
            profile.followers_count = 0
            return

        try:
            # Modern approach: Look for links ending with /following and /followers
            following_count = None
            followers_count = None

            # Try to find following count
            following_selectors = [
                "a[href$='/following'] span span",
                "a[href*='/following'] span",
                "[data-testid='UserFollowing-'] span",
            ]

            for selector in following_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and any(char.isdigit() for char in text):
                            following_count = self._parse_count(text)
                            if following_count is not None:
                                logger.debug(f"Found following count: {text} -> {following_count}")
                                break
                    if following_count is not None:
                        break
                except NoSuchElementException:
                    continue

            # Try to find followers count
            followers_selectors = [
                "a[href$='/followers'] span span",
                "a[href$='/verified_followers'] span span",
                "a[href*='/followers'] span",
                "[data-testid='UserFollowers-'] span",
            ]

            for selector in followers_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and any(char.isdigit() for char in text):
                            followers_count = self._parse_count(text)
                            if followers_count is not None:
                                logger.debug(f"Found followers count: {text} -> {followers_count}")
                                break
                    if followers_count is not None:
                        break
                except NoSuchElementException:
                    continue

            # Fallback: Try to extract from link text directly (like TypeScript implementation)
            if following_count is None or followers_count is None:
                try:
                    # Look for following link
                    if following_count is None:
                        following_link = self.driver.find_element(By.CSS_SELECTOR, "a[href$='/following']")
                        following_text = following_link.text
                        import re

                        numbers = re.findall(r"[\d,]+", following_text)
                        if numbers:
                            following_count = self._parse_count(numbers[0])
                            logger.debug(f"Found following from link text: {following_text} -> {following_count}")
                except NoSuchElementException:
                    pass

                try:
                    # Look for followers link
                    if followers_count is None:
                        followers_link = self.driver.find_element(
                            By.CSS_SELECTOR, "a[href$='/followers'], a[href$='/verified_followers']"
                        )
                        followers_text = followers_link.text
                        import re

                        numbers = re.findall(r"[\d,]+", followers_text)
                        if numbers:
                            followers_count = self._parse_count(numbers[0])
                            logger.debug(f"Found followers from link text: {followers_text} -> {followers_count}")
                except NoSuchElementException:
                    pass

            profile.following_count = following_count or 0
            profile.followers_count = followers_count or 0

            logger.info(
                f"Profile stats extracted - Following: {profile.following_count}, Followers: {profile.followers_count}"
            )

        except Exception as e:
            logger.warning(f"Error extracting profile stats: {e}")
            profile.following_count = 0
            profile.followers_count = 0

    def _parse_count(self, count_str: str | None) -> int:
        """
        Parse count string (e.g., "1.2K", "10M") to integer.

        Args:
            count_str: Count string to parse (can be None)

        Returns:
            Parsed count as integer, 0 if parsing fails
        """
        if not count_str:
            return 0

        # Clean and normalize the string
        count_str = count_str.strip().replace(",", "")
        if not count_str:
            return 0

        try:
            # Convert to uppercase for case-insensitive matching
            upper_str = count_str.upper()

            # Extract numeric part
            num_str = ""
            for char in upper_str:
                if char.isdigit() or char == ".":
                    num_str += char
                elif char in ["K", "M", "B"]:
                    break

            if not num_str:
                return 0

            num = float(num_str)

            # Apply multipliers based on suffix
            if "K" in upper_str:
                return int(num * 1000)
            elif "M" in upper_str:
                return int(num * 1000000)
            elif "B" in upper_str:
                return int(num * 1000000000)
            else:
                return int(num)

        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse count '{count_str}': {e}")
            return 0

    def _debug_page_state(self, context: str) -> None:
        """
        Debug helper function to capture detailed page state on errors.

        Args:
            context: Description of when this debug was called
        """
        if not self.driver:
            logger.error("Cannot debug page state - driver not initialized")
            return

        try:
            # Basic page info
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.debug(f"=== DEBUG PAGE STATE: {context} ===")
            logger.debug(f"Current URL: {current_url}")
            logger.debug(f"Page title: {page_title}")

            # Check if we're on X.com
            if "x.com" not in current_url.lower():
                logger.warning(f"Not on X.com! Current URL: {current_url}")

            # Get all elements with data-testid attributes
            logger.debug("Checking elements with data-testid attributes:")
            try:
                testid_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid]")
                testid_values = []
                for elem in testid_elements[:20]:  # Limit to first 20
                    testid = elem.get_attribute("data-testid")
                    if testid:
                        testid_values.append(testid)

                if testid_values:
                    logger.debug(f"Found data-testid elements: {', '.join(set(testid_values))}")
                else:
                    logger.warning("No data-testid elements found!")
            except Exception as e:
                logger.debug(f"Error getting data-testid elements: {e}")

            # Get main structural elements
            logger.debug("Checking main structural elements:")
            structural_selectors = [
                "main",
                "div[role='main']",
                "section",
                "article",
                "nav",
                "header",
                "div[id]",
                "div[class]",
            ]

            for selector in structural_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.debug(f"  ✓ {selector}: {len(elements)} elements")
                        # Show first few elements with their attributes
                        for i, elem in enumerate(elements[:3]):
                            try:
                                tag = elem.tag_name
                                elem_id = elem.get_attribute("id") or "no-id"
                                elem_class = elem.get_attribute("class") or "no-class"
                                elem_role = elem.get_attribute("role") or "no-role"
                                logger.debug(
                                    f"    [{i}] {tag}: id='{elem_id}', class='{elem_class[:50]}...', role='{elem_role}'"
                                )
                            except Exception as e:
                                logger.debug(f"    [{i}] Error getting element info: {e}")
                    else:
                        logger.debug(f"  ✗ {selector}: Not found")
                except Exception as e:
                    logger.debug(f"  ✗ {selector}: Error - {e}")

            # Check for common error patterns
            try:
                body_element = self.driver.find_element(By.TAG_NAME, "body")
                body_text = body_element.text[:1000] if body_element.text else "No text content"
                logger.debug(f"Page content sample (first 1000 chars): {body_text}")

                # Check for error messages
                error_patterns = [
                    "rate limit",
                    "error",
                    "blocked",
                    "suspended",
                    "not found",
                    "try again",
                    "temporarily unavailable",
                    "something went wrong",
                    "this content is not available",
                    "please try again",
                ]
                page_text_lower = body_text.lower()
                found_errors = [pattern for pattern in error_patterns if pattern in page_text_lower]
                if found_errors:
                    logger.warning(f"Potential issues detected: {', '.join(found_errors)}")

            except Exception as e:
                logger.debug(f"Could not extract page content: {e}")

            # Check for modern X.com structure
            logger.debug("Checking for modern X.com structure:")
            modern_selectors = [
                "div[data-testid]",
                "section[role='region']",
                "main[role='main']",
                "div[dir='ltr']",
                "div[dir='auto']",
                "div[lang]",
                "nav[role='navigation']",
                "header[role='banner']",
            ]

            for selector in modern_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.debug(f"  ✓ {selector}: {len(elements)} elements")
                except Exception:
                    pass

            # Take screenshot for debugging
            self._save_debug_screenshot(context)

            logger.debug("=== END DEBUG PAGE STATE ===")

        except Exception as e:
            logger.error(f"Error during page state debugging: {e}")

    def _save_debug_screenshot(self, context: str) -> None:
        """
        Save a screenshot for debugging purposes.

        Args:
            context: Context description for filename
        """
        if not self.driver:
            return

        try:
            # Create debug directory if it doesn't exist
            debug_dir = Path("logs/debug_screenshots")
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_context = "".join(c for c in context if c.isalnum() or c in (" ", "-", "_")).rstrip()
            safe_context = safe_context.replace(" ", "_")[:50]  # Limit length

            filename = f"{timestamp}_{safe_context}.png"
            filepath = debug_dir / filename

            # Take screenshot
            self.driver.save_screenshot(str(filepath))
            logger.debug(f"Debug screenshot saved: {filepath}")

        except Exception as e:
            logger.debug(f"Could not save debug screenshot: {e}")

    def _check_element_exists(self, selector: str, timeout: int = 5) -> bool:
        """
        Check if an element exists with detailed logging.

        Args:
            selector: CSS selector to check
            timeout: Timeout in seconds

        Returns:
            True if element exists, False otherwise
        """
        if not self.driver:
            return False

        try:
            WebDriverWait(self.driver, timeout).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
            logger.debug(f"Element found: {selector}")
            return True
        except Exception as e:
            logger.debug(f"Element not found: {selector} - {e}")
            return False

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
