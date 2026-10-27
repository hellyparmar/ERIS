"""Transport and abuse protection: security headers, HTTPS redirect, body limit and rate limits."""
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.hardening import _SlidingWindow
from app.main import app


def _client(address: str) -> TestClient:
    # A separate client address per test keeps the rate-limit buckets from leaking between tests.
    return TestClient(app, client=(address, 50000))


def test_api_responses_carry_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert "strict-transport-security" not in r.headers  # HSTS is for production only


def test_production_adds_hsts(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = client.get("/api/health")
    assert r.headers["strict-transport-security"].startswith("max-age=31536000")


def test_plain_http_through_proxy_redirects_to_https_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = client.get("/api/dashboard?days=7", headers={"x-forwarded-proto": "http", "host": "eris.example"},
                   follow_redirects=False)
    assert r.status_code == 308
    assert r.headers["location"] == "https://eris.example/api/dashboard?days=7"


def test_health_check_is_not_redirected(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = client.get("/api/health", headers={"x-forwarded-proto": "http"}, follow_redirects=False)
    assert r.status_code == 200


def test_no_redirect_outside_production(client):
    r = client.get("/api/health", headers={"x-forwarded-proto": "http"}, follow_redirects=False)
    assert r.status_code == 200


def test_oversized_request_is_refused_before_it_is_read(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_BODY_MB", 0)  # any body is over the limit
    r = client.post("/api/auth/refresh", json={"refresh_token": "x" * 50})
    assert r.status_code == 413
    assert "too large" in r.json()["detail"]


def test_login_is_rate_limited_per_client(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_PER_MINUTE", 2)
    attacker = _client("198.51.100.7")
    bad = {"email": "admin@eris.demo", "password": "wrong-password"}
    codes = [attacker.post("/api/auth/login", json=bad).status_code for _ in range(3)]
    assert codes[2] == 429
    blocked = attacker.post("/api/auth/login", json=bad)
    assert blocked.status_code == 429
    assert "Too many requests" in blocked.json()["detail"]
    assert int(blocked.headers["retry-after"]) >= 1
    # another client address is not affected by this one's limit
    other = _client("198.51.100.8").post("/api/auth/login", json=bad)
    assert other.status_code != 429


def test_rate_limits_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_PER_MINUTE", 1)
    c = _client("198.51.100.9")
    codes = [c.post("/api/auth/login", json={"email": "x@eris.demo", "password": "nope"}).status_code for _ in range(3)]
    assert 429 not in codes


def test_sliding_window_counts_and_recovers():
    w = _SlidingWindow()
    assert w.hit(("k", "ip"), limit=2, window=60) is None
    assert w.hit(("k", "ip"), limit=2, window=60) is None
    wait = w.hit(("k", "ip"), limit=2, window=60)
    assert wait is not None and 0 < wait <= 60
    assert w.hit(("k", "other"), limit=2, window=60) is None  # separate key


@pytest.mark.parametrize("path", ["/docs", "/openapi.json"])
def test_api_docs_are_served(client, path):
    assert client.get(path).status_code == 200
