from datetime import datetime, timezone
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pydantic import BaseModel, Field
from typing import Any, Optional
from app.database import get_db
from app.models.inventory import Inventory
from app.models.commerce import Product, ProductCategory, StockMovement
from app.models.outlet import Outlet
from app.models.users import User
from app.api.deps import get_accessible_outlet_ids, get_current_active_user, require_role
from app.services.audit_service import log_audit_action, log_audit_action_sync
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])


async def _execute(db: Any, stmt: Any) -> Any:
    if isinstance(db, AsyncSession):
        return await db.execute(stmt)
    return db.execute(stmt)


class InventoryUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    reason: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class ProductInventoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    category: str = Field(min_length=2, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    unit_price: Decimal = Field(gt=0)
    cost_price: Decimal = Field(ge=0)
    current_stock: int = Field(ge=0)
    reorder_point: int = Field(default=10, ge=0)
    outlet_id: int = Field(gt=0)


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
    current_user: User = Depends(get_current_active_user),
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
            count_res = await _execute(db, count_stmt)
            total = count_res.scalar() or 0
            query = (
                query.order_by(Product.name.asc())
                .offset((effective_page - 1) * effective_per_page)
                .limit(effective_per_page)
            )
        else:
            query = query.order_by(Product.name.asc())

        result = await _execute(db, query)
        rows = result.fetchall()
        items = [
            {
                "id": str(r.Inventory.id),
                "product": {
                    "id": str(r.Product.id),
                    "name": r.Product.name,
                    "sku": r.Product.sku or f"SKU-{r.Product.id}",
                    "category": r.ProductCategory.name if r.ProductCategory else "General",
                    "selling_price": float(r.Product.selling_price or 0.0),
                    "gst_rate": float(r.ProductCategory.default_gst_rate)
                    if r.ProductCategory and r.ProductCategory.default_gst_rate
                    else 18.0,
                },
                "outlet_id": r.Inventory.outlet_id,
                "outlet_name": r.Outlet.name,
                "quantity": r.Inventory.current_stock,
                "reorder_level": r.Product.reorder_level or 10,
                "max_stock": (r.Product.reorder_quantity or 50) * 2,
                "last_restocked": str(r.Inventory.last_restocked_at) if r.Inventory.last_restocked_at else None,
                "status": "out"
                if r.Inventory.current_stock == 0
                else "low"
                if r.Inventory.current_stock <= (r.Product.reorder_level or 10)
                else "ok",
                "stock_pct": round(r.Inventory.current_stock / ((r.Product.reorder_quantity or 50) * 2) * 100, 1),
            }
            for r in rows
        ]

        if is_paginated:
            return {
                "items": items,
                "total": total,
                "page": effective_page,
                "per_page": effective_per_page,
                "limit": effective_per_page,
                "total_pages": (total + effective_per_page - 1) // effective_per_page if effective_per_page > 0 else 1,
            }

        return items
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to load inventory")


@router.get("/summary")
async def inventory_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if not allowed_outlets:
            allowed_outlets = [-1]

        total_result = await _execute(
            db, select(func.count(Inventory.id)).where(Inventory.outlet_id.in_(allowed_outlets))
        )
        total = total_result.scalar() or 0

        out_result = await _execute(
            db,
            select(func.count(Inventory.id))
            .where(Inventory.outlet_id.in_(allowed_outlets))
            .where(Inventory.current_stock == 0),
        )
        out = out_result.scalar() or 0

        low_result = await _execute(
            db,
            select(func.count(Inventory.id))
            .where(Inventory.outlet_id.in_(allowed_outlets))
            .where(Inventory.current_stock > 0)
            .where(
                Inventory.current_stock
                <= func.coalesce(
                    select(Product.reorder_level).where(Product.id == Inventory.product_id).scalar_subquery(), 10
                )
            ),
        )
        low = low_result.scalar() or 0

        return {"total": total, "out_of_stock": out, "low_stock": low, "healthy": total - out - low}
    except Exception as e:
        logger.error(f"Error getting inventory summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get inventory summary")


@router.get("/alerts/low-stock")
async def low_stock_alerts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
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

        result = await _execute(db, query)
        rows = result.fetchall()

        return [
            {
                "id": str(r.Inventory.id),
                "product_name": r.Product.name,
                "product_sku": r.Product.sku or f"SKU-{r.Product.id}",
                "outlet_name": r.Outlet.name,
                "current_stock": r.Inventory.current_stock,
                "reorder_level": r.Product.reorder_level or 10,
                "status": "out" if r.Inventory.current_stock == 0 else "low",
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching low stock alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch low stock alerts")


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_product_inventory(
    body: ProductInventoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Create an organization product and its initial outlet inventory."""
    allowed_outlets = await get_accessible_outlet_ids(current_user, db)
    if body.outlet_id not in allowed_outlets:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")

    outlet = (
        await _execute(
            db,
            select(Outlet).where(
                Outlet.id == body.outlet_id,
                Outlet.organization_id == current_user.organization_id,
                Outlet.is_deleted.is_(False),
            ),
        )
    ).scalar_one_or_none()
    if outlet is None:
        raise HTTPException(status_code=404, detail="Outlet not found")

    sku = (body.sku or f"ERIS-{uuid.uuid4().hex[:10].upper()}").strip().upper()
    if (await _execute(db, select(Product.id).where(Product.sku == sku))).first():
        raise HTTPException(status_code=409, detail="SKU already exists")

    category = (
        await _execute(
            db,
            select(ProductCategory).where(
                ProductCategory.organization_id == current_user.organization_id,
                func.lower(ProductCategory.name) == body.category.strip().lower(),
            ),
        )
    ).scalar_one_or_none()
    if category is None:
        category = ProductCategory(
            organization_id=current_user.organization_id,
            name=body.category.strip(),
            default_gst_rate=Decimal("5.00"),
        )
        db.add(category)
        if isinstance(db, AsyncSession):
            await db.flush()
        else:
            db.flush()

    product = Product(
        organization_id=current_user.organization_id,
        category_id=category.id,
        sku=sku,
        name=body.name.strip(),
        cost_price=body.cost_price,
        selling_price=body.unit_price,
        mrp=body.unit_price,
        reorder_level=body.reorder_point,
        reorder_quantity=max(body.reorder_point * 2, 1),
        unit="item",
        is_active=True,
        is_deleted=False,
    )
    db.add(product)
    if isinstance(db, AsyncSession):
        await db.flush()
    else:
        db.flush()

    inventory = Inventory(
        organization_id=current_user.organization_id,
        outlet_id=body.outlet_id,
        product_id=product.id,
        current_stock=body.current_stock,
        reserved_stock=0,
        last_restocked_at=datetime.now(timezone.utc),
    )
    db.add(inventory)
    if isinstance(db, AsyncSession):
        await db.flush()
    else:
        db.flush()
    if body.current_stock:
        db.add(
            StockMovement(
                organization_id=current_user.organization_id,
                outlet_id=body.outlet_id,
                product_id=product.id,
                movement_type="purchase",
                quantity=body.current_stock,
                stock_before=0,
                stock_after=body.current_stock,
                user_id=current_user.id,
                notes="Initial inventory",
            )
        )
    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()
    return {
        "success": True,
        "product_id": product.id,
        "inventory_id": inventory.id,
        "sku": product.sku,
    }


@router.get("/{inventory_id}/movement")
async def stock_movement(
    inventory_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    try:
        result = await _execute(db, select(Inventory).where(Inventory.id == inventory_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if item.outlet_id not in allowed_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this inventory item")

        movements = (
            (
                await _execute(
                    db,
                    select(StockMovement)
                    .where(
                        StockMovement.outlet_id == item.outlet_id,
                        StockMovement.product_id == item.product_id,
                    )
                    .order_by(StockMovement.created_at.desc())
                    .limit(100),
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": movement.id,
                "date": movement.created_at.isoformat() if movement.created_at else None,
                "type": movement.movement_type,
                "quantity": movement.quantity,
                "stock_before": movement.stock_before,
                "stock_after": movement.stock_after,
                "note": movement.notes,
            }
            for movement in movements
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock movement: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock movement")


@router.put("/{inventory_id}")
async def update_inventory(
    inventory_id: int,
    body: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    try:
        result = await _execute(db, select(Inventory).where(Inventory.id == inventory_id))
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        allowed_outlets = await get_accessible_outlet_ids(current_user, db)
        if item.outlet_id not in allowed_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this inventory item")

        if body.quantity is not None and body.quantity != item.current_stock:
            stock_before = item.current_stock
            item.current_stock = body.quantity
            item.last_restocked_at = func.now()
            db.add(
                StockMovement(
                    organization_id=current_user.organization_id,
                    outlet_id=item.outlet_id,
                    product_id=item.product_id,
                    movement_type="adjustment",
                    quantity=body.quantity - stock_before,
                    stock_before=stock_before,
                    stock_after=body.quantity,
                    user_id=current_user.id,
                    notes="; ".join(part for part in (body.reason, body.notes) if part) or "Manual stock adjustment",
                )
            )

        audit_context = {"inventory_id": str(inventory_id), "new_quantity": body.quantity}
        if isinstance(db, AsyncSession):
            await log_audit_action(
                db=db,
                action="update_inventory",
                performed_by=current_user.id,
                context=audit_context,
            )
            await db.commit()
        else:
            log_audit_action_sync(
                db=db,
                action="update_inventory",
                performed_by=current_user.id,
                context=audit_context,
            )
            db.commit()

        return {"message": "Stock updated successfully", "id": inventory_id}
    except HTTPException:
        raise
    except Exception as e:
        if isinstance(db, AsyncSession):
            await db.rollback()
        else:
            db.rollback()
        logger.error(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to update inventory")


@router.patch("/{inventory_id}")
async def patch_inventory(
    inventory_id: int,
    body: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    return await update_inventory(inventory_id, body, db, current_user)


categories_router = APIRouter(prefix="/categories", tags=["categories"])


@categories_router.get("")
@categories_router.get("/")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        result = await _execute(
            db,
            select(ProductCategory.id, ProductCategory.name)
            .join(Product, Product.category_id == ProductCategory.id)
            .where(Product.organization_id == current_user.organization_id)
            .distinct()
            .order_by(ProductCategory.name),
        )
        return [{"id": row.id, "name": row.name} for row in result.all()]
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to load categories")
