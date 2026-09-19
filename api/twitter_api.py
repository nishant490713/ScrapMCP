"""Controller for Twitter/X data: raw tweets + replies, no analysis.

Uses the third-party TwitterAPI.io service (https://twitterapi.io), which offers
free starter credits and cheap pay-as-you-go pricing since X's official API has
no free read access. Requires TWITTERAPI_IO_KEY.
"""

from typing import Any

import httpx

from env import TWITTERAPI_IO_KEY
from schema.twitter_schema import TwitterGetRepliesParams, TwitterSearchTweetsParams

BASE_URL = "https://api.twitterapi.io"


def _require_api_key() -> str:
    if not TWITTERAPI_IO_KEY:
        raise RuntimeError("TWITTERAPI_IO_KEY is not set. Sign up at https://twitterapi.io and set it as an env var.")
    return TWITTERAPI_IO_KEY


def _normalize_tweet(t: dict[str, Any]) -> dict[str, Any]:
    author = t.get("author") or {}
    return {
        "id": t.get("id") or t.get("tweet_id"),
        "text": t.get("text") or t.get("full_text"),
        "author": author.get("userName") or author.get("username") or t.get("author_username"),
        "created_at": t.get("createdAt") or t.get("created_at"),
        "like_count": t.get("likeCount") or t.get("like_count"),
        "reply_count": t.get("replyCount") or t.get("reply_count"),
        "retweet_count": t.get("retweetCount") or t.get("retweet_count"),
        "url": t.get("url") or t.get("twitterUrl"),
    }


async def _paged_search(query: str, limit: int) -> list[dict[str, Any]]:
    api_key = _require_api_key()
    headers = {"X-API-Key": api_key}
    tweets: list[dict[str, Any]] = []
    cursor = ""

    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(tweets) < limit:
            resp = await client.get(
                f"{BASE_URL}/twitter/tweet/advanced_search",
                params={"query": query, "queryType": "Latest", "cursor": cursor},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            for t in data.get("tweets", []):
                tweets.append(_normalize_tweet(t))
                if len(tweets) >= limit:
                    break

            if not data.get("has_next_page") or not data.get("next_cursor"):
                break
            cursor = data["next_cursor"]

    return tweets[:limit]


async def search_tweets(params: TwitterSearchTweetsParams) -> list[dict[str, Any]]:
    query = params.query
    if params.query_type == "Top" and "min_faves" not in query:
        query = f"{query} min_faves:5"
    return await _paged_search(query, params.limit)


async def get_replies(params: TwitterGetRepliesParams) -> list[dict[str, Any]]:
    query = f"conversation_id:{params.tweet_id} filter:replies"
    return await _paged_search(query, params.limit)
