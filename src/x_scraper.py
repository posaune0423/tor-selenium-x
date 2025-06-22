#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser with tbselenium - Simplified version
"""

import json
import os
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

from src.models import Tweet, UserProfile

TWITTER_LOGIN_URL = "https://twitter.com/i/flow/login"


class XScraper:
    """Simplified X (Twitter) scraper using Tor Browser"""

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

        # Create data directory for outputs
        self.data_dir = Path("reports/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"XScraper initialized with TBB path: {tbb_path}")

    def start(self) -> bool:
        """Start Tor Browser"""
        try:
            # Check if we're running in Docker
            is_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_ENV", "false").lower() == "true"

            if is_docker:
                logger.info("🐳 Running in Docker environment - using external Tor service")

            # Simple tbselenium initialization - let it handle Tor connection
            self.driver = TorBrowserDriver(
                self.tbb_path,
                headless=self.headless,
                tbb_logfile_path="/dev/null",
            )

            # Check if Tor is working - use a simpler test
            try:
                # First try to access a simple HTTP endpoint through Tor
                self.driver.get("http://httpbin.org/ip")
                time.sleep(5)

                # If we can get a page, try the Tor check
                if "origin" in self.driver.page_source:
                    logger.info("✅ Basic Tor connectivity verified")

                    # Now try the official Tor check
                    self.driver.get("https://check.torproject.org/")
                    time.sleep(5)

                    if "Congratulations" in self.driver.page_source or "You are using Tor" in self.driver.page_source:
                        logger.success("✅ Tor connection fully verified")
                        return True
                    else:
                        logger.warning("⚠️  Tor check page failed, but basic connectivity works")
                        return True  # Still proceed if basic connectivity works
                else:
                    logger.error("❌ No Tor connectivity detected")
                    return False

            except Exception as e:
                logger.error(f"❌ Tor connection test failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to start Tor Browser: {e}")
            return False

    def login(self) -> bool:
        """
        Login to X (Twitter)

        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        if not self.email and not self.username:
            logger.error("Email or username required for login")
            return False

        if not self.password:
            logger.error("Password required for login")
            return False

        logger.info("Logging in to X (Twitter)...")

        try:
            # Navigate to login page
            self.driver.get(TWITTER_LOGIN_URL)
            time.sleep(3)

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
                return True
            else:
                logger.error("❌ Login verification failed")
                return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

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
            try:
                username_field = self.driver.find_element(By.XPATH, "//input[@autocomplete='username']")

                username_field.clear()
                username_field.send_keys(login_identifier)
                username_field.send_keys(Keys.RETURN)
                time.sleep(3)

                logger.info("Username/email entered successfully")
                return True

            except NoSuchElementException:
                input_attempt += 1
                logger.warning(f"Attempt {input_attempt}/3: Username field not found, retrying...")
                time.sleep(2)

        logger.error("Failed to input username after 3 attempts")
        return False

    def _input_unusual_activity(self) -> None:
        """Handle unusual activity verification (optional step)"""
        if not self.driver:
            logger.error("Driver not initialized")
            return

        input_attempt = 0

        while input_attempt < 3:
            try:
                unusual_activity_field = self.driver.find_element(
                    By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"
                )

                # Use username for unusual activity verification
                verification_text = self.username or self.email or ""
                unusual_activity_field.clear()
                unusual_activity_field.send_keys(verification_text)
                unusual_activity_field.send_keys(Keys.RETURN)
                time.sleep(3)

                logger.info("Unusual activity verification completed")
                break

            except NoSuchElementException:
                input_attempt += 1
                if input_attempt >= 3:
                    logger.info("No unusual activity verification required")
                    break
                time.sleep(1)

    def _input_password(self) -> bool:
        """Input password"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        if not self.password:
            logger.error("Password not provided")
            return False

        input_attempt = 0

        while input_attempt < 3:
            try:
                password_field = self.driver.find_element(By.XPATH, "//input[@autocomplete='current-password']")

                password_field.clear()
                password_field.send_keys(self.password)
                password_field.send_keys(Keys.RETURN)
                time.sleep(3)

                logger.info("Password entered successfully")
                return True

            except NoSuchElementException:
                input_attempt += 1
                logger.warning(f"Attempt {input_attempt}/3: Password field not found, retrying...")
                time.sleep(2)

        logger.error("Failed to input password after 3 attempts")
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
                "//input[@placeholder*='code']",
                "//input[@placeholder*='Code']",
            ]

            tfa_field = None
            for selector in tfa_selectors:
                try:
                    tfa_field = self.driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue

            if tfa_field:
                logger.info("🔐 Two-factor authentication required")
                print("\n" + "=" * 50)
                print("🔐 TWO-FACTOR AUTHENTICATION REQUIRED")
                print("=" * 50)
                print("Please check your authenticator app or SMS for the verification code.")

                # Get 2FA code from user input
                tfa_code = input("Enter your 2FA code: ").strip()

                if not tfa_code:
                    logger.error("No 2FA code provided")
                    return False

                # Input 2FA code
                tfa_field.clear()
                tfa_field.send_keys(tfa_code)
                tfa_field.send_keys(Keys.RETURN)
                time.sleep(5)

                logger.info("2FA code submitted")

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
        """Search for tweets"""
        if not self.driver:
            logger.error("Driver not initialized")
            return []

        try:
            # Navigate to search
            search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
            self.driver.get(search_url)
            time.sleep(5)

            tweets = []
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")

            for element in tweet_elements[:max_tweets]:
                try:
                    tweet = self._extract_tweet_data(element)
                    if tweet:
                        tweets.append(tweet)
                except Exception as e:
                    logger.warning(f"Failed to extract tweet: {e}")
                    continue

            logger.info(f"Extracted {len(tweets)} tweets for query: {query}")
            return tweets

        except Exception as e:
            logger.error(f"Failed to search tweets: {e}")
            return []

    def get_user_profile(self, username: str) -> UserProfile | None:
        """Get user profile"""
        if not self.driver:
            logger.error("Driver not initialized")
            return None

        try:
            # Navigate to profile
            profile_url = f"https://x.com/{username}"
            self.driver.get(profile_url)
            time.sleep(5)

            return self._extract_profile_data(username)

        except Exception as e:
            logger.error(f"Failed to get profile for {username}: {e}")
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

            # Extract metrics (simplified)
            likes = self._extract_metric(element, "like")
            retweets = self._extract_metric(element, "retweet")
            replies = self._extract_metric(element, "reply")

            return Tweet(
                text=text,
                author=author,
                likes=likes,
                retweets=retweets,
                replies=replies,
                timestamp=datetime.now().isoformat(),
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
        """Save tweets to JSON file"""
        try:
            output_path = self.data_dir / f"{filename}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([tweet.__dict__ for tweet in tweets], f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(tweets)} tweets to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save tweets: {e}")
            return False

    def save_profile_to_json(self, profile: UserProfile, filename: str) -> bool:
        """Save profile to JSON file"""
        try:
            output_path = self.data_dir / f"{filename}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(profile.__dict__, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved profile to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            return False

    def take_screenshot(self, filename: str | None = None) -> str | None:
        """
        現在表示されている画面のスクリーンショットを取得する

        Args:
            filename: 保存するファイル名(拡張子不要)。Noneの場合はタイムスタンプを使用

        Returns:
            str | None: 保存されたファイルパス(成功時)、None(失敗時)
        """
        if not self.driver:
            logger.error("Driver not initialized - cannot take screenshot")
            return None

        try:
            # スクリーンショット保存ディレクトリを作成
            screenshot_dir = Path("reports/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            # ファイル名生成(指定されない場合はタイムスタンプを使用)
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}"

            # .png拡張子を追加(まだ付いていない場合)
            if not filename.endswith(".png"):
                filename = f"{filename}.png"

            # フルパス生成
            screenshot_path = screenshot_dir / filename

            # スクリーンショット取得
            success = self.driver.save_screenshot(str(screenshot_path))

            if success:
                logger.info(f"✅ Screenshot saved: {screenshot_path}")
                return str(screenshot_path)
            else:
                logger.error("❌ Failed to save screenshot")
                return None

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

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
