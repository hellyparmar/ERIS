"""
Test authentication module including bcrypt, JWT, and auth endpoints.
"""
import pytest
from app.core.security import hash_password, verify_password


class TestBcryptPasslib:
    """Tests for bcrypt password hashing."""

    def test_password_hashing_uses_bcrypt(self):
        """Verify password hashing uses bcrypt format ($2b$)."""
        hashed = hash_password("test123")
        assert hashed.startswith("$2b$"), "Hash must be bcrypt format (starts with $2b$)"

    def test_password_verification_correct(self):
        """Verify correct password passes verification."""
        pwd = "SecurePass123!"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed), "Correct password must verify successfully"

    def test_password_verification_wrong(self):
        """Verify wrong password fails verification."""
        pwd = "SecurePass123!"
        hashed = hash_password(pwd)
        assert not verify_password("WrongPass123!", hashed), "Wrong password must fail"

    def test_each_hash_is_unique(self):
        """Verify each hash is unique due to random salt."""
        pwd = "test123"
        hash1 = hash_password(pwd)
        hash2 = hash_password(pwd)
        assert hash1 != hash2, "Two hashes of same password must differ (random salt)"

    def test_verify_with_different_hash_fails(self):
        """Verify password cannot be verified with unrelated hash."""
        hashed1 = hash_password("password1")
        assert not verify_password("password2", hashed1), "Wrong password with wrong hash must fail"


class TestLoginEndpoint:
    """Tests for login endpoint."""

    def test_login_success(self, client, seed_users):
        """Verify valid credentials return JWT token."""
        res = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "admin123"})
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_login_wrong_password(self, client, seed_users):
        """Verify wrong password returns 401."""
        res = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "wrongpass"})
        assert res.status_code == 401

    def test_login_unknown_email(self, client):
        """Verify unknown email returns 401."""
        res = client.post("/api/v1/auth/login", data={"username": "nobody@test.com", "password": "any"})
        assert res.status_code == 401

    def test_me_endpoint_requires_auth(self, client):
        """Verify /me endpoint rejects unauthenticated requests."""
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401

    def test_me_endpoint_with_valid_token(self, client, seed_users, admin_token):
        """Verify /me endpoint returns user with valid token."""
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.json()["email"] == "admin@test.com"
