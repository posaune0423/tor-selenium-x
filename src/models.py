#!/usr/bin/env python3
"""
Data models for X (Twitter) scraper
"""

from dataclasses import dataclass, field


@dataclass
class XCredentials:
    """X (Twitter) login credentials"""

    email: str
    password: str
    username: str


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


@dataclass
class SessionState:
    """Session management state"""

    is_logged_in: bool = False
    current_user: str | None = None
    session_cookies: list[dict] = field(default_factory=list)
    last_activity: str | None = None
    login_timestamp: str | None = None
