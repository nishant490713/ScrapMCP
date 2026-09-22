from env import MCP_SERVER_SECRET

LOGIN_FORM = """
<form method="post" style="font-family:sans-serif;max-width:320px;margin:80px auto">
  <h3>pain-point-mcp</h3>
  <input type="hidden" name="request_id" value="{request_id}">
  <input type="password" name="secret" placeholder="Server secret" autofocus
         style="width:100%;padding:8px;box-sizing:border-box">
  <button type="submit" style="width:100%;padding:8px;margin-top:8px">Authorize</button>
  <p style="color:red">{error}</p>
</form>
"""


def register_login_route(mcp, oauth_provider):
    @mcp.custom_route("/login", methods=["GET", "POST"])
    async def login(request):
        from starlette.responses import HTMLResponse, RedirectResponse

        request_id = request.query_params.get("request_id", "")
        if request.method == "GET":
            return HTMLResponse(LOGIN_FORM.format(request_id=request_id, error=""))

        form = await request.form()
        if str(form.get("secret", "")).strip() != MCP_SERVER_SECRET:
            return HTMLResponse(LOGIN_FORM.format(request_id=request_id, error="Wrong secret"), status_code=401)

        redirect_uri = oauth_provider.complete_login(str(form.get("request_id", "")))
        if redirect_uri is None:
            return HTMLResponse("Request expired", status_code=400)
        return RedirectResponse(redirect_uri, status_code=302)
