#!/usr/bin/env python3
"""Check a deployed ERIS for the connectivity and security settings the code relies on.

Run it from any computer (standard library only):

    python3 scripts/verify_deployment.py https://eris-tvro.onrender.com --web https://<your-site>.vercel.app

Add --local to test a server on this machine over plain HTTP (the HTTPS-only checks are then skipped).
Exit code 0 when every check passes, 1 otherwise. Demo sign-in is used (the demo accounts are public, see README).
"""
import argparse
import http.cookiejar
import ssl
import json
import re
import sys
import urllib.error
import urllib.request

DEMO = {"email": "admin@eris.demo", "password": "Admin@123"}
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


CA_FILE: str | None = None  # --ca: trust this certificate (e.g. a self-signed test certificate); verification stays on


def _https_context():
    return ssl.create_default_context(cafile=CA_FILE) if CA_FILE else None


def _headers(response) -> dict:
    """Lower-cased headers; every Set-Cookie line is kept (joined by newlines under 'set-cookie-all')."""
    out = {k.lower(): v for k, v in response.headers.items()}
    out["set-cookie-all"] = "\n".join(response.headers.get_all("set-cookie") or [])
    return out


def cookie_line(headers: dict, name: str) -> str:
    return next((c for c in headers.get("set-cookie-all", "").split("\n") if c.startswith(name + "=")), "")


def request(url, method="GET", headers=None, body=None, opener=None, follow=True):
    req = urllib.request.Request(url, method=method, data=body, headers=headers or {})
    handlers = [urllib.request.HTTPSHandler(context=_https_context())]
    if not follow:
        handlers.append(NoRedirect())
    op = opener or urllib.request.build_opener(*handlers)
    try:
        with op.open(req, timeout=60) as r:
            return r.status, _headers(r), r.read()
    except urllib.error.HTTPError as e:
        return e.code, _headers(e), e.read()


def api_checks(api: str, local: bool, web_origin: str | None) -> None:
    status, headers, body = request(f"{api}/api/health")
    check("API health answers 200", status == 200 and b'"ok"' in body, f"HTTP {status}")
    check("nosniff on API responses", headers.get("x-content-type-options") == "nosniff")
    check("frame denial on API responses", headers.get("x-frame-options") == "DENY")
    check("API content security policy", "default-src 'none'" in headers.get("content-security-policy", ""))
    if not local:
        check("HSTS on the API", "max-age=" in headers.get("strict-transport-security", ""))
        if api.startswith("https://"):
            plain = "http://" + api[len("https://"):]
            try:
                status, headers, _ = request(f"{plain}/api/health", follow=False)
                check("plain HTTP is redirected to HTTPS", status in (301, 308) and headers.get("location", "").startswith("https://"),
                      f"HTTP {status} {headers.get('location', '')}")
            except OSError as e:  # URLError, refused or closed connections
                check("plain HTTP is redirected to HTTPS", False, f"no plain-HTTP answer: {getattr(e, 'reason', e)}")
        # the application itself redirects a request that reached it as plain HTTP through a proxy
        status, headers, _ = request(f"{api}/api/dashboard", headers={"X-Forwarded-Proto": "http"}, follow=False)
        check("application redirects plain-HTTP requests to HTTPS", status in (307, 308) and headers.get("location", "").startswith("https://"),
              f"HTTP {status}")

    status, _, _ = request(f"{api}/api/dashboard")
    check("data needs a sign-in", status == 401, f"HTTP {status}")

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), urllib.request.HTTPSHandler(context=_https_context()))
    login = json.dumps(DEMO).encode()
    status, headers, body = request(f"{api}/api/auth/login", "POST", {"Content-Type": "application/json", "X-ERIS-Client": "web"}, login, opener)
    data = json.loads(body) if status == 200 else {}
    check("browser sign-in works", status == 200 and "user" in data, f"HTTP {status}")
    check("browser sign-in puts no token in the page's reach", status == 200 and "access_token" not in data and "refresh_token" not in data)
    refresh = cookie_line(headers, "eris_refresh")
    access = cookie_line(headers, "eris_access")
    check("refresh cookie is HttpOnly and scoped to /api/auth", "httponly" in refresh.lower() and "path=/api/auth" in refresh.lower())
    check("access cookie is HttpOnly and scoped to /api", "httponly" in access.lower() and "path=/api" in access.lower())
    if not local:
        check("session cookies are Secure", "secure" in refresh.lower() and "secure" in access.lower())
        check("session cookies allow cross-site use (SameSite=None)",
              "samesite=none" in refresh.lower() and "samesite=none" in access.lower(),
              "needed when the web app is on another site" if "samesite=none" not in refresh.lower() else "")

    if not local:
        status, _, _ = request(f"{api}/api/auth/me", "GET", {"X-ERIS-Client": "web"}, None, opener)
        check("the session cookie is accepted by the API", status == 200, f"HTTP {status}")
        status, _, _ = request(f"{api}/api/customers", "POST", {"Content-Type": "application/json"},
                               b'{"name": "verify", "phone": "9800000001"}', opener)
        check("a cookie-authenticated change without the web header is refused", status == 403, f"HTTP {status}")
        status, _, _ = request(f"{api}/api/auth/refresh", "POST", {"Content-Type": "application/json", "X-ERIS-Client": "web"}, b"{}", opener)
        check("refresh with the cookie renews the session", status == 200, f"HTTP {status}")
        status, _, _ = request(f"{api}/api/auth/refresh", "POST", {"Content-Type": "application/json"}, b"{}", opener)
        check("a refresh cookie request without the web header is refused", status == 403, f"HTTP {status}")

    evil = {"Origin": "https://evil.example", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-eris-client"}
    _, headers, _ = request(f"{api}/api/auth/refresh", "OPTIONS", evil)
    check("other sites cannot use the API from a browser", headers.get("access-control-allow-origin") != "https://evil.example")
    if web_origin:
        ok = {"Origin": web_origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-eris-client"}
        _, headers, _ = request(f"{api}/api/auth/refresh", "OPTIONS", ok)
        check("the web app's origin is allowed", headers.get("access-control-allow-origin") == web_origin,
              f"got {headers.get('access-control-allow-origin')!r}")


def web_checks(web: str, local: bool) -> None:
    status, headers, body = request(web + "/")
    html = body.decode(errors="replace")
    check("web app answers 200", status == 200, f"HTTP {status}")
    csp = headers.get("content-security-policy", "")
    check("web content security policy blocks other scripts", "script-src 'self'" in csp)
    check("web app has no inline scripts", not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html))
    check("web app: frame denial", headers.get("x-frame-options") == "DENY")
    if not local:
        check("web app: HSTS", "max-age=" in headers.get("strict-transport-security", ""))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("api", help="API base address, e.g. https://eris-tvro.onrender.com")
    p.add_argument("--web", help="web app address, e.g. https://<site>.vercel.app")
    p.add_argument("--local", action="store_true", help="plain-HTTP test server on this machine")
    p.add_argument("--ca", help="certificate file to trust (for a test server with a self-signed certificate)")
    a = p.parse_args()
    global CA_FILE
    CA_FILE = a.ca
    api = a.api.rstrip("/")
    try:
        api_checks(api, a.local, a.web.rstrip("/") if a.web else None)
        if a.web:
            web_checks(a.web.rstrip("/"), a.local)
    except OSError as e:
        check("the address can be reached", False, str(getattr(e, "reason", e)))
    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}".rstrip())
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
