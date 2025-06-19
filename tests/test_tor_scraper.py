"""
Tor Scraperのテスト
"""

from unittest.mock import Mock, patch

import pytest

from src.tor_scraper import TorScraper


class TestTorScraper:
    """TorScraperクラスのテスト"""

    def test_init(self):
        """初期化テスト"""
        scraper = TorScraper(proxy_port=9050, headless=True)
        assert scraper.proxy_port == 9050
        assert scraper.headless is True
        assert scraper.driver is None

    def test_create_chromium_options(self):
        """Chrome オプション設定テスト"""
        scraper = TorScraper(proxy_port=9050, headless=True)
        options = scraper._create_chromium_options()

        # オプションが設定されていることを確認
        assert options is not None
        # より詳細なテストは実際のSeleniumインスタンスで行う

    @patch("src.tor_scraper.webdriver.Chrome")
    @patch("src.tor_scraper.ChromeDriverManager")
    def test_start_driver_success(self, mock_driver_manager, mock_chrome):
        """WebDriver開始成功テスト"""
        # モックの設定
        mock_driver_manager().install.return_value = "/path/to/chromedriver"
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        scraper = TorScraper()
        scraper.start_driver()

        # WebDriverが設定されていることを確認
        assert scraper.driver == mock_driver
        mock_chrome.assert_called_once()

    def test_close_with_driver(self):
        """WebDriver終了テスト(ドライバーあり)"""
        scraper = TorScraper()
        mock_driver = Mock()
        scraper.driver = mock_driver

        scraper.close()

        mock_driver.quit.assert_called_once()

    def test_close_without_driver(self):
        """WebDriver終了テスト(ドライバーなし)"""
        scraper = TorScraper()
        # ドライバーがNoneの状態でcloseを呼んでもエラーにならないことを確認
        scraper.close()  # エラーが発生しないことを確認


@pytest.fixture
def mock_scraper():
    """テスト用のモックスクレーパー"""
    scraper = TorScraper()
    scraper.driver = Mock()
    return scraper


class TestTorScraperWithMock:
    """モックを使用したTorScraperのテスト"""

    def test_check_tor_connection_success(self, mock_scraper):
        """Tor接続確認成功テスト"""
        # モックの設定
        mock_scraper.driver.title.lower.return_value = "congratulations - tor browser"
        mock_find_element = Mock()
        mock_find_element.text = "192.168.1.100"
        mock_scraper.driver.find_element.return_value = mock_find_element

        result = mock_scraper.check_tor_connection()

        assert result is True
        mock_scraper.driver.get.assert_called_with("https://check.torproject.org")

    def test_check_tor_connection_failure(self, mock_scraper):
        """Tor接続確認失敗テスト"""
        # モックの設定
        mock_scraper.driver.title.lower.return_value = "error page"

        result = mock_scraper.check_tor_connection()

        assert result is False

    def test_search_duckduckgo(self, mock_scraper):
        """DuckDuckGo検索テスト"""
        # モックの設定
        mock_search_box = Mock()
        mock_search_button = Mock()
        mock_results = [Mock(), Mock(), Mock()]

        for i, result in enumerate(mock_results):
            result.text = f"Search result {i + 1}"

        mock_scraper.driver.find_element.side_effect = [mock_search_button]
        mock_scraper.driver.find_elements.return_value = mock_results

        # WebDriverWaitのモック
        with patch("src.tor_scraper.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = mock_search_box

            mock_scraper.search_duckduckgo("test query")

            # 適切なメソッドが呼ばれたことを確認
            mock_scraper.driver.get.assert_called_with("https://duckduckgo.com")
            mock_search_box.send_keys.assert_called_with("test query")
            mock_search_button.click.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
