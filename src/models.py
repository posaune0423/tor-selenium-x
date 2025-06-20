#!/usr/bin/env python3
"""
Data models for X (Twitter) scraper
"""

from dataclasses import dataclass, field


@dataclass
class Tweet:
    """Data class for tweet information"""

    id: str | None = None
    text: str = ""
    author: str = ""
    timestamp: str | None = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: str | None = None
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
    followers_count: int | None = None
    following_count: int | None = None
    tweets_count: int | None = None
    verified: bool = False
    profile_image_url: str | None = None
    banner_image_url: str | None = None
    joined_date: str | None = None
