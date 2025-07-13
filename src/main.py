#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser - Simplified Example
"""

import os
import sys

from dotenv import load_dotenv
from loguru import logger

from src.constants import DEFAULT_MAX_TWEETS, DEFAULT_TBB_PATH_MACOS, ENV_VARS
from src.utils.logger import configure_logging
from src.x_scraper import XScraper

# Load environment variables
load_dotenv()

# Configure logging
configure_logging()


def main() -> int:
    """Main function demonstrating X scraper usage with cookie persistence"""
    logger.info("Starting X scraper application...")

    # Get configuration from environment variables with fallbacks
    tbb_path = os.environ.get(ENV_VARS["TBB_PATH"], DEFAULT_TBB_PATH_MACOS)
    headless = os.environ.get(ENV_VARS["HEADLESS"], "false").lower() == "true"

    # Get credentials from environment variables
    email = os.environ.get(ENV_VARS["X_EMAIL"])
    username = os.environ.get(ENV_VARS["X_USERNAME"])
    password = os.environ.get(ENV_VARS["X_PASSWORD"])

    # Initialize scraper with configuration
    scraper = XScraper(
        tbb_path=tbb_path,
        headless=headless,
        email=email,
        username=username,
        password=password,
    )

    try:
        # Start Tor Browser
        if not scraper.start():
            logger.error("Failed to start Tor Browser")
            return 1

        # Check for existing valid cookies and provide user feedback
        has_valid_cookies = scraper.cookie_manager.has_valid_cookies()

        if has_valid_cookies:
            logger.info("✅ Valid authentication cookies found - attempting automatic login")
            logger.info("📋 Form login will be skipped if cookie authentication succeeds")
        else:
            logger.info("🔐 No valid cookies found - manual login will be required")
            if not (email or username) or not password:
                logger.warning("⚠️ Login credentials not provided - manual login may fail")

        # Perform login (XScraper.login() handles cookie-first logic internally)
        if not scraper.login():
            logger.error("❌ Failed to login to X")
            return 1

        # Verify final login status and proceed with scraping
        if scraper.is_logged_in():
            if has_valid_cookies:
                logger.success("🎉 Successfully authenticated using saved cookies - form login skipped!")
            else:
                logger.success("🎉 Successfully authenticated using manual login")

            logger.info("🚀 Proceeding with scraping operations...")

            # Execute scraping examples
            success = _run_scraping_examples(scraper)
            if not success:
                logger.warning("⚠️ Some scraping operations failed")
        else:
            logger.error("❌ Login verification failed")
            return 1

    except KeyboardInterrupt:
        logger.info("⏹️ Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1
    finally:
        # Clean up
        scraper.close()

    logger.success("✅ X scraper application completed successfully")
    return 0


def _run_scraping_examples(scraper: XScraper) -> bool:
    """
    Run example scraping operations

    Args:
        scraper: Initialized XScraper instance

    Returns:
        bool: True if all operations succeeded
    """
    success = True

    try:
        # Example: Search for tweets
        logger.info("Searching for tweets about 'python'...")
        tweets = scraper.search_tweets("python", max_tweets=DEFAULT_MAX_TWEETS)
        logger.info(f"Found {len(tweets)} tweets")

        # Save tweets to JSON file
        if tweets:
            if scraper.save_tweets_to_json(tweets, "python_tweets.json"):
                logger.info("Tweets saved to python_tweets.json")
            else:
                logger.warning("Failed to save tweets")
                success = False

        # Example: Get user profile
        logger.info("Getting profile for user 'elonmusk'...")
        profile = scraper.get_user_profile("elonmusk")
        if profile:
            logger.info(f"Profile found: {profile.display_name}")
            if scraper.save_profile_to_json(profile, "twitter_profile.json"):
                logger.info("Profile saved to twitter_profile.json")
            else:
                logger.warning("Failed to save profile")
                success = False
        else:
            logger.warning("Failed to get user profile")
            success = False

        # Take a screenshot
        screenshot_file = scraper.take_screenshot()
        if screenshot_file:
            logger.info(f"Screenshot saved: {screenshot_file}")
        else:
            logger.warning("Failed to take screenshot")
            success = False

    except Exception as e:
        logger.error(f"Error during scraping examples: {e}")
        success = False

    return success


def demo_cookie_management() -> None:
    """Demonstrate cookie management features"""
    logger.info("Demonstrating cookie management...")

    tbb_path = os.environ.get(ENV_VARS["TBB_PATH"], DEFAULT_TBB_PATH_MACOS)
    scraper = XScraper(tbb_path=tbb_path)

    try:
        if not scraper.start():
            logger.error("Failed to start Tor Browser")
            return

        # Check login status
        if scraper.is_logged_in():
            logger.info("Already logged in via cookies")
        else:
            logger.info("Not logged in, would need credentials for manual login")

        # Clear saved cookies if needed
        if scraper.clear_saved_cookies():
            logger.info("Cookies cleared successfully")

        # After clearing cookies, login status should be false
        if not scraper.is_logged_in():
            logger.info("Login status confirmed as false after cookie clearing")

    finally:
        scraper.close()


if __name__ == "__main__":
    sys.exit(main())
