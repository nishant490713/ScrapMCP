from typing import Literal

from pydantic import BaseModel, Field


class TwitterSearchTweetsParams(BaseModel):
    query: str = Field(
        ...,
        description=(
            "X/Twitter advanced-search query, e.g. 'invoicing software annoying' or "
            "'\"billing software\" lang:en -filter:retweets'. Same syntax as x.com/search-advanced."
        ),
    )
    query_type: Literal["Latest", "Top"] = Field("Latest", description="Whether to fetch latest or top tweets.")
    limit: int = Field(20, ge=1, le=100, description="Max number of tweets to return.")


class TwitterGetRepliesParams(BaseModel):
    tweet_id: str = Field(..., description="Id of the tweet to fetch replies for.")
    limit: int = Field(20, ge=1, le=100, description="Max number of replies to return.")
