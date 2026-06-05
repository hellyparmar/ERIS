"""
Zoho Books OAuth 2.0 Authentication
Handles OAuth flow, token management, and refresh
"""

import os
from sqlalchemy import select
import secrets
from datetime import datetime, timedelta
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.api.db.models import IntegrationToken
from app.api.utils.encryption import encrypt_data, decrypt_data


# Zoho OAuth configuration
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/zoho/callback")
ZOHO_ACCOUNTS_URL = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")  # .in for India, .com for global
ZOHO_API_BASE_URL = os.getenv("ZOHO_API_BASE_URL", "https://books.zoho.in/api/v3")

# OAuth endpoints
AUTHORIZE_URL = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/auth"
TOKEN_URL = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token"
REVOKE_URL = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token/revoke"

# Required scopes
SCOPES = [
    "ZohoBooks.fullaccess.all",  # Full access to Zoho Books
]


class ZohoOAuthError(Exception):
    """Custom exception for Zoho OAuth errors"""
    pass


class ZohoAuthService:
    """Handles Zoho Books OAuth authentication"""

    def __init__(self, db: Session):
        self.db = db
        self.client = httpx.AsyncClient()

    async def get_authorization_url(self, organization_id: str) -> dict:
        """
        Generate OAuth authorization URL
        
        Args:
            organization_id: R-DIOS organization ID
            
        Returns:
            dict with authorization URL and state
        """
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session/cache (you'll need to implement session storage)
        # For now, return it to be stored client-side
        
        params = {
            "client_id": ZOHO_CLIENT_ID,
            "redirect_uri": ZOHO_REDIRECT_URI,
            "response_type": "code",
            "scope": ",".join(SCOPES),
            "state": state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent"  # Force consent screen
        }
        
        # Build authorization URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{AUTHORIZE_URL}?{query_string}"
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "organization_id": organization_id
        }

    async def exchange_code_for_token(
        self, 
        code: str, 
        organization_id: str,
        state: str = None
    ) -> dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            organization_id: R-DIOS organization ID
            state: CSRF token (optional, should validate)
            
        Returns:
            dict with token information
        """
        try:
            # Exchange code for token
            response = await self.client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": ZOHO_CLIENT_ID,
                    "client_secret": ZOHO_CLIENT_SECRET,
                    "redirect_uri": ZOHO_REDIRECT_URI,
                    "grant_type": "authorization_code"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise ZohoOAuthError(f"Token exchange failed: {response.text}")
            
            token_data = response.json()
            
            # Validate response
            if "access_token" not in token_data:
                raise ZohoOAuthError("No access token in response")
            
            # Save tokens to database
            await self._save_tokens(organization_id, token_data)
            
            return {
                "success": True,
                "access_token": token_data["access_token"],
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in", 3600),
                "organization_id": organization_id
            }
            
        except httpx.HTTPError as e:
            raise ZohoOAuthError(f"HTTP error during token exchange: {str(e)}")
        except Exception as e:
            raise ZohoOAuthError(f"Unexpected error: {str(e)}")

    async def _save_tokens(self, organization_id: str, token_data: dict):
        """
        Save or update tokens in database
        
        Args:
            organization_id: R-DIOS organization ID
            token_data: Token data from Zoho
        """
        # Calculate expiry time
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Encrypt sensitive tokens
        encrypted_access_token = encrypt_data(token_data["access_token"])
        encrypted_refresh_token = encrypt_data(token_data.get("refresh_token", ""))
        
        # Check if token already exists
        existing_token = self.db.query(IntegrationToken).filter(
            IntegrationToken.organization_id == organization_id,
            IntegrationToken.integration_type == "zoho_books"
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.access_token = encrypted_access_token
            existing_token.refresh_token = encrypted_refresh_token
            existing_token.token_type = token_data.get("token_type", "Bearer")
            existing_token.expires_at = expires_at
            existing_token.scopes = ",".join(SCOPES)
            existing_token.updated_at = datetime.utcnow()
        else:
            # Create new token
            new_token = IntegrationToken(
                organization_id=organization_id,
                integration_type="zoho_books",
                access_token=encrypted_access_token,
                refresh_token=encrypted_refresh_token,
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=expires_at,
                scopes=",".join(SCOPES),
                additional_data=token_data.get("api_domain")  # Store API domain if provided
            )
            self.db.add(new_token)
        
        self.db.commit()

    async def get_valid_token(self, organization_id: str) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary
        
        Args:
            organization_id: R-DIOS organization ID
            
        Returns:
            Valid access token or None if not connected
        """
        # Get token from database
        token_record = self.db.query(IntegrationToken).filter(
            IntegrationToken.organization_id == organization_id,
            IntegrationToken.integration_type == "zoho_books"
        ).first()
        
        if not token_record:
            return None
        
        # Check if token is expired (with 5-minute buffer)
        if token_record.expires_at <= datetime.utcnow() + timedelta(minutes=5):
            # Token expired or about to expire, refresh it
            await self.refresh_access_token(organization_id)
            
            # Re-fetch token
            token_record = self.db.query(IntegrationToken).filter(
                IntegrationToken.organization_id == organization_id,
                IntegrationToken.integration_type == "zoho_books"
            ).first()
        
        if not token_record:
            return None
        
        # Decrypt and return access token
        return decrypt_data(token_record.access_token)

    async def refresh_access_token(self, organization_id: str) -> dict:
        """
        Refresh access token using refresh token
        
        Args:
            organization_id: R-DIOS organization ID
            
        Returns:
            dict with new token information
        """
        # Get current token
        token_record = self.db.query(IntegrationToken).filter(
            IntegrationToken.organization_id == organization_id,
            IntegrationToken.integration_type == "zoho_books"
        ).first()
        
        if not token_record or not token_record.refresh_token:
            raise ZohoOAuthError("No refresh token available")
        
        # Decrypt refresh token
        refresh_token = decrypt_data(token_record.refresh_token)
        
        try:
            # Request new access token
            response = await self.client.post(
                TOKEN_URL,
                data={
                    "refresh_token": refresh_token,
                    "client_id": ZOHO_CLIENT_ID,
                    "client_secret": ZOHO_CLIENT_SECRET,
                    "grant_type": "refresh_token"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise ZohoOAuthError(f"Token refresh failed: {response.text}")
            
            token_data = response.json()
            
            # Save new tokens
            await self._save_tokens(organization_id, {
                **token_data,
                "refresh_token": refresh_token  # Keep existing refresh token
            })
            
            return {
                "success": True,
                "access_token": token_data["access_token"],
                "expires_in": token_data.get("expires_in", 3600)
            }
            
        except httpx.HTTPError as e:
            raise ZohoOAuthError(f"HTTP error during token refresh: {str(e)}")

    async def revoke_token(self, organization_id: str) -> bool:
        """
        Revoke access token and delete from database
        
        Args:
            organization_id: R-DIOS organization ID
            
        Returns:
            True if successful
        """
        # Get token
        token = await self.get_valid_token(organization_id)
        
        if not token:
            return False
        
        try:
            # Revoke token on Zoho
            response = await self.client.post(
                REVOKE_URL,
                data={"token": token},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Delete from database regardless of Zoho response
            self.db.query(IntegrationToken).filter(
                IntegrationToken.organization_id == organization_id,
                IntegrationToken.integration_type == "zoho_books"
            ).delete()
            self.db.commit()
            
            return True
            
        except Exception as e:
            # Still try to delete from database
            try:
                self.db.query(IntegrationToken).filter(
                    IntegrationToken.organization_id == organization_id,
                    IntegrationToken.integration_type == "zoho_books"
                ).delete()
                self.db.commit()
            except:
                pass
            
            raise ZohoOAuthError(f"Error revoking token: {str(e)}")

    async def get_connection_status(self, organization_id: str) -> dict:
        """
        Check if organization is connected to Zoho Books
        
        Args:
            organization_id: R-DIOS organization ID
            
        Returns:
            dict with connection status
        """
        token_record = self.db.query(IntegrationToken).filter(
            IntegrationToken.organization_id == organization_id,
            IntegrationToken.integration_type == "zoho_books"
        ).first()
        
        if not token_record:
            return {
                "connected": False,
                "message": "Not connected to Zoho Books"
            }
        
        # Check if token is valid
        is_expired = token_record.expires_at <= datetime.utcnow()
        
        return {
            "connected": True,
            "expires_at": token_record.expires_at.isoformat(),
            "is_expired": is_expired,
            "scopes": token_record.scopes.split(",") if token_record.scopes else [],
            "connected_at": token_record.created_at.isoformat()
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
