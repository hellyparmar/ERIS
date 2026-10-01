"""
Enterprise Retail Intelligence System v3.0
Customers Router - Customer management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db_sync_dependency
from app.api.deps import get_current_active_user, get_outlet_scope, require_role
from app.models.users import User
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


# Pydantic models
class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    address: Optional[str] = None


# Endpoints
@router.post("/")
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Create a new customer"""
    try:
        # Check if phone already exists
        existing = CustomerService.get_customer_by_phone(db, customer.phone, current_user.organization_id)
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        new_customer = CustomerService.create_customer(db, customer.model_dump(), current_user.organization_id)

        return {"success": True, "data": new_customer.to_dict(), "message": "Customer created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_customers(
    segment: Optional[str] = Query(None, pattern="^(VIP|Regular|New)$"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    """List customers with filters and pagination"""
    try:
        result = CustomerService.list_customers(
            db,
            segment=segment,
            search=search,
            page=page,
            per_page=per_page,
            organization_id=current_user.organization_id,
        )

        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_customer_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    """Get overall customer statistics"""
    try:
        stats = CustomerService.get_customer_stats(db, current_user.organization_id)

        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}")
async def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    """Get customer details"""
    try:
        customer = CustomerService.get_customer(db, customer_id, current_user.organization_id)

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True, "data": customer.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{customer_id}")
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Update customer information"""
    try:
        updated_customer = CustomerService.update_customer(
            db, customer_id, current_user.organization_id, customer_data.model_dump(exclude_unset=True)
        )

        if not updated_customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True, "data": updated_customer.to_dict(), "message": "Customer updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Delete a customer"""
    try:
        deleted = CustomerService.delete_customer(db, customer_id, current_user.organization_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True, "message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/purchase-history")
async def get_purchase_history(
    customer_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    """Retrieve the transaction history for a specific customer scoped to user's accessible outlets."""
    try:
        from app.models.customers import Customer
        from app.models.commerce import Sale
        from sqlalchemy import select, func

        customer = db.execute(
            select(Customer).where(Customer.id == customer_id, Customer.organization_id == current_user.organization_id)
        ).scalar_one_or_none()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        allowed_outlets = get_outlet_scope(current_user, db)
        stmt = select(Sale).where(Sale.customer_id == customer_id)
        stmt = stmt.where(Sale.outlet_id.in_(allowed_outlets)) if allowed_outlets else stmt.where(False)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        sales = (
            db.execute(stmt.order_by(Sale.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
            .scalars()
            .all()
        )

        history = []
        for sale in sales:
            history.append(
                {
                    "sale_id": sale.id,
                    "transaction_date": sale.created_at,
                    "total_amount": float(sale.total_amount) if sale.total_amount else 0,
                    "status": sale.status,
                }
            )

        return {
            "success": True,
            "data": history,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
