#!/usr/bin/env python3
"""
Simplified data storage utilities for scraping results
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from src.constants import JSON_DATA_DIR
from src.models import SearchResult, Tweet, UserProfile


def ensure_directory_exists(directory: Path) -> None:
    """
    ディレクトリの存在を確認し、必要に応じて作成

    Args:
        directory: 作成するディレクトリパス
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {directory.resolve()}")
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise


def generate_filename(data_type: str, target: str | None = None, query: str | None = None) -> str:
    """
    シンプルなファイル名生成

    Args:
        data_type: データの種別
        target: 対象ユーザーまたはクエリ
        query: 検索クエリ

    Returns:
        str: 生成されたファイル名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parts = [data_type, timestamp]

    if target:
        # ファイル名に使用できない文字を置換
        safe_target = target.replace("@", "").replace("/", "_").replace("\\", "_")[:30]
        parts.insert(1, safe_target)

    if query:
        # クエリを安全なファイル名に変換
        safe_query = query.replace(" ", "_").replace("/", "_").replace("\\", "_")[:30]
        parts.insert(-1, safe_query)

    return "_".join(parts) + ".json"


def save_json_data(
    data: Any,
    data_type: str = "scraping_data",
    target: str | None = None,
    query: str | None = None,
    filename: str | None = None,
) -> bool:
    """
    汎用的なJSONデータ保存機能

    Args:
        data: 保存するデータ
        data_type: データの種別
        target: 対象ユーザー
        query: 検索クエリ
        filename: カスタムファイル名

    Returns:
        bool: 保存成功の場合True
    """
    try:
        # ディレクトリを確保
        ensure_directory_exists(JSON_DATA_DIR)

        # ファイル名を生成
        if filename is None:
            final_filename = generate_filename(data_type, target, query)
        else:
            final_filename = filename if filename.endswith(".json") else f"{filename}.json"

        # ファイルパス
        file_path = JSON_DATA_DIR / final_filename

        # データをシリアライズ可能な形式に変換
        serialized_data = _serialize_data(data)

        # メタデータを追加
        save_data = {
            "metadata": {
                "data_type": data_type,
                "target": target,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "total_items": len(serialized_data) if isinstance(serialized_data, list) else 1,
            },
            "data": serialized_data,
        }

        # JSONとして保存
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Data saved: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        return False


def _serialize_data(data: Any) -> Any:
    """
    データをJSON serializable形式に変換

    Args:
        data: 変換するデータ

    Returns:
        Any: JSON serializable形式のデータ
    """
    if hasattr(data, "__dict__"):
        # dataclassの場合
        result = {}
        for key, value in data.__dict__.items():
            if hasattr(value, "value"):  # Enum
                result[key] = value.value
            elif isinstance(value, list):
                result[key] = [_serialize_data(item) for item in value]
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [_serialize_data(item) for item in data]
    elif hasattr(data, "value"):  # Enum
        return data.value
    else:
        return data


def load_json_data(file_path: Path) -> dict[str, Any] | None:
    """
    JSONデータファイルを読み込み

    Args:
        file_path: ファイルパス

    Returns:
        dict | None: 読み込んだデータ、失敗時はNone
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load data from {file_path}: {e}")
        return None


def list_json_files() -> list[Path]:
    """
    保存されたJSONファイルのリストを取得

    Returns:
        list[Path]: ファイルパスのリスト(新しい順)
    """
    try:
        if not JSON_DATA_DIR.exists():
            return []

        json_files = list(JSON_DATA_DIR.glob("*.json"))
        # 更新日時順でソート(新しい順)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return json_files

    except Exception as e:
        logger.error(f"Failed to list JSON files: {e}")
        return []


# 後方互換性のためのヘルパー関数
def save_tweets(
    tweets: list[Tweet], target_user: str | None = None, query: str | None = None, filename: str | None = None
) -> bool:
    """ツイートデータを保存(後方互換性)"""
    return save_json_data(tweets, "tweets", target_user, query, filename)


def save_profiles(profiles: list[UserProfile], target_user: str | None = None, filename: str | None = None) -> bool:
    """プロフィールデータを保存(後方互換性)"""
    return save_json_data(profiles, "profiles", target_user, None, filename)


def save_search_results(search_result: SearchResult, filename: str | None = None) -> bool:
    """検索結果を保存(後方互換性)"""
    return save_json_data(search_result, "search_results", None, search_result.query, filename)
