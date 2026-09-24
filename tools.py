from mcp.server.fastmcp import FastMCP

from api import reddit_api, twitter_api, youtube_api
from schema.reddit_schema import RedditGetCommentsParams, RedditSearchPostsParams
from schema.twitter_schema import TwitterGetRepliesParams, TwitterSearchTweetsParams
from schema.youtube_schema import YoutubeGetCommentsParams, YoutubeGetTranscriptParams, YoutubeSearchVideosParams


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="reddit_search_posts",
        description="Search Reddit for posts matching a query, optionally within one subreddit. Returns raw post data (title, body snippet, score, comment count, permalink) for an agent to read.",
    )
    async def reddit_search_posts(params: RedditSearchPostsParams) -> list[dict]:
        return await reddit_api.search_posts(params)

    @mcp.tool(
        name="reddit_get_comments",
        description="Fetch the comment thread for a Reddit post (by id or URL). Returns raw comment bodies, authors, and scores.",
    )
    async def reddit_get_comments(params: RedditGetCommentsParams) -> list[dict]:
        return await reddit_api.get_comments(params)

    @mcp.tool(
        name="youtube_search_videos",
        description="Search YouTube for videos matching a query. Returns raw video metadata (id, title, channel, description) for an agent to pick videos to pull comments from.",
    )
    async def youtube_search_videos(params: YoutubeSearchVideosParams) -> list[dict]:
        return await youtube_api.search_videos(params)

    @mcp.tool(
        name="youtube_get_comments",
        description="Fetch top-level comments for a YouTube video by video id. Returns raw comment text, author, and like/reply counts.",
    )
    async def youtube_get_comments(params: YoutubeGetCommentsParams) -> list[dict]:
        return await youtube_api.get_comments(params)

    @mcp.tool(
        name="youtube_get_transcript",
        description="Fetch the transcript/captions for a YouTube video by video id. Returns the full transcript text plus timed snippets.",
    )
    async def youtube_get_transcript(params: YoutubeGetTranscriptParams) -> dict:
        return await youtube_api.get_transcript(params)

    @mcp.tool(
        name="twitter_search_tweets",
        description="Search X/Twitter using advanced-search syntax (e.g. 'invoicing software annoying lang:en'). Returns raw tweet text, author, and engagement counts.",
    )
    async def twitter_search_tweets(params: TwitterSearchTweetsParams) -> list[dict]:
        return await twitter_api.search_tweets(params)

    @mcp.tool(
        name="twitter_get_replies",
        description="Fetch replies to a specific tweet by tweet id. Returns raw reply text, author, and engagement counts.",
    )
    async def twitter_get_replies(params: TwitterGetRepliesParams) -> list[dict]:
        return await twitter_api.get_replies(params)
