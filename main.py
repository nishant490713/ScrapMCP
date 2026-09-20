"""Entry point: start the Pain Point MCP server.

Locally (no PORT env var), runs over stdio -- the transport an MCP client
like Claude Desktop/Code launches directly as a subprocess.

When hosted (Render sets PORT automatically), runs over Streamable HTTP
instead, guarded by a shared-secret header so random internet traffic can't
spend your API quota/credits.
"""

from env import PORT
from mcp.server.fastmcp import FastMCP

from tools import register_tools

mcp = FastMCP("pain-point-mcp", host="0.0.0.0", port=int(PORT) if PORT else 8000)
register_tools(mcp)


def build_http_app():
    """Streamable HTTP app wrapped with shared-secret auth, for hosting."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    from env import MCP_SERVER_SECRET

    app = mcp.streamable_http_app()

    if MCP_SERVER_SECRET:

        class AuthMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                if request.headers.get("X-MCP-Auth") != MCP_SERVER_SECRET:
                    return JSONResponse({"error": "unauthorized"}, status_code=401)
                return await call_next(request)

        app.add_middleware(AuthMiddleware)

    return app


if __name__ == "__main__":
    if PORT:
        import uvicorn

        uvicorn.run(build_http_app(), host="0.0.0.0", port=int(PORT))
    else:
        mcp.run()
