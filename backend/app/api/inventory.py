"""
Inventory Management API Router

FastAPI router for comprehensive inventory management with outlet-level access control.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_, desc, text, case
from sqlalchemy.orm import joinedload

from app.database import get_db_dependency
from app.core.security import get_current_user, require_roles
from app.models.models import (
    User, UserRole, Product, Inventory, Alert, AlertType, AlertStatus,
    Sale, Outlet
)

# Pydantic models
class InventoryItem(BaseModel):
    inventory_id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    category: str
    outlet_id: UUID
    outlet_name: str
    current_stock: int
    reserved_stock: int
    reorder_level: int
    unit_price: float
    cost_price: float
    snapshot_date: date
    last_updated: datetime

class InventoryListResponse(BaseModel):
    items: List[InventoryItem]
    total: int
    page: int
    per_page: int
    total_pages: int

class InventoryAlert(BaseModel):
    alert_id: UUID
    product_name: str
    product_sku: str
    outlet_name: str
    current_stock: int
    threshold: float
    alert_type: AlertType
    days_since_created: int
    created_at: datetime

class StockUpdateRequest(BaseModel):
    new_stock: int = Field(..., ge=0)
    reason: str = Field(..., min_length=1, max_length=500)

class BulkStockUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., min_items=1)

class StockMovement(BaseModel):
    date: date
    opening_stock: int
    sales_out: int
    adjustments_in: int
    adjustments_out: int
    closing_stock: int

class ReorderSuggestion(BaseModel):
    product_id: UUID
    product_name: str
    product_sku: str
    outlet_name: str
    current_stock: int
    reorder_level: int
    avg_daily_sales: float
    days_until_stockout: Optional[float]
    suggested_order_qty: int
    urgency_level: str  # "critical", "high", "medium", "low"

# Create router
router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

def get_user_outlet_scope(current_user: User) -> Optional[UUID]:
    """Get outlet scope for access control"""
    if current_user.role == UserRole.superadmin:
        return None  # Access to all outlets
    elif current_user.role in [UserRole.manager, UserRole.staff]:
        return current_user.outlet_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

@router.get("/", response_model=InventoryListResponse)
async def get_inventory(
    outlet_id: Optional[UUID] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_dependency)
) -> InventoryListResponse:
    """
    Get paginated inventory list with filters.

    Returns latest inventory snapshots joined with product details.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    # Base query - get latest inventory snapshot per product per outlet
    base_query = select(
        Inventory.inventory_id,
        Inventory.outlet_id,
        Inventory.product_id,
        Inventory.current_stock,
        Inventory.reserved_stock,
        Inventory.snapshot_date,
        Inventory.created_at.label("last_updated"),
        Product.name.label("product_name"),
        Product.sku.label("product_sku"),
        Product.category,
        Product.reorder_level,
        Product.unit_price,
        Product.cost_price,
        Outlet.name.label("outlet_name")
    ).select_from(
        Inventory
    ).join(
        Product, Inventory.product_id == Product.product_id
    ).join(
        Outlet, Inventory.outlet_id == Outlet.outlet_id
    ).where(
        and_(
            Product.is_active == True,
            Outlet.is_active == True,
            # Get only the latest snapshot per product per outlet
            Inventory.snapshot_date == select(
                func.max(Inventory.snapshot_date)
            ).where(
                and_(
                    Inventory.product_id == Product.product_id,
                    Inventory.outlet_id == Outlet.outlet_id
                )
            ).scalar_subquery()
        )
    )

    # Apply outlet scope filter
    if user_outlet_scope:
        base_query = base_query.where(Inventory.outlet_id == user_outlet_scope)

    # Apply user filters
    if outlet_id:
        if user_outlet_scope and outlet_id != user_outlet_scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access inventory for other outlets"
            )
        base_query = base_query.where(Inventory.outlet_id == outlet_id)

    if category:
        base_query = base_query.where(Product.category == category)

    if search:
        base_query = base_query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    if low_stock_only:
        base_query = base_query.where(
            Inventory.current_stock <= Product.reorder_level
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * per_page
    paginated_query = base_query.offset(offset).limit(per_page).order_by(
        Product.category, Product.name
    )

    # Execute query
    result = await session.execute(paginated_query)
    rows = result.all()

    # Convert to response model
    items = [
        InventoryItem(
            inventory_id=row.inventory_id,
            product_id=row.product_id,
            product_name=row.product_name,
            product_sku=row.product_sku,
            category=row.category,
            outlet_id=row.outlet_id,
            outlet_name=row.outlet_name,
            current_stock=row.current_stock,
            reserved_stock=row.reserved_stock,
            reorder_level=row.reorder_level,
            unit_price=row.unit_price,
            cost_price=row.cost_price,
            snapshot_date=row.snapshot_date,
            last_updated=row.last_updated
        )
        for row in rows
    ]

    total_pages = (total + per_page - 1) // per_page

    return InventoryListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/alerts", response_model=List[InventoryAlert])
async def get_inventory_alerts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_dependency)
) -> List[InventoryAlert]:
    """
    Get all active inventory alerts for user's scope.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    query = select(
        Alert.alert_id,
        Alert.threshold_value,
        Alert.current_value,
        Alert.alert_type,
        Alert.created_at,
        Product.name.label("product_name"),
        Product.sku.label("product_sku"),
        Outlet.name.label("outlet_name")
    ).select_from(
        Alert
    ).join(
        Product, Alert.product_id == Product.product_id
    ).join(
        Outlet, Alert.outlet_id == Outlet.outlet_id
    ).where(
        and_(
            Alert.status == AlertStatus.active,
            Product.is_active == True,
            Outlet.is_active == True
        )
    )

    # Apply outlet scope
    if user_outlet_scope:
        query = query.where(Alert.outlet_id == user_outlet_scope)

    query = query.order_by(desc(Alert.created_at))

    result = await session.execute(query)
    rows = result.all()

    alerts = []
    for row in rows:
        days_since = (datetime.utcnow() - row.created_at).days
        alerts.append(InventoryAlert(
            alert_id=row.alert_id,
            product_name=row.product_name,
            product_sku=row.product_sku,
            outlet_name=row.outlet_name,
            current_stock=int(row.current_value),
            threshold=row.threshold_value,
            alert_type=row.alert_type,
            days_since_created=days_since,
            created_at=row.created_at
        ))

    return alerts

@router.put("/{inventory_id}")
async def update_stock_level(
    inventory_id: UUID,
    request: StockUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.superadmin)),
    session: AsyncSession = Depends(get_db_dependency)
) -> Dict[str, str]:
    """
    Update stock level for a specific inventory item.
    Only managers and superadmin can update stock.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    # Get current inventory
    inventory_query = select(Inventory).where(Inventory.inventory_id == inventory_id)
    result = await session.execute(inventory_query)
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    # Check outlet access
    if user_outlet_scope and inventory.outlet_id != user_outlet_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update inventory for other outlets"
        )

    old_stock = inventory.current_stock

    # Update inventory
    await session.execute(
        update(Inventory)
        .where(Inventory.inventory_id == inventory_id)
        .values(current_stock=request.new_stock)
    )

    # Create audit log entry (simple insert without model)
    audit_query = text("""
        INSERT INTO inventory_audit_logs
        (inventory_id, user_id, old_stock, new_stock, reason, created_at)
        VALUES (:inventory_id, :user_id, :old_stock, :new_stock, :reason, :created_at)
    """)

    # Create audit table if it doesn't exist
    create_table_query = text("""
        CREATE TABLE IF NOT EXISTS inventory_audit_logs (
            audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            inventory_id UUID NOT NULL REFERENCES inventories(inventory_id),
            user_id UUID NOT NULL REFERENCES users(user_id),
            old_stock INTEGER NOT NULL,
            new_stock INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    try:
        await session.execute(create_table_query)
        await session.execute(audit_query, {
            "inventory_id": str(inventory_id),
            "user_id": str(current_user.user_id),
            "old_stock": old_stock,
            "new_stock": request.new_stock,
            "reason": request.reason,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        # If audit logging fails, still commit the inventory update
        pass

    await session.commit()

    return {"message": "Stock level updated successfully"}

@router.post("/bulk-update")
async def bulk_update_stock(
    request: BulkStockUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.superadmin)),
    session: AsyncSession = Depends(get_db_dependency)
) -> Dict[str, str]:
    """
    Perform bulk stock updates in a single transaction.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    if not request.updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )

    # Validate all updates first
    inventory_ids = []
    audit_entries = []

    for update_item in request.updates:
        try:
            product_id = UUID(update_item["product_id"])
            outlet_id = UUID(update_item["outlet_id"])
            new_stock = int(update_item["new_stock"])
            reason = str(update_item["reason"])

            if new_stock < 0:
                raise ValueError("Stock cannot be negative")

        except (KeyError, ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid update data: {str(e)}"
            )

        # Check outlet access
        if user_outlet_scope and outlet_id != user_outlet_scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update inventory for other outlets"
            )

        inventory_ids.append((product_id, outlet_id, new_stock, reason))

    # Perform updates in transaction
    try:
        for product_id, outlet_id, new_stock, reason in inventory_ids:
            # Get current inventory
            inventory_query = select(Inventory).where(
                and_(
                    Inventory.product_id == product_id,
                    Inventory.outlet_id == outlet_id,
                    Inventory.snapshot_date == select(
                        func.max(Inventory.snapshot_date)
                    ).where(
                        and_(
                            Inventory.product_id == product_id,
                            Inventory.outlet_id == outlet_id
                        )
                    ).scalar_subquery()
                )
            )
            result = await session.execute(inventory_query)
            inventory = result.scalar_one_or_none()

            if inventory:
                old_stock = inventory.current_stock
                await session.execute(
                    update(Inventory)
                    .where(Inventory.inventory_id == inventory.inventory_id)
                    .values(current_stock=new_stock)
                )

                audit_entries.append({
                    "inventory_id": str(inventory.inventory_id),
                    "user_id": str(current_user.user_id),
                    "old_stock": old_stock,
                    "new_stock": new_stock,
                    "reason": reason
                })

        # Create audit table and insert logs
        create_table_query = text("""
            CREATE TABLE IF NOT EXISTS inventory_audit_logs (
                audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                inventory_id UUID NOT NULL REFERENCES inventories(inventory_id),
                user_id UUID NOT NULL REFERENCES users(user_id),
                old_stock INTEGER NOT NULL,
                new_stock INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        await session.execute(create_table_query)

        for audit_entry in audit_entries:
            audit_query = text("""
                INSERT INTO inventory_audit_logs
                (inventory_id, user_id, old_stock, new_stock, reason, created_at)
                VALUES (:inventory_id, :user_id, :old_stock, :new_stock, :reason, :created_at)
            """)
            audit_entry["created_at"] = datetime.utcnow()
            await session.execute(audit_query, audit_entry)

        await session.commit()

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk update failed: {str(e)}"
        )

    return {"message": f"Successfully updated {len(inventory_ids)} inventory items"}

@router.get("/movement/{product_id}")
async def get_stock_movement(
    product_id: UUID,
    outlet_id: Optional[UUID] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_dependency)
) -> List[StockMovement]:
    """
    Get stock movement history for a product.
    Returns daily in/out derived from inventory snapshots and sales data.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    # Apply outlet scope
    if not outlet_id and user_outlet_scope:
        outlet_id = user_outlet_scope
    elif outlet_id and user_outlet_scope and outlet_id != user_outlet_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access inventory for other outlets"
        )

    if not outlet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="outlet_id is required"
        )

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get inventory snapshots for the period
    inventory_query = select(
        Inventory.snapshot_date,
        Inventory.current_stock
    ).where(
        and_(
            Inventory.product_id == product_id,
            Inventory.outlet_id == outlet_id,
            Inventory.snapshot_date >= start_date,
            Inventory.snapshot_date <= end_date
        )
    ).order_by(Inventory.snapshot_date)

    inventory_result = await session.execute(inventory_query)
    inventory_data = {row.snapshot_date: row.current_stock for row in inventory_result.all()}

    # Get sales data for the period
    sales_query = select(
        Sale.sale_date,
        func.sum(Sale.quantity).label("total_sold")
    ).where(
        and_(
            Sale.product_id == product_id,
            Sale.outlet_id == outlet_id,
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        )
    ).group_by(Sale.sale_date).order_by(Sale.sale_date)

    sales_result = await session.execute(sales_query)
    sales_data = {row.sale_date: row.total_sold for row in sales_result.all()}

    # Build movement data
    movements = []
    current_date = start_date

    while current_date <= end_date:
        opening_stock = inventory_data.get(current_date - timedelta(days=1), 0)
        sales_out = sales_data.get(current_date, 0)

        # Calculate adjustments (change in inventory not explained by sales)
        current_stock = inventory_data.get(current_date, opening_stock)
        expected_stock = opening_stock - sales_out

        if current_stock > expected_stock:
            adjustments_in = current_stock - expected_stock
            adjustments_out = 0
        else:
            adjustments_in = 0
            adjustments_out = expected_stock - current_stock

        movements.append(StockMovement(
            date=current_date,
            opening_stock=opening_stock,
            sales_out=sales_out,
            adjustments_in=adjustments_in,
            adjustments_out=adjustments_out,
            closing_stock=current_stock
        ))

        current_date += timedelta(days=1)

    return movements

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_dependency)
) -> Dict[str, str]:
    """
    Mark an inventory alert as resolved.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    # Get alert
    alert_query = select(Alert).where(Alert.alert_id == alert_id)
    result = await session.execute(alert_query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Check outlet access
    if user_outlet_scope and alert.outlet_id != user_outlet_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot resolve alerts for other outlets"
        )

    # Update alert
    await session.execute(
        update(Alert)
        .where(Alert.alert_id == alert_id)
        .values(
            status=AlertStatus.resolved,
            resolved_at=datetime.utcnow()
        )
    )

    await session.commit()

    return {"message": "Alert resolved successfully"}

@router.get("/reorder-suggestions", response_model=List[ReorderSuggestion])
async def get_reorder_suggestions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_dependency)
) -> List[ReorderSuggestion]:
    """
    Get products that need reordering based on current stock vs reorder level.
    Includes urgency calculation based on average daily sales.
    """
    user_outlet_scope = get_user_outlet_scope(current_user)

    # Calculate average daily sales for the last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)

    sales_avg_query = select(
        Sale.product_id,
        Sale.outlet_id,
        func.avg(Sale.quantity).label("avg_daily_sales")
    ).where(
        and_(
            Sale.sale_date >= thirty_days_ago,
            Sale.sale_date <= date.today()
        )
    ).group_by(Sale.product_id, Sale.outlet_id)

    sales_result = await session.execute(sales_avg_query)
    sales_avg_data = {(row.product_id, row.outlet_id): row.avg_daily_sales for row in sales_result.all()}

    # Get products at or below reorder level
    query = select(
        Inventory.inventory_id,
        Inventory.outlet_id,
        Inventory.product_id,
        Inventory.current_stock,
        Product.name.label("product_name"),
        Product.sku.label("product_sku"),
        Product.reorder_level,
        Outlet.name.label("outlet_name")
    ).select_from(
        Inventory
    ).join(
        Product, Inventory.product_id == Product.product_id
    ).join(
        Outlet, Inventory.outlet_id == Outlet.outlet_id
    ).where(
        and_(
            Product.is_active == True,
            Outlet.is_active == True,
            Inventory.current_stock <= Product.reorder_level,
            # Get latest snapshot
            Inventory.snapshot_date == select(
                func.max(Inventory.snapshot_date)
            ).where(
                and_(
                    Inventory.product_id == Product.product_id,
                    Inventory.outlet_id == Outlet.outlet_id
                )
            ).scalar_subquery()
        )
    )

    # Apply outlet scope
    if user_outlet_scope:
        query = query.where(Inventory.outlet_id == user_outlet_scope)

    query = query.order_by(
        # Order by urgency: days until stockout (ascending = more urgent)
        case(
            (func.coalesce(sales_avg_data.get((Product.product_id, Outlet.outlet_id), 0), 0) > 0,
             Inventory.current_stock / func.coalesce(sales_avg_data.get((Product.product_id, Outlet.outlet_id), 0), 1)),
            else_=999
        )
    )

    result = await session.execute(query)
    rows = result.all()

    suggestions = []
    for row in rows:
        avg_daily_sales = sales_avg_data.get((row.product_id, row.outlet_id), 0)

        if avg_daily_sales > 0:
            days_until_stockout = row.current_stock / avg_daily_sales
            suggested_order_qty = int(avg_daily_sales * 30 * 1.5)  # 30-day avg * 1.5 safety factor

            if days_until_stockout <= 1:
                urgency = "critical"
            elif days_until_stockout <= 3:
                urgency = "high"
            elif days_until_stockout <= 7:
                urgency = "medium"
            else:
                urgency = "low"
        else:
            days_until_stockout = None
            suggested_order_qty = row.reorder_level * 2  # Default suggestion
            urgency = "low"

        suggestions.append(ReorderSuggestion(
            product_id=row.product_id,
            product_name=row.product_name,
            product_sku=row.product_sku,
            outlet_name=row.outlet_name,
            current_stock=row.current_stock,
            reorder_level=row.reorder_level,
            avg_daily_sales=avg_daily_sales,
            days_until_stockout=days_until_stockout,
            suggested_order_qty=suggested_order_qty,
            urgency_level=urgency
        ))

    return suggestions
