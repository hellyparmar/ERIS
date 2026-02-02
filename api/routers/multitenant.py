"""
Organizations & Stores API Routes
Multi-tenant management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from api.schemas.multitenant import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationSummary, OrganizationStats,
    Store, StoreCreate, StoreUpdate, StoreSummary, StoreStats,
    StoreTransferRequest, UserStoreAccess, UpdateUserStoreAccess
)
from api.db.multitenant_models import Organization as OrgModel, Store as StoreModel
from api.middleware.tenant_context import get_current_organization, require_organization
from api.dependencies import get_db, get_current_user
from sqlalchemy import func

router = APIRouter(prefix="/api/v1", tags=["Multi-Tenant"])


# ============================================================
# ORGANIZATION ENDPOINTS
# ============================================================

@router.get("/organizations/current", response_model=Organization)
async def get_current_organization_details(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's organization details"""
    org_id = current_user.get('organization_id')
    
    if not org_id:
        raise HTTPException(404, "User has no organization")
    
    org = db.query(OrgModel).filter(OrgModel.id == org_id).first()
    
    if not org:
        raise HTTPException(404, "Organization not found")
    
    return org


@router.put("/organizations/current", response_model=Organization)
async def update_current_organization(
    org_update: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current organization details (owner/admin only)"""
    # Check permissions
    if current_user.get('role') not in ['owner', 'admin']:
        raise HTTPException(403, "Only owner or admin can update organization")
    
    org_id = current_user.get('organization_id')
    org = db.query(OrgModel).filter(OrgModel.id == org_id).first()
    
    if not org:
        raise HTTPException(404, "Organization not found")
    
    # Update fields
    update_data = org_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)
    
    db.commit()
    db.refresh(org)
    
    return org


@router.get("/organizations/stats", response_model=OrganizationStats)
async def get_organization_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get organization statistics"""
    org_id = current_user.get('organization_id')
    
    # Count stores
    total_stores = db.query(StoreModel).filter(
        StoreModel.organization_id == org_id
    ).count()
    
    active_stores = db.query(StoreModel).filter(
        StoreModel.organization_id == org_id,
        StoreModel.is_active == True
    ).count()
    
    # TODO: Add more stats queries
    # - total_products
    # - total_customers
    # - invoices_this_month
    # - revenue_this_month
    
    return OrganizationStats(
        total_stores=total_stores,
        active_stores=active_stores,
        total_products=0,  # Placeholder
        total_customers=0,
        total_invoices_this_month=0,
        revenue_this_month=0.0,
        storage_used_mb=0.0
    )


# ============================================================
# STORE ENDPOINTS
# ============================================================

@router.get("/stores", response_model=List[Store])
async def list_stores(
    request: Request,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all stores in organization"""
    org_id = current_user.get('organization_id')
    
    query = db.query(StoreModel).filter(StoreModel.organization_id == org_id)
    
    if active_only:
        query = query.filter(StoreModel.is_active == True)
    
    stores = query.order_by(StoreModel.created_at.desc()).all()
    
    return stores


@router.get("/stores/{store_id}", response_model=Store)
async def get_store(
    store_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get store by ID"""
    store = db.query(StoreModel).filter(
        StoreModel.id == store_id,
        StoreModel.organization_id == current_user.get('organization_id')
    ).first()
    
    if not store:
        raise HTTPException(404, "Store not found")
    
    return store


@router.post("/stores", response_model=Store, status_code=status.HTTP_201_CREATED)
async def create_store(
    store: StoreCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new store (owner/admin/manager only)"""
    # Check permissions
    if current_user.get('role') not in ['owner', 'admin', 'manager']:
        raise HTTPException(403, "Only owner/admin/manager can create stores")
    
    org_id = current_user.get('organization_id')
    
    # Check if code already exists
    if store.code:
        existing = db.query(StoreModel).filter(
            StoreModel.organization_id == org_id,
            StoreModel.code == store.code
        ).first()
        
        if existing:
            raise HTTPException(400, f"Store with code '{store.code}' already exists")
    
    # Create store
    new_store = StoreModel(**store.dict())
    new_store.organization_id = org_id
    
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    
    return new_store


@router.put("/stores/{store_id}", response_model=Store)
async def update_store(
    store_id: UUID,
    store_update: StoreUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update store details"""
    # Check permissions
    if current_user.get('role') not in ['owner', 'admin', 'manager']:
        raise HTTPException(403, "Only owner/admin/manager can update stores")
    
    store = db.query(StoreModel).filter(
        StoreModel.id == store_id,
        StoreModel.organization_id == current_user.get('organization_id')
    ).first()
    
    if not store:
        raise HTTPException(404, "Store not found")
    
    # Update fields
    update_data = store_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(store, key, value)
    
    db.commit()
    db.refresh(store)
    
    return store


@router.delete("/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: UUID,
    soft_delete: bool = True,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete store (owner/admin only)"""
    # Check permissions
    if current_user.get('role') not in ['owner', 'admin']:
        raise HTTPException(403, "Only owner/admin can delete stores")
    
    store = db.query(StoreModel).filter(
        StoreModel.id == store_id,
        StoreModel.organization_id == current_user.get('organization_id')
    ).first()
    
    if not store:
        raise HTTPException(404, "Store not found")
    
    if soft_delete:
        # Soft delete
        from datetime import datetime
        store.is_active = False
        store.deleted_at = datetime.now()
        db.commit()
    else:
        # Hard delete (careful!)
        db.delete(store)
        db.commit()
    
    return None


@router.get("/stores/{store_id}/stats", response_model=StoreStats)
async def get_store_stats(
    store_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get store statistics"""
    store = db.query(StoreModel).filter(
        StoreModel.id == store_id,
        StoreModel.organization_id == current_user.get('organization_id')
    ).first()
    
    if not store:
        raise HTTPException(404, "Store not found")
    
    # TODO: Implement actual stats queries
    
    return StoreStats(
        store_id=store.id,
        store_name=store.name,
        total_products=0,
        low_stock_items=0,
        invoices_today=0,
        revenue_today=0.0,
        revenue_this_month=0.0
    )


# ============================================================
# USER STORE ACCESS
# ============================================================

@router.get("/users/{user_id}/store-access", response_model=UserStoreAccess)
async def get_user_store_access(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's store access permissions (admin only)"""
    if current_user.get('role') not in ['owner', 'admin']:
        raise HTTPException(403, "Permission denied")
    
    # TODO: Query user and return store access
    
    raise HTTPException(501, "Not implemented yet")


@router.put("/users/{user_id}/store-access", response_model=UserStoreAccess)
async def update_user_store_access(
    user_id: UUID,
    access_update: UpdateUserStoreAccess,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update user's store access (admin only)"""
    if current_user.get('role') not in ['owner', 'admin']:
        raise HTTPException(403, "Permission denied")
    
    # TODO: Update user's assigned_stores
    
    raise HTTPException(501, "Not implemented yet")


# ============================================================
# MULTI-STORE OPERATIONS
# ============================================================

@router.post("/stores/transfer", status_code=status.HTTP_201_CREATED)
async def transfer_inventory_between_stores(
    transfer: StoreTransferRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Transfer inventory between stores"""
    if current_user.get('role') not in ['owner', 'admin', 'manager']:
        raise HTTPException(403, "Permission denied")
    
    # Verify both stores belong to organization
    org_id = current_user.get('organization_id')
    
    from_store = db.query(StoreModel).filter(
        StoreModel.id == transfer.from_store_id,
        StoreModel.organization_id == org_id
    ).first()
    
    to_store = db.query(StoreModel).filter(
        StoreModel.id == transfer.to_store_id,
        StoreModel.organization_id == org_id
    ).first()
    
    if not from_store or not to_store:
        raise HTTPException(404, "Store not found or access denied")
    
    # TODO: Implement actual inventory transfer logic
    # - Deduct from from_store inventory
    # - Add to to_store inventory
    # - Create inventory movement records
    
    raise HTTPException(501, "Transfer logic not implemented yet")
