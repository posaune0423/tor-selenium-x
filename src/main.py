#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser - Simplified Example
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from src.utils.logger import configure_logging
from src.x_scraper import XScraper

# Load environment variables
load_dotenv()

# Configure logging
configure_logging()


def main():
    """Simplified main function for X scraping"""
    logger.info("🚀 Starting X (Twitter) Scraper")

    # Get Tor Browser path from environment
    tbb_path = os.getenv("TOR_BROWSER_PATH")
    if not tbb_path or not Path(tbb_path).exists():
        logger.error("❌ TOR_BROWSER_PATH not set or path doesn't exist")
        logger.info("Set TOR_BROWSER_PATH environment variable to your Tor Browser directory")
        return False

    # Get login credentials from environment (optional)
    email = os.getenv("X_EMAIL")
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")

    # Create scraper instance
    scraper = XScraper(
        tbb_path=tbb_path,
        headless=True,  # Set to False to see the browser
        email=email,
        username=username,
        password=password,
    )

    try:
        # Start the scraper
        logger.info("🔧 Starting Tor Browser...")
        if not scraper.start():
            logger.error("❌ Failed to start scraper")
            return False

        # Login if credentials are provided
        if email or username:
            if password:
                logger.info("🔐 Attempting to login...")
                if scraper.login():
                    logger.success("✅ Login successful!")
                else:
                    logger.error("❌ Login failed")
                    return False
            else:
                logger.warning("⚠️ Email/username provided but no password. Skipping login.")
        else:
            logger.info("No login credentials provided. Using anonymous browsing.")

        # Navigate to X.com
        if not scraper.navigate_to_x():
            logger.error("❌ Failed to navigate to X.com")
            return False

        # Example: Search for tweets
        logger.info("🔍 Searching for tweets...")
        search_query = "Python programming"
        tweets = scraper.search_tweets(search_query, max_tweets=5)

        if tweets:
            logger.success(f"📊 Found {len(tweets)} tweets for '{search_query}'")
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"  {i}. @{tweet.author}: {tweet.text[:100]}...")

            # Save results to JSON
            if scraper.save_tweets_to_json(tweets, f"search_results_{search_query.replace(' ', '_')}"):
                logger.success("💾 Search results saved to JSON")
        else:
            logger.warning("❌ No tweets found for the search query")

        # Example: Get user profile
        profile_username = "elonmusk"  # Example username
        logger.info(f"👤 Getting profile for @{profile_username}...")

        profile = scraper.get_user_profile(profile_username)
        if profile:
            logger.success(f"✅ Retrieved profile for @{profile_username}")
            logger.info(f"  Display name: {profile.display_name}")
            logger.info(
                f"  Followers: {profile.followers_count:,}" if profile.followers_count else "  Followers: Unknown"
            )
            logger.info(
                f"  Following: {profile.following_count:,}" if profile.following_count else "  Following: Unknown"
            )

            # Save profile to JSON
            if scraper.save_profile_to_json(profile, f"profile_{profile_username}"):
                logger.success("💾 Profile data saved to JSON")
        else:
            logger.warning(f"❌ Could not retrieve profile for @{profile_username}")

        logger.success("🎉 Scraping completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        return False

    finally:
        # Always clean up
        scraper.close()
        logger.info("🧹 Cleanup completed")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
