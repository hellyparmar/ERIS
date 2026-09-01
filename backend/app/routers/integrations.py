"""
Integrations Router — Odoo and Zoho Integrations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.api.integrations.odoo_connector import OdooClient
from app.api.integrations.zoho_client import ZohoClient
from app.api.integrations.zoho_auth import ZohoAuthService

router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
)

class OdooConfigRequest(BaseModel):
    url: str
    db: str
    username: str
    api_key: str
    mock_mode: bool = False

class ZohoConfigRequest(BaseModel):
    organization_id: str
    mock_mode: bool = False

# ======================= ODOO =======================

@router.post("/odoo/test-connection")
def test_odoo_connection(config: OdooConfigRequest):
    """Test connection to Odoo ERP (supports mock mode)"""
    client = OdooClient(
        url=config.url,
        db=config.db,
        username=config.username,
        api_key=config.api_key,
        mock_mode=config.mock_mode
    )
    result = client.test_connection()
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result)
    return result

@router.post("/odoo/products")
def get_odoo_products(config: OdooConfigRequest, limit: int = 100):
    """Get products from Odoo"""
    client = OdooClient(
        url=config.url,
        db=config.db,
        username=config.username,
        api_key=config.api_key,
        mock_mode=config.mock_mode
    )
    products = client.get_products(limit)
    return {"products": products}

# ======================= ZOHO =======================

@router.post("/zoho/test-connection")
async def test_zoho_connection(config: ZohoConfigRequest):
    """Test connection to Zoho Books (supports mock mode)"""
    auth = ZohoAuthService()
    client = ZohoClient(
        auth_service=auth,
        organization_id=config.organization_id,
        mock_mode=config.mock_mode
    )
    result = await client.test_connection()
    if not result.get("connected"):
        raise HTTPException(status_code=502, detail=result)
    return result

@router.post("/zoho/items")
async def get_zoho_items(config: ZohoConfigRequest, page: int = 1, per_page: int = 50):
    """Get items from Zoho Books"""
    auth = ZohoAuthService()
    client = ZohoClient(
        auth_service=auth,
        organization_id=config.organization_id,
        mock_mode=config.mock_mode
    )
    items = await client.get_items(page, per_page)
    return items
