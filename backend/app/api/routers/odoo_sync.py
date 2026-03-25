"""
Odoo Sync API Router
Endpoints to manage Odoo integration and trigger syncs
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict

from app.api.db.database_postgres import get_db
from app.api.integrations.odoo_connector import OdooClient
from sqlalchemy import text
# In production, we would use a DB model to fetch credentials
# from app.api.db.models import OdooConfig, Organization 

router = APIRouter(prefix="/api/v1/integrations/odoo", tags=["Integrations"])

# --- Pydantic Models ---
class OdooConfigCreate(BaseModel):
    url: str
    db_name: str
    username: str
    api_key: str
    sync_products: bool = True
    sync_customers: bool = True
    organization_id: str # Simplified for demo

class OdooConfigResponse(BaseModel):
    id: str
    url: str
    username: str
    sync_products: bool
    sync_customers: bool
    is_active: bool
    last_sync_at: Optional[str] = None
    last_sync_status: Optional[str] = None

class OdooConnectionRequest(BaseModel):
    url: str
    db_name: str
    username: str
    api_key: str

class OdooSyncResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict] = None

# --- Helpers ---
def get_odoo_client_from_request(req: OdooConnectionRequest) -> OdooClient:
    return OdooClient(req.url, req.db_name, req.username, req.api_key)

# --- Routes ---

@router.post("/test-connection", response_model=OdooSyncResponse)
async def test_odoo_connection(config: OdooConnectionRequest):
    """Test connection with provided Odoo credentials"""
    client = get_odoo_client_from_request(config)
    result = client.test_connection()
    
    if result.get("success"):
        return {
            "status": "success",
            "message": "Successfully connected to Odoo",
            "details": {
                "server_version": result.get("version"),
                "uid": result.get("uid")
            }
        }
    else:
        raise HTTPException(status_code=400, detail=f"Connection failed: {result.get('error')}")

@router.post("/config", response_model=Dict)
async def save_odoo_config(config: OdooConfigCreate, db: Session = Depends(get_db)):
    """Save or Update Odoo Configuration"""
    try:
        # Check if config exists for org
        result = db.execute(text("SELECT id FROM odoo_configs WHERE organization_id = :org_id"), {"org_id": config.organization_id})
        existing = result.fetchone()
        
        if existing:
            # Update
            query = text("""
                UPDATE odoo_configs 
                SET url = :url, db_name = :db_name, username = :username, api_key = :api_key, 
                    sync_products = :sync_products, sync_customers = :sync_customers, updated_at = NOW()
                WHERE organization_id = :org_id
            """)
        else:
            # Insert
            query = text("""
                INSERT INTO odoo_configs (organization_id, url, db_name, username, api_key, sync_products, sync_customers)
                VALUES (:org_id, :url, :db_name, :username, :api_key, :sync_products, :sync_customers)
            """)
            
        db.execute(query, {
            "org_id": config.organization_id,
            "url": config.url,
            "db_name": config.db_name,
            "username": config.username,
            "api_key": config.api_key,
            "sync_products": config.sync_products,
            "sync_customers": config.sync_customers
        })
        db.commit()
        return {"status": "success", "message": "Odoo configuration saved successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/{organization_id}", response_model=OdooConfigResponse)
async def get_odoo_config(organization_id: str, db: Session = Depends(get_db)):
    """Get Odoo Configuration (Masked)"""
    result = db.execute(text("SELECT * FROM odoo_configs WHERE organization_id = :org_id"), {"org_id": organization_id})
    config = result.fetchone()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    return {
        "id": str(config.id),
        "url": config.url,
        "username": config.username,
        "sync_products": config.sync_products,
        "sync_customers": config.sync_customers,
        "is_active": config.is_active,
        "last_sync_at": str(config.last_sync_at) if config.last_sync_at else None,
        "last_sync_status": config.last_sync_status
    }

@router.post("/sync/products")
async def sync_products(config: OdooConnectionRequest, background_tasks: BackgroundTasks):
    """Trigger background product sync (Demo: returns immediate count)"""
    client = get_odoo_client_from_request(config)
    
    if not client.connect():
         raise HTTPException(status_code=400, detail="Could not authenticate with Odoo")

    # In a real app, this would be a background task saving to DB
    # For demo, we just fetch to prove it works
    products = client.get_products(limit=5)
    
    return {
        "status": "success",
        "message": f"Fetched {len(products)} products from Odoo",
        "data": products # Returning data just for demo/verification
    }

@router.post("/sync/customers")
async def sync_customers(config: OdooConnectionRequest):
    """Trigger customer sync"""
    client = get_odoo_client_from_request(config)
    if not client.connect():
         raise HTTPException(status_code=400, detail="Connection failed")
         
    customers = client.get_customers(limit=5)
    return {
        "status": "success",
        "message": f"Fetched {len(customers)} customers from Odoo",
        "data": customers
    }
