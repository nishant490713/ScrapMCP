import os

from dotenv import load_dotenv

load_dotenv()

REDDIT_API_KEY = os.environ.get("REDDIT_API_KEY")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

TWITTERAPI_IO_KEY = os.environ.get("TWITTERAPI_IO_KEY")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

MCP_SERVER_SECRET = (os.environ.get("MCP_SERVER_SECRET") or "").strip() or None
PORT = os.environ.get("PORT")
BASE_URL = os.environ.get("BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL")
