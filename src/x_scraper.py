#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser with tbselenium - X scraping specific functionality
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver

from src.constants import (
    LOGIN_PAGE_LOAD_TIMEOUT,
    SCRAPING_RESULTS_DIR,
    TWITTER_LOGIN_URL,
    WAIT_MEDIUM,
    WAIT_SHORT,
)
from src.models import Tweet, UserProfile
from src.utils import CookieManager, create_tor_browser_driver, take_screenshot, verify_tor_connection
from src.utils.data_storage import save_profiles, save_tweets


class XScraper:
    """X (Twitter) scraper using Tor Browser - focused on scraping functionality"""

    def __init__(
        self,
        tbb_path: str,
        headless: bool = True,
        email: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Initialize scraper with minimal configuration

        Args:
            tbb_path: Path to Tor Browser directory
            headless: Run in headless mode
            email: Email for login (optional)
            username: Username for login (optional)
            password: Password for login (optional)
        """
        self.tbb_path = tbb_path
        self.headless = headless
        self.email = email
        self.username = username
        self.password = password
        self.driver: TorBrowserDriver | None = None

        # Create data directory for outputs using constants
        self.data_dir = SCRAPING_RESULTS_DIR
        self._ensure_directory_exists(self.data_dir)

        # Initialize cookie manager with user identifier
        user_identifier = self.email or self.username
        self.cookie_manager = CookieManager(user_identifier)

        logger.info(f"XScraper initialized with TBB path: {tbb_path}")
        if user_identifier:
            logger.info(f"Cookie management enabled for user: {user_identifier}")
        else:
            logger.info("Cookie management using default session")

    def _ensure_directory_exists(self, directory: Path) -> None:
        """
        Ensure directory exists, create if necessary

        Args:
            directory: Directory path to ensure exists
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory.resolve()}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

    def start(self) -> bool:
        """Start Tor Browser and verify Tor connection"""
        try:
            # Create Tor Browser driver using utils
            self.driver = create_tor_browser_driver(
                self.tbb_path,
                headless=self.headless,
            )

            # Verify Tor connection using utils
            if verify_tor_connection(self.driver):
                logger.success("✅ Tor Browser started successfully with verified Tor connection")
                return True
            else:
                logger.error("❌ Tor connection verification failed")
                return False

        except Exception as e:
            logger.error(f"Failed to start Tor Browser: {e}")
            return False

    def login(self) -> bool:
        """
        Login to X (Twitter) with cookie-based session persistence

        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        # Try to login with saved cookies first
        if self._try_cookie_login():
            logger.success("✅ Logged in using saved cookies")
            return True

        # Fall back to manual login
        return self._perform_manual_login()

    def _try_cookie_login(self) -> bool:
        """
        Try to login using saved cookies

        Returns:
            bool: True if cookie login successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        # Check if valid cookies exist
        if not self.cookie_manager.has_valid_cookies():
            logger.debug("No valid saved cookies found")
            return False

        # Load cookies using cookie manager
        cookies = self.cookie_manager.load_cookies()
        if not cookies:
            logger.debug("Failed to load cookies")
            return False

        return self._apply_cookies_to_session(cookies)

    def _remove_expired_cookies(self) -> None:
        """Remove expired cookie file"""
        try:
            self.cookie_manager.clear_cookies()
        except Exception as e:
            logger.warning(f"Failed to remove expired cookie file: {e}")

    def _apply_cookies_to_session(self, cookies: list[dict[str, Any]]) -> bool:
        """
        Apply cookies to current browser session

        Args:
            cookies: List of cookie dictionaries to apply

        Returns:
            bool: True if cookies applied successfully
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            # Navigate to X homepage first
            self.driver.get("https://twitter.com")
            time.sleep(WAIT_SHORT)

            # Add each cookie to the browser
            for cookie in cookies:
                try:
                    # Clean cookie data for Selenium
                    clean_cookie = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie.get("domain", ".twitter.com"),
                        "path": cookie.get("path", "/"),
                    }

                    # Add secure and httpOnly if present
                    if "secure" in cookie:
                        clean_cookie["secure"] = cookie["secure"]
                    if "httpOnly" in cookie:
                        clean_cookie["httpOnly"] = cookie["httpOnly"]

                    self.driver.add_cookie(clean_cookie)
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue

            # Refresh the page to apply cookies
            self.driver.refresh()
            time.sleep(WAIT_MEDIUM)

            # Check if login was successful
            if self._verify_login():
                logger.info("✅ Successfully logged in using saved cookies")
                return True
            else:
                logger.debug("Cookie login verification failed")
                return False

        except Exception as e:
            logger.error(f"Failed to apply cookies: {e}")
            return False

    def _perform_manual_login(self) -> bool:
        """
        Perform manual login flow

        Returns:
            bool: True if manual login successful
        """
        # Validate credentials
        if not self._validate_credentials():
            return False

        logger.info("Logging in to X (Twitter) with credentials...")

        try:
            # Navigate to login page
            if not self._navigate_to_login_page():
                return False

            # Execute login steps
            return self._execute_login_steps()

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _validate_credentials(self) -> bool:
        """
        Validate that required credentials are provided

        Returns:
            bool: True if credentials are valid
        """
        if not self.email and not self.username:
            logger.error("Email or username required for login")
            return False

        if not self.password:
            logger.error("Password required for login")
            return False

        return True

    def _navigate_to_login_page(self) -> bool:
        """
        Navigate to X login page

        Returns:
            bool: True if navigation successful
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            logger.info(f"Navigating to login page: {TWITTER_LOGIN_URL}")
            self.driver.get(TWITTER_LOGIN_URL)
            time.sleep(LOGIN_PAGE_LOAD_TIMEOUT)

            # Log page state after navigation
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"After navigation - URL: {current_url}, Title: {page_title}")

            # Take debug screenshot
            self.take_debug_snapshot("initial_login_page")
            self._log_page_elements_for_debugging("initial_login_page")

            return True

        except Exception as e:
            logger.error(f"Failed to navigate to login page: {e}")
            return False

    def _execute_login_steps(self) -> bool:
        """
        Execute the multi-step login process

        Returns:
            bool: True if all login steps completed successfully
        """
        # Step 1: Input username/email
        if not self._input_username():
            return False

        # Step 2: Handle unusual activity verification (if appears)
        self._input_unusual_activity()

        # Step 3: Input password
        if not self._input_password():
            return False

        # Step 4: Handle 2FA if present
        if not self._handle_2fa():
            return False

        # Verify login success
        if self._verify_login():
            logger.success("✅ Login successful")
            # Save cookies after successful login
            self._save_session_cookies()
            return True
        else:
            logger.error("❌ Login verification failed")
            return False

    def _save_session_cookies(self) -> None:
        """Save current session cookies to file"""
        if not self.driver:
            logger.error("Driver not initialized")
            return

        try:
            # Get all cookies from current session
            cookies = self.driver.get_cookies()

            if cookies:
                # Use cookie manager to save cookies (it handles filtering automatically)
                success = self.cookie_manager.save_cookies(cookies)
                if success:
                    logger.info("Session cookies saved successfully")
                else:
                    logger.warning("Failed to save session cookies")
            else:
                logger.warning("No cookies found in current session")

        except Exception as e:
            logger.error(f"Failed to save session cookies: {e}")

    def _input_username(self) -> bool:
        """Input username or email"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        input_attempt = 0
        login_identifier = self.email or self.username

        if not login_identifier:
            logger.error("No email or username provided")
            return False

        while input_attempt < 3:
            input_attempt += 1

            # Log current page state for debugging
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"Username attempt {input_attempt}/3: Current URL: {current_url}")
            logger.info(f"Username attempt {input_attempt}/3: Page title: {page_title}")

            try:
                username_field = self.driver.find_element(By.XPATH, "//input[@autocomplete='username']")

                username_field.clear()
                username_field.send_keys(login_identifier)
                username_field.send_keys(Keys.RETURN)
                time.sleep(4)  # Increased wait time for page transition

                logger.info("Username/email entered successfully")
                return True

            except NoSuchElementException:
                logger.warning(f"Attempt {input_attempt}/3: Username field not found, retrying...")
                self.take_debug_snapshot(f"username_field_not_found_attempt_{input_attempt}")
                if input_attempt < 3:
                    time.sleep(2)

        logger.error("Failed to input username after 3 attempts")
        self.take_debug_snapshot("username_input_final_failure")
        return False

    def _input_unusual_activity(self) -> None:
        """Handle unusual activity verification (optional step)"""
        if not self.driver:
            logger.error("Driver not initialized")
            return

        try:
            # First, look for unusual activity field
            unusual_activity_field = None
            try:
                unusual_activity_field = self.driver.find_element(
                    By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"
                )
                logger.info("Found unusual activity verification field")

                # Use username for unusual activity verification
                verification_text = self.username or self.email or ""
                unusual_activity_field.clear()
                unusual_activity_field.send_keys(verification_text)
                logger.info("Entered verification text for unusual activity")

            except NoSuchElementException:
                logger.info("No unusual activity verification field found")

            # Always try to click the "Next" button to proceed
            time.sleep(2)  # Wait for any dynamic loading

            next_button_selectors = [
                "//button[contains(text(), 'Next')]",
                "//div[@role='button'][contains(text(), 'Next')]",
                "//span[contains(text(), 'Next')]/ancestor::button",
                "//button[@data-testid='LoginForm_Login_Button']",
            ]

            next_button_clicked = False
            for selector in next_button_selectors:
                try:
                    next_button = self.driver.find_element(By.XPATH, selector)
                    next_button.click()
                    logger.info(f"Successfully clicked Next button using selector: {selector}")
                    next_button_clicked = True
                    break
                except NoSuchElementException:
                    continue

            if not next_button_clicked:
                logger.warning("Could not find Next button to proceed")
                # Fallback: try pressing Enter on the unusual activity field if it exists
                if unusual_activity_field:
                    unusual_activity_field.send_keys(Keys.RETURN)
                    logger.info("Used Enter key as fallback")

            time.sleep(4)  # Wait for page transition

        except Exception as e:
            logger.warning(f"Error in unusual activity verification: {e}")

        logger.info("Unusual activity verification step completed")

    def _input_password(self) -> bool:
        """Input password"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        if not self.password:
            logger.error("Password not provided")
            return False

        # Multiple password field selectors to try
        password_selectors = [
            "//input[@autocomplete='current-password']",
            "//input[@name='password']",
            "//input[@type='password']",
            "//input[@data-testid='ocfPasswordTextInput']",
            "//input[contains(@placeholder, 'Password')]",
            "//input[contains(@placeholder, 'password')]",
            "//input[contains(@placeholder, 'パスワード')]",
        ]

        input_attempt = 0

        while input_attempt < 3:
            input_attempt += 1

            # Log current page state for debugging
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"Attempt {input_attempt}/3: Current URL: {current_url}")
            logger.info(f"Attempt {input_attempt}/3: Page title: {page_title}")

            password_field = None
            used_selector = None

            # Try each password selector
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.XPATH, selector)
                    used_selector = selector
                    logger.debug(f"Found password field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if password_field:
                try:
                    # Clear and input password
                    password_field.clear()
                    time.sleep(0.5)

                    # Human-like typing
                    for char in self.password:
                        password_field.send_keys(char)
                        time.sleep(0.1)

                    # Try to click the Login button instead of pressing Enter
                    login_button_selectors = [
                        "//button[contains(text(), 'Log in')]",
                        "//button[@data-testid='LoginForm_Login_Button']",
                        "//div[@role='button'][contains(text(), 'Log in')]",
                        "//span[contains(text(), 'Log in')]/ancestor::button",
                    ]

                    login_button_clicked = False
                    for selector in login_button_selectors:
                        try:
                            login_button = self.driver.find_element(By.XPATH, selector)
                            login_button.click()
                            logger.info(f"Successfully clicked Login button using selector: {selector}")
                            login_button_clicked = True
                            break
                        except NoSuchElementException:
                            continue

                    if not login_button_clicked:
                        # Fallback to pressing Enter
                        password_field.send_keys(Keys.RETURN)
                        logger.info("Used Enter key as fallback for login")

                    time.sleep(5)  # Increased wait time for login processing

                    logger.info(f"Password entered successfully using selector: {used_selector}")

                    # Add debug information after password input
                    current_url_after_password = self.driver.current_url
                    page_title_after_password = self.driver.title
                    logger.info(f"After password input - URL: {current_url_after_password}")
                    logger.info(f"After password input - Title: {page_title_after_password}")

                    # Take debug screenshot after password input
                    self.take_debug_snapshot("after_password_input")

                    # Log page elements to see what's available
                    self._log_page_elements_for_debugging("after_password_input")

                    return True

                except Exception as e:
                    logger.warning(f"Error entering password: {e}")
                    # Take screenshot on error
                    self.take_debug_snapshot(f"password_input_error_attempt_{input_attempt}")
            else:
                logger.warning(f"Attempt {input_attempt}/3: No password field found with any selector")

                # Log page content for debugging
                self._log_page_elements_for_debugging(f"password_field_not_found_attempt_{input_attempt}")

                # Take screenshot for debugging
                self.take_debug_snapshot(f"password_field_not_found_attempt_{input_attempt}")

                # Wait before retrying
                if input_attempt < 3:
                    time.sleep(2)

        logger.error("Failed to input password after 3 attempts")
        self._log_page_elements_for_debugging("password_input_final_failure")
        self.take_debug_snapshot("password_input_final_failure")
        return False

    def _handle_2fa(self) -> bool:
        """Handle two-factor authentication if present"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            # Check for 2FA input field
            time.sleep(2)

            # Common 2FA selectors
            tfa_selectors = [
                "//input[@data-testid='ocfEnterTextTextInput']",
                "//input[@autocomplete='one-time-code']",
                "//input[@name='text']",
                "//input[contains(@placeholder, 'code')]",
                "//input[contains(@placeholder, 'Code')]",
            ]

            tfa_field = None
            for selector in tfa_selectors:
                try:
                    tfa_field = self.driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue

            if tfa_field:
                # Determine 2FA type by checking page content
                page_source = self.driver.page_source.lower()
                is_email_verification = any(
                    keyword in page_source
                    for keyword in [
                        "メール",
                        "email",
                        "確認コード",
                        "confirmation code",
                        "@",
                        "送信",
                        "sent",
                        "inbox",
                        "受信",
                    ]
                )

                logger.info("🔐 Two-factor authentication required")
                print("\n" + "=" * 60)
                print("🔐 TWO-FACTOR AUTHENTICATION REQUIRED")
                print("=" * 60)

                if is_email_verification:
                    print("📧 メールでの確認コードが必要です")
                    print("📧 Email verification code required")
                    print("-" * 60)
                    print("メールボックスを確認して、確認コードを入力してください。")
                    print("Please check your email inbox for the confirmation code.")
                    print("(通常、数分以内にメールが届きます / Usually arrives within a few minutes)")
                else:
                    print("📱 認証アプリまたはSMSでの確認コードが必要です")
                    print("📱 Authenticator app or SMS verification code required")
                    print("-" * 60)
                    print("認証アプリまたはSMSを確認して、確認コードを入力してください。")
                    print("Please check your authenticator app or SMS for the verification code.")

                print("-" * 60)

                # Get 2FA code from user input
                tfa_code = input("確認コード / Verification code: ").strip()

                if not tfa_code:
                    logger.error("No 2FA code provided")
                    return False

                if not tfa_code.isdigit():
                    logger.warning("Warning: Code should typically be numeric")

                # Input 2FA code
                tfa_field.clear()

                # Add human-like typing delay for anti-detection
                for char in tfa_code:
                    tfa_field.send_keys(char)
                    time.sleep(0.1)  # Small delay between keystrokes

                tfa_field.send_keys(Keys.RETURN)
                time.sleep(5)

                logger.info("2FA code submitted")

                # Verify if code was accepted
                time.sleep(2)
                if "login" not in self.driver.current_url.lower() and "flow" not in self.driver.current_url.lower():
                    logger.success("✅ 2FA verification successful")
                else:
                    logger.warning("⚠️  2FA verification may have failed - please check")

            else:
                logger.info("No 2FA required")

            return True

        except Exception as e:
            logger.error(f"Error handling 2FA: {e}")
            return False

    def _verify_login(self) -> bool:
        """Verify login success by checking auth_token cookie"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            time.sleep(3)
            cookies = self.driver.get_cookies()

            auth_token = None
            for cookie in cookies:
                if cookie["name"] == "auth_token":
                    auth_token = cookie["value"]
                    break

            if auth_token:
                logger.info("Auth token found - login verified")
                return True
            else:
                logger.warning("Auth token not found - login may have failed")

                # Additional check: look for home page elements
                try:
                    self.driver.get("https://twitter.com/home")
                    time.sleep(3)

                    # Check if we're redirected to login page
                    if "login" in self.driver.current_url.lower():
                        return False

                    # Check for home page indicators
                    home_indicators = [
                        "//div[@data-testid='primaryColumn']",
                        "//h1[contains(text(), 'Home')]",
                        "//nav[@role='navigation']",
                    ]

                    for indicator in home_indicators:
                        try:
                            self.driver.find_element(By.XPATH, indicator)
                            logger.info("Home page detected - login verified")
                            return True
                        except NoSuchElementException:
                            continue

                except Exception:
                    pass

                return False

        except Exception as e:
            logger.error(f"Error verifying login: {e}")
            return False

    def navigate_to_x(self) -> bool:
        """Navigate to X.com"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            self.driver.get("https://x.com")
            time.sleep(5)
            logger.info("Navigated to X.com")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to X.com: {e}")
            return False

    def search_tweets(self, query: str, max_tweets: int = 10) -> list[Tweet]:
        """
        Search for tweets based on a query

        Args:
            query: Search query
            max_tweets: Maximum number of tweets to collect

        Returns:
            list[Tweet]: List of collected tweets
        """
        tweets: list[Tweet] = []

        if not self.driver:
            logger.error("Driver not initialized")
            return tweets

        try:
            # Navigate to search URL
            search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
            self.driver.get(search_url)
            time.sleep(WAIT_MEDIUM)

            # Basic implementation - would need more sophisticated extraction
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')[:max_tweets]

            for element in tweet_elements:
                tweet = self._extract_tweet_data(element)
                if tweet:
                    tweets.append(tweet)

            logger.info(f"✅ Collected {len(tweets)} tweets for query: {query}")

            # Auto-save using new storage system
            if tweets:
                save_tweets(tweets, target_user=None, query=query)

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")

        return tweets

    def get_user_profile(self, username: str) -> UserProfile | None:
        """
        Get user profile information

        Args:
            username: Username to get profile for

        Returns:
            UserProfile | None: Profile data if successful, None otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return None

        try:
            # Navigate to user profile
            profile_url = f"https://x.com/{username}"
            self.driver.get(profile_url)
            time.sleep(WAIT_MEDIUM)

            profile = self._extract_profile_data(username)

            if profile:
                logger.info(f"✅ Retrieved profile for: @{username}")
                # Auto-save using new storage system
                save_profiles([profile], target_user=username)

            return profile

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    def _extract_tweet_data(self, element: WebElement) -> Tweet | None:
        """Extract tweet data from element"""
        if not element:
            return None

        try:
            # Extract basic tweet information
            text_element = element.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']")
            text = text_element.text if text_element else ""

            # Extract author
            author_element = element.find_element(By.CSS_SELECTOR, "[data-testid='User-Name'] a")
            href = author_element.get_attribute("href") if author_element else None
            author = href.split("/")[-1] if href else "unknown"

            # Extract tweet ID and URL from timestamp link
            tweet_id = None
            tweet_url = None
            timestamp = datetime.now().isoformat()  # Default fallback

            try:
                # 日付部分のaタグを探す (time要素を含むリンク)
                timestamp_link = element.find_element(By.CSS_SELECTOR, "a[href*='/status/'] time")
                if timestamp_link:
                    # 親のaタグからhref属性を取得
                    link_element = timestamp_link.find_element(By.XPATH, "./..")
                    href_attr = link_element.get_attribute("href")

                    if href_attr and "/status/" in href_attr:
                        # URLからツイートIDを抽出
                        # href="/username/status/1234567890" -> ID: 1234567890
                        tweet_id = href_attr.split("/status/")[-1]
                        # 完全なURLを構築
                        tweet_url = f"https://twitter.com{href_attr}" if href_attr.startswith("/") else href_attr
                        logger.debug(f"Extracted tweet ID: {tweet_id}, URL: {tweet_url}")

                    # time要素のdatetime属性から正確な投稿時刻を取得
                    datetime_attr = timestamp_link.get_attribute("datetime")
                    if datetime_attr:
                        timestamp = datetime_attr
                        logger.debug(f"Extracted timestamp: {timestamp}")

            except NoSuchElementException:
                logger.debug("Timestamp link not found, using fallback values")
            except Exception as e:
                logger.debug(f"Error extracting timestamp data: {e}")

            # Extract metrics (simplified)
            likes = self._extract_metric(element, "like")
            retweets = self._extract_metric(element, "retweet")
            replies = self._extract_metric(element, "reply")

            return Tweet(
                id=tweet_id,
                text=text,
                author=author,
                url=tweet_url,
                likes=likes,
                retweets=retweets,
                replies=replies,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.debug(f"Failed to extract tweet data: {e}")
            return None

    def _extract_profile_data(self, username: str) -> UserProfile | None:
        """Extract user profile data"""
        if not self.driver:
            return None

        try:
            # Extract display name
            display_name_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserName'] span")
            display_name = display_name_element.text if display_name_element else username

            # Extract bio
            bio_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserDescription'] span")
            bio = bio_element.text if bio_element else ""

            # Extract follower count (simplified)
            followers_count = self._extract_count_from_profile("followers")
            following_count = self._extract_count_from_profile("following")

            return UserProfile(
                username=username,
                display_name=display_name,
                bio=bio,
                followers_count=followers_count,
                following_count=following_count,
            )

        except Exception as e:
            logger.debug(f"Failed to extract profile data: {e}")
            return None

    def _extract_metric(self, element: WebElement, metric_type: str) -> int:
        """Extract metric from tweet element"""
        if not element:
            return 0

        try:
            metric_element = element.find_element(By.CSS_SELECTOR, f"[data-testid='{metric_type}']")
            metric_text = metric_element.get_attribute("aria-label") or "0"
            # Simple number extraction
            numbers = "".join(filter(str.isdigit, metric_text))
            return int(numbers) if numbers else 0
        except Exception:
            return 0

    def _extract_count_from_profile(self, count_type: str) -> int:
        """Extract follower/following count from profile"""
        if not self.driver:
            return 0

        try:
            count_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/followers'], a[href*='/following']")
            for element in count_elements:
                href = element.get_attribute("href")
                if href and count_type in href:
                    count_text = element.text
                    numbers = "".join(filter(str.isdigit, count_text.replace(",", "")))
                    return int(numbers) if numbers else 0
            return 0
        except Exception:
            return 0

    def save_tweets_to_json(self, tweets: list[Tweet], filename: str) -> bool:
        """
        Save tweets to JSON file (legacy method - use save_tweets from utils instead)

        Args:
            tweets: List of tweets to save
            filename: Filename to save to

        Returns:
            bool: True if successful, False otherwise
        """
        # Use new storage system with custom filename
        return save_tweets(tweets, filename=filename)

    def save_profile_to_json(self, profile: UserProfile, filename: str) -> bool:
        """
        Save profile to JSON file (legacy method - use save_profiles from utils instead)

        Args:
            profile: Profile to save
            filename: Filename to save to

        Returns:
            bool: True if successful, False otherwise
        """
        # Use new storage system with custom filename
        return save_profiles([profile], filename=filename)

    def take_screenshot(self, filename: str | None = None) -> str | None:
        """
        Take a single screenshot of the current page

        Creates a single PNG file in the screenshots directory.

        Args:
            filename: Filename to save (without extension). If None, uses timestamp

        Returns:
            str | None: Path to saved screenshot file, None if failed
        """
        if not self.driver:
            logger.error("Driver not initialized - cannot take screenshot")
            return None

        try:
            # Use constants for screenshot directory with environment detection
            import os

            from src.constants import SCREENSHOTS_DIR, is_docker_environment

            is_docker = is_docker_environment()
            logger.info(f"🐳 Docker env: {is_docker}")
            logger.info(f"📁 Screenshot dir: {SCREENSHOTS_DIR.absolute()}")
            logger.info(f"📺 DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")

            # Ensure screenshots directory exists
            try:
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                logger.debug(f"✅ Screenshots directory ensured: {SCREENSHOTS_DIR}")
            except Exception as e:
                logger.error(f"❌ Failed to create screenshots directory: {e}")
                return None

            # Test directory write permissions
            test_file = SCREENSHOTS_DIR / "test_write_permission.tmp"
            try:
                test_file.write_text("screenshot_test", encoding="utf-8")
                content = test_file.read_text(encoding="utf-8")
                test_file.unlink()

                if content == "screenshot_test":
                    logger.debug("✅ Screenshots directory write permission verified")
                else:
                    logger.error("❌ Screenshots directory write test: content mismatch")
                    return None
            except Exception as e:
                logger.error(f"❌ Screenshots directory write permission failed: {e}")
                return None

            result = take_screenshot(self.driver, filename, str(SCREENSHOTS_DIR))

            if result:
                # Verify the file actually exists and has content
                screenshot_file = Path(result)
                if screenshot_file.exists():
                    file_size = screenshot_file.stat().st_size
                    logger.info(f"✅ Single screenshot saved: {result} ({file_size} bytes)")

                    # Additional verification - check PNG header
                    try:
                        with open(screenshot_file, "rb") as f:
                            header = f.read(8)
                        if header.startswith(b"\x89PNG\r\n\x1a\n"):
                            logger.debug("✅ PNG format verified")
                        else:
                            logger.warning("⚠️ Screenshot file may not be valid PNG format")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not verify PNG format: {e}")
                else:
                    logger.error(f"❌ Screenshot file not found: {result}")
                    return None
            else:
                logger.error("❌ Screenshot failed - no path returned")

            return result

        except Exception as e:
            logger.error(f"❌ Unexpected error in take_screenshot: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def take_debug_snapshot(self, description: str) -> str | None:
        """
        Take comprehensive debug snapshot for troubleshooting

        Creates a folder containing:
        - screenshot.png: Page screenshot
        - page_source.html: HTML source code
        - metadata.txt: Debug information

        Args:
            description: Description of the error or state

        Returns:
            str | None: Path to debug folder, None if failed
        """
        if not self.driver:
            logger.warning("Driver not initialized - cannot take debug snapshot")
            return None

        try:
            import time

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            folder_name = f"{timestamp}_{description}"

            # Create debug snapshots directory using unified constants
            from src.constants import SCREENSHOTS_DIR, is_docker_environment

            debug_dir = SCREENSHOTS_DIR / "debug" / folder_name
            logger.info(f"📁 Creating debug snapshot folder: {debug_dir.absolute()}")

            try:
                debug_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Debug folder created: {debug_dir}")
            except Exception as e:
                logger.error(f"❌ Failed to create debug folder: {e}")
                return None

            # Docker environment debugging with unified detection
            import os

            is_docker = is_docker_environment()
            logger.info(f"🐳 Docker environment: {is_docker}")
            logger.info(f"📁 Debug folder: {debug_dir.absolute()}")
            logger.info(f"📊 Folder exists: {debug_dir.exists()}")
            logger.info(f"👤 Current user: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
            logger.info(f"📺 DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")

            # Enhanced directory permission verification
            try:
                test_file = debug_dir / "test_write.tmp"
                test_data = f"permission_test_{timestamp}"
                test_file.write_text(test_data, encoding="utf-8")
                test_content = test_file.read_text(encoding="utf-8")
                test_file.unlink()

                if test_content == test_data:
                    logger.info("✅ Debug folder write permission: OK")
                else:
                    logger.error("❌ Debug folder write permission: Content mismatch")
                    return None
            except Exception as e:
                logger.error(f"❌ Debug folder write permission failed: {e}")
                return None

            # Track successfully created files
            created_files = []

            # 1. Take screenshot
            screenshot_path = debug_dir / "screenshot.png"
            logger.info(f"📸 Taking debug screenshot: {screenshot_path.absolute()}")

            # Check driver state before screenshot
            try:
                driver_info = {
                    "current_url": self.driver.current_url,
                    "title": self.driver.title,
                    "window_size": self.driver.get_window_size(),
                }
                logger.info(f"🌐 Driver state: {driver_info}")
            except Exception as e:
                logger.warning(f"Failed to get driver state: {e}")
                driver_info = {"error": str(e)}

            # Take screenshot with retry mechanism
            screenshot_success = False
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    logger.info(f"📸 Screenshot attempt {attempt + 1}/{max_retries}")
                    screenshot_success = self.driver.save_screenshot(str(screenshot_path))

                    if screenshot_success and screenshot_path.exists():
                        file_size = screenshot_path.stat().st_size
                        if file_size > 0:
                            logger.info(f"✅ Screenshot saved: {file_size:,} bytes")

                            # Verify PNG format
                            try:
                                with open(screenshot_path, "rb") as f:
                                    header = f.read(8)
                                if header.startswith(b"\x89PNG\r\n\x1a\n"):
                                    logger.info("✅ PNG format verified")
                                    created_files.append("screenshot.png")
                                    break
                                else:
                                    logger.warning(f"⚠️ Attempt {attempt + 1}: Invalid PNG header")
                                    screenshot_success = False
                            except Exception as e:
                                logger.warning(f"⚠️ Attempt {attempt + 1}: PNG verification failed: {e}")
                                screenshot_success = False
                        else:
                            logger.warning(f"⚠️ Screenshot attempt {attempt + 1}: File empty")
                            screenshot_success = False
                    else:
                        logger.warning(f"⚠️ Screenshot attempt {attempt + 1}: Failed or file not found")

                except Exception as e:
                    logger.error(f"❌ Screenshot attempt {attempt + 1} failed: {e}")

                # Wait before retry
                if attempt < max_retries - 1 and not screenshot_success:
                    time.sleep(1)

            # 2. Save HTML source
            html_path = debug_dir / "page_source.html"
            logger.info(f"📄 Saving HTML source: {html_path.absolute()}")

            try:
                page_source = self.driver.page_source
                if page_source and len(page_source.strip()) > 0:
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(page_source)

                    # Verify HTML file
                    if html_path.exists():
                        html_size = html_path.stat().st_size
                        if html_size > 0:
                            logger.info(f"✅ HTML source saved: {html_size:,} bytes")

                            # Basic HTML validation
                            try:
                                with open(html_path, encoding="utf-8") as f:
                                    content = f.read(100)  # Read first 100 chars
                                if any(tag in content.lower() for tag in ["<html", "<head", "<body", "<!doctype"]):
                                    logger.info("✅ HTML content format verified")
                                    created_files.append("page_source.html")
                                else:
                                    logger.warning("⚠️ HTML file created but may not contain valid HTML")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not verify HTML content: {e}")
                        else:
                            logger.error(f"❌ HTML file created but empty: {html_path}")
                    else:
                        logger.error(f"❌ HTML file not found after save: {html_path}")
                else:
                    logger.warning("⚠️ Page source is empty or None")

            except Exception as e:
                logger.error(f"❌ Failed to save HTML source: {e}")

            # 3. Save metadata
            metadata_path = debug_dir / "metadata.txt"
            logger.info(f"📋 Saving metadata: {metadata_path.absolute()}")

            try:
                metadata_content = []
                metadata_content.append("Debug Snapshot Metadata")
                metadata_content.append("========================")
                metadata_content.append(f"Timestamp: {timestamp}")
                metadata_content.append(f"Description: {description}")
                metadata_content.append(f"Docker Environment: {is_docker}")
                metadata_content.append(f"Debug Folder: {debug_dir.absolute()}")

                # Safe driver info writing
                try:
                    metadata_content.append(f"Current URL: {self.driver.current_url}")
                    metadata_content.append(f"Page Title: {self.driver.title}")
                    metadata_content.append(f"Window Size: {self.driver.get_window_size()}")
                except Exception as e:
                    metadata_content.append(f"Driver Info Error: {e}")

                # System information
                import sys

                metadata_content.append(f"Python Version: {sys.version}")
                metadata_content.append(f"Working Directory: {os.getcwd()}")
                metadata_content.append("Environment Variables:")
                for key in ["DISPLAY", "TBB_PATH", "PYTHONPATH"]:
                    metadata_content.append(f"  {key}: {os.environ.get(key, 'Not set')}")

                # File information
                metadata_content.append("\nFiles Created:")
                for filename in created_files:
                    file_path = debug_dir / filename
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        metadata_content.append(f"  {filename}: {file_size:,} bytes")
                    else:
                        metadata_content.append(f"  {filename}: Not created")

                # Write metadata
                with open(metadata_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(metadata_content))

                # Verify metadata file
                if metadata_path.exists():
                    metadata_size = metadata_path.stat().st_size
                    if metadata_size > 0:
                        logger.info(f"✅ Metadata saved: {metadata_size:,} bytes")
                        created_files.append("metadata.txt")
                    else:
                        logger.error(f"❌ Metadata file created but empty: {metadata_path}")
                else:
                    logger.error(f"❌ Metadata file not found after save: {metadata_path}")

            except Exception as e:
                logger.error(f"❌ Failed to save metadata: {e}")

            # Final summary
            if created_files:
                logger.success(f"🎯 Debug snapshot completed: {debug_dir}")
                logger.info(f"📄 Files created: {', '.join(created_files)}")
                return str(debug_dir)
            else:
                logger.error(f"❌ Debug snapshot failed: No files created in {debug_dir}")
                return None

        except Exception as e:
            logger.error(f"❌ Unexpected error in take_debug_snapshot: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _log_page_elements_for_debugging(self, context: str) -> None:
        """
        Log current page elements for debugging purposes

        Args:
            context: Context description for the debug log
        """
        if not self.driver:
            logger.warning("Driver not initialized - cannot log page elements")
            return

        try:
            logger.info(f"=== PAGE ELEMENTS DEBUG ({context}) ===")

            # Log all input fields
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Found {len(input_fields)} input fields:")

            for i, field in enumerate(input_fields[:10]):  # Limit to first 10
                try:
                    field_type = field.get_attribute("type") or "text"
                    field_name = field.get_attribute("name") or "no-name"
                    field_id = field.get_attribute("id") or "no-id"
                    field_placeholder = field.get_attribute("placeholder") or "no-placeholder"
                    field_autocomplete = field.get_attribute("autocomplete") or "no-autocomplete"
                    field_data_testid = field.get_attribute("data-testid") or "no-testid"

                    logger.info(
                        f"  Input {i + 1}: type='{field_type}', name='{field_name}', "
                        f"id='{field_id}', placeholder='{field_placeholder}', "
                        f"autocomplete='{field_autocomplete}', data-testid='{field_data_testid}'"
                    )
                except Exception as e:
                    logger.warning(f"  Input {i + 1}: Error reading attributes - {e}")

            # Log specific password-related elements
            try:
                password_elements = self.driver.find_elements(By.XPATH, "//input[@type='password']")
                logger.info(f"Found {len(password_elements)} password type input fields")

                autocomplete_password = self.driver.find_elements(By.XPATH, "//input[@autocomplete='current-password']")
                logger.info(f"Found {len(autocomplete_password)} autocomplete='current-password' fields")

                testid_password = self.driver.find_elements(By.XPATH, "//input[@data-testid='ocfPasswordTextInput']")
                logger.info(f"Found {len(testid_password)} data-testid='ocfPasswordTextInput' fields")

            except Exception as e:
                logger.warning(f"Error searching for password elements: {e}")

            # Log current form elements
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                logger.info(f"Found {len(forms)} form elements")

                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"Found {len(buttons)} button elements")

                # Log button text for context
                for i, button in enumerate(buttons[:5]):  # First 5 buttons
                    try:
                        button_text = button.text or button.get_attribute("aria-label") or "no-text"
                        button_type = button.get_attribute("type") or "button"
                        logger.info(f"  Button {i + 1}: text='{button_text}', type='{button_type}'")
                    except Exception as e:
                        logger.warning(f"  Button {i + 1}: Error reading - {e}")

            except Exception as e:
                logger.warning(f"Error analyzing form elements: {e}")

            # Log page title and URL again for reference
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            logger.info("=== END PAGE ELEMENTS DEBUG ===")

        except Exception as e:
            logger.error(f"Failed to log page elements for debugging: {e}")

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

    def __enter__(self) -> "XScraper":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        self.close()

    def clear_saved_cookies(self) -> bool:
        """
        Clear saved cookies file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return self.cookie_manager.clear_cookies()
        except Exception as e:
            logger.error(f"Failed to clear saved cookies: {e}")
            return False

    def logout(self) -> bool:
        """
        Logout from X (Twitter) and clear saved cookies

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            # Try to navigate to logout URL
            self.driver.get("https://twitter.com/logout")
            time.sleep(2)

            # Look for logout confirmation button
            try:
                logout_button = self.driver.find_element(By.XPATH, "//div[@data-testid='confirmationSheetConfirm']")
                logout_button.click()
                time.sleep(3)
                logger.info("Logged out successfully")
            except NoSuchElementException:
                logger.info("Already logged out or logout button not found")

            # Clear cookies from browser session
            self.driver.delete_all_cookies()

            # Clear saved cookies file
            self.clear_saved_cookies()

            logger.success("✅ Logout completed and cookies cleared")
            return True

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    def is_logged_in(self) -> bool:
        """
        Check if currently logged in to X (Twitter)

        Returns:
            bool: True if logged in, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            # Navigate to home page
            self.driver.get("https://twitter.com/home")
            time.sleep(3)

            # Check for login indicators
            return self._verify_login()

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
