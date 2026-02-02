"""
Authentication Tests
Test user registration, login, token refresh, and protected routes
"""

import pytest
from fastapi import status

def test_register_new_user(client):
    """Test user registration with valid data"""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert data["role"] == "user"
    assert "password" not in data  # Password should not be returned

def test_register_duplicate_username(client, test_user):
    """Test registration with existing username fails"""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()

def test_register_duplicate_email(client, test_user):
    """Test registration with existing email fails"""
    response = client.post(
        "/auth/register",
        json={
            "username": "different_user",
            "email": "test@example.com",  # Already exists
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()

def test_register_weak_password(client):
    """Test registration with weak password fails"""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "123"  # Too short
        }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_login_with_valid_credentials(client, test_user):
    """Test login with correct username and password"""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "TestPass123!"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0

def test_login_with_invalid_username(client):
    """Test login with non-existent username fails"""
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent", "password": "SomePassword123!"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()

def test_login_with_invalid_password(client, test_user):
    """Test login with wrong password fails"""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "WrongPassword123!"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()

def test_access_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without authentication fails"""
    response = client.post(
        "/api/invoices/create",
        json={"sale_id": 1, "payment_terms_days": 30}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_access_protected_endpoint_with_invalid_token(client):
    """Test accessing protected endpoint with invalid token fails"""
    response = client.post(
        "/api/invoices/create",
        json={"sale_id": 1, "payment_terms_days": 30},
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_access_protected_endpoint_with_valid_token(client, auth_headers):
    """Test accessing protected endpoint with valid token works"""
    # This will fail with 404 (sale not found) but that means auth passed!
    response = client.post(
        "/api/invoices/create",
        json={"sale_id": 999, "payment_terms_days": 30},
        headers=auth_headers
    )
    
    # Should get past authentication (401) but fail on business logic
    assert response.status_code != status.HTTP_401_UNAUTHORIZED
    # Will be 404 (sale not found) or 500 (other error) - that's OK for this test

def test_get_current_user_info(client, auth_headers, test_user):
    """Test getting current user information"""
    response = client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

def test_token_refresh(client, test_user):
    """Test refreshing access token with refresh token"""
    # First login
    login_response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "TestPass123!"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_token_refresh_with_invalid_token(client):
    """Test token refresh with invalid refresh token fails"""
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid_refresh_token"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_change_password(client, auth_headers, test_user):
    """Test changing user password"""
    response = client.post(
        "/auth/change-password",
        params={
            "old_password": "TestPass123!",
            "new_password": "NewSecurePass456!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verify can login with new password
    login_response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "NewSecurePass456!"}
    )
    assert login_response.status_code == status.HTTP_200_OK

def test_change_password_with_wrong_old_password(client, auth_headers):
    """Test changing password with incorrect old password fails"""
    response = client.post(
        "/auth/change-password",
        params={
            "old_password": "WrongOldPassword!",
            "new_password": "NewSecurePass456!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "incorrect" in response.json()["detail"].lower()

def test_admin_endpoint_requires_admin_role(client, auth_headers, admin_headers):
    """Test admin-only endpoints reject regular users"""
    # Regular user should be rejected
    response = client.post("/api/invoices/mark-overdue", headers=auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Admin should be allowed (will fail on business logic but auth passes)
    response = client.post("/api/invoices/mark-overdue", headers=admin_headers)
    assert response.status_code != status.HTTP_403_FORBIDDEN
