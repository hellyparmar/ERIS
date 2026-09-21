"""
Outlets Management API Router
"""

from datetime import datetime
from typing import Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.database import get_db
from app.models.sales import SaleTransaction, SaleItem
from app.models.models_v6 import Sale, Product
from app.models.users import User
from app.models.outlet import Outlet
from app.models.alert import Alert
from app.models.inventory import Inventory
from app.models.employee_models import Employee
from app.api.deps import get_current_active_user, get_accessible_outlet_ids
from app.core.data_isolation import OutletDataAccess, require_outlet_access

router = APIRouter(prefix="/outlets", tags=["outlets"])


@router.get("")
@router.get("/")
async def list_outlets(
    page: Optional[int] = Query(None, ge=1),
    per_page: Optional[int] = Query(None, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    allowed_outlet_ids = await get_accessible_outlet_ids(current_user, db)
    stmt = select(
        Outlet.id,
        Outlet.name,
        Outlet.city,
        Outlet.address,
        Outlet.phone,
        Outlet.is_active
    )
    if allowed_outlet_ids:
        if not allowed_outlet_ids:
            return []
        stmt = stmt.where(Outlet.id.in_(allowed_outlet_ids))

    effective_limit = per_page or limit
    if page or effective_limit:
        effective_page = page or 1
        page_size = effective_limit or 50
        stmt = stmt.order_by(Outlet.id).offset((effective_page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    rows = result.fetchall()

    return [{
        "id": r[0],
        "name": r[1],
        "city": r[2],
        "address": r[3],
        "phone": r[4],
        "is_active": r[5]
    } for r in rows]


@router.get("/{outlet_id}")
async def get_outlet_details(
    outlet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get outlet details with performance summary.
    Revenue this month, active alerts, employee count, top product.
    """
    allowed_outlet_ids = await get_accessible_outlet_ids(current_user, db)
    if allowed_outlet_ids and outlet_id not in allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    result = await db.execute(select(Outlet).where(Outlet.id == outlet_id))
    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Revenue this month
    rev_result = await db.execute(
        select(func.sum(SaleTransaction.total_amount)).where(
            SaleTransaction.outlet_id == outlet_id,
            func.date(SaleTransaction.transaction_at) >= month_start
        )
    )
    revenue = rev_result.scalar() or 0

    # Active alerts
    alert_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.outlet_id == outlet_id,
            Alert.is_acknowledged == False
        )
    )
    alerts_count = alert_result.scalar() or 0

    # Employee count
    emp_result = await db.execute(
        select(func.count(Employee.id)).where(
            Employee.store_id == outlet_id,
            Employee.is_active == True
        )
    )
    employee_count = emp_result.scalar() or 0

    # Top product this month
    top_prod_result = await db.execute(
        select(
            Product.name,
            func.sum(SaleItem.quantity).label("qty")
        ).join(SaleItem, Product.id == SaleItem.product_id).join(
            SaleTransaction, SaleTransaction.id == SaleItem.sale_id
        ).where(
            SaleTransaction.outlet_id == outlet_id,
            func.date(SaleTransaction.transaction_at) >= month_start
        ).group_by(Product.id, Product.name).order_by(
            func.sum(SaleItem.quantity).desc()
        )
    )
    top_product = top_prod_result.first()

    return {
        "id": outlet.id,
        "name": outlet.name,
        "city": outlet.city,
        "address": outlet.address,
        "phone": outlet.phone,
        "is_active": outlet.is_active,
        "performance": {
            "revenue_this_month": float(revenue),
            "active_alerts": int(alerts_count),
            "employee_count": int(employee_count),
            "top_product": top_product[0] if top_product else None
        }
    }


@router.put("/{outlet_id}")
async def update_outlet(
    outlet_id: int,
    name: Optional[str] = None,
    address: Optional[str] = None,
    phone: Optional[str] = None,
    city: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update outlet info. Superadmin/Admin only."""
    role_name = getattr(current_user.role, 'name', str(current_user.role or '')).lower()
    if role_name not in ["super_admin", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can update outlets"
        )

    result = await db.execute(select(Outlet).where(Outlet.id == outlet_id))
    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if name:
        outlet.name = name
    if address:
        outlet.address = address
    if phone:
        outlet.phone = phone
    if city:
        outlet.city = city

    await db.commit()
    await db.refresh(outlet)

    return {
        "id": outlet.id,
        "name": outlet.name,
        "message": "Outlet updated successfully"
    }


@router.get("/{outlet_id}/compare")
async def compare_outlet_performance(
    outlet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Returns this outlet's performance vs system average for current month.
    """
    allowed_outlet_ids = await get_accessible_outlet_ids(current_user, db)
    if allowed_outlet_ids and outlet_id not in allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Outlet revenue
    r = await db.execute(
        select(func.sum(SaleTransaction.total_amount)).where(
            SaleTransaction.outlet_id == outlet_id,
            func.date(SaleTransaction.transaction_at) >= month_start
        )
    )
    outlet_revenue = r.scalar() or 0

    # Outlet transactions
    r = await db.execute(
        select(func.count(SaleTransaction.id)).where(
            SaleTransaction.outlet_id == outlet_id,
            func.date(SaleTransaction.transaction_at) >= month_start
        )
    )
    outlet_transactions = r.scalar() or 0

    outlet_avg_basket = (float(outlet_revenue) / int(outlet_transactions)) if outlet_transactions > 0 else 0

    # Outlet low stock
    r = await db.execute(
        select(func.count(Inventory.id)).join(
            Product, Inventory.product_id == Product.id
        ).where(
            Inventory.outlet_id == outlet_id,
            Inventory.current_stock <= Product.reorder_level
        )
    )
    outlet_low_stock = r.scalar() or 0

    # System total revenue
    r = await db.execute(
        select(func.sum(SaleTransaction.total_amount)).where(func.date(SaleTransaction.transaction_at) >= month_start)
    )
    all_revenue = r.scalar() or 0

    # System total transactions
    r = await db.execute(
        select(func.count(SaleTransaction.id)).where(func.date(SaleTransaction.transaction_at) >= month_start)
    )
    all_transactions = r.scalar() or 0

    system_avg_basket = (float(all_revenue) / int(all_transactions)) if all_transactions > 0 else 0

    # Outlet count
    r = await db.execute(select(func.count(Outlet.id)))
    outlet_count = r.scalar() or 1

    # System low stock total
    r = await db.execute(
        select(func.count(Inventory.id)).join(
            Product, Inventory.product_id == Product.id
        ).where(Inventory.current_stock <= Product.reorder_level)
    )
    system_total_low_stock = r.scalar() or 0
    system_avg_low_stock = system_total_low_stock / outlet_count if outlet_count > 0 else 0

    return {
        "outlet_id": outlet_id,
        "period": "current_month",
        "outlet_metrics": {
            "revenue": float(outlet_revenue),
            "transactions": int(outlet_transactions),
            "avg_basket_size": round(outlet_avg_basket, 2),
            "low_stock_count": int(outlet_low_stock)
        },
        "system_average": {
            "revenue": float(all_revenue) / outlet_count if outlet_count > 0 else 0,
            "transactions": int(all_transactions) / outlet_count if outlet_count > 0 else 0,
            "avg_basket_size": round(system_avg_basket, 2),
            "low_stock_count": round(system_avg_low_stock, 2)
        },
        "performance_vs_average": {
            "revenue_diff_pct": ((float(outlet_revenue) - (float(all_revenue) / outlet_count)) / (float(all_revenue) / outlet_count) * 100) if outlet_count > 0 and all_revenue > 0 else 0,
            "above_avg": float(outlet_revenue) > (float(all_revenue) / outlet_count) if outlet_count > 0 and all_revenue > 0 else False
        }
    }


@router.post("/")
async def create_outlet(
    name: str,
    city: str,
    address: str,
    phone: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new outlet. Superadmin only."""
    role_name = getattr(current_user.role, 'name', str(current_user.role or '')).lower()
    if role_name not in ["super_admin", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can create outlets"
        )

    new_outlet = Outlet(
        name=name,
        city=city,
        address=address,
        phone=phone,
        is_active=True
    )
    db.add(new_outlet)
    await db.commit()
    await db.refresh(new_outlet)

    return {
        "id": new_outlet.id,
        "name": new_outlet.name,
        "city": new_outlet.city,
        "address": new_outlet.address,
        "phone": new_outlet.phone,
        "message": "Outlet created successfully"
    }


@router.delete("/{outlet_id}")
async def delete_outlet(
    outlet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete outlet. Superadmin only."""
    role_name = getattr(current_user.role, 'name', str(current_user.role or '')).lower()
    if role_name not in ["super_admin", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can delete outlets"
        )

    result = await db.execute(select(Outlet).where(Outlet.id == outlet_id))
    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    outlet.is_active = False
    await db.commit()

    return {
        "id": outlet_id,
        "message": "Outlet deleted successfully"
    }
