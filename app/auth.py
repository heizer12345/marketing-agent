"""Auth middleware and login router for Sourcy Marketing Agent."""

import os
from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin123")
DEV_MODE = os.getenv("DEV_MODE", "0") == "1"
# Prototype / Vercel: allow v2 REST + WS without session login (set on backend host only).
V2_PUBLIC_ACCESS = os.getenv("V2_PUBLIC_ACCESS", "0") == "1"

_PASS_THROUGH = {"/login", "/logout", "/_health"}

login_router = APIRouter()

_LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Sourcy — Login</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #0f0f0f; display: flex;
           align-items: center; justify-content: center; min-height: 100vh; }}
    .card {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px;
            padding: 40px; width: 360px; }}
    .logo {{ font-size: 24px; font-weight: 700; color: #fff; margin-bottom: 8px; }}
    .sub {{ color: #888; font-size: 13px; margin-bottom: 32px; }}
    label {{ display: block; font-size: 12px; color: #aaa; margin-bottom: 6px; }}
    input {{ width: 100%; background: #111; border: 1px solid #333; border-radius: 8px;
            padding: 10px 14px; color: #fff; font-size: 14px; outline: none; }}
    input:focus {{ border-color: #555; }}
    .btn {{ width: 100%; background: #6366f1; color: #fff; border: none; border-radius: 8px;
           padding: 11px; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 24px; }}
    .btn:hover {{ background: #4f46e5; }}
    .field {{ margin-bottom: 16px; }}
    .error {{ color: #f87171; font-size: 13px; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">Sourcy</div>
    <div class="sub">Marketing Analyst — Internal Tool</div>
    <form method="post" action="/login">
      <div class="field">
        <label>Username</label>
        <input type="text" name="username" autocomplete="username" required>
      </div>
      <div class="field">
        <label>Password</label>
        <input type="password" name="password" autocomplete="current-password" required>
      </div>
      {error}
      <button class="btn" type="submit">Sign in</button>
    </form>
  </div>
</body>
</html>"""


@login_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return _LOGIN_HTML.format(error="")


@login_router.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    if username == AUTH_USERNAME and password == AUTH_PASSWORD:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    html = _LOGIN_HTML.format(error='<div class="error">Invalid username or password.</div>')
    return HTMLResponse(html, status_code=401)


@login_router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


def _is_public_v2_path(path: str) -> bool:
    return V2_PUBLIC_ACCESS and (
        path.startswith("/api/v2")
        or path.startswith("/ws")
        or path.startswith("/reports/")
        or path.startswith("/content/")
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if DEV_MODE:
            return await call_next(request)

        path = request.url.path
        if path in _PASS_THROUGH or path.startswith("/static") or _is_public_v2_path(path):
            return await call_next(request)

        user = request.session.get("user")
        if user:
            return await call_next(request)

        # API and WebSocket handshakes get 401; HTML requests get redirect to login
        if path.startswith("/api/") or path.startswith("/ws"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return RedirectResponse(f"/login", status_code=302)


async def require_session(websocket) -> bool:
    """Return True if WS session is valid; close with 1008 and return False if not."""
    if DEV_MODE or V2_PUBLIC_ACCESS:
        return True
    user = websocket.session.get("user") if hasattr(websocket, "session") else None
    if not user:
        await websocket.close(code=1008)
        return False
    return True
