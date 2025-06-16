#!/usr/bin/env python3
"""
シンプルなTor + Seleniumスクレーパー
参考: https://qiita.com/kawagoe6884/items/381a938dd3d8744f29d4
参考: https://zenn.dev/harurow/articles/7b845931350cb8
"""

import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class TorScraper:
    """Tor経由でSeleniumスクレーピングを行うクラス"""

    def __init__(self, proxy_port: int = 9050, headless: bool = True):
        self.proxy_port = proxy_port
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None

    def _create_chrome_options(self) -> Options:
        """Chrome オプションを設定"""
        options = Options()

        # Tor プロキシ設定
        options.add_argument(f'--proxy-server=socks5://localhost:{self.proxy_port}')

        # ヘッドレスモード
        if self.headless:
            options.add_argument('--headless')

        # セキュリティ・パフォーマンス設定
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')

        # User-Agent設定（簡略化）
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # webdriver検出回避
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # 通知を無効化
        prefs = {'profile.default_content_setting_values.notifications': 2}
        options.add_experimental_option('prefs', prefs)

        return options

    def start_driver(self) -> None:
        """WebDriverを開始"""
        try:
            options = self._create_chrome_options()
            self.driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=options
            )
            self.driver.implicitly_wait(10)
            print("✅ WebDriver started successfully")

        except Exception as e:
            print(f"❌ Failed to start WebDriver: {e}")
            raise

    def check_tor_connection(self) -> bool:
        """Tor接続を確認"""
        if not self.driver:
            print("❌ WebDriver not started")
            return False

        try:
            # Torプロジェクトの接続確認ページにアクセス
            print("🔍 Checking Tor connection...")
            self.driver.get('https://check.torproject.org')

            # ページが読み込まれるまで待機
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # タイトルに"congratulations"が含まれているかチェック
            if "congratulations" in self.driver.title.lower():
                print("✅ Tor connection confirmed!")

                # IPアドレス情報を取得
                try:
                    ip_element = self.driver.find_element(By.TAG_NAME, "strong")
                    ip_address = ip_element.text
                    print(f"🌐 Current IP: {ip_address}")
                except:
                    print("🌐 Tor connection active (IP address not found)")

                return True
            else:
                print("❌ Tor connection not detected")
                return False

        except Exception as e:
            print(f"❌ Error checking Tor connection: {e}")
            return False

    def search_duckduckgo(self, query: str) -> None:
        """DuckDuckGoで検索を実行"""
        if not self.driver:
            print("❌ WebDriver not started")
            return

        try:
            print(f"🔍 Searching for: {query}")
            self.driver.get('https://duckduckgo.com')

            # 検索ボックスを見つけて入力
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(query)

            # 検索ボタンをクリック
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            search_button.click()

            # 結果が読み込まれるまで待機
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
            )

            print("✅ Search completed successfully")

            # 検索結果の最初の3つのタイトルを取得
            results = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result'] h2")
            for i, result in enumerate(results[:3], 1):
                print(f"📝 Result {i}: {result.text}")

        except Exception as e:
            print(f"❌ Error during search: {e}")

    def close(self) -> None:
        """WebDriverを終了"""
        if self.driver:
            self.driver.quit()
            print("✅ WebDriver closed")


def main():
    """メイン実行関数"""
    scraper = None
    try:
        print("🚀 Starting Tor Scraper...")

        # スクレーパーを初期化
        scraper = TorScraper(headless=True)

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