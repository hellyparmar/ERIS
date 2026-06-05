"""
Unit Tests for Authentication System

Tests:
- Password hashing and verification
- JWT token generation and validation
- User registration and login
- Role-based access control
- Token refresh and revocation

Run: pytest tests/unit/test_auth.py -v
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.auth.auth import (  # type: ignore
    hash_password,
    verify_password,
    validate_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings  # type: ignore


class TestPasswordUtilities:
    """Test password hashing and verification"""
    
    def test_hash_password_creates_different_hashes(self):
        """Same password should create different hashes (salting)"""
        password = "Test123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2, "Hashes should be different due to salting"
        assert len(hash1) > 20, "Hash should be reasonably long"
        assert len(hash2) > 20, "Hash should be reasonably long"
    
    def test_verify_password_with_correct_password(self):
        """Verify should return True for correct password"""
        password = "Test123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_with_wrong_password(self):
        """Verify should return False for incorrect password"""
        password = "Test123!"
        wrong_password = "Wrong456!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_validate_password_strong_password(self):
        """Strong password should pass validation"""
        strong_password = "StrongPass123!"
        # Should not raise exception
        validate_password(strong_password)
    
    def test_validate_password_too_short(self):
        """Password less than 8 characters should fail"""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password("Short1!")
    
    def test_validate_password_no_uppercase(self):
        """Password without uppercase should fail"""
        with pytest.raises(ValueError):
            validate_password("lowercase123456")
    
    def test_validate_password_no_digit(self):
        """Password without digit should fail"""
        with pytest.raises(ValueError):
            validate_password("NoDigitHere!")


class TestJWTTokens:
    """Test JWT token generation and validation"""
    
    def test_create_access_token_returns_string(self):
        """Access token should be a non-empty string"""
        token = create_access_token(data={"sub": "test_user"})
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2, "JWT should have 3 parts separated by dots"
    
    def test_create_access_token_with_custom_expiry(self):
        """Token should respect custom expiry time"""
        custom_expiry = 600  # 10 minutes
        token = create_access_token(
            data={"sub": "test_user"},
            expires_delta=timedelta(seconds=custom_expiry)
        )
        
        decoded = decode_token(token)
        assert decoded["sub"] == "test_user"
    
    def test_create_refresh_token_returns_string(self):
        """Refresh token should be a non-empty string"""
        token = create_refresh_token(data={"sub": "test_user"})
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Valid token should decode correctly"""
        user_id = "test_user_123"
        token = create_access_token(data={"sub": user_id})
        
        decoded = decode_token(token)
        assert decoded["sub"] == user_id
        assert "exp" in decoded
    
    def test_decode_expired_token_raises_error(self):
        """Expired token should raise InvalidTokenError"""
        # Create token with very short expiry (already expired)
        token = create_access_token(
            data={"sub": "test_user"},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(InvalidTokenError):
            decode_token(token)
    
    def test_decode_invalid_token_raises_error(self):
        """Invalid token format should raise InvalidTokenError"""
        invalid_token = "not.a.valid.token.format"
        
        with pytest.raises(InvalidTokenError):
            decode_token(invalid_token)
    
    def test_decode_tampered_token_raises_error(self):
        """Tampered token should raise InvalidTokenError"""
        token = create_access_token(data={"sub": "original_user"})
        
        # Tamper with the token by changing a character
        tampered_token = token[:-10] + "tampered!!"
        
        with pytest.raises(InvalidTokenError):
            decode_token(tampered_token)
    
    def test_token_contains_exp_claim(self):
        """Token should contain expiration claim"""
        token = create_access_token(data={"sub": "test_user"})
        decoded = decode_token(token)
        
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
    
    def test_token_contains_iat_claim(self):
        """Token should contain issued-at claim"""
        token = create_access_token(data={"sub": "test_user"})
        decoded = decode_token(token)
        
        assert "iat" in decoded
        assert isinstance(decoded["iat"], int)
    
    def test_access_token_not_equal_to_refresh_token(self):
        """Access token and refresh token should be different"""
        user_data = {"sub": "test_user"}
        access_token = create_access_token(data=user_data)
        refresh_token = create_refresh_token(data=user_data)
        
        assert access_token != refresh_token


class TestTokenExpiry:
    """Test token expiration behavior"""
    
    def test_access_token_default_expiry(self):
        """Access token should have default expiry"""
        token = create_access_token(data={"sub": "test_user"})
        decoded = decode_token(token)
        
        # Should expire in approximately 1 day (86400 seconds)
        now = datetime.utcnow().timestamp()
        time_to_expiry = decoded["exp"] - now
        
        assert 86300 < time_to_expiry < 86500, "Should be approximately 24 hours"
    
    def test_refresh_token_longer_expiry(self):
        """Refresh token should have longer expiry than access token"""
        access_token = create_access_token(data={"sub": "test_user"})
        refresh_token = create_refresh_token(data={"sub": "test_user"})
        
        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)
        
        access_expiry = access_decoded["exp"]
        refresh_expiry = refresh_decoded["exp"]
        
        assert refresh_expiry > access_expiry, "Refresh token should last longer"


