# JWT Authentication Implementation Guide

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
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
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
curl -X GET "http://localhost:8000/api/analytics/sales/summary" \
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
