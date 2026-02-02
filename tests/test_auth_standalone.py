"""
Simple Authentication Tests (Standalone)
Can run without full app dependencies
"""

import pytest
from api.auth.password import hash_password, verify_password
from api.auth.jwt_handler import create_access_token, decode_access_token, verify_token

def test_password_hashing():
    """Test password hashing works"""
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Should be able to verify
    assert verify_password(password, hashed)
    
    # Wrong password should not verify
    assert not verify_password("WrongPassword", hashed)

def test_jwt_token_creation():
    """Test JWT token can be created"""
    data = {"sub": "user123"}
    token = create_access_token(data)
    
    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

def test_jwt_token_verification():
    """Test JWT token can be verified"""
    data = {"sub": "user123"}
    token = create_access_token(data)
    
    # Should be able to decode
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"

def test_jwt_token_decode():
    """Test extracting user ID from token"""
    user_id = "42"
    data = {"sub": user_id}
    token = create_access_token(data)
    
    # Should extract user ID
    extracted_id = decode_access_token(token)
    assert extracted_id == user_id

def test_invalid_jwt_token():
    """Test invalid token returns None"""
    invalid_token = "this.is.invalid"
    
    payload = verify_token(invalid_token)
    assert payload is None
    
    user_id = decode_access_token(invalid_token)
    assert user_id is None

if __name__ == "__main__":
    # Run tests
    test_password_hashing()
    print("✅ Password hashing works")
    
    test_jwt_token_creation()
    print("✅ JWT token creation works")
    
    test_jwt_token_verification()
    print("✅ JWT token verification works")
    
    test_jwt_token_decode()
    print("✅ JWT token decode works")
    
    test_invalid_jwt_token()
    print("✅ Invalid token handling works")
    
    print("\n🎉 All standalone auth tests passed!")