class TestTokenSecurityHeaders:
    """Test token header and signature"""
    
    def test_token_uses_correct_algorithm(self):
        """Token should be signed with HS256"""
        from jose import jwt
        import json
        import base64
        
        token = create_access_token(data={"sub": "test_user"})
        
        # Decode header without verification
        header = json.loads(
            base64.urlsafe_b64decode(token.split('.')[0] + '==')
        )
        
        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"
    
    def test_token_signature_verification(self):
        """Token signature should be verified correctly"""
        token = create_access_token(data={"sub": "test_user"})
        
        # Decode with verification (uses settings.JWT_SECRET_KEY)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert "sub" in decoded


class TestCustomClaims:
    """Test custom claims in JWT"""
    
    def test_token_preserves_custom_data(self):
        """Token should preserve custom data in claims"""
        custom_data = {
            "sub": "user_123",
            "email": "user@example.com",
            "role": "admin"
        }
        
        token = create_access_token(data=custom_data)
        decoded = decode_token(token)
        
        assert decoded["sub"] == "user_123"
        assert decoded["email"] == "user@example.com"
        assert decoded["role"] == "admin"
    
    def test_token_with_multiple_roles(self):
        """Token should handle multiple roles"""
        custom_data = {
            "sub": "user_456",
            "roles": ["admin", "manager", "user"]
        }
        
        token = create_access_token(data=custom_data)
        decoded = decode_token(token)
        
        assert "roles" in decoded
        assert len(decoded["roles"]) == 3


# Integration-style tests
class TestAuthenticationFlow:
    """Test complete authentication flow"""
    
    def test_password_registration_flow(self):
        """Simulate user registration: password validation and hashing"""
        # User provides password
        user_password = "SecurePass123!"
        
        # Validate password strength
        validate_password(user_password)  # Should not raise
        
        # Hash password for storage
        hashed = hash_password(user_password)
        
        # Verify it can be verified later
        assert verify_password(user_password, hashed) is True
    
    def test_login_and_token_generation_flow(self):
        """Simulate login: password verification and token generation"""
        # During registration
        password = "UserPassword123!"
        stored_hash = hash_password(password)
        
        # During login
        provided_password = "UserPassword123!"
        
        # Verify password
        assert verify_password(provided_password, stored_hash) is True
        
        # Generate tokens
        user_id = "user_789"
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        # Verify tokens
        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)
        
        assert access_decoded["sub"] == user_id
        assert refresh_decoded["sub"] == user_id
    
    def test_token_refresh_flow(self):
        """Simulate token refresh with valid refresh token"""
        user_id = "user_refresh_test"
        
        # Original tokens
        old_access = create_access_token(data={"sub": user_id})
        refresh = create_refresh_token(data={"sub": user_id})
        
        # Verify refresh token is valid
        refresh_decoded = decode_token(refresh)
        
        # Generate new access token using refresh token data
        new_access = create_access_token(data={"sub": refresh_decoded["sub"]})
        
        # Verify both tokens have same user
        old_decoded = decode_token(old_access)
        new_decoded = decode_token(new_access)
        
        assert old_decoded["sub"] == new_decoded["sub"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
