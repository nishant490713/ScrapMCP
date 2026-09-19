"""Entry point: start the Pain Point MCP server."""

import env  # noqa: F401  (loads .env before anything reads os.environ)
from mcp.server.fastmcp import FastMCP

from tools import register_tools

mcp = FastMCP("pain-point-mcp")
register_tools(mcp)


if __name__ == "__main__":
    mcp.run()
