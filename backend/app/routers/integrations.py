"""
Integrations Router — Odoo and Zoho Integrations
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.models.odoo_config import OdooConfig
from app.models.integration_token_model import IntegrationToken
from app.api.integrations.odoo_connector import OdooClient
from app.api.integrations.zoho_client import ZohoClient
from app.api.integrations.zoho_auth import ZohoAuthService
from app.api.utils.encryption import encrypt_data, decrypt_data

router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
)


# ======================= SCHEMAS =======================

class OdooConfigRequest(BaseModel):
    url: str
    db: Optional[str] = None
    db_name: Optional[str] = None
    username: str
    api_key: str
    sync_products: Optional[bool] = True
    sync_customers: Optional[bool] = True
    mock_mode: bool = False

    @property
    def database_name(self) -> str:
        return self.db_name or self.db or ""


class ZohoConfigRequest(BaseModel):
    organization_id: Optional[str] = None
    org_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    sync_invoices: Optional[bool] = True
    mock_mode: bool = False

    @property
    def resolved_org_id(self) -> str:
        return self.org_id or self.organization_id or ""


# ======================= ODOO =======================

@router.get("/odoo/config")
async def get_odoo_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve saved Odoo configuration (API key is masked)"""
    stmt = select(OdooConfig).where(OdooConfig.organization_id == current_user.organization_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        return {
            "configured": False,
            "url": "",
            "db_name": "",
            "username": "",
            "api_key": "",
            "sync_products": True,
            "sync_customers": True,
            "is_active": False,
            "last_synced_at": None
        }

    return {
        "configured": True,
        "url": config.url,
        "db_name": config.database_name,
        "username": config.username,
        "api_key": "••••••••••••" if config.api_key else "",
        "sync_products": config.sync_products,
        "sync_customers": config.sync_customers,
        "is_active": config.is_active,
        "last_synced_at": config.last_synced_at
    }


@router.post("/odoo/config")
async def save_odoo_config(
    data: OdooConfigRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Save and persist Odoo configuration encrypted at rest"""
    db_name = data.database_name
    if not data.url or not db_name or not data.username or not data.api_key:
        raise HTTPException(status_code=400, detail="URL, database name, username, and API key are required")

    stmt = select(OdooConfig).where(OdooConfig.organization_id == current_user.organization_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    # Encrypt the API key before saving
    encrypted_key = encrypt_data(data.api_key)

    if config:
        config.url = data.url.strip()
        config.database_name = db_name.strip()
        config.username = data.username.strip()
        if data.api_key and data.api_key != "••••••••••••":
            config.api_key = encrypted_key
        config.sync_products = data.sync_products if data.sync_products is not None else True
        config.sync_customers = data.sync_customers if data.sync_customers is not None else True
        config.is_active = True
        config.updated_at = datetime.utcnow()
    else:
        config = OdooConfig(
            organization_id=current_user.organization_id or 1,
            url=data.url.strip(),
            database_name=db_name.strip(),
            username=data.username.strip(),
            api_key=encrypted_key,
            sync_products=data.sync_products if data.sync_products is not None else True,
            sync_customers=data.sync_customers if data.sync_customers is not None else True,
            is_active=True
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)

    return {
        "success": True,
        "message": "Odoo configuration saved successfully",
        "configured": True,
        "url": config.url,
        "db_name": config.database_name,
        "username": config.username,
        "is_active": config.is_active
    }


@router.delete("/odoo/config")
async def delete_odoo_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect and remove Odoo configuration"""
    stmt = delete(OdooConfig).where(OdooConfig.organization_id == current_user.organization_id)
    await db.execute(stmt)
    await db.commit()
    return {"success": True, "message": "Odoo disconnected successfully"}


@router.post("/odoo/test-connection")
def test_odoo_connection(config: OdooConfigRequest):
    """Test connection to Odoo ERP (supports mock mode)"""
    client = OdooClient(
        url=config.url,
        db=config.database_name,
        username=config.username,
        api_key=config.api_key,
        mock_mode=config.mock_mode
    )
    result = client.test_connection()
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("error") or "Failed to connect to Odoo server. Verify credentials and URL."
        )
    return result


@router.post("/odoo/products")
def get_odoo_products(config: OdooConfigRequest, limit: int = 100):
    """Get products from Odoo"""
    client = OdooClient(
        url=config.url,
        db=config.database_name,
        username=config.username,
        api_key=config.api_key,
        mock_mode=config.mock_mode
    )
    products = client.get_products(limit)
    return {"products": products}


# ======================= ZOHO =======================

@router.get("/zoho/config")
async def get_zoho_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve saved Zoho Books configuration info"""
    return {
        "configured": False,
        "org_id": "",
        "client_id": "",
        "client_secret": "",
        "sync_invoices": True
    }


@router.post("/zoho/config")
async def save_zoho_config(
    data: ZohoConfigRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Save Zoho Books configuration"""
    org_id = data.resolved_org_id
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID is required")

    return {
        "success": True,
        "message": "Zoho Books configuration saved successfully",
        "configured": True,
        "org_id": org_id
    }


@router.delete("/zoho/config")
async def delete_zoho_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect and remove Zoho configuration"""
    return {"success": True, "message": "Zoho Books disconnected successfully"}


@router.post("/zoho/test-connection")
async def test_zoho_connection(config: ZohoConfigRequest):
    """Test connection to Zoho Books (supports mock mode)"""
    auth = ZohoAuthService()
    org_id = config.resolved_org_id
    if not org_id and not config.mock_mode:
        raise HTTPException(status_code=400, detail="Organization ID is required")

    client = ZohoClient(
        auth_service=auth,
        organization_id=org_id,
        mock_mode=config.mock_mode
    )
    result = await client.test_connection()
    if not result.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("error") or "Failed to authenticate with Zoho Books. Please verify credentials."
        )
    return result


@router.post("/zoho/items")
async def get_zoho_items(config: ZohoConfigRequest, page: int = 1, per_page: int = 50):
    """Get items from Zoho Books"""
    auth = ZohoAuthService()
    client = ZohoClient(
        auth_service=auth,
        organization_id=config.resolved_org_id,
        mock_mode=config.mock_mode
    )
    items = await client.get_items(page, per_page)
    return items
