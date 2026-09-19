"""Controller for YouTube data: raw video results + top-level comments, no analysis.

Uses the free YouTube Data API v3 (10,000 quota units/day per project).
Requires YOUTUBE_API_KEY.
"""

from typing import Any

import httpx

from env import YOUTUBE_API_KEY
from schema.youtube_schema import YoutubeGetCommentsParams, YoutubeSearchVideosParams

BASE_URL = "https://www.googleapis.com/youtube/v3"


def _require_api_key() -> str:
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not set. Create one in Google Cloud Console and set it as an env var.")
    return YOUTUBE_API_KEY


async def search_videos(params: YoutubeSearchVideosParams) -> list[dict[str, Any]]:
    api_key = _require_api_key()
    query = {
        "part": "snippet",
        "q": params.query,
        "type": "video",
        "order": params.order,
        "maxResults": params.limit,
        "key": api_key,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{BASE_URL}/search", params=query)
        resp.raise_for_status()
        data = resp.json()

    videos = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        videos.append(
            {
                "video_id": item.get("id", {}).get("videoId"),
                "title": snippet.get("title"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "description": snippet.get("description"),
            }
        )
    return videos


async def get_comments(params: YoutubeGetCommentsParams) -> list[dict[str, Any]]:
    api_key = _require_api_key()
    comments: list[dict[str, Any]] = []
    page_token = None

    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(comments) < params.limit:
            query = {
                "part": "snippet",
                "videoId": params.video_id,
                "order": params.order,
                "textFormat": "plainText",
                "maxResults": min(100, params.limit - len(comments)),
                "key": api_key,
            }
            if page_token:
                query["pageToken"] = page_token

            resp = await client.get(f"{BASE_URL}/commentThreads", params=query)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                top = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                comments.append(
                    {
                        "author": top.get("authorDisplayName"),
                        "text": top.get("textDisplay"),
                        "like_count": top.get("likeCount"),
                        "reply_count": item.get("snippet", {}).get("totalReplyCount"),
                        "published_at": top.get("publishedAt"),
                    }
                )
                if len(comments) >= params.limit:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return comments[: params.limit]
