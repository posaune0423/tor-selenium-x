#!/usr/bin/env python3
"""
Data models for X (Twitter) scraper
"""

from dataclasses import dataclass, field
from enum import Enum


class DataType(Enum):
    """スクレイピングデータの種別 - シンプル化版"""

    JSON_DATA = "json_data"  # 全てのスクレイピングデータ(ツイート、プロフィール、検索結果等)
    COOKIES = "cookies"  # セッション用クッキーデータ
    SCREENSHOTS = "screenshots"  # スクリーンショット画像
    LOGS = "logs"  # ログファイル


class ContentType(Enum):
    """コンテンツの種別"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    POLL = "poll"
    RETWEET = "retweet"
    QUOTE_TWEET = "quote_tweet"


@dataclass
class Tweet:
    """Data class for tweet information"""

    id: str | None = None
    text: str = ""
    author: str = ""
    timestamp: str = ""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: str | None = None
    # TypeScript実装に合わせてengagement countsを追加
    reply_count: int = 0
    retweet_count: int = 0
    like_count: int = 0
    impression_count: int | None = None
    media_urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    content_type: ContentType = ContentType.TEXT
    is_retweet: bool = False
    is_reply: bool = False
    parent_tweet_id: str | None = None
    conversation_id: str | None = None
    lang: str | None = None
    source: str | None = None  # Twitter for iPhone, Twitter Web App, etc.


@dataclass
class UserProfile:
    """Data class for user profile information"""

    username: str = ""
    display_name: str = ""
    bio: str = ""
    location: str = ""
    website: str | None = None
    followers_count: int = 0
    following_count: int = 0
    tweets_count: int = 0
    verified: bool = False
    profile_image_url: str | None = None
    banner_image_url: str | None = None
    joined_date: str | None = None
    user_id: str | None = None
    is_protected: bool = False
    is_verified_blue: bool = False  # X Premium verification
    pinned_tweet_id: str | None = None


@dataclass
class SearchResult:
    """検索結果のデータ"""

    query: str
    search_type: str  # "top", "latest", "people", "photos", "videos"
    tweets: list[Tweet] = field(default_factory=list)
    profiles: list[UserProfile] = field(default_factory=list)
    total_results: int = 0
    has_more: bool = False
    next_cursor: str | None = None
