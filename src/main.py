#!/usr/bin/env python3
"""
X scraper main execution
"""

import os
import sys
from pathlib import Path

from loguru import logger

from src.x_scraper import XScraper


def main() -> None:
    """Main execution function"""
    scraper = None

    try:
        # Get Tor Browser path from environment variable
        tbb_path = os.getenv("TBB_PATH")
        if not tbb_path:
            logger.error("TBB_PATH environment variable not set")
            logger.info("Please set TBB_PATH to your Tor Browser installation directory")
            logger.info("Example: export TBB_PATH=/path/to/tor-browser")
            sys.exit(1)

        # Verify TBB path exists
        if not Path(tbb_path).exists():
            logger.error(f"Tor Browser path does not exist: {tbb_path}")
            sys.exit(1)

        logger.info("🚀 Starting X Scraper with Tor Browser...")
        logger.info(f"📁 TBB Path: {tbb_path}")

        # Initialize scraper
        scraper = XScraper(tbb_path=tbb_path, headless=True)

        # Start the scraper
        if not scraper.start():
            logger.error("❌ Failed to start scraper")
            return

        # Navigate to X
        if not scraper.navigate_to_x():
            logger.error("❌ Failed to navigate to X")
            return

        # Example: Search for tweets
        search_query = "Python programming"
        logger.info(f"🔍 Searching for tweets about: {search_query}")

        tweets = scraper.search_tweets(search_query, max_tweets=10)

        if tweets:
            logger.success(f"✅ Found {len(tweets)} tweets!")

            # Display tweets
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"Tweet {i}:")
                logger.info(f"  Author: @{tweet.author}")
                logger.info(f"  Text: {tweet.text[:100]}...")
                logger.info(f"  Likes: {tweet.likes}")
                logger.info("  " + "-" * 50)

            # Save tweets to JSON
            filename = f"tweets_{search_query.replace(' ', '_')}.json"
            scraper.save_tweets_to_json(tweets, filename)

        else:
            logger.warning("⚠️ No tweets found")

        # Example: Get user profile
        username = "elonmusk"  # Example username
        logger.info(f"👤 Getting profile for: @{username}")

        profile = scraper.get_user_profile(username)
        if profile:
            logger.success(f"✅ Profile found for @{username}")
            logger.info(f"  Display Name: {profile.display_name}")
            logger.info(f"  Bio: {profile.bio[:100]}...")
            logger.info(f"  Followers: {profile.followers_count}")
            logger.info(f"  Following: {profile.following_count}")

            # Save profile to JSON
            profile_filename = f"profile_{username}.json"
            scraper.save_profile_to_json(profile, profile_filename)
        else:
            logger.warning(f"⚠️ Profile not found for @{username}")

        logger.success("✅ Scraping completed successfully!")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        level="INFO",
    )

    main()
