#!/usr/bin/env python3
"""
STEP 2.5: JWT Authentication Implementation
Adds JWT-based authentication to FastAPI for protecting analytics endpoints

Run with: python implement_jwt_auth.py
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def create_auth_config():
    """Create JWT authentication configuration"""
    
    config = {
        "jwt_secret_key": "your-secret-key-change-in-production-2026!rdios",
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7,
        "environment": "development"
    }
    
    return config

def create_auth_utils():
    """Create JWT utility functions"""
    
    auth_utils_code = '''"""
JWT Authentication Utilities for R-DIOS API
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2026!rdios")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# Fake users database (in production, use real database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@rdios.local",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lm",  # secret
        "disabled": False,
    },
    "user": {
        "username": "user",
        "full_name": "Test User",
        "email": "user@rdios.local",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lm",  # secret
        "disabled": False,
    }
}

def verify_password(plain_password, hashed_password):
    """Verify password hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash password"""
    return pwd_context.hash(password)

def get_user(db, username: str):
    """Get user from database"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    """Authenticate user"""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credential_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
'''
    
    return auth_utils_code

def create_login_endpoint():
    """Create login endpoint code"""
    
    login_code = '''"""
Authentication endpoints for R-DIOS API
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from api.utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    User,
    Token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - Returns JWT access token
    
    Test credentials:
    - username: admin, password: secret
    - username: user, password: secret
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    Requires valid JWT token
    """
    return current_user

@router.get("/status")
async def auth_status():
    """
    Check authentication service status
    """
    return {
        "status": "active",
        "service": "JWT Authentication",
        "version": "1.0",
        "test_credentials": {
            "username": "admin or user",
            "password": "secret"
        }
    }
'''
    
    return login_code

def create_implementation_guide():
    """Create implementation guide"""
    
    guide = '''# JWT Authentication Implementation Guide

## Overview
This guide implements JWT (JSON Web Token) authentication for R-DIOS API, enabling secure access to analytics endpoints.

## Installation

### 1. Install Required Packages
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 2. Create Auth Utils File
Place the `auth.py` file in: `api/utils/auth.py`

### 3. Create Login Router
Place the `login.py` file in: `api/routers/login.py`

### 4. Update Main Application

Add to `api/main.py`:

```python
# Add import
from api.routers import login

# Include router
app.include_router(login.router, tags=["Authentication"])
```

## Environment Variables

Create `.env` file or set:
```bash
JWT_SECRET_KEY="your-secret-key-change-in-production-2026!rdios"
```

## Testing JWT Authentication

### 1. Get Access Token
```bash
curl -X POST "http://localhost:8000/auth/login" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=admin&password=secret"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Use Token to Access Protected Endpoints
```bash
curl -X GET "http://localhost:8000/api/analytics/sales/summary" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Test Credentials
- **Username**: admin or user
- **Password**: secret

## Protecting Endpoints

To protect any endpoint, add the `get_current_active_user` dependency:

```python
from api.utils.auth import get_current_active_user, User

@router.get("/protected-endpoint")
async def protected_endpoint(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.username}"}
```

## Architecture

```
User Login
    ↓
JWT Token Generation
    ↓
Store Token (LocalStorage/Cookies)
    ↓
Include in API Requests
    ↓
Server Validates Token
    ↓
Grant Access to Protected Resources
```

## Security Notes

1. **Change Secret Key** in production
2. **Use HTTPS** in production
3. **Set secure cookie flags** for token storage
4. **Implement token refresh** for long sessions
5. **Rate limit** login attempts

## Frontend Integration

### JavaScript/React Example

```javascript
// Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'username=admin&password=secret'
});
const data = await response.json();
const token = data.access_token;

// Store token
localStorage.setItem('token', token);

// Use token in requests
const apiResponse = await fetch('http://localhost:8000/api/analytics/sales/summary', {
  headers: {'Authorization': `Bearer ${token}`}
});
```

## Troubleshooting

### "Could not validate credentials"
- Check if token is correctly formatted
- Verify token hasn't expired
- Ensure `Bearer ` prefix in Authorization header

### "Invalid password"
- Test with correct credentials: admin/secret or user/secret
- Check if user exists in database

### Token Expired
- Implement token refresh endpoint
- Re-login to get new token

## Next Steps

1. Implement token refresh endpoint
2. Set up token storage in frontend
3. Add logout functionality
4. Implement role-based access control (RBAC)
5. Add audit logging for auth events
'''
    
    return guide

def main():
    """Generate authentication files"""
    
    print("\n" + "="*80)
    print(" JWT AUTHENTICATION IMPLEMENTATION FOR R-DIOS")
    print("="*80 + "\n")
    
    # Create utils directory
    utils_dir = Path("api/utils")
    utils_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory: {utils_dir}")
    
    # Create __init__.py if it doesn't exist
    init_file = utils_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Utils package\n")
        print(f"✅ Created: {init_file}")
    
    # Create auth.py
    auth_code = create_auth_utils()
    auth_file = utils_dir / "auth.py"
    auth_file.write_text(auth_code)
    print(f"✅ Created: {auth_file} ({len(auth_code)} bytes)")
    
    # Create login router
    login_code = create_login_endpoint()
    routers_dir = Path("api/routers")
    routers_dir.mkdir(parents=True, exist_ok=True)
    login_file = routers_dir / "auth_login.py"
    login_file.write_text(login_code)
    print(f"✅ Created: {login_file} ({len(login_code)} bytes)")
    
    # Create implementation guide
    guide = create_implementation_guide()
    guide_file = Path("AUTH_IMPLEMENTATION_GUIDE.md")
    guide_file.write_text(guide)
    print(f"✅ Created: {guide_file}")
    
    # Create config file
    config = create_auth_config()
    config_file = Path("auth_config.json")
    config_file.write_text(json.dumps(config, indent=2))
    print(f"✅ Created: {config_file}")
    
    print("\n" + "="*80)
    print(" IMPLEMENTATION COMPLETE")
    print("="*80)
    
    print("\n📋 Next Steps:")
    print("   1. Review AUTH_IMPLEMENTATION_GUIDE.md")
    print("   2. Update api/main.py to include auth router:")
    print("      from api.routers import auth_login")
    print("      app.include_router(auth_login.router, tags=['Authentication'])")
    print("   3. Restart backend server")
    print("   4. Test login endpoint: python test_auth_setup.py")
    print("\n")

if __name__ == "__main__":
    main()
