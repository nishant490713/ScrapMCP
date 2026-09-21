"""Centralized environment variable access. Loads .env once on import."""

import os

from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "pain-point-mcp/0.1 (by u/unknown)")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

TWITTERAPI_IO_KEY = os.environ.get("TWITTERAPI_IO_KEY")

MCP_SERVER_SECRET = os.environ.get("MCP_SERVER_SECRET")
PORT = os.environ.get("PORT")
BASE_URL = os.environ.get("BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL")
