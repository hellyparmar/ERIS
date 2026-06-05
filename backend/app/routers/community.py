from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import get_db
from app.models import Product, Outlet, User
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/community", tags=["community"])

class ListingCreate(BaseModel):
    product_id: int
    listing_type: str = "sell"
    available_qty: int
    price_per_unit: float
    description: Optional[str] = None
    expires_at: Optional[date] = None

@router.get("/listings")
def get_listings(
    listing_type: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(CommunityListing, Product.name, Product.category, Product.sku, Outlet.name.label("outlet_name"), Outlet.city)
        .join(Product, Product.id == CommunityListing.product_id)
        .join(Outlet, Outlet.id == CommunityListing.outlet_id)
        .filter(CommunityListing.is_active == True)
    )
    if listing_type:
        q = q.filter(CommunityListing.listing_type == listing_type)
    if category:
        q = q.filter(Product.category == category)
    total = q.count()
    rows = q.order_by(CommunityListing.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "listings": [{
            "id": r.CommunityListing.id,
            "product_name": r.name,
            "category": r.category,
            "sku": r.sku,
            "outlet_name": r.outlet_name,
            "city": r.city,
            "listing_type": r.CommunityListing.listing_type,
            "available_qty": r.CommunityListing.available_qty,
            "price_per_unit": r.CommunityListing.price_per_unit,
            "description": r.CommunityListing.description,
            "expires_at": str(r.CommunityListing.expires_at) if r.CommunityListing.expires_at else None,
            "created_at": str(r.CommunityListing.created_at),
        } for r in rows]
    }

@router.post("/listings")
def create_listing(
    body: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = CommunityListing(
        outlet_id=current_user.outlet_id or 1,
        product_id=body.product_id,
        listing_type=body.listing_type,
        available_qty=body.available_qty,
        price_per_unit=body.price_per_unit,
        description=body.description,
        expires_at=body.expires_at,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return {"id": listing.id, "message": "Listing created"}

@router.delete("/listings/{listing_id}")
def deactivate_listing(listing_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = db.query(CommunityListing).filter(CommunityListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.is_active = False
    db.commit()
    return {"message": "Listing deactivated"}
