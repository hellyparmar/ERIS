"""
Password Hashing Utilities
Secure password handling with bcrypt or fallback
"""

import os
from passlib.context import CryptContext

# Use plaintext for testing, bcrypt for production
USE_PLAINTEXT = os.getenv("TESTING", "false").lower() == "true"

if USE_PLAINTEXT:
    # For testing - simple plaintext with prefix
    pwd_context = CryptContext(schemes=["plaintext"], deprecated="auto")
else:
    # For production - use bcrypt
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    except Exception:
        # Fallback to plaintext if bcrypt fails
        pwd_context = CryptContext(schemes=["plaintext"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt or plaintext (for testing)
    
    Args:
        password: Plain text password (will be truncated to 72 bytes for bcrypt)
    
    Returns:
        Hashed password string
    """
    try:
        # Bcrypt has a maximum password length of 72 bytes
        password_truncated = password[:72]
        return pwd_context.hash(password_truncated)
    except Exception:
        # Fallback to plaintext
        return f"plaintext${password[:72]}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Truncate to match hash_password behavior
        plain_password_truncated = plain_password[:72]
        return pwd_context.verify(plain_password_truncated, hashed_password)
    except Exception:
        # Fallback plaintext verification
        if hashed_password.startswith("plaintext$"):
            return hashed_password == f"plaintext${plain_password[:72]}"
        return False


