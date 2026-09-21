import secrets
import time

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from env import MCP_SERVER_SECRET

TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30
CODE_TTL_SECONDS = 600


class SingleUserOAuthProvider(OAuthAuthorizationServerProvider):
    def __init__(self):
        self.clients: dict[str, OAuthClientInformationFull] = {}
        self.pending: dict[str, tuple[OAuthClientInformationFull, AuthorizationParams]] = {}
        self.auth_codes: dict[str, AuthorizationCode] = {}
        self.access_tokens: dict[str, AccessToken] = {}
        self.refresh_tokens: dict[str, RefreshToken] = {}

    async def get_client(self, client_id):
        return self.clients.get(client_id)

    async def register_client(self, client_info):
        self.clients[client_info.client_id] = client_info

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        request_id = secrets.token_urlsafe(16)
        self.pending[request_id] = (client, params)
        return f"/login?request_id={request_id}"

    def complete_login(self, request_id: str) -> str | None:
        pending = self.pending.pop(request_id, None)
        if pending is None:
            return None
        client, params = pending
        code = secrets.token_urlsafe(32)
        self.auth_codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + CODE_TTL_SECONDS,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
        )
        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    async def load_authorization_code(self, client, authorization_code):
        code = self.auth_codes.get(authorization_code)
        if code and code.client_id == client.client_id:
            return code
        return None

    async def exchange_authorization_code(self, client, authorization_code):
        self.auth_codes.pop(authorization_code.code, None)
        return self._issue_token(client.client_id, authorization_code.scopes, authorization_code.resource)

    async def load_refresh_token(self, client, refresh_token):
        token = self.refresh_tokens.get(refresh_token)
        if token and token.client_id == client.client_id:
            return token
        return None

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        self.refresh_tokens.pop(refresh_token.token, None)
        return self._issue_token(client.client_id, scopes or refresh_token.scopes, refresh_token.resource)

    def _issue_token(self, client_id, scopes, resource):
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + TOKEN_TTL_SECONDS
        self.access_tokens[access_token] = AccessToken(
            token=access_token, client_id=client_id, scopes=scopes, expires_at=expires_at, resource=resource
        )
        self.refresh_tokens[refresh_token] = RefreshToken(
            token=refresh_token, client_id=client_id, scopes=scopes, resource=resource
        )
        return OAuthToken(
            access_token=access_token,
            token_type="bearer",
            expires_in=TOKEN_TTL_SECONDS,
            refresh_token=refresh_token,
            scope=" ".join(scopes),
        )

    async def load_access_token(self, token):
        if token == MCP_SERVER_SECRET:
            return AccessToken(token=token, client_id="static", scopes=[])
        access_token = self.access_tokens.get(token)
        if access_token and access_token.expires_at and access_token.expires_at < time.time():
            self.access_tokens.pop(token, None)
            return None
        return access_token

    async def revoke_token(self, token):
        self.access_tokens.pop(token.token, None)
        self.refresh_tokens.pop(token.token, None)
