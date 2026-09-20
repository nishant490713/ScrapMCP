"""Entry point: start the Pain Point MCP server."""

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
                auth_header = request.headers.get("Authorization", "")
                bearer_token = auth_header.removeprefix("Bearer ").strip()
                if request.headers.get("X-MCP-Auth") != MCP_SERVER_SECRET and bearer_token != MCP_SERVER_SECRET:
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
