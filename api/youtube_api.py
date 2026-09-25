from typing import Any

import httpx

from env import YOUTUBE_API_KEY, YOUTUBE_TRANSCRIPT_API_KEY
from schema.youtube_schema import YoutubeGetCommentsParams, YoutubeGetTranscriptParams, YoutubeSearchVideosParams

BASE_URL = "https://www.googleapis.com/youtube/v3"
TRANSCRIPT_ACTOR_URL = "https://api.apify.com/v2/acts/pintostudio~youtube-transcript-scraper/run-sync-get-dataset-items"


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


async def get_transcript(params: YoutubeGetTranscriptParams) -> dict[str, Any]:
    if not YOUTUBE_TRANSCRIPT_API_KEY:
        raise RuntimeError(
            "YOUTUBE_TRANSCRIPT_API_KEY is not set. It's an Apify token -- sign up at https://apify.com and set it as an env var."
        )

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            TRANSCRIPT_ACTOR_URL,
            params={"token": YOUTUBE_TRANSCRIPT_API_KEY, "timeout": 100},
            json={
                "videoUrl": f"https://www.youtube.com/watch?v={params.video_id}",
                "targetLanguage": params.languages[0] if params.languages else "en",
            },
        )
        resp.raise_for_status()
        items = resp.json()

    if not items or items[0].get("error"):
        raise RuntimeError(f"No transcript available for video {params.video_id}.")

    item = items[0]
    segments = item.get("data") or item.get("transcript") or item.get("segments") or []

    return {
        "video_id": params.video_id,
        "text": " ".join(s.get("text", "") for s in segments) if segments else item.get("text") or item.get("fullText"),
        "snippets": [
            {"text": s.get("text"), "start": s.get("offset") or s.get("start"), "duration": s.get("duration")}
            for s in segments
        ],
    }
