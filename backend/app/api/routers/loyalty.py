"""
Enterprise Retail Intelligence System v3.0
Loyalty Router - Loyalty points management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

from app.api.db import get_db
from app.api.services.loyalty_service import LoyaltyService


router = APIRouter(prefix="/loyalty", tags=["loyalty"])


# Pydantic models
class EarnPoints(BaseModel):
    customer_id: int = Field(..., gt=0)
    sale_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class RedeemPoints(BaseModel):
    customer_id: int = Field(..., gt=0)
    points: int = Field(..., gt=0)
    notes: Optional[str] = None


# Endpoints
@router.post("/earn")
async def earn_loyalty_points(earn_data: EarnPoints, db: Session = Depends(get_db)):
    """Award loyalty points for a purchase"""
    try:
        result = LoyaltyService.earn_points(
            db,
            earn_data.customer_id,
            earn_data.sale_id,
            float(earn_data.amount),
            earn_data.notes
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "success": True,
            "data": result,
            "message": f"Earned {result['points_earned']} points"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/redeem")
async def redeem_loyalty_points(redeem_data: RedeemPoints, db: Session = Depends(get_db)):
    """Redeem loyalty points"""
    try:
        result = LoyaltyService.redeem_points(
            db,
            redeem_data.customer_id,
            redeem_data.points,
            redeem_data.notes
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "success": True,
            "data": result,
            "message": f"Redeemed {result['points_redeemed']} points for ₹{result['discount_value']:.2f} discount"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiers")
async def get_tier_info():
    """Get loyalty tier information and benefits"""
    try:
        tiers = LoyaltyService.get_tier_benefits()
        
        return {
            "success": True,
            "data": tiers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/balance")
async def get_loyalty_balance(customer_id: int, db: Session = Depends(get_db)):
    """Get customer's loyalty points balance"""
    try:
        balance = LoyaltyService.get_loyalty_balance(db, customer_id)
        
        return {
            "success": True,
            "data": balance
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/transactions")
async def get_loyalty_transactions(
    customer_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get loyalty transaction history"""
    try:
        transactions = LoyaltyService.get_transaction_history(db, customer_id, limit)
        
        return {
            "success": True,
            "data": {
                "transactions": transactions,
                "count": len(transactions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expire")
async def expire_old_points(db: Session = Depends(get_db)):
    """Expire loyalty points older than 1 year (admin only)"""
    try:
        result = LoyaltyService.expire_old_points(db)
        
        return {
            "success": True,
            "data": result,
            "message": f"Expired {result['expired_transactions']} transactions totaling {result['total_expired_points']} points"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
