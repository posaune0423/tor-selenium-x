#!/usr/bin/env python3
"""
Docker環境でのファイル保存権限テスト(シンプル化版)

主要な検証項目:
- ディレクトリ作成とファイル書き込み権限
- XScraperのファイル保存機能
- Docker環境の適切な動作
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models import Tweet, UserProfile
from src.utils import CookieManager
from src.x_scraper import XScraper


class TestDockerFilePermissions:
    """Docker環境でのファイル権限テスト(シンプル化版)"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.temp_dir = tempfile.mkdtemp(prefix="tor_scraper_test_")
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """各テストメソッドの後にクリーンアップ"""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_basic_file_permissions(self):
        """基本的なファイル作成・書き込み権限のテスト"""
        # ディレクトリ作成テスト
        test_dir = Path(self.temp_dir) / "test_permissions"
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists()
        assert test_dir.is_dir()

        # ファイル作成・書き込みテスト
        test_file = test_dir / "test_write.json"
        test_data = {"test": "data", "timestamp": "2025-01-01T00:00:00", "docker_test": True}

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        assert test_file.exists()
        assert test_file.is_file()

        # ファイル内容確認
        with open(test_file, encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_docker_environment_detection(self):
        """Docker環境の検出と基本設定テスト"""
        is_docker = os.path.exists("/.dockerenv")
        uid = os.getuid()
        gid = os.getgid()

        print(f"Current UID: {uid}, GID: {gid}")
        print(f"Docker environment: {is_docker}")

        if is_docker:
            # Docker環境では appuser (UID 1000) で実行されるはず
            assert uid == 1000, f"Expected UID 1000 in Docker, got {uid}"

            # Tor Browser パスの確認
            tor_browser_path = os.environ.get("TOR_BROWSER_PATH")
            assert tor_browser_path == "/opt/torbrowser"
            assert Path(tor_browser_path).exists()

    @patch("src.x_scraper.create_tor_browser_driver")
    def test_x_scraper_file_saving(self, mock_driver):
        """XScraperでのファイル保存機能テスト"""
        # モックドライバー設定
        mock_driver.return_value = Mock()

        # XScraperインスタンス作成
        scraper = XScraper(tbb_path="/opt/torbrowser", headless=True)
        assert scraper.data_dir.exists()

        # テストツイートデータ
        test_tweets = [
            Tweet(
                text="Test tweet 1",
                author="test_user1",
                likes=10,
                retweets=5,
                replies=2,
                timestamp="2025-01-01T00:00:00",
            ),
            Tweet(
                text="Test tweet 2",
                author="test_user2",
                likes=20,
                retweets=10,
                replies=4,
                timestamp="2025-01-01T01:00:00",
            ),
        ]

        # ツイート保存テスト
        success = scraper.save_tweets_to_json(test_tweets, "test_docker_permissions")
        assert success, "Failed to save tweets in Docker environment"

        # 保存ファイルの確認
        saved_files = list(scraper.data_dir.glob("test_docker_permissions*"))
        assert len(saved_files) > 0, f"No files found in {scraper.data_dir}"

        saved_file = saved_files[0]
        assert saved_file.exists()

        # ファイル内容の確認
        with open(saved_file, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert "data" in loaded_data
        assert "metadata" in loaded_data
        tweets_data = loaded_data["data"]
        assert len(tweets_data) == 2
        assert tweets_data[0]["text"] == "Test tweet 1"

        # プロフィール保存テスト
        test_profile = UserProfile(
            username="test_user", display_name="Test User", bio="Test bio", followers_count=1000, following_count=500
        )

        success = scraper.save_profile_to_json(test_profile, "test_docker_profile")
        assert success, "Failed to save profile in Docker environment"

        # プロフィールファイルの確認
        profile_files = list(scraper.data_dir.glob("test_docker_profile*"))
        assert len(profile_files) > 0, f"No profile files found in {scraper.data_dir}"

        profile_file = profile_files[0]
        assert profile_file.exists()

        with open(profile_file, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert "data" in loaded_data
        profile_data = loaded_data["data"][0]
        assert profile_data["username"] == "test_user"

    def test_cookie_manager_basic_functionality(self):
        """CookieManagerの基本機能テスト(シンプル化版)"""
        test_identifier = "test_user_permissions"
        cookie_manager = CookieManager(test_identifier)

        # テストクッキー
        test_cookies = [
            {
                "name": "auth_token",
                "value": "test_auth_token_123",
                "domain": ".twitter.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "expiry": 2000000000,
            }
        ]

        try:
            # 保存テスト
            save_result = cookie_manager.save_cookies(test_cookies)
            assert save_result, "Cookie save should succeed"
            assert cookie_manager.cookie_file.exists(), "Cookie file should be created"

            # 読み込みテスト
            loaded_cookies = cookie_manager.load_cookies()
            assert len(loaded_cookies) > 0, "Should load cookies"

            loaded_names = [cookie["name"] for cookie in loaded_cookies]
            assert "auth_token" in loaded_names, "auth_token should be loaded"
            assert cookie_manager.has_valid_cookies(), "Should have valid cookies"

        finally:
            # クリーンアップ
            if cookie_manager.cookie_file.exists():
                cookie_manager.cookie_file.unlink()
            if cookie_manager.backup_file.exists():
                cookie_manager.backup_file.unlink()


if __name__ == "__main__":
    # テストを直接実行する場合
    pytest.main([__file__, "-v"])
