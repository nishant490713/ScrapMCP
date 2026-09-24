from typing import Literal

from pydantic import BaseModel, Field


class YoutubeSearchVideosParams(BaseModel):
    query: str = Field(..., description="Keywords describing the topic/problem to find relevant videos for.")
    order: Literal["relevance", "date", "viewCount", "rating"] = Field(
        "relevance", description="How to order the returned videos."
    )
    limit: int = Field(10, ge=1, le=50, description="Max number of videos to return.")


class YoutubeGetCommentsParams(BaseModel):
    video_id: str = Field(..., description="YouTube video id, e.g. 'dQw4w9WgXcQ' (from a URL or from youtube_search_videos).")
    order: Literal["relevance", "time"] = Field(
        "relevance", description="How to order the returned top-level comments."
    )
    limit: int = Field(50, ge=1, le=200, description="Max number of top-level comments to return.")


class YoutubeGetTranscriptParams(BaseModel):
    video_id: str = Field(..., description="YouTube video id, e.g. 'dQw4w9WgXcQ' (from a URL or from youtube_search_videos).")
    languages: list[str] = Field(
        default_factory=lambda: ["en"],
        description="Preferred transcript language codes in priority order, e.g. ['en', 'en-US']. Falls back automatically if none are available.",
    )
