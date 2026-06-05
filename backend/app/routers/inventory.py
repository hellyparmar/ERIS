from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Inventory, Product, Outlet, Alert, User
from app.core.deps import get_current_user
from datetime import date
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    reorder_level: Optional[int] = None
    max_stock: Optional[int] = None

@router.get("/list")
async def list_inventory(
    outlet_id: Optional[int] = None,
    low_stock_only: bool = False,
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List inventory items with optional filters.
    
    ERROR FIXES:
    - Uses AsyncSession instead of sync Session
    - All database operations use await
    - Proper error handling for async context
    """
    try:
        # Build query with proper async patterns
        query = (
            select(Inventory, Product.name, Product.category, Product.sku,
                   Product.selling_price, Product.gst_rate, Outlet.name.label("outlet_name"))
            .join(Product, Product.id == Inventory.product_id)
            .join(Outlet, Outlet.id == Inventory.outlet_id)
        )
        
        if outlet_id:
            query = query.where(Inventory.outlet_id == outlet_id)
        elif current_user.role == "manager" and current_user.outlet_id:
            query = query.where(Inventory.outlet_id == current_user.outlet_id)
        
        if low_stock_only:
            query = query.where(Inventory.current_stock <= Inventory.reorder_level)
        
        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))
        
        if category:
            query = query.where(Product.category == category)
        
        # Get total count
        count_query = select(func.count()).select_from(Inventory).where(Inventory.outlet_id == outlet_id if outlet_id else True)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Inventory.current_stock.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.fetchall()
        
        return {
            "total": total,
            "items": [{
                "id": r.Inventory.id,
                "product_name": r.name,
                "category": r.category,
                "sku": r.sku,
                "outlet_name": r.outlet_name,
                "selling_price": r.selling_price,
                "gst_rate": r.gst_rate,
                "current_stock": r.Inventory.current_stock,
                "reorder_level": r.Inventory.reorder_level,
                "max_stock": r.Inventory.max_stock,
                "last_restocked": str(r.Inventory.last_restocked) if r.Inventory.last_restocked else None,
                "status": "out" if r.Inventory.current_stock == 0 else "low" if r.Inventory.current_stock <= r.Inventory.reorder_level else "ok",
                "stock_pct": round(r.Inventory.current_stock / r.Inventory.max_stock * 100, 1) if r.Inventory.max_stock > 0 else 0,
            } for r in rows]
        }
    except Exception as e:
        logger.error(f"Error listing inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to list inventory")

@router.get("/summary")
async def inventory_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get inventory summary statistics.
    
    ERROR FIXES:
    - Uses AsyncSession with await
    - Proper async query execution
    """
    try:
        # Count total inventory
        total_result = await db.execute(select(func.count(Inventory.id)))
        total = total_result.scalar() or 0
        
        # Count out of stock
        out_result = await db.execute(
            select(func.count(Inventory.id)).where(Inventory.current_stock == 0)
        )
        out = out_result.scalar() or 0
        
        # Count low stock
        low_result = await db.execute(
            select(func.count(Inventory.id)).where(
                Inventory.current_stock > 0,
                Inventory.current_stock <= Inventory.reorder_level
            )
        )
        low = low_result.scalar() or 0
        
        return {
            "total": total,
            "out_of_stock": out,
            "low_stock": low,
            "healthy": total - out - low
        }
    except Exception as e:
        logger.error(f"Error getting inventory summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get inventory summary")

@router.patch("/{inventory_id}")
async def update_inventory(
    inventory_id: int,
    body: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update inventory item with new stock levels.
    
    ERROR FIXES:
    - Uses async database operations with await
    - Proper transaction handling
    """
    try:
        # Fetch inventory item
        result = await db.execute(
            select(Inventory).where(Inventory.id == inventory_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        # Update fields
        if body.current_stock is not None:
            item.current_stock = body.current_stock
            item.last_restocked = date.today()
            await _check_and_resolve_alert(db, item.outlet_id, item.product_id)
        
        if body.reorder_level is not None:
            item.reorder_level = body.reorder_level
        
        if body.max_stock is not None:
            item.max_stock = body.max_stock
        
        await db.commit()
        
        return {"message": "Updated", "id": inventory_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to update inventory")

async def _check_and_resolve_alert(db: AsyncSession, outlet_id: int, product_id: int):
    """Resolve inventory-related alerts"""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.outlet_id == outlet_id,
                Alert.product_id == product_id,
                Alert.category == "inventory",
                Alert.is_resolved == False
            )
        )
        alerts = result.scalars().all()
        
        for alert in alerts:
            alert.is_resolved = True
        
        if alerts:
            await db.commit()
    except Exception as e:
        logger.error(f"Error resolving alerts: {e}")
        # Don't raise - this is a side effect

