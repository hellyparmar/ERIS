"""
Enterprise Retail Intelligence System v3.0
Customers Router - Customer management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

from api.db import get_db
from api.services.customer_service import CustomerService
from api.services.loyalty_service import LoyaltyService
from api.services.credit_service import CreditService


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


class CreditLimitAssign(BaseModel):
    limit: Decimal = Field(..., ge=0)


class PaymentRecord(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., regex="^(cash|card|upi|bank_transfer)$")
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None


# Endpoints
@router.post("/")
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
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
    segment: Optional[str] = Query(None, regex="^(VIP|Regular|New)$"),
    tier: Optional[str] = Query(None, regex="^(Bronze|Silver|Gold|Platinum)$"),
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
    db: Session = Depends(get_db)
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
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
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


@router.get("/{customer_id}/loyalty")
async def get_customer_loyalty(customer_id: int, db: Session = Depends(get_db)):
    """Get customer loyalty details"""
    try:
        balance = LoyaltyService.get_loyalty_balance(db, customer_id)
        transactions = LoyaltyService.get_transaction_history(db, customer_id, limit=20)
        
        return {
            "success": True,
            "data": {
                "balance": balance,
                "recent_transactions": transactions
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/credit")
async def get_customer_credit(customer_id: int, db: Session = Depends(get_db)):
    """Get customer credit status"""
    try:
        status = CreditService.get_credit_status(db, customer_id)
        payments = CreditService.get_payment_history(db, customer_id, limit=20)
        
        return {
            "success": True,
            "data": {
                "status": status,
                "recent_payments": payments
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{customer_id}/credit/limit")
async def assign_credit_limit(
    customer_id: int,
    limit_data: CreditLimitAssign,
    db: Session = Depends(get_db)
):
    """Assign or update credit limit"""
    try:
        result = CreditService.assign_credit_limit(db, customer_id, limit_data.limit)
        
        return {
            "success": True,
            "data": result,
            "message": "Credit limit updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{customer_id}/credit/pay")
async def record_credit_payment(
    customer_id: int,
    payment: PaymentRecord,
    db: Session = Depends(get_db)
):
    """Record a credit payment"""
    try:
        result = CreditService.record_payment(
            db,
            customer_id,
            payment.amount,
            payment.payment_method,
            payment.reference_number,
            payment.notes,
            payment.created_by
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "success": True,
            "data": result,
            "message": "Payment recorded successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
