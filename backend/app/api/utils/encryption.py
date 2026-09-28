"""
Encryption utilities for sensitive data
"""

import os
from cryptography.fernet import Fernet
import base64


_DISALLOWED_PLACEHOLDERS = {
    "change_me",
    "change_me_or_leave_blank",
    "changeme",
    "your_secret_key",
    "your-secret-key",
    "placeholder",
    "dummy",
}

def get_encryption_key() -> str:
    key = os.getenv("ENCRYPTION_KEY", "").strip()
    if not key:
        raise RuntimeError("ENCRYPTION_KEY environment variable is not set. A 32-byte Fernet key is required.")
    if key.lower() in _DISALLOWED_PLACEHOLDERS or key.lower().startswith("change_me"):
        raise RuntimeError(f"ENCRYPTION_KEY contains a placeholder value ({key!r}). A valid Fernet key must be supplied.")
    return key


def get_cipher() -> Fernet:
    key = get_encryption_key()
    return Fernet(key.encode() if isinstance(key, str) else key)



def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data
    
    Args:
        data: Plain text string to encrypt
        
    Returns:
        Encrypted string (base64 encoded)
    """
    if not data:
        return ""
    
    encrypted = get_cipher().encrypt(data.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data
    
    Args:
        encrypted_data: Encrypted string (base64 encoded)
        
    Returns:
        Decrypted plain text string
    """
    if not encrypted_data:
        return ""
    
    try:
        decoded = base64.b64decode(encrypted_data.encode())
        decrypted = get_cipher().decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

