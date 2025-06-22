#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser - Simple Example
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from src.models import XCredentials
from src.x_scraper import XScraper

# Load environment variables from .env file
load_dotenv()


def find_tor_browser_path() -> str | None:
    """
    Find Tor Browser installation path automatically.

    Returns:
        Path to Tor Browser directory or None if not found
    """
    # Check environment variable first
    env_path = os.getenv("TOR_BROWSER_PATH")
    if env_path and Path(env_path).exists():
        logger.info(f"Using Tor Browser path from environment: {env_path}")
        return env_path

    # Common installation paths for different platforms
    common_paths = [
        # Linux
        "/opt/torbrowser",
        "/usr/local/tor-browser",
        "/usr/share/tor-browser",
        "~/tor-browser",
        "~/tor-browser_en-US",
        # macOS
        "/Applications/Tor Browser.app",
        "~/Applications/Tor Browser.app",
        # Development/Docker
        "/app/tor-browser",
        "/usr/local/bin/tor-browser",
    ]

    # Expand user paths and check existence
    for path_str in common_paths:
        path = Path(path_str).expanduser()
        if path.exists() and path.is_dir():
            logger.info(f"Found Tor Browser at: {path}")
            return str(path)

    logger.warning("Tor Browser not found in common locations")
    logger.info("Available locations checked:")
    for path_str in common_paths:
        path = Path(path_str).expanduser()
        logger.info(f"  - {path} {'✓' if path.exists() else '✗'}")

    return None


def main():
    """Simple main function for X scraping example."""
    logger.info("🚀 Starting X (Twitter) Scraper")

    # Find Tor Browser path
    tbb_path = find_tor_browser_path()
    if not tbb_path:
        logger.error(
            "❌ Tor Browser not found. Please install Tor Browser or set TOR_BROWSER_PATH environment variable."
        )
        return False

    # Get credentials from environment variables (optional)
    email = os.getenv("X_EMAIL")
    password = os.getenv("X_PASSWORD")
    username = os.getenv("X_USERNAME")

    credentials = None
    if email and password and username:
        credentials = XCredentials(email=email, password=password, username=username)
        logger.info("✅ Credentials loaded from environment variables")
    else:
        logger.info("No credentials provided - will work in anonymous mode")

    # Create scraper instance
    scraper = XScraper(
        tbb_path=tbb_path,
        headless=True,  # Set to False to see the browser
        credentials=credentials,
    )

    try:
        # Start the scraper
        logger.info("🔧 Starting Tor Browser...")
        if not scraper.start():
            logger.error("❌ Failed to start scraper")
            return False

        # Navigate to X.com
        if not scraper.navigate_to_x():
            logger.error("❌ Failed to navigate to X.com")
            return False

        # Try to log in if credentials are provided
        if credentials:
            logger.info("🔐 Attempting to log in...")
            if scraper.login(credentials):
                logger.success(f"✅ Successfully logged in as @{credentials.username}")
            else:
                logger.warning("⚠️  Login failed, continuing in anonymous mode")

        # Example: Search for tweets
        logger.info("🔍 Searching for tweets...")
        search_query = "Python"
        tweets = scraper.search_tweets(search_query, max_tweets=5)

        if tweets:
            logger.success(f"📊 Found {len(tweets)} tweets for '{search_query}'")
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"  {i}. @{tweet.author}: {tweet.text[:100]}...")

            # Save results to JSON (if method exists)
            try:
                if scraper.save_tweets_to_json(tweets, f"search_results_{search_query.replace(' ', '_')}.json"):
                    logger.success("💾 Search results saved to JSON")
            except AttributeError:
                logger.debug("JSON save method not available")

        else:
            logger.warning("❌ No tweets found for the search query")

        # Example: Get user profile
        profile_username = "elonmusk"  # Example username
        logger.info(f"👤 Getting profile for @{profile_username}...")

        try:
            profile = scraper.get_user_profile(profile_username)
        except AttributeError:
            # Fallback to get_profile if get_user_profile doesn't exist
            profile = scraper.get_profile(profile_username)

        if profile:
            logger.success(f"✅ Retrieved profile for @{profile_username}")
            logger.info(f"  Display name: {profile.display_name}")
            logger.info(
                f"  Followers: {profile.followers_count:,}" if profile.followers_count else "  Followers: Unknown"
            )
            logger.info(
                f"  Following: {profile.following_count:,}" if profile.following_count else "  Following: Unknown"
            )

            # Save profile to JSON (if method exists)
            try:
                if scraper.save_profile_to_json(profile, f"profile_{profile_username}.json"):
                    logger.success("💾 Profile data saved to JSON")
            except AttributeError:
                logger.debug("Profile JSON save method not available")
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
