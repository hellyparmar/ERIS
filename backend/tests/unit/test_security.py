import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

def test_auth_rate_limiting():
    """
    Test that the rate limiter on /api/v1/auth/login triggers a 429 after repeated failed attempts.
    """
    client = TestClient(app)
    payload = {
        "username": "dummy_user",
        "password": "wrong_password"
    }

    # Make requests up to the rate limit
    got_429 = False
    for _ in range(10):
        response = client.post("/api/v1/auth/login/json", json=payload)
        if response.status_code == 429:
            got_429 = True
            break
        assert response.status_code in (401, 404)

    assert got_429, "Rate limiter should trigger 429 after repeated requests"

def test_short_lived_access_token():
    """
    Test that ACCESS_TOKEN_EXPIRE_MINUTES is short (<= 30 minutes) for stateless security.
    """
    from app.core.config import settings
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 30, "Access token expiry should be 30 minutes or less for stateless JWT security"
