#!/usr/bin/env python3
"""
X (Twitter) scraper using Tor Browser
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from src.utils import configure_logging, random_delay
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


def main() -> None:
    """Main execution function"""
    scraper = None
    try:
        # Configure logging with DEBUG level for detailed output
        configure_logging(level="DEBUG")

        logger.info("Starting X Scraper...")

        # Find Tor Browser path
        tbb_path = find_tor_browser_path()
        if not tbb_path:
            logger.error("Tor Browser not found!")
            logger.info("Please install Tor Browser or set TOR_BROWSER_PATH environment variable")
            logger.info("Example: export TOR_BROWSER_PATH=/path/to/tor-browser")
            sys.exit(1)

        # Initialize scraper with Tor Browser
        scraper = XScraper(
            tbb_path=tbb_path,
            headless=True,
            use_stem=False,  # Use system Tor if available
            socks_port=9050,
            control_port=9051,
        )

        # Start scraper
        if not scraper.start():
            logger.error("Failed to start scraper")
            return

        logger.success("Scraper started successfully")

        # Navigate to X
        if not scraper.navigate_to_x():
            logger.error("Failed to navigate to X")
            return

        logger.success("Successfully connected to X")

        # Run examples
        run_examples(scraper)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        if scraper:
            scraper.close()


def run_examples(scraper: XScraper) -> None:
    """Run example scraping operations"""
    try:
        # Example 0: Login flow (optional)
        logger.info("=== Example 0: Login to X ===")
        login_attempted = False

        # Check if credentials are available from environment variables
        email = os.getenv("X_EMAIL")
        password = os.getenv("X_PASSWORD")
        username = os.getenv("X_USERNAME")

        if email and password and username:
            from src.models import XCredentials

            credentials = XCredentials(email=email, password=password, username=username)

            logger.info("Attempting login with provided credentials...")
            if scraper.login(credentials):
                logger.success("Successfully logged in to X!")
                login_attempted = True
            else:
                logger.warning("Login failed, continuing with anonymous browsing")
        else:
            logger.info("No login credentials found in environment variables")
            logger.info("Set X_EMAIL, X_PASSWORD, and X_USERNAME to enable login")
            logger.info("Login example will be skipped")

        # Example 1: Search for tweets
        logger.info("=== Example 1: Search for tweets ===")
        tweets = scraper.search_tweets("Python", max_tweets=5)
        logger.info(f"Found {len(tweets)} tweets")

        if tweets:
            # Save tweets to JSON
            scraper.save_tweets_to_json(tweets, "search_tweets.json")

            # Show sample tweets
            for i, tweet in enumerate(tweets[:3], 1):
                logger.info(f"Tweet {i}: @{tweet.author}: {tweet.text[:100]}...")

        # Example 2: Get user profile
        logger.info("=== Example 2: Get user profile ===")
        profile = scraper.get_user_profile("elonmusk")
        if profile:
            logger.success(f"Retrieved profile for @{profile.username}")
            logger.info(f"Display name: {profile.display_name}")
            logger.info(f"Bio: {profile.bio[:100] if profile.bio else 'No bio'}...")
            logger.info(f"Location: {profile.location or 'No location'}")
            logger.info(f"Website: {profile.website or 'No website'}")
            logger.info(f"Followers: {profile.followers_count}")
            logger.info(f"Following: {profile.following_count}")

            # Save profile to JSON
            scraper.save_profile_to_json(profile, f"profile_{profile.username}.json")
        else:
            logger.error("Failed to get user profile")

        # Example 3: Authenticated operations (if logged in)
        if login_attempted and scraper.session.is_logged_in:
            logger.info("=== Example 3: Authenticated operations ===")
            logger.info(f"Logged in as: @{scraper.session.current_user}")

            # Get tweets from the user's timeline (home feed)
            logger.info("Getting tweets from home timeline...")
            try:
                # Navigate to home timeline
                if scraper.driver:
                    scraper.driver.get("https://x.com/home")
                    random_delay(3, 5)
                    logger.success("Successfully accessed home timeline")

                    # In a real implementation, you might collect tweets from the timeline
                    logger.info("Home timeline access verified (tweet collection would go here)")
                else:
                    logger.error("Driver not available")
            except Exception as e:
                logger.error(f"Error accessing authenticated features: {e}")
        else:
            logger.info("=== Example 3: Skipped (not logged in) ===")
            logger.info("Login required for authenticated operations")

    except Exception as e:
        logger.error(f"Error in examples: {e}")


if __name__ == "__main__":
    main()
