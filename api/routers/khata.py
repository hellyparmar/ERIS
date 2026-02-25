"""
Khata (Credit Tracking) API Router
Uses khata_service for business logic
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from api.db import get_db
from api.services import khata_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/khata", tags=["Khata Credit Tracking"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class CreditSaleRequest(BaseModel):
    customer_id: int
    amount: float
    notes: Optional[str] = None


class PaymentRequest(BaseModel):
    customer_id: int
    amount: float
    payment_method: str = "cash"
    notes: Optional[str] = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """Summary of all credit accounts"""
    try:
        data = khata_service.get_khata_summary(db)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(500, "Failed to fetch summary")


@router.get("/accounts")
async def list_accounts(
    search: Optional[str] = Query(None),
    has_balance: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all customer credit accounts with optional filters"""
    try:
        result = khata_service.list_credit_accounts(db, search, has_balance, page, per_page)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"List accounts error: {e}")
        raise HTTPException(500, "Failed to fetch accounts")


@router.get("/customer/{customer_id}")
async def get_customer_balance(customer_id: int, db: Session = Depends(get_db)):
    """Get outstanding balance for a specific customer"""
    try:
        account = khata_service.get_or_create_credit_account(db, customer_id)
        return {
            "success": True,
            "data": {
                **account,
                "has_outstanding": account["current_balance"] > 0,
                "available_credit": max(0, account["credit_limit"] - account["current_balance"])
            }
        }
    except Exception as e:
        logger.error(f"Balance fetch error: {e}")
        raise HTTPException(500, "Failed to fetch balance")


@router.post("/credit-sale")
async def record_credit_sale(request: CreditSaleRequest, db: Session = Depends(get_db)):
    """Record a new credit sale — adds to customer balance"""
    try:
        result = khata_service.record_credit_sale(
            db, request.customer_id, request.amount, request.notes
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Credit sale error: {e}")
        raise HTTPException(500, "Failed to record credit sale")


@router.post("/payment")
async def record_payment(request: PaymentRequest, db: Session = Depends(get_db)):
    """Record a payment against an outstanding balance"""
    try:
        result = khata_service.record_payment(
            db, request.customer_id, request.amount,
            request.payment_method, request.notes
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Payment error: {e}")
        raise HTTPException(500, "Failed to record payment")


@router.get("/overdue")
async def get_overdue(db: Session = Depends(get_db)):
    """List all customers with outstanding balances"""
    try:
        data = khata_service.get_overdue_accounts(db)
        return {
            "success": True,
            "data": data,
            "total": len(data),
            "total_outstanding": sum(a["outstanding_balance"] for a in data)
        }
    except Exception as e:
        logger.error(f"Overdue error: {e}")
        raise HTTPException(500, "Failed to fetch overdue accounts")


@router.put("/credit-limit/{customer_id}")
async def update_credit_limit(
    customer_id: int,
    limit: float = Query(..., description="New credit limit in rupees"),
    db: Session = Depends(get_db)
):
    """Update credit limit for a customer"""
    try:
        from sqlalchemy import text
        db.execute(
            text("UPDATE customer_credits SET credit_limit = :limit, updated_at = NOW() WHERE customer_id = :cid"),
            {"limit": limit, "cid": customer_id}
        )
        db.commit()
        return {"success": True, "data": {"customer_id": customer_id, "new_limit": limit}}
    except Exception as e:
        db.rollback()
        logger.error(f"Credit limit update error: {e}")
        raise HTTPException(500, "Failed to update credit limit")
