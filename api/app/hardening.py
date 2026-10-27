"""Transport and abuse protection for every request.

- Security headers on every response: no MIME sniffing, no framing, a strict referrer policy, and a
  Content-Security-Policy. HSTS is added in production.
- In production, a plain-HTTP request that reached the server through a proxy (X-Forwarded-Proto: http) is
  redirected to HTTPS.
- Request bodies above MAX_BODY_MB are refused before they are read.
- Sliding-window rate limits per client address for sign-in, the heavy endpoints (forecasts, assistant,
  imports, exports) and the API as a whole. Blocked requests get HTTP 429 and a Retry-After header.

It is a plain ASGI middleware, so it runs for every request, including the static web app.
"""
import math
import threading
import time
from collections import deque
from dataclasses import dataclass

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse, RedirectResponse

from app.config import settings

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
# The web app: its own scripts and styles only (no inline scripts), and API calls to its own origin or any https host
# (the web app may be hosted on another origin than the API).
APP_CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
           "font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; "
           "form-action 'self'; object-src 'none'")
# The interactive API documentation loads Swagger UI from a CDN and uses one inline script.
DOCS_PATHS = ("/docs", "/redoc")
DOCS_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'")
BASE_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "camera=(), geolocation=(), payment=()",
    "cross-origin-opener-policy": "same-origin",
}
HSTS = "max-age=31536000; includeSubDomains"
HEALTH_PATH = "/api/health"  # health checks run inside the container over plain HTTP


@dataclass(frozen=True)
class Rule:
    name: str
    methods: frozenset[str]
    prefixes: tuple[str, ...]
    limit: int
    window: int = 60  # seconds
    contains: tuple[str, ...] = ()


def _rules() -> list[Rule]:
    get_post = frozenset({"GET", "POST"})
    return [
        Rule("login", frozenset({"POST"}), ("/api/auth/login",), settings.RATE_LIMIT_LOGIN_PER_MINUTE),
        Rule("heavy-forecast", frozenset({"GET", "POST"}), ("/api/forecast",), settings.RATE_LIMIT_HEAVY_PER_MINUTE),
        Rule("heavy-assistant", frozenset({"POST"}), ("/api/assistant/chat",), settings.RATE_LIMIT_HEAVY_PER_MINUTE),
        Rule("heavy-imports", frozenset({"POST"}), ("/api/imports/",), settings.RATE_LIMIT_HEAVY_PER_MINUTE),
        Rule("heavy-exports", frozenset({"GET"}), ("/api/",), settings.RATE_LIMIT_HEAVY_PER_MINUTE,
             contains=("/export",)),
        Rule("api", get_post | {"PUT", "PATCH", "DELETE"}, ("/api/",), settings.RATE_LIMIT_API_PER_MINUTE),
    ]


class _SlidingWindow:
    """Counts hits per key over the last `window` seconds. Thread-safe; memory is bounded by pruning idle keys."""

    MAX_KEYS = 50_000

    def __init__(self) -> None:
        self._hits: dict[tuple, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: tuple, limit: int, window: int) -> float | None:
        """Record one hit. Returns None if allowed, or the seconds to wait if the key is over its limit."""
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > self.MAX_KEYS:
                for k in [k for k, q in self._hits.items() if not q or now - q[-1] >= window]:
                    del self._hits[k]
            q = self._hits.setdefault(key, deque())
            while q and now - q[0] >= window:
                q.popleft()
            if len(q) >= limit:
                return window - (now - q[0])
            q.append(now)
            return None


_window = _SlidingWindow()


def _matching_rule(method: str, path: str) -> Rule | None:
    for rule in _rules():
        if method not in rule.methods or not path.startswith(rule.prefixes):
            continue
        if rule.contains and not any(c in path for c in rule.contains):
            continue
        return rule
    return None


def _client_address(scope) -> str:
    client = scope.get("client")
    return client[0] if client else "unknown"


def _https_url(headers: Headers, scope) -> str:
    query = scope.get("query_string", b"").decode("latin-1")
    return f"https://{headers.get('host', '')}{scope['path']}" + (f"?{query}" if query else "")


class HardeningMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        path, method = scope["path"], scope["method"]

        if settings.ENVIRONMENT == "production" and path != HEALTH_PATH and headers.get("x-forwarded-proto") == "http":
            return await RedirectResponse(_https_url(headers, scope), status_code=308)(scope, receive, send)

        length = headers.get("content-length", "")
        if length.isdigit() and int(length) > settings.MAX_BODY_MB * 1024 * 1024:
            return await JSONResponse({"detail": "The request is too large."}, status_code=413)(scope, receive, send)

        rule = _matching_rule(method, path) if settings.RATE_LIMIT_ENABLED else None
        if rule is not None:
            wait = _window.hit((rule.name, _client_address(scope)), rule.limit, rule.window)
            if wait is not None:
                return await JSONResponse(
                    {"detail": "Too many requests. Please wait a moment and try again."}, status_code=429,
                    headers={"Retry-After": str(max(1, math.ceil(wait)))},
                )(scope, receive, send)

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                out = MutableHeaders(scope=message)
                for name, value in BASE_HEADERS.items():
                    out[name] = value
                is_html = out.get("content-type", "").startswith("text/html")
                if path.startswith(DOCS_PATHS):
                    out["content-security-policy"] = DOCS_CSP
                else:
                    out["content-security-policy"] = APP_CSP if is_html else API_CSP
                if settings.ENVIRONMENT == "production":
                    out["strict-transport-security"] = HSTS
            await send(message)

        return await self.app(scope, receive, send_with_security_headers)
