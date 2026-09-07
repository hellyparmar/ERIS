from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.inventory import Inventory
from app.models.models_v6 import Product, ProductCategory
from app.models.outlet import Outlet
from app.models.users import User
from app.core.deps import get_current_user
from app.api.deps import get_accessible_outlet_ids
from datetime import date
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
@router.get("/")
async def list_inventory(
    outlet_id: Optional[int] = None,
    low_stock_only: bool = False,
    search: Optional[str] = None,
    category: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    per_page: Optional[int] = Query(None, ge=1, le=200),
    limit: Optional[int] = Query(None, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = (
            select(Inventory, Product, Outlet, ProductCategory)
            .join(Product, Product.id == Inventory.product_id)
            .join(Outlet, Outlet.id == Inventory.outlet_id)
            .outerjoin(ProductCategory, ProductCategory.id == Product.category_id)
        )

        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if not allowed_outlets:
            allowed_outlets = [-1]

        if outlet_id:
            if outlet_id not in allowed_outlets:
                raise HTTPException(status_code=403, detail="Access denied to this outlet")
            query = query.where(Inventory.outlet_id == outlet_id)
        else:
            query = query.where(Inventory.outlet_id.in_(allowed_outlets))

        if low_stock_only:
            query = query.where(Inventory.current_stock <= Product.reorder_level)

        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))

        if category:
            query = query.where(ProductCategory.name.ilike(f"%{category}%"))

        page_val = page if isinstance(page, int) else None
        per_page_val = per_page if isinstance(per_page, int) else None
        limit_val = limit if isinstance(limit, int) else None

        is_paginated = page_val is not None or per_page_val is not None or limit_val is not None
        effective_page = page_val or 1
        effective_per_page = per_page_val or limit_val or 50
        total = 0

        if is_paginated:
            count_stmt = select(func.count()).select_from(query.subquery())
            count_res = await db.execute(count_stmt)
            total = count_res.scalar() or 0
            query = query.order_by(Product.name.asc()).offset((effective_page - 1) * effective_per_page).limit(effective_per_page)
        else:
            query = query.order_by(Product.name.asc())

        result = await db.execute(query)
        rows = result.fetchall()
        items = [{
            "id": str(r.Inventory.id),
            "product": {
                "id": str(r.Product.id),
                "name": r.Product.name,
                "sku": r.Product.sku or f"SKU-{r.Product.id}",
                "category": r.ProductCategory.name if r.ProductCategory else "General",
                "selling_price": float(r.Product.selling_price or 0.0),
                "gst_rate": float(r.ProductCategory.default_gst_rate) if r.ProductCategory and r.ProductCategory.default_gst_rate else 18.0,
            },
            "outlet_id": r.Inventory.outlet_id,
            "outlet_name": r.Outlet.name,
            "quantity": r.Inventory.current_stock,
            "reorder_level": r.Product.reorder_level or 10,
            "max_stock": (r.Product.reorder_quantity or 50) * 2,
            "last_restocked": str(r.Inventory.last_restocked_at) if r.Inventory.last_restocked_at else None,
            "status": "out" if r.Inventory.current_stock == 0 else "low" if r.Inventory.current_stock <= (r.Product.reorder_level or 10) else "ok",
            "stock_pct": round(r.Inventory.current_stock / ((r.Product.reorder_quantity or 50) * 2) * 100, 1),
        } for r in rows]

        if is_paginated:
            return {
                "items": items,
                "total": total,
                "page": effective_page,
                "per_page": effective_per_page,
                "limit": effective_per_page,
                "total_pages": (total + effective_per_page - 1) // effective_per_page if effective_per_page > 0 else 1
            }

        return items
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to load inventory")

@router.get("/summary")
async def inventory_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if not allowed_outlets:
            allowed_outlets = [-1]

        total_result = await db.execute(
            select(func.count(Inventory.id)).where(Inventory.outlet_id.in_(allowed_outlets))
        )
        total = total_result.scalar() or 0

        out_result = await db.execute(
            select(func.count(Inventory.id))
            .where(Inventory.outlet_id.in_(allowed_outlets))
            .where(Inventory.current_stock == 0)
        )
        out = out_result.scalar() or 0

        low_result = await db.execute(
            select(func.count(Inventory.id))
            .where(Inventory.outlet_id.in_(allowed_outlets))
            .where(Inventory.current_stock > 0)
            .where(
                Inventory.current_stock <= func.coalesce(
                    select(Product.reorder_level).where(Product.id == Inventory.product_id).scalar_subquery(), 10
                )
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

@router.get("/alerts/low-stock")
async def low_stock_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        query = (
            select(Inventory, Product, Outlet)
            .join(Product, Product.id == Inventory.product_id)
            .join(Outlet, Outlet.id == Inventory.outlet_id)
            .where(Inventory.current_stock <= Product.reorder_level)
            .order_by(Inventory.current_stock.asc())
        )
        
        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if not allowed_outlets:
            allowed_outlets = [-1]
        query = query.where(Inventory.outlet_id.in_(allowed_outlets))

        result = await db.execute(query)
        rows = result.fetchall()

        return [{
            "id": str(r.Inventory.id),
            "product_name": r.Product.name,
            "product_sku": r.Product.sku or f"SKU-{r.Product.id}",
            "outlet_name": r.Outlet.name,
            "current_stock": r.Inventory.current_stock,
            "reorder_level": r.Product.reorder_level or 10,
            "status": "out" if r.Inventory.current_stock == 0 else "low",
        } for r in rows]
    except Exception as e:
        logger.error(f"Error fetching low stock alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch low stock alerts")

@router.get("/{inventory_id}/movement")
async def stock_movement(
    inventory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        inv_uuid = uuid.UUID(inventory_id)
        result = await db.execute(
            select(Inventory).where(Inventory.id == inv_uuid)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if item.outlet_id not in allowed_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this inventory item")

        return [
            {"date": str(date.today()), "type": "current", "quantity": item.current_stock, "note": "Current stock level"}
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock movement: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock movement")

from app.services.audit_service import log_audit_action

@router.put("/{inventory_id}")
async def update_inventory(
    inventory_id: str,
    body: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        inv_uuid = uuid.UUID(inventory_id)
        result = await db.execute(
            select(Inventory).where(Inventory.id == inv_uuid)
        )
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if item.outlet_id not in allowed_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this inventory item")

        if body.quantity is not None:
            item.current_stock = body.quantity
            item.last_restocked_at = func.now()

        await db.commit()
        
        await log_audit_action(
            db=db,
            action="update_inventory",
            performed_by=current_user.id,
            context={"inventory_id": str(inventory_id), "new_quantity": body.quantity}
        )

        return {"message": "Stock updated successfully", "id": inventory_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to update inventory")

@router.patch("/{inventory_id}")
async def patch_inventory(
    inventory_id: str,
    body: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_inventory(inventory_id, body, db, current_user)

categories_router = APIRouter(prefix="/categories", tags=["categories"])

@categories_router.get("")
@categories_router.get("/")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(Product.category).distinct().order_by(Product.category)
        )
        rows = result.scalars().all()
        return [{"id": i + 1, "name": row} for i, row in enumerate(rows)]
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to load categories")
