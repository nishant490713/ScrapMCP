import re
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
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            APIFY_RUN_URL,
            params={"token": api_key, "timeout": 100},
            json=actor_input,
        )
        resp.raise_for_status()
        return resp.json()


def _extract_post_id(post_id_or_url: str) -> str:
    match = re.search(r"/comments/([a-z0-9]+)", post_id_or_url)
    if match:
        return match.group(1)
    return post_id_or_url.strip("/")


def _normalize_post(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id") or item.get("postId"),
        "title": item.get("title"),
        "selftext": (item.get("body") or item.get("text") or item.get("selftext") or "")[:1500],
        "subreddit": item.get("communityName") or item.get("subreddit"),
        "author": item.get("username") or item.get("author"),
        "score": item.get("upVotes") or item.get("score"),
        "num_comments": item.get("numberOfComments") or item.get("numComments"),
        "created_utc": item.get("createdAt") or item.get("created_utc"),
        "permalink": item.get("url") or item.get("permalink"),
        "url": item.get("link") or item.get("url"),
    }


def _normalize_comment(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id") or item.get("commentId"),
        "author": item.get("username") or item.get("author"),
        "body": item.get("body") or item.get("text"),
        "score": item.get("upVotes") or item.get("score"),
        "created_utc": item.get("createdAt") or item.get("created_utc"),
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
    post_id = _extract_post_id(params.post_id)
    url = params.post_id if params.post_id.startswith("http") else f"https://www.reddit.com/comments/{post_id}"

    actor_input = {
        "startUrls": [{"url": url}],
        "skipComments": False,
        "maxComments": params.limit,
        "maxItems": params.limit + 1,
    }

    items = await _run_actor(actor_input)
    comments = [_normalize_comment(i) for i in items if i.get("dataType") == "comment"]
    return comments[: params.limit]
