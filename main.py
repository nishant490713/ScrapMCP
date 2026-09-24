from env import BASE_URL, MCP_SERVER_SECRET, PORT
from mcp.server.fastmcp import FastMCP

from tools import register_tools

if BASE_URL and MCP_SERVER_SECRET:
    from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions

    from oauth_provider import SingleUserOAuthProvider

    from login import register_login_route

    oauth_provider = SingleUserOAuthProvider()
    mcp = FastMCP(
        "pain-point-mcp",
        host="0.0.0.0",
        port=int(PORT) if PORT else 8000,
        auth_server_provider=oauth_provider,
        auth=AuthSettings(
            issuer_url=BASE_URL,
            resource_server_url=f"{BASE_URL.rstrip('/')}/mcp",
            client_registration_options=ClientRegistrationOptions(enabled=True),
            revocation_options=RevocationOptions(enabled=True),
            validate_token_resource=False,
        ),
    )
    register_login_route(mcp, oauth_provider)

else:
    mcp = FastMCP("pain-point-mcp", host="0.0.0.0", port=int(PORT) if PORT else 8000)

register_tools(mcp)


def build_http_app():
    app = mcp.streamable_http_app()

    if MCP_SERVER_SECRET:
        from starlette.datastructures import MutableHeaders

        class StaticSecretMiddleware:
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                if scope["type"] == "http":
                    headers = MutableHeaders(scope=scope)
                    if "authorization" not in headers:
                        token = headers.get("x-mcp-auth")
                        if not token:
                            query_string = scope.get("query_string", b"").decode()
                            from urllib.parse import parse_qs

                            token = (parse_qs(query_string).get("key") or [None])[0]
                        if token:
                            headers["authorization"] = f"Bearer {token}"
                await self.app(scope, receive, send)

        app.add_middleware(StaticSecretMiddleware)

    return app


if __name__ == "__main__":
    if PORT:
        import uvicorn

        uvicorn.run(build_http_app(), host="0.0.0.0", port=int(PORT))
    else:
        mcp.run()
