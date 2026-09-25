from typing import Literal, Optional

from pydantic import BaseModel, Field


class RedditSearchPostsParams(BaseModel):
    query: str = Field(..., description="Keywords describing the problem/pain point to search for, e.g. 'invoicing software is a pain'")
    subreddit: Optional[str] = Field(
        None, description="Restrict the search to one subreddit, without the 'r/' prefix, e.g. 'smallbusiness'. Omit to search all of Reddit."
    )
    sort: Literal["relevance", "hot", "top", "new", "comments"] = Field(
        "relevance", description="How to sort results."
    )
    time_filter: Literal["hour", "day", "week", "month", "year", "all"] = Field(
        "year", description="Only return posts from within this time window."
    )
    limit: int = Field(25, ge=1, le=100, description="Max number of posts to return.")


class RedditGetCommentsParams(BaseModel):
    post_id: str = Field(
        ..., description="Full Reddit post URL/permalink, as returned in 'permalink' by reddit_search_posts."
    )
    limit: int = Field(50, ge=1, le=200, description="Max number of comments to return.")
