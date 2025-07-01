#!/usr/bin/env python3
"""
Docker環境でのファイル保存権限テスト

主要な検証項目:
- ディレクトリ作成とファイル書き込み権限
- XScraperのファイル保存機能
- Docker環境の適切な動作
"""

import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models import Tweet, UserProfile
from src.x_scraper import XScraper


class TestDockerFilePermissions:
    """Docker環境でのファイル権限テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        # 一時ディレクトリを使用して test_reports ディレクトリの作成を避ける
        self.temp_dir = tempfile.mkdtemp(prefix="tor_scraper_test_")
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """各テストメソッドの後にクリーンアップ"""
        # 一時ディレクトリ全体を削除
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_directory_creation_permissions(self):
        """ディレクトリ作成権限のテスト"""
        test_dir = Path(self.temp_dir) / "test_permissions"

        # ディレクトリが存在しない場合は作成
        assert not test_dir.exists()

        # ディレクトリを作成
        test_dir.mkdir(parents=True, exist_ok=True)

        # 作成されたディレクトリの確認
        assert test_dir.exists()
        assert test_dir.is_dir()

        # 権限の確認
        dir_stat = test_dir.stat()
        assert stat.S_ISDIR(dir_stat.st_mode)

    def test_file_write_permissions(self):
        """ファイル書き込み権限のテスト"""
        test_file = self.test_data_dir / "test_write_permissions.json"
        test_data = {"test": "data", "timestamp": "2025-01-01T00:00:00", "docker_test": True}

        # ファイルに書き込み
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        # ファイルが作成されたことを確認
        assert test_file.exists()
        assert test_file.is_file()

        # ファイル権限の確認
        file_stat = test_file.stat()
        assert stat.S_ISREG(file_stat.st_mode)

        # ファイルの内容を確認
        with open(test_file, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data

    def test_current_user_permissions(self):
        """現在のユーザー権限の確認"""
        # ユーザーIDとグループIDを取得
        uid = os.getuid()
        gid = os.getgid()

        print(f"Current UID: {uid}")
        print(f"Current GID: {gid}")

        # Docker環境では appuser (UID 1000) で実行されるはず
        if os.path.exists("/.dockerenv"):
            assert uid == 1000, f"Expected UID 1000 in Docker, got {uid}"

        # 作業ディレクトリの権限確認
        cwd = Path.cwd()
        cwd_stat = cwd.stat()

        print(f"Working directory: {cwd}")
        print(f"Working directory owner UID: {cwd_stat.st_uid}")
        print(f"Working directory owner GID: {cwd_stat.st_gid}")

    def test_data_directory_access(self):
        """dataディレクトリへのアクセステスト"""
        data_dir = Path("data")
        scraping_results_dir = data_dir / "scraping_results"

        # ディレクトリが作成できることを確認
        data_dir.mkdir(parents=True, exist_ok=True)
        scraping_results_dir.mkdir(parents=True, exist_ok=True)

        assert data_dir.exists()
        assert scraping_results_dir.exists()

        # テストファイルの作成
        test_file = scraping_results_dir / "test_data_access.json"
        test_data = {"data_test": True}

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        assert test_file.exists()

        # ファイルの読み取り
        with open(test_file, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data

        # クリーンアップ
        test_file.unlink()

    def test_docker_environment_detection(self):
        """Docker環境の検出と基本設定テスト"""
        is_docker = os.path.exists("/.dockerenv")

        if is_docker:
            print("Running in Docker environment")
            # 環境変数とTorブラウザパスの確認
            tor_browser_path = os.environ.get("TOR_BROWSER_PATH")
            assert tor_browser_path == "/opt/torbrowser"
            assert Path(tor_browser_path).exists()
        else:
            print("Running in local environment")

    @patch("src.x_scraper.create_tor_browser_driver")
    def test_x_scraper_file_saving_permissions(self, mock_driver):
        """XScraperでのファイル保存権限テスト"""
        # モックドライバーを設定
        mock_driver.return_value = Mock()

        # XScraperインスタンスを作成
        scraper = XScraper(tbb_path="/opt/torbrowser", headless=True)

        # データディレクトリが作成されることを確認
        assert scraper.data_dir.exists()

        # テストデータを作成
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

        # ツイートの保存テスト
        success = scraper.save_tweets_to_json(test_tweets, "test_docker_permissions")
        assert success, "Failed to save tweets in Docker environment"

        # 保存されたファイルの確認
        saved_file = scraper.data_dir / "test_docker_permissions.json"
        assert saved_file.exists()

        # ファイル内容の確認
        with open(saved_file, encoding="utf-8") as f:
            loaded_tweets = json.load(f)

        assert len(loaded_tweets) == 2
        assert loaded_tweets[0]["text"] == "Test tweet 1"
        assert loaded_tweets[1]["text"] == "Test tweet 2"

        # プロフィールの保存テスト
        test_profile = UserProfile(
            username="test_user", display_name="Test User", bio="Test bio", followers_count=1000, following_count=500
        )

        success = scraper.save_profile_to_json(test_profile, "test_docker_profile")
        assert success, "Failed to save profile in Docker environment"

        # 保存されたプロフィールファイルの確認
        profile_file = scraper.data_dir / "test_docker_profile.json"
        assert profile_file.exists()

        # プロフィール内容の確認
        with open(profile_file, encoding="utf-8") as f:
            loaded_profile = json.load(f)

        assert loaded_profile["username"] == "test_user"
        assert loaded_profile["display_name"] == "Test User"


if __name__ == "__main__":
    # テストを直接実行する場合
    pytest.main([__file__, "-v"])
