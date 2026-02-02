"""
Zoho Books Integration API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from api.db.session import get_db
from api.integrations.zoho_auth import ZohoAuthService, ZohoOAuthError
from api.integrations.zoho_client import ZohoClient, ZohoAPIError
from api.middleware.auth import get_current_user
from api.schemas.user import User


router = APIRouter(prefix="/integrations/zoho", tags=["Zoho Books Integration"])


# ========== OAuth Endpoints ==========

@router.get("/authorize")
async def authorize_zoho(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate Zoho Books OAuth authorization flow
    
    Returns authorization URL to redirect user to
    """
    try:
        auth_service = ZohoAuthService(db)
        
        result = await auth_service.get_authorization_url(organization_id)
        
        return {
            "authorization_url": result["authorization_url"],
            "state": result["state"],
            "message": "Redirect user to authorization_url"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")


@router.get("/callback")
async def zoho_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: Optional[str] = Query(None, description="CSRF state token"),
    organization_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db)
):
    """
    OAuth callback endpoint
    
    Zoho redirects here after user authorization
    """
    try:
        auth_service = ZohoAuthService(db)
        
        # Exchange code for token
        result = await auth_service.exchange_code_for_token(code, organization_id, state)
        
        return {
            "success": True,
            "message": "Successfully connected to Zoho Books",
            "organization_id": organization_id,
            "expires_in": result["expires_in"]
        }
        
    except ZohoOAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.get("/status")
async def get_connection_status(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Zoho Books connection status for organization"""
    try:
        auth_service = ZohoAuthService(db)
        status = await auth_service.get_connection_status(organization_id)
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/disconnect")
async def disconnect_zoho(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect from Zoho Books (revoke access)"""
    try:
        auth_service = ZohoAuthService(db)
        success = await auth_service.revoke_token(organization_id)
        
        if success:
            return {
                "success": True,
                "message": "Disconnected from Zoho Books"
            }
        else:
            raise HTTPException(status_code=404, detail="No connection found")
            
    except ZohoOAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== API Test Endpoint ==========

@router.post("/test-connection")
async def test_zoho_connection(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connection to Zoho Books API"""
    try:
        auth_service =ZohoOAuthService(db)
        client = ZohoClient(auth_service, organization_id)
        
        result = await client.test_connection()
        await client.close()
        
        return result
        
    except ZohoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Items (Products) Endpoints ==========

@router.get("/items")
async def get_zoho_items(
    organization_id: str = Query(..., description="Organization ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(200, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get items (products) from Zoho Books"""
    try:
        auth_service = ZohoAuthService(db)
        client = ZohoClient(auth_service, organization_id)
        
        result = await client.get_items(page=page, per_page=per_page)
        await client.close()
        
        return result
        
    except ZohoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items")
async def create_zoho_item(
    item_data: dict,
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create item in Zoho Books"""
    try:
        auth_service = ZohoAuthService(db)
        client = ZohoClient(auth_service, organization_id)
        
        result = await client.create_item(item_data)
        await client.close()
        
        return result
        
    except ZohoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Contacts (Customers) Endpoints ==========

@router.get("/contacts")
async def get_zoho_contacts(
    organization_id: str = Query(..., description="Organization ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(200, ge=1, le=200, description="Contacts per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get contacts (customers) from Zoho Books"""
    try:
        auth_service = ZohoAuthService(db)
        client = ZohoClient(auth_service, organization_id)
        
        result = await client.get_contacts(page=page, per_page=per_page)
        await client.close()
        
        return result
        
    except ZohoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Invoices Endpoints ==========

@router.post("/invoices")
async def create_zoho_invoice(
    invoice_data: dict,
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create invoice in Zoho Books"""
    try:
        auth_service = ZohoAuthService(db)
        client = ZohoClient(auth_service, organization_id)
        
        result = await client.create_invoice(invoice_data)
        await client.close()
        
        return result
        
    except ZohoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices")
async def get_zoho_invoices(
    organization_id: str = Query(..., description="Organization ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(200, ge=1, le=200, description="Invoices per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoices from Zoho Books"""
    try:
        auth_service = ZohoAuthService(db)
        client = ZohoClient(auth_service, organization_id)
        
        result = await client.get_invoices(page=page, per_page=per_page)
        await client.close()
        
        return result
        
    except ZohoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
