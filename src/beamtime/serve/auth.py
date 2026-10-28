"""The token that guards the UI and API, and the content security policy."""

import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

TOKEN_FILE = "serve.token"
PUBLIC = ("/static/",)
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; connect-src 'self'; frame-src 'self'; worker-src 'self' blob:; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


def load_token(cache: Path) -> str:
    """Read the root's token, creating it on first use.

    The token outlives restarts, so a browser that has its cookie stays signed in.

    :param cache: The root's cache directory.
    :return: The token."""
    path = cache / TOKEN_FILE
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        pass
    cache.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(24)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token)
    return token


class TokenGuard:
    """ASGI middleware: static files are public, everything else needs the token."""

    def __init__(self, app: ASGIApp, *, token: str, port: int) -> None:
        """Wrap an app.

        :param app: The Starlette app.
        :param token: The token.
        :param port: The port, which names the cookie, since cookies ignore ports."""
        self.app = app
        self.token = token
        self.cookie = f"beamtime-{port}"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Check the token, then pass the request on with the security headers.

        :param scope: The ASGI scope.
        :param receive: The ASGI receive channel.
        :param send: The ASGI send channel."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        path = request.url.path
        if not path.startswith(PUBLIC):
            if (given := request.query_params.get("token")) is not None and not path.startswith(
                "/api/"
            ):
                if not self.valid(given):
                    await denied(path)(scope, receive, send)
                    return
                rest = {k: v for k, v in request.query_params.items() if k != "token"}
                response = RedirectResponse(path + (f"?{urlencode(rest)}" if rest else ""), 303)
                response.set_cookie(
                    self.cookie, self.token, httponly=True, samesite="strict", max_age=400 * 86400
                )
                await response(scope, receive, send)
                return
            auth = request.headers.get("authorization", "")
            given = request.cookies.get(self.cookie) or auth.removeprefix("Bearer ").strip()
            if not self.valid(given):
                await denied(path)(scope, receive, send)
                return

        async def secured(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers += [
                    (b"content-security-policy", CSP.encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                message = message | {"headers": headers}
            await send(message)

        await self.app(scope, receive, secured)

    def valid(self, given: str | None) -> bool:
        """Compare a token in constant time.

        :param given: The token sent, if any.
        :return: Whether it is the right one."""
        return bool(given) and secrets.compare_digest(given.encode(), self.token.encode())


def denied(path: str) -> Response:
    """Answer a request without a valid token.

    :param path: The requested path.
    :return: JSON for the API, a short text for pages."""
    if path.startswith("/api/"):
        return JSONResponse({"error": "missing or wrong token", "code": 401}, status_code=401)
    return PlainTextResponse(
        "Beamtime needs its token: open the URL that `beamtime serve` printed "
        "(it ends in ?token=...).",
        status_code=401,
    )
