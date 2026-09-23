import pytest
from datetime import datetime, timedelta
import time
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token
)
from app.api.auth.jwt_handler import (
    create_access_token as jwt_create_access_token,
    create_refresh_token as jwt_create_refresh_token,
    verify_token as jwt_verify_token
)


def test_short_lived_access_token():
    """
    Test that ACCESS_TOKEN_EXPIRE_MINUTES is short (<= 30 minutes) for stateless security.
    """
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 30, (
        f"Access token expiry should be 30 minutes or less for stateless JWT security, got {settings.ACCESS_TOKEN_EXPIRE_MINUTES}"
    )
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS >= 7, (
        f"Refresh token expiry should be at least 7 days, got {settings.REFRESH_TOKEN_EXPIRE_DAYS}"
    )


def test_access_token_past_expiration_rejected():
    """
    Test that an access token past its expiration is rejected by verify_token()
    with HTTP 401 Unauthorized, and decode_token() returns None.
    """
    # Create token with a negative delta so it is already expired
    expired_token = create_access_token(
        {"sub": "expired_user", "role": "staff"},
        expires_delta=timedelta(seconds=-10)
    )

    # verify_token must raise HTTPException with 401 UNAUTHORIZED
    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail

    # decode_token must return None on expired token
    assert decode_token(expired_token) is None


def test_access_token_valid():
    """
    Test that a newly created access token is valid, decodes with correct payload,
    and has type 'access'.
    """
    data = {"sub": "alice", "role": "outlet_manager", "outlet_id": "out-101"}
    token = create_access_token(data)

    payload = verify_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "outlet_manager"
    assert payload["outlet_id"] == "out-101"
    assert payload.get("type") == "access"
    assert payload["exp"] > time.time()


def test_refresh_token_past_expiration_rejected():
    """
    Test that a refresh token past its expiration is rejected by verify_token()
    with HTTP 401 Unauthorized.
    """
    expired_refresh_token = create_refresh_token(
        {"sub": "expired_refresh_user"},
        expires_delta=timedelta(seconds=-10)
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_refresh_token)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail

    assert decode_token(expired_refresh_token) is None


def test_refresh_token_valid():
    """
    Test that a newly created refresh token is valid and has type 'refresh'.
    """
    data = {"sub": "bob", "role": "admin"}
    token = create_refresh_token(data)

    payload = verify_token(token)
    assert payload["sub"] == "bob"
    assert payload["role"] == "admin"
    assert payload.get("type") == "refresh"
    assert payload["exp"] > time.time()


def test_jwt_handler_token_expiry():
    """
    Test that jwt_handler module's create_access_token and create_refresh_token
    also correctly honor expiration and reject expired tokens.
    """
    expired_jwt = jwt_create_access_token(
        {"sub": "jwt_user"},
        expires_delta=timedelta(seconds=-5)
    )
    assert jwt_verify_token(expired_jwt) is None

    valid_jwt = jwt_create_access_token({"sub": "jwt_user"})
    decoded = jwt_verify_token(valid_jwt)
    assert decoded is not None
    assert decoded["sub"] == "jwt_user"
    assert decoded.get("type") == "access"


def test_auth_rate_limiting(client):
    """
    Test that the rate limiter on /api/v1/auth/login triggers a 429 after repeated failed attempts.
    Uses the client fixture with SQLite in-memory database to avoid hanging on Postgres.
    """
    payload = {
        "username": "dummy_rate_limit_user",
        "password": "wrong_password"
    }

    got_429 = False
    for _ in range(15):
        response = client.post("/api/v1/auth/login/json", json=payload)
        if response.status_code == 429:
            got_429 = True
            break
        assert response.status_code in (401, 404)

    assert got_429, "Rate limiter should trigger 429 after repeated requests"
