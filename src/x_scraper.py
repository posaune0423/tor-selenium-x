#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser with tbselenium
"""

import contextlib
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
    """X (Twitter) scraper using Tor Browser"""

    def __init__(
        self,
        tbb_path: str,
        headless: bool = True,
        use_stem: bool = True,
        socks_port: int = 9050,
        control_port: int = 9051,
        data_dir: str | None = None,
        credentials: XCredentials | None = None,
    ):
        self.tbb_path = Path(tbb_path).resolve()
        self.headless = headless
        self.use_stem = use_stem
        self.socks_port = socks_port
        self.control_port = control_port

        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path.cwd() / "reports" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.driver: TorBrowserDriver | None = None
        self.tor_process = None
        self.credentials = credentials
        self.session = SessionState()
        self.cookies_file = self.data_dir / "session_cookies.json"

        logger.info(f"Initialized X scraper with TBB path: {self.tbb_path}")

    def start(self) -> bool:
        """Start Tor Browser and connect to Tor network"""
        try:
            if not self._start_tor():
                return False

            if not self._init_driver():
                return False

            if not self._check_tor():
                logger.error("Failed to connect to Tor network")
                return False

            if self.driver:
                add_anti_detection_measures(self.driver)

            logger.success("Successfully connected to Tor network")
            return True

        except Exception as e:
            logger.error(f"Error starting scraper: {e}")
            return False

    def login(self, credentials: XCredentials | None = None) -> bool:
        """Login to X with credentials"""
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        creds = credentials or self.credentials
        if not creds:
            logger.error("No credentials provided")
            return False

        try:
            if self._restore_session():
                logger.success("Restored session from cookies")
                self.session.is_logged_in = True
                self.session.current_user = creds.username
                return True

            logger.info("Starting fresh login")
            return self._do_login(creds)

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _do_login(self, creds: XCredentials) -> bool:
        """Perform enhanced login flow"""
        if not self.driver:
            return False

        try:
            logger.info("Navigating to login page")
            self.driver.get("https://x.com/i/flow/login")
            random_delay(3, 5)

            # Step 1: Email input
            if not self._input_email(creds.email):
                return False

            # Step 2: Handle unusual activity check
            self._handle_unusual_activity(creds.username)

            # Step 3: Password input
            if not self._input_password(creds.password):
                return False

            # Step 4: Email verification (optional - sometimes appears)
            self._handle_email_verification(creds.email)

            # Step 5: Verify success
            if not self._verify_login():
                return False

            self._save_cookies()
            self.session.is_logged_in = True
            self.session.current_user = creds.username
            self.session.login_timestamp = datetime.now().isoformat()

            logger.success(f"Successfully logged in as @{creds.username}")
            return True

        except Exception as e:
            logger.error(f"Login process failed: {e}")
            return False

    def _input_email(self, email: str) -> bool:
        """Input email with retry logic"""
        if not self.driver:
            return False

        for attempt in range(3):
            try:
                logger.info(f"Inputting email (attempt {attempt + 1}/3)")

                email_input = WebDriverWait(self.driver, 30).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']"))
                )

                email_input.clear()
                random_delay(0.5, 1.5)

                for char in email:
                    email_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                random_delay(1, 2)

                next_btn = self._find_next_button()
                if next_btn:
                    simulate_human_click_delay()
                    safe_click_element(self.driver, next_btn)
                    logger.success("Email submitted")
                    random_delay(2, 4)
                    return True

            except NoSuchElementException:
                if attempt == 2:
                    logger.error("Failed to input email")
                    return False
                time.sleep(2)

        return False

    def _handle_unusual_activity(self, username: str) -> bool:
        """Handle unusual activity check if present"""
        if not self.driver:
            return True

        try:
            unusual_input = WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']"))
            )

            logger.info("Handling unusual activity check")
            unusual_input.clear()
            random_delay(0.5, 1.0)

            for char in username:
                unusual_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            random_delay(1, 2)

            next_btn = self._find_next_button()
            if next_btn:
                safe_click_element(self.driver, next_btn)
                logger.success("Unusual activity check completed")
                random_delay(2, 4)

        except TimeoutException:
            logger.debug("No unusual activity check")

        return True

    def _input_password(self, password: str) -> bool:
        """Input password with retry logic"""
        if not self.driver:
            return False

        for attempt in range(3):
            try:
                logger.info(f"Inputting password (attempt {attempt + 1}/3)")

                password_input = WebDriverWait(self.driver, 30).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='current-password']"))
                )

                password_input.clear()
                random_delay(0.5, 1.5)

                for char in password:
                    password_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.12))

                random_delay(1, 2)
                password_input.send_keys(Keys.RETURN)

                logger.success("Password submitted")
                random_delay(3, 6)
                return True

            except NoSuchElementException:
                if attempt == 2:
                    logger.error("Failed to input password")
                    return False
                time.sleep(2)

        return False

    def _handle_email_verification(self, email: str) -> bool:
        """
        Handle email verification if present.

        Note: このメール入力フローはある時と無い時があります。
        Xのセキュリティ設定により、パスワード入力後にメール確認が要求される場合があります。
        タイムアウトを短く設定して、必要な場合のみ処理します。
        """
        if not self.driver:
            return True

        try:
            logger.info("Checking for email verification (sometimes required)")

            # Check for email verification input with short timeout since it's optional
            verification_selectors = [
                "input[data-testid='ocfEnterTextTextInput']",
                "input[placeholder*='email']",
                "input[type='email']",
                "input[name='email']",
            ]

            verification_input = None
            for selector in verification_selectors:
                try:
                    verification_input = WebDriverWait(self.driver, 3).until(
                        ec.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Email verification found: {selector}")
                    break
                except TimeoutException:
                    continue

            if not verification_input:
                logger.debug("No email verification needed")
                return True

            logger.info("Handling email verification")
            verification_input.clear()
            random_delay(0.5, 1.5)

            for char in email:
                verification_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            random_delay(1, 2)

            next_btn = self._find_next_button()
            if next_btn:
                safe_click_element(self.driver, next_btn)
            else:
                verification_input.send_keys(Keys.RETURN)

            logger.success("Email verification completed")
            random_delay(3, 5)

        except Exception as e:
            logger.warning(f"Email verification error: {e}")

        return True

    def _find_next_button(self):
        """Find Next button"""
        if not self.driver:
            return None

        selectors = [
            "//span[text()='Next']//ancestor::button",
            "//span[text()='次へ']//ancestor::button",
            "[data-testid='LoginForm_Login_Button']",
            "button[type='submit']",
        ]

        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = self.driver.find_element(By.XPATH, selector)
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.is_enabled():
                    return element
            except NoSuchElementException:
                continue

        return None

    def _restore_session(self) -> bool:
        """Try to restore session from cookies"""
        if not self.driver:
            return False

        try:
            cookies = load_cookies_from_file(str(self.cookies_file))
            if not cookies or are_cookies_expired(cookies):
                return False

            logger.info("Restoring session from cookies")
            self.driver.get("https://x.com")
            random_delay(2, 4)

            for cookie in cookies:
                with contextlib.suppress(Exception):
                    self.driver.add_cookie(cookie)

            self.driver.get("https://x.com/home")
            random_delay(3, 5)

            if self._check_logged_in():
                self.session.session_cookies = cookies
                return True

        except Exception as e:
            logger.warning(f"Failed to restore session: {e}")

        return False

    def _check_logged_in(self) -> bool:
        """Check if logged in"""
        if not self.driver:
            return False

        selectors = [
            "[data-testid='primaryColumn']",
            "[data-testid='AppTabBar_Home_Link']",
            "[data-testid='SideNav_AccountSwitcher_Button']",
        ]

        for selector in selectors:
            try:
                WebDriverWait(self.driver, 5).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return True
            except TimeoutException:
                continue

        return False

    def _verify_login(self) -> bool:
        """Verify login success"""
        if not self.driver:
            return False

        try:
            if not detect_and_handle_captcha(self.driver):
                return False

            selectors = [
                "[data-testid='primaryColumn']",
                "[data-testid='AppTabBar_Home_Link']",
                "main[role='main']",
            ]

            for selector in selectors:
                try:
                    WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    return True
                except TimeoutException:
                    continue

            return False

        except Exception as e:
            logger.error(f"Login verification failed: {e}")
            return False

    def _save_cookies(self) -> None:
        """Save session cookies"""
        if not self.driver:
            return

        try:
            cookies = self.driver.get_cookies()
            if cookies:
                save_cookies_to_file(cookies, str(self.cookies_file))
                self.session.session_cookies = cookies
                logger.info(f"Saved {len(cookies)} cookies")

        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def search_tweets(self, query: str, max_tweets: int = 20, latest: bool = True) -> list[Tweet]:
        """Search for tweets"""
        if not query.strip() or not self.driver:
            return []

        clean_query = query.replace(" ", "")
        logger.info(f"Searching tweets: '{query}' -> '{clean_query}'")

        if not self._go_to_search(clean_query, latest):
            return []

        return self._collect_tweets(max_tweets)

    def _go_to_search(self, query: str, latest: bool = True) -> bool:
        """Navigate to search page"""
        if not self.driver:
            return False

        try:
            search_url = f"https://x.com/search?q={query}&src=typed_query"
            if latest:
                search_url += "&f=live"

            self.driver.get(search_url)

            selectors = ["main[role='main']", "div[data-testid='primaryColumn']", "section[role='region']"]

            for selector in selectors:
                try:
                    WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    random_delay(3, 5)
                    return True
                except TimeoutException:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error navigating to search: {e}")
            return False

    def _collect_tweets(self, max_tweets: int) -> list[Tweet]:
        """Collect tweets from search results"""
        if not self.driver:
            return []

        tweets = []
        tweet_ids = set()
        scroll_count = 0
        max_scrolls = 15

        logger.info(f"Collecting {max_tweets} tweets...")

        try:
            while len(tweets) < max_tweets and scroll_count < max_scrolls:
                tweet_selectors = [
                    "article[data-testid='tweet']",
                    "div[data-testid='tweet']",
                    "article[role='article']",
                ]

                elements = find_elements_by_selectors(self.driver, tweet_selectors)

                for element in elements[-15:]:
                    if len(tweets) >= max_tweets:
                        break

                    tweet_id = str(element)
                    if tweet_id not in tweet_ids:
                        tweet_ids.add(tweet_id)

                        if not self._is_ad(element):
                            tweet = self._extract_tweet(element)
                            if tweet and tweet.text:
                                tweets.append(tweet)
                                logger.debug(f"Tweet {len(tweets)}: {tweet.text[:50]}...")

                if len(tweets) < max_tweets:
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    scroll_count += 1
                    random_delay(2, 4)

        except Exception as e:
            logger.error(f"Error collecting tweets: {e}")

        logger.success(f"Collected {len(tweets)} tweets")
        return tweets

    def _is_ad(self, element) -> bool:
        """Check if element is an ad"""
        try:
            indicators = ["//span[text()='Promoted']", "//span[text()='Ad']"]
            for indicator in indicators:
                try:
                    element.find_element(By.XPATH, indicator)
                    return True
                except NoSuchElementException:
                    continue
        except Exception:
            pass
        return False

    def _extract_tweet(self, element) -> Tweet | None:
        """Extract tweet data from element"""
        if not element:
            return None

        tweet = Tweet()
        tweet.text = self._get_tweet_text(element)
        tweet.author = self._get_tweet_author(element)
        tweet.likes = self._get_tweet_likes(element)
        tweet.retweets = self._get_tweet_retweets(element)
        tweet.replies = self._get_tweet_replies(element)

        self._get_tweet_time(element, tweet)

        return tweet if tweet.text or tweet.author else None

    def _get_tweet_text(self, element) -> str:
        """Get tweet text"""
        selectors = [
            "[data-testid='tweetText'] span",
            "[data-testid='tweetText']",
            "[lang] span",
        ]
        return extract_text_by_selectors(element, selectors)

    def _get_tweet_author(self, element) -> str:
        """Get tweet author"""
        try:
            author_element = element.find_element(By.CSS_SELECTOR, "[data-testid='User-Name'] a")
            href = author_element.get_attribute("href")
            return href.split("/")[-1] if href else ""
        except NoSuchElementException:
            return ""

    def _get_tweet_likes(self, element) -> int:
        """Get likes count"""
        selectors = ["[data-testid='like'] span", "[aria-label*='like'] span"]
        return extract_count_by_selectors(element, selectors, self._parse_count)

    def _get_tweet_retweets(self, element) -> int:
        """Get retweets count"""
        selectors = ["[data-testid='retweet'] span", "[aria-label*='retweet'] span"]
        return extract_count_by_selectors(element, selectors, self._parse_count)

    def _get_tweet_replies(self, element) -> int:
        """Get replies count"""
        selectors = ["[data-testid='reply'] span", "[aria-label*='repl'] span"]
        return extract_count_by_selectors(element, selectors, self._parse_count)

    def _get_tweet_time(self, element, tweet: Tweet) -> None:
        """Get tweet timestamp and URL"""
        try:
            time_element = element.find_element(By.CSS_SELECTOR, "time")
            tweet.timestamp = time_element.get_attribute("datetime") or ""

            time_link = time_element.find_element(By.XPATH, "..")
            tweet_url = time_link.get_attribute("href")
            if tweet_url:
                tweet.url = tweet_url
                url_parts = tweet_url.split("/")
                if "status" in url_parts:
                    status_index = url_parts.index("status")
                    if status_index + 1 < len(url_parts):
                        tweet.id = url_parts[status_index + 1]
        except NoSuchElementException:
            pass

    def get_profile(self, username: str) -> UserProfile | None:
        """Get user profile"""
        if not validate_x_username(username) or not self.driver:
            return None

        try:
            profile_url = f"https://x.com/{username}"
            logger.info(f"Getting profile: @{username}")
            self.driver.get(profile_url)

            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']"))
            )
            random_delay(3, 5)

            return self._extract_profile(username)

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None

    def _extract_profile(self, username: str) -> UserProfile:
        """Extract profile data"""
        profile = UserProfile(username=username)
        random_delay(2, 4)

        profile.display_name = self._get_display_name()
        profile.bio = self._get_bio()
        profile.location = self._get_location()
        profile.website = self._get_website()
        self._get_stats(profile)

        return profile

    def _get_display_name(self) -> str:
        """Get display name"""
        selectors = ["h1[role='heading'] span span", "[data-testid='UserName'] span"]
        return extract_text_from_driver_by_selectors(self.driver, selectors)

    def _get_bio(self) -> str:
        """Get bio"""
        selectors = ["[data-testid='UserDescription'] span", "[data-testid='UserDescription']"]
        return extract_text_from_driver_by_selectors(self.driver, selectors)

    def _get_location(self) -> str:
        """Get location"""
        selectors = ["[data-testid='UserLocation'] span"]
        return extract_text_from_driver_by_selectors(self.driver, selectors)

    def _get_website(self) -> str:
        """Get website"""
        selectors = ["[data-testid='UserUrl'] a"]
        return extract_attribute_from_driver_by_selectors(self.driver, selectors, "href")

    def _get_stats(self, profile: UserProfile) -> None:
        """Get follower/following counts"""
        if not self.driver:
            return

        try:
            # Following count
            following_selectors = ["a[href$='/following'] span span", "a[href*='/following'] span"]
            for selector in following_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and any(char.isdigit() for char in text):
                        count = self._parse_count(text)
                        if count is not None:
                            profile.following_count = count
                            break
                if profile.following_count is not None and profile.following_count > 0:
                    break

            # Followers count
            followers_selectors = ["a[href$='/followers'] span span", "a[href*='/followers'] span"]
            for selector in followers_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and any(char.isdigit() for char in text):
                        count = self._parse_count(text)
                        if count is not None:
                            profile.followers_count = count
                            break
                if profile.followers_count is not None and profile.followers_count > 0:
                    break

        except Exception as e:
            logger.warning(f"Error getting stats: {e}")

    def _parse_count(self, count_str: str | None) -> int:
        """Parse count string to int"""
        if not count_str:
            return 0

        count_str = count_str.strip().replace(",", "")
        if not count_str:
            return 0

        try:
            upper_str = count_str.upper()
            num_str = ""

            for char in upper_str:
                if char.isdigit() or char == ".":
                    num_str += char
                elif char in ["K", "M", "B"]:
                    break

            if not num_str:
                return 0

            num = float(num_str)

            if "K" in upper_str:
                return int(num * 1000)
            elif "M" in upper_str:
                return int(num * 1000000)
            elif "B" in upper_str:
                return int(num * 1000000000)
            else:
                return int(num)

        except (ValueError, TypeError):
            return 0

    def _start_tor(self) -> bool:
        """Start Tor process"""
        if not self.use_stem:
            return True

        try:
            logger.info("Starting Tor process...")
            # Dockerコンテナ内では既にTorが起動している可能性があるため、
            # まず接続をテストしてから起動を試行
            try:
                import stem.control

                with stem.control.Controller.from_port(port=str(self.control_port)) as controller:
                    controller.authenticate()
                    logger.info("Tor is already running on correct port")
                    return True
            except Exception:
                logger.info("Tor not running on expected port, attempting to start...")

            # tbseliumのTor起動を試行
            try:
                self.tor_process = launch_tbb_tor_with_stem(tbb_path=str(self.tbb_path))
                time.sleep(3)
                return True
            except Exception as e:
                logger.warning(f"tbselenium Tor start failed: {e}, trying system Tor...")

                # システムのTorを使用
                import subprocess

                try:
                    # 既存のTorプロセスを停止
                    try:
                        subprocess.run(["pkill", "-f", "tor"], check=False, capture_output=True)
                        time.sleep(2)
                    except Exception:
                        pass

                    # 正しいポートでシステムのTorを起動
                    self.tor_process = subprocess.Popen(
                        [
                            "tor",
                            "--SocksPort",
                            str(self.socks_port),
                            "--ControlPort",
                            str(self.control_port),
                            "--CookieAuthentication",
                            "0",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    time.sleep(5)  # Torの起動を待つ

                    # Tor接続をテスト
                    try:
                        import stem.control

                        with stem.control.Controller.from_port(port=str(self.control_port)) as controller:
                            controller.authenticate()
                            logger.success("System Tor started successfully")
                            return True
                    except Exception as test_e:
                        logger.error(f"Failed to connect to started Tor: {test_e}")
                        return False

                except Exception as sys_e:
                    logger.error(f"Failed to start system Tor: {sys_e}")
                    return False

        except Exception as e:
            logger.error(f"Failed to start Tor: {e}")
            return False

    def _init_driver(self) -> bool:
        """Initialize Tor Browser driver"""
        try:
            logger.info("Starting Tor Browser...")
            tor_cfg = tb_common.USE_STEM if self.use_stem else tb_common.USE_RUNNING_TOR

            pref_dict = {
                "network.proxy.type": 1,
                "network.proxy.socks": "127.0.0.1",
                "network.proxy.socks_port": self.socks_port,
                "network.proxy.socks_version": 5,
                "network.proxy.socks_remote_dns": True,
            }

            if self.headless:
                pref_dict["general.useragent.override"] = get_user_agent()

            self.driver = TorBrowserDriver(
                tbb_path=str(self.tbb_path),
                tor_cfg=tor_cfg,
                socks_port=self.socks_port,
                control_port=self.control_port,
                headless=self.headless,
                pref_dict=pref_dict,
            )

            return self.driver is not None

        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            return False

    def _check_tor(self) -> bool:
        """Check Tor connection"""
        if not self.driver:
            return False

        try:
            logger.info("Checking Tor connection...")
            self.driver.get("https://check.torproject.org")
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.TAG_NAME, "body")))

            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()

            tor_working = any(
                [
                    "congratulations" in page_title,
                    "congratulations" in page_source,
                    "using tor" in page_source,
                ]
            )

            if tor_working:
                logger.info("Tor connection verified")
                return True
            else:
                logger.warning("Tor connection verification failed")
                return False

        except Exception as e:
            logger.error(f"Error checking Tor: {e}")
            return False

    def close(self) -> None:
        """Close browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None

            if self.tor_process:
                self.tor_process.kill()
                self.tor_process = None

            logger.success("Scraper closed")

        except Exception as e:
            logger.error(f"Error closing: {e}")

    def navigate_to_x(self) -> bool:
        """
        Navigate to X.com

        Returns:
            True if navigation successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            logger.info("📍 Navigating to X.com...")
            self.driver.get("https://x.com")

            # Wait for page to load
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.TAG_NAME, "body")))

            # Check if we reached X.com
            current_url = self.driver.current_url.lower()
            if "x.com" in current_url or "twitter.com" in current_url:
                logger.success("✅ Successfully navigated to X.com")
                return True
            else:
                logger.error(f"❌ Failed to reach X.com, current URL: {current_url}")
                return False

        except Exception as e:
            logger.error(f"Error navigating to X.com: {e}")
            return False

    def _try_restore_session(self) -> bool:
        """
        Try to restore session from saved cookies

        Returns:
            True if session restored successfully, False otherwise
        """
        try:
            if self._restore_session():
                logger.success("✅ Session restored from cookies")
                return True
            else:
                logger.warning("❌ Failed to restore session from cookies")
                return False
        except Exception as e:
            logger.error(f"Error trying to restore session: {e}")
            return False

    def save_tweets_to_json(self, tweets: list[Tweet], filename: str) -> bool:
        """
        Save tweets to JSON file

        Args:
            tweets: List of tweets to save
            filename: Output filename

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            import json

            if not tweets:
                logger.warning("No tweets to save")
                return False

            if not filename.endswith(".json"):
                filename += ".json"

            filepath = self.data_dir / filename

            # Convert tweets to dictionaries
            tweets_data = []
            for tweet in tweets:
                tweet_dict = {
                    "id": tweet.id,
                    "author": tweet.author,
                    "text": tweet.text,
                    "timestamp": tweet.timestamp,
                    "likes": tweet.likes,
                    "retweets": tweet.retweets,
                    "replies": tweet.replies,
                    "url": tweet.url,
                }
                tweets_data.append(tweet_dict)

            # Save to JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(tweets_data, f, indent=2, ensure_ascii=False)

            logger.success(f"💾 Saved {len(tweets)} tweets to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving tweets to JSON: {e}")
            return False

    def get_user_profile(self, username: str) -> UserProfile | None:
        """
        Get user profile - alias for get_profile()

        Args:
            username: Username to get profile for

        Returns:
            UserProfile object or None if not found
        """
        return self.get_profile(username)

    def save_profile_to_json(self, profile: UserProfile, filename: str) -> bool:
        """
        Save user profile to JSON file

        Args:
            profile: UserProfile object to save
            filename: Output filename

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            import json

            if not profile:
                logger.warning("No profile to save")
                return False

            if not filename.endswith(".json"):
                filename += ".json"

            filepath = self.data_dir / filename

            # Convert profile to dictionary
            profile_dict = {
                "username": profile.username,
                "display_name": profile.display_name,
                "bio": profile.bio,
                "location": profile.location,
                "website": profile.website,
                "tweets_count": profile.tweets_count,
                "following_count": profile.following_count,
                "followers_count": profile.followers_count,
                "joined_date": profile.joined_date,
                "verified": profile.verified,
                "profile_image_url": profile.profile_image_url,
                "banner_image_url": profile.banner_image_url,
            }

            # Save to JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False)

            logger.success(f"💾 Saved profile for @{profile.username} to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving profile to JSON: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
