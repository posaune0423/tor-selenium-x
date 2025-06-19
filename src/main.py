#!/usr/bin/env python3
"""
Tor Scraperのメイン実行処理
"""

import os
import time

from src import TorScraper


def main() -> None:
    """メイン実行関数"""
    scraper = None
    try:
        print("🚀 Starting Tor Scraper...")

        # 環境変数からブラウザタイプを取得 (デフォルト: chromium)
        browser = os.getenv("BROWSER", "chromium").lower()
        print(f"🌐 Using browser: {browser}")

        # スクレーパーを初期化
        scraper = TorScraper(headless=True, browser=browser)

        # WebDriverを開始
        scraper.start_driver()

        # Tor接続を確認
        if not scraper.check_tor_connection():
            print("❌ Tor connection failed. Exiting...")
            return

        # 少し待機
        time.sleep(2)

        # DuckDuckGoで検索
        scraper.search_duckduckgo("Python web scraping")

        # 結果を確認するため少し待機
        time.sleep(3)

        print("✅ Scraping completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()
