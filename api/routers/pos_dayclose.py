"""
Day Open/Close Workflow for POS
Manager workflow:
1. Open day: Register opening float (cash in register at start)
2. Throughout day: Cashiers process transactions
3. Close day: Count physical cash, compare to system, reconcile

All reconciliation data is saved for audit.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

from api.db import get_db
from api.utils.jwt_auth import verify_access_token, PERMISSIONS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pos", tags=["Cash Register Management"])

# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class DayOpenRequest(BaseModel):
    """Open cash register for the day"""
    opening_float: float  # Cash/cheques in register at start
    notes: Optional[str] = None

class DayCloseRequest(BaseModel):
    """Close cash register at end of day"""
    physical_cash_count: float  # Actual cash counted
    cheques_count: float = 0.0  # Physical cheques
    notes: Optional[str] = None

class DayCloseResponse(BaseModel):
    """Reconciliation results"""
    success: bool
    day_close_id: int
    date: date
    opening_float: float
    closing_float: float
    expected_cash: float  # System calculated
    physical_cash: float  # Counted by manager
    variance: float  # Difference
    variance_percent: float  # As percentage
    reconciliation_status: str  # "matched", "small_variance", "large_variance"
    sales_summary: Dict[str, Any]

# ═══════════════════════════════════════════════════════════════
# DAY OPEN ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/day/open")
async def open_day(
    request: DayOpenRequest,
    manager: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """
    Open cash register for the day
    Manager registers opening float
    """
    try:
        # Check manager permissions
        if manager.get("role") not in ["manager", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can open the register"
            )
        
        # Check if day already open
        from sqlalchemy import func, and_
        from api.db.models import DayClose  # Assuming this table exists
        
        today = date.today()
        existing = db.query(DayClose).filter(
            and_(
                func.date(DayClose.created_at) == today,
                DayClose.closed_at == None  # Not closed
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Register already open for today"
            )
        
        # Create day open record
        day_close = DayClose(
            date=today,
            opening_float=request.opening_float,
            opened_by=manager.get("user_id"),
            opened_at=datetime.utcnow(),
            notes=request.notes,
            created_at=datetime.utcnow()
        )
        db.add(day_close)
        db.commit()
        
        logger.info(f"Register opened: Opening float ₹{request.opening_float}")
        
        return {
            "success": True,
            "data": {
                "day_id": day_close.id,
                "date": today,
                "opening_float": request.opening_float,
                "opened_by": manager.get("user_id"),
                "opened_at": datetime.utcnow(),
                "message": f"Register opened with opening float ₹{request.opening_float}"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Day open error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open register"
        )

# ═══════════════════════════════════════════════════════════════
# DAY CLOSE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/day/close")
async def close_day(
    request: DayCloseRequest,
    manager: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """
    Close cash register and reconcile
    Manager counts physical cash and compares to system
    """
    try:
        # Check manager permissions
        if manager.get("role") not in ["manager", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can close the register"
            )
        
        # Get today's open record
        from sqlalchemy import func, and_, text
        from api.db.models import DayClose, Sale
        
        today = date.today()
        day_record = db.query(DayClose).filter(
            and_(
                func.date(DayClose.created_at) == today,
                DayClose.closed_at == None
            )
        ).first()
        
        if not day_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No open register found for today"
            )
        
        # Calculate sales from today
        try:
            result = db.execute(text("""
                SELECT 
                  COUNT(*) as transaction_count,
                  SUM(total_amount) as total_sales,
                  SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END) as cash_sales,
                  SUM(CASE WHEN payment_method = 'upi' THEN total_amount ELSE 0 END) as upi_sales,
                  SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END) as card_sales,
                  SUM(CASE WHEN payment_method = 'khata' THEN total_amount ELSE 0 END) as khata_sales
                FROM sales
                WHERE DATE(created_at) = CURRENT_DATE
                  AND status = 'completed'
            """))
            
            sales_data = result.fetchone()
            transaction_count = sales_data[0] or 0
            total_sales = float(sales_data[1] or 0)
            cash_sales = float(sales_data[2] or 0)
            upi_sales = float(sales_data[3] or 0)
            card_sales = float(sales_data[4] or 0)
            khata_sales = float(sales_data[5] or 0)
        
        except Exception as e:
            logger.error(f"Sales calculation error: {e}")
            total_sales = 0
            cash_sales = 0
        
        # Calculate expected cash
        expected_cash = day_record.opening_float + cash_sales
        physical_cash = request.physical_cash_count
        variance = physical_cash - expected_cash
        variance_percent = (variance / expected_cash * 100) if expected_cash > 0 else 0
        
        # Determine reconciliation status
        if abs(variance) < 1:  # Within ₹1 (rounding errors)
            reconciliation_status = "matched"
        elif abs(variance) < 50:  # Within ₹50
            reconciliation_status = "small_variance"
        else:
            reconciliation_status = "large_variance"
        
        # Update day close record
        day_record.closed_at = datetime.utcnow()
        day_record.closing_float = physical_cash
        day_record.closed_by = manager.get("user_id")
        day_record.expected_cash = expected_cash
        day_record.physical_cash = physical_cash
        day_record.variance = variance
        day_record.reconciliation_status = reconciliation_status
        day_record.notes = request.notes
        
        db.commit()
        
        logger.info(f"Register closed: Variance ₹{variance} ({reconciliation_status})")
        
        return DayCloseResponse(
            success=True,
            day_close_id=day_record.id,
            date=today,
            opening_float=day_record.opening_float,
            closing_float=physical_cash,
            expected_cash=expected_cash,
            physical_cash=physical_cash,
            variance=variance,
            variance_percent=round(variance_percent, 2),
            reconciliation_status=reconciliation_status,
            sales_summary={
                "transaction_count": transaction_count,
                "total_sales": round(total_sales, 2),
                "cash_sales": round(cash_sales, 2),
                "upi_sales": round(upi_sales, 2),
                "card_sales": round(card_sales, 2),
                "khata_sales": round(khata_sales, 2)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Day close error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close register"
        )

# ═══════════════════════════════════════════════════════════════
# STATUS ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/day/status")
async def get_day_status(
    current_user: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """Get current day's register status"""
    try:
        from sqlalchemy import func, and_
        from api.db.models import DayClose
        
        today = date.today()
        day_record = db.query(DayClose).filter(
            and_(
                func.date(DayClose.created_at) == today
            )
        ).order_by(DayClose.created_at.desc()).first()
        
        if not day_record:
            return {
                "success": True,
                "data": {
                    "status": "not_opened",
                    "date": today,
                    "message": "Register not opened for today"
                }
            }
        
        return {
            "success": True,
            "data": {
                "status": "open" if not day_record.closed_at else "closed",
                "date": today,
                "opening_float": day_record.opening_float,
                "opened_at": day_record.opened_at,
                "closed_at": day_record.closed_at,
                "closing_float": day_record.closing_float,
                "variance": day_record.variance,
                "reconciliation_status": day_record.reconciliation_status
            }
        }
    
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get day status"
        )
