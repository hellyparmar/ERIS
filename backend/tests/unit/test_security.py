import pytest
from httpx import AsyncClient
from app.main import app
import time

@pytest.mark.asyncio
async def test_auth_rate_limiting(client: AsyncClient):
    """
    Test that the rate limiter on /api/v1/auth/login triggers a 429 after 5 failed attempts.
    """
    payload = {
        "username": "dummy_user",
        "password": "wrong_password"
    }

    # Make 5 requests (the limit is 5 per minute)
    for _ in range(5):
        response = await client.post("/api/v1/auth/login/json", json=payload)
        # It should return 401 Unauthorized for bad credentials, not 429
        assert response.status_code in (401, 404)

    # The 6th request should hit the rate limit (429 Too Many Requests)
    response = await client.post("/api/v1/auth/login/json", json=payload)
    assert response.status_code == 429

@pytest.mark.asyncio
async def test_short_lived_access_token():
    """
    Test that ACCESS_TOKEN_EXPIRE_MINUTES is short (<= 30 minutes) for stateless security.
    """
    from app.core.config import settings
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 30, "Access token expiry should be 30 minutes or less for stateless JWT security"
