"""
Community Commerce Router - Stock Swapping & Bulk Buying API
Marketplace for retailers to collaborate
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from api.db.database import get_db
from api.db.models import User
from api.services.community_service import CommunityCommerceService
from api.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/community", tags=["community"])

# ==================== REQUEST/RESPONSE MODELS ====================

class CreateListingRequest(BaseModel):
    retailer_id: int
    product_id: int
    quantity: int = Field(gt=0)
    price_per_unit: float = Field(gt=0)
    reason: str = Field(..., description="dead_stock, overstock, seasonal")
    location: str = Field(..., min_length=1)
    expires_days: int = Field(default=30, ge=1, le=365)

class CreateBulkBuyRequest(BaseModel):
    coordinator_id: int
    product_id: int
    target_quantity: int = Field(gt=0)
    target_price: float = Field(gt=0)
    deadline_days: int = Field(default=14, ge=1, le=90)

class JoinBulkBuyRequest(BaseModel):
    retailer_id: int
    quantity: int = Field(gt=0)

class ListingResponse(BaseModel):
    id: int
    retailer_id: int
    product_id: int
    quantity_available: int
    price_per_unit: float
    reason: str
    location: str
    status: str
    
    class Config:
        from_attributes = True

class BulkBuyGroupResponse(BaseModel):
    id: int
    product_id: int
    target_quantity: int
    current_quantity: int
    target_price: float
    status: str
    
    class Config:
        from_attributes = True

# ==================== STOCK SWAPPING ENDPOINTS ====================

@router.post("/listings", response_model=ListingResponse, status_code=201)
async def create_stock_listing(
    request: CreateListingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a stock swap listing
    
    **Perfect for:**
    - Clearing dead stock (no sales >180 days)
    - Selling overstock
    - Seasonal clearance
    """
    service = CommunityCommerceService(db)
    
    listing = service.create_stock_listing(
        retailer_id=request.retailer_id,
        product_id=request.product_id,
        quantity=request.quantity,
        price_per_unit=Decimal(str(request.price_per_unit)),
        reason=request.reason,
        location=request.location,
        expires_days=request.expires_days
    )
    
    return listing

@router.get("/listings", response_model=List[ListingResponse])
async def get_available_listings(
    location: Optional[str] = Query(None),
    reason: Optional[str] = Query(None, description="dead_stock, overstock, seasonal"),
    product_category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Browse available stock swap listings
    
    **Filter by:**
    - Location (your city/area)
    - Reason (dead_stock, overstock, seasonal)
    - Product category
    """
    service = CommunityCommerceService(db)
    return service.get_available_listings(location, reason, product_category, limit)

@router.get("/listings/match/{product_id}")
async def find_matching_listings(
    product_id: int,
    location: str = Query(...),
    max_distance_km: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Find listings that match your buying needs"""
    service = CommunityCommerceService(db)
    return service.find_matching_listings(product_id, location, max_distance_km)

@router.post("/listings/{listing_id}/match")
async def mark_listing_matched(
    listing_id: int,
    buyer_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a listing as matched with a buyer"""
    try:
        service = CommunityCommerceService(db)
        listing = service.mark_listing_matched(listing_id, buyer_id)
        return {"status": "matched", "listing_id": listing.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dead-stock-opportunities")
async def get_dead_stock_opportunities(
    min_days_no_sale: int = Query(180, ge=30),
    db: Session = Depends(get_db)
):
    """
    Find your dead stock that could be listed
    
    **Returns:**
    - Products with no sales >180 days
    - Suggested pricing (70% of cost)
    - Not already listed
    """
    service = CommunityCommerceService(db)
    return service.get_dead_stock_opportunities(min_days_no_sale)

# ==================== BULK BUYING ENDPOINTS ====================

@router.post("/bulk-buy", response_model=BulkBuyGroupResponse, status_code=201)
async def create_bulk_buy_group(
    request: CreateBulkBuyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a bulk buying group
    
    **Benefits:**
    - Lower prices through volume
    - Share shipping costs
    - Coordinated purchasing
    """
    service = CommunityCommerceService(db)
    
    group = service.create_bulk_buy_group(
        coordinator_id=request.coordinator_id,
        product_id=request.product_id,
        target_quantity=request.target_quantity,
        target_price=Decimal(str(request.target_price)),
        deadline_days=request.deadline_days
    )
    
    return group

@router.post("/bulk-buy/{group_id}/join")
async def join_bulk_buy_group(
    group_id: int,
    request: JoinBulkBuyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Join a bulk buying group
    
    - Add your quantity to the group
    - Automatically updates group progress
    - Group marked "ready" when target reached
    """
    try:
        service = CommunityCommerceService(db)
        participant = service.join_bulk_buy_group(
            group_id=group_id,
            retailer_id=request.retailer_id,
            quantity=request.quantity
        )
        
        return {
            "status": "joined",
            "participant_id": participant.id,
            "quantity": participant.quantity
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bulk-buy", response_model=List[BulkBuyGroupResponse])
async def get_active_bulk_buy_groups(
    product_category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Browse active bulk buying groups"""
    service = CommunityCommerceService(db)
    return service.get_active_bulk_buy_groups(product_category, limit)

@router.get("/bulk-buy/{group_id}")
async def get_bulk_buy_details(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a bulk buy group
    
    **Returns:**
    - Group progress (current/target quantity)
    - List of participants
    - Deadline
    - Status
    """
    try:
        service = CommunityCommerceService(db)
        return service.get_bulk_buy_details(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/bulk-buy/{group_id}/finalize")
async def finalize_bulk_buy(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Finalize bulk buy and place order
    
    **Requirements:**
    - Group status must be "ready"
    - Target quantity reached
    """
    try:
        service = CommunityCommerceService(db)
        group = service.finalize_bulk_buy(group_id)
        return {
            "status": "finalized",
            "group_id": group.id,
            "order_status": group.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== MARKETPLACE STATS ====================

@router.get("/stats")
async def get_marketplace_stats(db: Session = Depends(get_db)):
    """
    Get Community Commerce marketplace statistics
    
    **Metrics:**
    - Active stock swap listings
    - Match rate
    - Active bulk buy groups
    - Participants
    """
    service = CommunityCommerceService(db)
    return service.get_marketplace_stats()
