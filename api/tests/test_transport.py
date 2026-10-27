"""Connections to the database are encrypted in production."""
from app.db import require_tls


def test_production_postgres_requires_tls():
    assert require_tls("postgresql+psycopg2://u:p@db:5432/eris", "production") == \
        "postgresql+psycopg2://u:p@db:5432/eris?sslmode=require"
    assert require_tls("postgresql+psycopg2://u:p@db/eris?connect_timeout=5", "production").endswith("&sslmode=require")


def test_an_explicit_sslmode_is_kept():
    url = "postgresql+psycopg2://u:p@db/eris?sslmode=verify-full"
    assert require_tls(url, "production") == url


def test_development_and_sqlite_are_unchanged():
    assert require_tls("postgresql+psycopg2://u:p@localhost/eris", "development") == \
        "postgresql+psycopg2://u:p@localhost/eris"
    assert require_tls("sqlite:///x.db", "production") == "sqlite:///x.db"


# --- browser sessions: the refresh token lives in an HTTP-only cookie ---------------------------------------------

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

ADMIN = {"email": "admin@eris.demo", "password": "Admin@123"}
WEB = {"x-eris-client": "web"}


def _fresh(address: str) -> TestClient:
    return TestClient(app, client=(address, 50001))


def test_browser_login_sets_an_http_only_cookie_and_hides_the_refresh_token():
    r = _fresh("203.0.113.20").post("/api/auth/login", json=ADMIN, headers=WEB)
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and "refresh_token" not in body
    cookie = r.headers["set-cookie"]
    assert cookie.startswith(f"{settings.REFRESH_COOKIE_NAME}=")
    assert "HttpOnly" in cookie and "Path=/api/auth" in cookie and "SameSite=lax" in cookie


def test_api_clients_still_receive_the_refresh_token_in_the_body():
    r = _fresh("203.0.113.21").post("/api/auth/login", json=ADMIN)
    assert r.status_code == 200 and "refresh_token" in r.json()
    assert "set-cookie" not in r.headers


def test_refresh_with_the_cookie_rotates_it():
    c = _fresh("203.0.113.22")
    first = c.post("/api/auth/login", json=ADMIN, headers=WEB)
    assert first.status_code == 200
    r = c.post("/api/auth/refresh", headers=WEB)  # the TestClient keeps the cookie, as a browser would
    assert r.status_code == 200
    assert r.json()["access_token"] and "refresh_token" not in r.json()
    assert r.headers["set-cookie"].startswith(f"{settings.REFRESH_COOKIE_NAME}=")


def test_a_cookie_without_the_web_header_is_refused_as_forged():
    c = _fresh("203.0.113.23")
    c.post("/api/auth/login", json=ADMIN, headers=WEB)
    r = c.post("/api/auth/refresh")  # cookie present, header missing: a cross-site request shape
    assert r.status_code == 403
    assert "x-eris-client" in r.json()["detail"]


def test_logout_removes_the_cookie():
    c = _fresh("203.0.113.24")
    c.post("/api/auth/login", json=ADMIN, headers=WEB)
    r = c.post("/api/auth/logout", headers=WEB)
    assert r.status_code == 200
    assert f"{settings.REFRESH_COOKIE_NAME}=" in r.headers["set-cookie"] and "Max-Age=0" in r.headers["set-cookie"]
    assert c.post("/api/auth/logout").status_code == 403  # the header is required here too


def test_refresh_cookie_is_secure_in_production(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = _fresh("203.0.113.25").post("/api/auth/login", json=ADMIN, headers=WEB)
    assert "Secure" in r.headers["set-cookie"]


def test_plain_http_ollama_is_refused_in_production(monkeypatch):
    from app.services.assistant import llm

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "OLLAMA_URL", "http://ollama.internal:11434")
    llm._status["checked"] = 0.0
    s = llm.status(force=True)
    assert s["available"] is False and "https" in s["error"]


def test_localhost_and_https_ollama_are_allowed_in_production(monkeypatch):
    from app.services.assistant import llm

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert llm._transport_allowed("http://localhost:11434")
    assert llm._transport_allowed("https://ollama.example.com")
    assert not llm._transport_allowed("http://ollama.internal:11434")
