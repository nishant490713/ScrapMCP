from typing import Any

import httpx

from env import REDDIT_API_KEY
from schema.reddit_schema import RedditGetCommentsParams, RedditSearchPostsParams

APIFY_RUN_URL = "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items"


def _require_api_key() -> str:
    if not REDDIT_API_KEY:
        raise RuntimeError("REDDIT_API_KEY is not set. It's an Apify token -- sign up at https://apify.com and set it as an env var.")
    return REDDIT_API_KEY


async def _run_actor(actor_input: dict[str, Any]) -> list[dict[str, Any]]:
    api_key = _require_api_key()
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            APIFY_RUN_URL,
            params={"token": api_key, "timeout": 280},
            json=actor_input,
        )
        resp.raise_for_status()
        return resp.json()


def _normalize_post(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("parsedId") or item.get("id"),
        "title": item.get("title"),
        "selftext": (item.get("body") or "")[:1500],
        "subreddit": item.get("parsedCommunityName") or item.get("communityName"),
        "author": item.get("username"),
        "score": item.get("upVotes"),
        "num_comments": item.get("numberOfComments"),
        "created_at": item.get("createdAt"),
        "permalink": item.get("url"),
        "external_url": item.get("link"),
    }


def _normalize_comment(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("parsedId") or item.get("id"),
        "author": item.get("username"),
        "body": item.get("body"),
        "score": item.get("upVotes"),
        "created_at": item.get("createdAt"),
        "depth": item.get("depth"),
    }


async def search_posts(params: RedditSearchPostsParams) -> list[dict[str, Any]]:
    actor_input: dict[str, Any] = {
        "searches": [params.query],
        "searchPosts": True,
        "searchComments": False,
        "searchCommunities": False,
        "searchUsers": False,
        "sort": params.sort,
        "maxItems": params.limit,
        "skipComments": True,
    }
    if params.subreddit:
        actor_input["searchCommunityName"] = params.subreddit
    if params.time_filter != "all":
        actor_input["time"] = params.time_filter

    items = await _run_actor(actor_input)
    posts = [_normalize_post(i) for i in items if i.get("dataType", "post") == "post"]
    return posts[: params.limit]


async def get_comments(params: RedditGetCommentsParams) -> list[dict[str, Any]]:
    if not params.post_id.startswith("http"):
        raise RuntimeError(
            "post_id must be the full post URL/permalink (as returned in 'permalink' by reddit_search_posts), not a bare id."
        )

    actor_input = {
        "startUrls": [{"url": params.post_id}],
        "skipComments": False,
        "maxComments": params.limit,
        "maxItems": params.limit + 1,
    }

    items = await _run_actor(actor_input)
    comments = [_normalize_comment(i) for i in items if i.get("dataType") == "comment"]
    return comments[: params.limit]
