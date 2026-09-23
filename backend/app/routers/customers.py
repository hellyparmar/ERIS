"""
Enterprise Retail Intelligence System v3.0
Customers Router - Customer management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

from app.database import get_db
from app.api.deps import get_current_active_user, get_outlet_scope
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new customer"""
    try:
        # Check if phone already exists
        existing = CustomerService.get_customer_by_phone(db, customer.phone)
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        new_customer = CustomerService.create_customer(db, customer.dict())
        
        return {
            "success": True,
            "data": new_customer.to_dict(),
            "message": "Customer created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_customers(
    segment: Optional[str] = Query(None, pattern="^(VIP|Regular|New)$"),
    tier: Optional[str] = Query(None, pattern="^(Bronze|Silver|Gold|Platinum)$"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List customers with filters and pagination"""
    try:
        result = CustomerService.list_customers(
            db,
            segment=segment,
            tier=tier,
            search=search,
            page=page,
            per_page=per_page
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_customer_stats(db: Session = Depends(get_db)):
    """Get overall customer statistics"""
    try:
        stats = CustomerService.get_customer_stats(db)
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}")
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer details"""
    try:
        customer = CustomerService.get_customer(db, customer_id)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "success": True,
            "data": customer.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{customer_id}")
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update customer information"""
    try:
        updated_customer = CustomerService.update_customer(
            db,
            customer_id,
            customer_data.dict(exclude_unset=True)
        )
        
        if not updated_customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "success": True,
            "data": updated_customer.to_dict(),
            "message": "Customer updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a customer"""
    try:
        deleted = CustomerService.delete_customer(db, customer_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "success": True,
            "message": "Customer deleted successfully"
        }
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
    db: Session = Depends(get_db)
):
    """Retrieve the transaction history for a specific customer scoped to user's accessible outlets."""
    try:
        from app.models.customers import Customer
        from app.models.models_v6 import Sale
        from sqlalchemy import select, func
        
        customer = db.execute(
            select(Customer).where(Customer.id == customer_id)
        ).scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
            
        allowed_outlets = get_outlet_scope(current_user, db)
        stmt = select(Sale).where(Sale.customer_id == customer_id)
        if allowed_outlets:
            stmt = stmt.where(Sale.outlet_id.in_(allowed_outlets))
            
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        sales = db.execute(
            stmt.order_by(Sale.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).scalars().all()
        
        history = []
        for sale in sales:
            history.append({
                "sale_id": sale.id,
                "transaction_date": sale.created_at,
                "total_amount": float(sale.total_amount) if sale.total_amount else 0,
                "status": sale.status
            })
            
        return {
            "success": True,
            "data": history,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/credit-balance")
async def get_credit_balance(customer_id: int, db: Session = Depends(get_db)):
    """Return customer credit limit and outstanding balance."""
    try:
        customer = db.execute(select(Customer).where(Customer.id == customer_id)).scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {
            "success": True,
            "data": {
                "customer_id": customer_id,
                "name": f"{customer.first_name} {customer.last_name}",
                "credit_rating": getattr(customer, "credit_rating", "A"),
                "credit_limit": float(getattr(customer, "credit_limit", 100000.0)),
                "outstanding_balance": float(getattr(customer, "outstanding_balance", 0.0)),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{customer_id}/credit-rating")
async def update_credit_rating(
    customer_id: int,
    rating: str = Query(..., pattern="^(A|B|C|D)$", description="New credit rating: A | B | C | D"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update customer credit rating tier."""
    try:
        customer = db.execute(select(Customer).where(Customer.id == customer_id)).scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        setattr(customer, "credit_rating", rating)
        db.commit()
        return {
            "success": True,
            "data": {"customer_id": customer_id, "new_rating": rating},
            "message": "Credit rating updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

