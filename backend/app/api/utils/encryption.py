"""
Encryption utilities for sensitive data
"""

import os
from cryptography.fernet import Fernet
import base64


# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Generate a key for development (NEVER use this in production)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"WARNING: Using generated encryption key. Set ENCRYPTION_KEY in production!")
    print(f"Generated key: {ENCRYPTION_KEY}")

# Initialize Fernet cipher
cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


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
    
    encrypted = cipher.encrypt(data.encode())
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
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
