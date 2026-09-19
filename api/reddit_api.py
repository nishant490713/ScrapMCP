"""Controller for Reddit data: raw posts + comments, no analysis.

Uses Reddit's free "application-only" OAuth (client_credentials grant) when
REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are set, and falls back to Reddit's
public read-only .json endpoints otherwise (lower, unofficial rate limits).
"""

import re
import time
from typing import Any, Optional

import httpx

from env import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from schema.reddit_schema import RedditGetCommentsParams, RedditSearchPostsParams

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


async def _get_access_token(client: httpx.AsyncClient) -> Optional[str]:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    resp = await client.post(
        "https://www.reddit.com/api/v1/access_token",
        data={"grant_type": "client_credentials"},
        auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
        headers={"User-Agent": REDDIT_USER_AGENT},
    )
    resp.raise_for_status()
    payload = resp.json()

    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = time.time() + payload.get("expires_in", 3600) - 60
    return _token_cache["access_token"]


async def _reddit_get(client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
    token = await _get_access_token(client)

    if token:
        url = f"https://oauth.reddit.com{path}"
        headers = {"User-Agent": REDDIT_USER_AGENT, "Authorization": f"Bearer {token}"}
    else:
        url = f"https://www.reddit.com{path}.json"
        headers = {"User-Agent": REDDIT_USER_AGENT}

    resp = await client.get(url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()


def _extract_post_id(post_id_or_url: str) -> str:
    """Accepts a raw id36 (e.g. '1abcde') or a full Reddit post URL/permalink."""
    match = re.search(r"/comments/([a-z0-9]+)", post_id_or_url)
    if match:
        return match.group(1)
    return post_id_or_url.strip("/")


async def search_posts(params: RedditSearchPostsParams) -> list[dict[str, Any]]:
    path = f"/r/{params.subreddit}/search" if params.subreddit else "/search"
    query: dict[str, Any] = {
        "q": params.query,
        "sort": params.sort,
        "t": params.time_filter,
        "limit": params.limit,
        "restrict_sr": 1 if params.subreddit else 0,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        data = await _reddit_get(client, path, query)

    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        posts.append(
            {
                "id": d.get("id"),
                "title": d.get("title"),
                "selftext": (d.get("selftext") or "")[:1500],
                "subreddit": d.get("subreddit"),
                "author": d.get("author"),
                "score": d.get("score"),
                "num_comments": d.get("num_comments"),
                "created_utc": d.get("created_utc"),
                "permalink": f"https://www.reddit.com{d.get('permalink', '')}",
                "url": d.get("url"),
            }
        )
    return posts


async def get_comments(params: RedditGetCommentsParams) -> list[dict[str, Any]]:
    post_id = _extract_post_id(params.post_id)
    path = f"/comments/{post_id}"
    query = {"limit": params.limit, "depth": 5, "sort": "top"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        data = await _reddit_get(client, path, query)

    comments: list[dict[str, Any]] = []

    def walk(children: list[dict[str, Any]]) -> None:
        for child in children:
            if len(comments) >= params.limit:
                return
            if child.get("kind") != "t1":
                continue
            d = child.get("data", {})
            comments.append(
                {
                    "id": d.get("id"),
                    "author": d.get("author"),
                    "body": d.get("body"),
                    "score": d.get("score"),
                    "created_utc": d.get("created_utc"),
                    "depth": d.get("depth"),
                }
            )
            replies = d.get("replies")
            if isinstance(replies, dict):
                walk(replies.get("data", {}).get("children", []))

    if isinstance(data, list) and len(data) > 1:
        walk(data[1].get("data", {}).get("children", []))

    return comments[: params.limit]
