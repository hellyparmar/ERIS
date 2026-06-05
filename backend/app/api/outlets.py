"""
Outlets Management API Router
"""

from datetime import datetime, timedelta
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
from uuid import UUID

from app.database import get_db
from app.models import User, Outlet, Sale, Alert, Inventory, Product, Employee
from app.api.deps import get_current_active_user
from app.core.data_isolation import OutletDataAccess

router = APIRouter(prefix="/api/v1/outlets", tags=["outlets"])


@router.get("/")
async def list_outlets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all outlets.
    Superadmin sees all. Manager sees only their outlet.
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    outlets = db.query(
        Outlet.outlet_id,
        Outlet.name,
        Outlet.city,
        Outlet.address,
        Outlet.manager_name,
        Outlet.is_active
    ).filter(Outlet.outlet_id.in_(allowed_outlet_ids)).all()

    return {
        "total": len(outlets),
        "items": [
            {
                "id": row[0],
                "name": row[1],
                "city": row[2],
                "address": row[3],
                "manager_name": row[4],
                "is_active": row[5]
            }
            for row in outlets
        ]
    }


@router.get("/{outlet_id}")
async def get_outlet_details(
    outlet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get outlet details with performance summary.
    Revenue this month, active alerts, employee count, top product.
    """
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    result = await db.execute(select(Outlet).where(Outlet.outlet_id == outlet_id))

    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Revenue this month
    revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.outlet_id == outlet_id,
        Sale.sale_date >= month_start
    ).scalar() or 0

    # Active alerts
    alerts_count = db.query(func.count(Alert.id)).filter(
        Alert.outlet_id == outlet_id,
        Alert.is_acknowledged == False
    ).scalar() or 0

    # Employee count
    employee_count = db.query(func.count(Employee.employee_id)).filter(
        Employee.outlet_id == outlet_id,
        Employee.is_active == True
    ).scalar() or 0

    # Top product this month
    top_product = db.query(
        Product.name,
        func.sum(Sale.quantity).label("qty")
    ).join(Sale, Product.product_id == Sale.product_id).filter(
        Sale.outlet_id == outlet_id,
        Sale.sale_date >= month_start
    ).group_by(Product.product_id, Product.name).order_by(
        func.sum(Sale.quantity).desc()
    ).first()

    return {
        "id": outlet.outlet_id,
        "name": outlet.name,
        "city": outlet.city,
        "address": outlet.address,
        "manager_name": outlet.manager_name,
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
    outlet_id: UUID,
    name: Optional[str] = None,
    manager_name: Optional[str] = None,
    address: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update outlet info. Superadmin only."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can update outlets"
        )

    result = await db.execute(select(Outlet).where(Outlet.outlet_id == outlet_id))

    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if name:
        outlet.name = name
    if manager_name:
        outlet.manager_name = manager_name
    if address:
        outlet.address = address

    db.commit()
    db.refresh(outlet)

    return {
        "id": outlet.outlet_id,
        "name": outlet.name,
        "message": "Outlet updated successfully"
    }


@router.get("/{outlet_id}/compare")
async def compare_outlet_performance(
    outlet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns this outlet's performance vs system average for current month.
    Metrics: revenue, transactions, avg_basket_size, low_stock_rate.
    """
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Outlet metrics
    outlet_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.outlet_id == outlet_id,
        Sale.sale_date >= month_start
    ).scalar() or 0

    outlet_transactions = db.query(func.count(Sale.sale_id)).filter(
        Sale.outlet_id == outlet_id,
        Sale.sale_date >= month_start
    ).scalar() or 0

    outlet_avg_basket = (float(outlet_revenue) / int(outlet_transactions)) if outlet_transactions > 0 else 0

    outlet_low_stock = db.query(func.count(Inventory.inventory_id)).filter(
        Inventory.outlet_id == outlet_id,
        Inventory.current_stock <= Product.reorder_level
    ).join(Product, Inventory.product_id == Product.product_id).scalar() or 0

    # System average
    all_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= month_start
    ).scalar() or 0

    all_transactions = db.query(func.count(Sale.sale_id)).filter(
        Sale.sale_date >= month_start
    ).scalar() or 0

    system_avg_basket = (float(all_revenue) / int(all_transactions)) if all_transactions > 0 else 0

    outlet_count = db.query(func.count(Outlet.outlet_id)).scalar() or 1
    system_avg_low_stock = db.query(func.count(Inventory.inventory_id)).filter(
        Inventory.current_stock <= Product.reorder_level
    ).join(Product, Inventory.product_id == Product.product_id).scalar() or 0
    system_avg_low_stock = system_avg_low_stock / outlet_count if outlet_count > 0 else 0

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
    manager_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create new outlet. Superadmin only."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can create outlets"
        )

    new_outlet = Outlet(
        name=name,
        city=city,
        address=address,
        manager_name=manager_name,
        is_active=True
    )
    db.add(new_outlet)
    db.commit()
    db.refresh(new_outlet)

    return {
        "id": new_outlet.outlet_id,
        "name": new_outlet.name,
        "city": new_outlet.city,
        "address": new_outlet.address,
        "manager_name": new_outlet.manager_name,
        "message": "Outlet created successfully"
    }


@router.delete("/{outlet_id}")
async def delete_outlet(
    outlet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete outlet. Superadmin only."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can delete outlets"
        )

    result = await db.execute(select(Outlet).where(Outlet.outlet_id == outlet_id))

    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    # Mark as inactive instead of hard delete (safer)
    outlet.is_active = False
    db.commit()

    return {
        "id": outlet_id,
        "message": "Outlet deleted successfully"
    }
