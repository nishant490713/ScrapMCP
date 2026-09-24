"""Controller for Twitter/X data: raw tweets + replies, no analysis.

Primary source is the third-party TwitterAPI.io service (https://twitterapi.io),
since X's official API has no free read access. Requires TWITTERAPI_IO_KEY.

If that fails (unset key, rate limit, outage) and APIFY_TOKEN is set, falls back
to the apidojo/tweet-scraper actor on Apify (https://apify.com), which offers
$5/month in free platform credits.
"""

from typing import Any

import httpx

from env import APIFY_TOKEN, TWITTERAPI_IO_KEY
from schema.twitter_schema import TwitterGetRepliesParams, TwitterSearchTweetsParams

TWITTERAPI_IO_BASE_URL = "https://api.twitterapi.io"
APIFY_RUN_URL = "https://api.apify.com/v2/acts/apidojo~tweet-scraper/run-sync-get-dataset-items"


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


async def _twitterapi_io_search(query: str, limit: int) -> list[dict[str, Any]]:
    if not TWITTERAPI_IO_KEY:
        raise RuntimeError("TWITTERAPI_IO_KEY is not set.")

    headers = {"X-API-Key": TWITTERAPI_IO_KEY}
    tweets: list[dict[str, Any]] = []
    cursor = ""

    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(tweets) < limit:
            resp = await client.get(
                f"{TWITTERAPI_IO_BASE_URL}/twitter/tweet/advanced_search",
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


async def _apify_search(actor_input: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN is not set.")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            APIFY_RUN_URL,
            params={"token": APIFY_TOKEN, "timeout": 100},
            json={**actor_input, "maxItems": limit},
        )
        resp.raise_for_status()
        items = resp.json()

    return [_normalize_tweet(t) for t in items[:limit]]


async def search_tweets(params: TwitterSearchTweetsParams) -> list[dict[str, Any]]:
    query = params.query
    if params.query_type == "Top" and "min_faves" not in query:
        query = f"{query} min_faves:5"

    try:
        return await _twitterapi_io_search(query, params.limit)
    except (RuntimeError, httpx.HTTPError):
        return await _apify_search(
            {"searchTerms": [params.query], "sort": params.query_type}, params.limit
        )


async def get_replies(params: TwitterGetRepliesParams) -> list[dict[str, Any]]:
    query = f"conversation_id:{params.tweet_id} filter:replies"

    try:
        return await _twitterapi_io_search(query, params.limit)
    except (RuntimeError, httpx.HTTPError):
        return await _apify_search({"conversationIds": [params.tweet_id]}, params.limit)
