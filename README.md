# Pain Point MCP

An MCP server that fetches **raw** posts/comments/replies from Reddit, YouTube,
and X/Twitter, so a connected AI agent (e.g. Claude) can read them, understand
the problems people are describing, and brief you on potential product ideas.

The server does no summarization itself — it's a data-fetching layer. All
reading/understanding happens in the AI client you connect it to.

## Layout

- `main.py` — starts the MCP server.
- `tools.py` — registers each MCP tool, wiring schema -> api controller.
- `api/` — one file per source, does the actual HTTP calls (`reddit_api.py`, `youtube_api.py`, `twitter_api.py`).
- `schema/` — pydantic input schemas for each tool, one file per source.

## Tools

| Tool | Source | Description |
|---|---|---|
| `reddit_search_posts` | Reddit | Search posts by query, optional subreddit |
| `reddit_get_comments` | Reddit | Fetch a post's comment thread |
| `youtube_search_videos` | YouTube | Search videos by query |
| `youtube_get_comments` | YouTube | Fetch a video's top-level comments |
| `twitter_search_tweets` | X/Twitter | Search tweets by advanced-search query |
| `twitter_get_replies` | X/Twitter | Fetch replies to a tweet |

## Setup

1. Create a virtualenv and install deps (Python 3.10+; 3.11 recommended):

   ```
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in the keys you have. See below for
   how to get each one for free.

3. Run the server directly to sanity-check it starts:

   ```
   python main.py
   ```

4. Point your MCP client (e.g. Claude Code / Claude Desktop) at this server,
   typically via a config entry like:

   ```json
   {
     "mcpServers": {
       "pain-point-mcp": {
         "command": "C:\\path\\to\\Web-MCP\\.venv\\Scripts\\python.exe",
         "args": ["C:\\path\\to\\Web-MCP\\main.py"]
       }
     }
   }
   ```

## Getting API keys (all free to start)

- **Reddit** — free for non-commercial use, 100 requests/min once approved.
  Create an app at https://www.reddit.com/prefs/apps. Reddit currently
  requires manual approval for new OAuth apps, so this can take a while.
  **`REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` are effectively required**: the
  code falls back to Reddit's public `.json` endpoints when they're unset,
  but as of testing (Sep 2026) Reddit now blocks that fallback outright
  (403, anti-bot challenge page) — this matches Reddit's ongoing crackdown
  on unauthenticated API access. Until your app is approved, Reddit tools
  won't return data.
- **YouTube** — genuinely free, 10,000 quota units/day. Enable "YouTube Data
  API v3" in a Google Cloud project and create an API key:
  https://console.cloud.google.com/apis/library/youtube.googleapis.com
- **Twitter/X** — via [twitterapi.io](https://twitterapi.io) (third-party,
  since X's official API has no free read access). Sign up with just an
  email for ~$1 of free trial credit (~6,000 calls), then top up cents at a
  time (~$0.15–0.20 per 1,000 tweets) if you need more.

## Notes / limitations

- Reddit's public `.json` fallback and TwitterAPI.io are third-party paths
  with their own rate limits and terms — fine for personal research, treat
  accordingly for anything commercial.
- `twitter_get_replies` uses `conversation_id:<tweet_id> filter:replies` under
  the hood, matching X's own advanced-search syntax.
