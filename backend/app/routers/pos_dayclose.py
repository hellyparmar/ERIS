"""
Day Open/Close Workflow for POS
Manager workflow:
1. Open day: Register opening float (cash in register at start)
2. Throughout day: Cashiers process transactions
3. Close day: Count physical cash, compare to system, reconcile

All reconciliation data is saved for audit.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select, and_, text
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

from app.database import get_db
from app.api.utils.jwt_auth import verify_access_token
from app.models.outlet import Outlet
from app.models.users import User, UserOutletAccess
from app.models.day_close import DayClose

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pos", tags=["Cash Register Management"])

# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class DayOpenRequest(BaseModel):
    """Open cash register for the day"""
    opening_float: float
    outlet_id: Optional[int] = None
    notes: Optional[str] = None

class DayCloseRequest(BaseModel):
    """Close cash register at end of day"""
    physical_cash_count: float
    cheques_count: float = 0.0
    outlet_id: Optional[int] = None
    notes: Optional[str] = None

class DayCloseResponse(BaseModel):
    """Reconciliation results"""
    success: bool
    day_close_id: int
    date: date
    outlet_id: int
    opening_float: float
    closing_float: float
    expected_cash: float
    physical_cash: float
    variance: float
    variance_percent: float
    reconciliation_status: str
    sales_summary: Dict[str, Any]

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

async def get_accessible_outlets(user_id: int, role: str, db) -> List[Dict[str, Any]]:
    """Get IDs and names of outlets accessible to the user"""
    if role == "super_admin":
        result = await db.execute(select(Outlet).where(Outlet.is_deleted == False).order_by(Outlet.name))
        outlets = result.scalars().all()
        return [{"id": o.id, "name": o.name} for o in outlets]
        
    elif role == "area_manager":
        result = await db.execute(
            select(Outlet).join(UserOutletAccess, UserOutletAccess.outlet_id == Outlet.id)
            .where(and_(UserOutletAccess.user_id == user_id, Outlet.is_deleted == False))
            .order_by(Outlet.name)
        )
        outlets = result.scalars().all()
        return [{"id": o.id, "name": o.name} for o in outlets]
        
    elif role == "outlet_manager":
        # Check user_outlets table first
        result = await db.execute(
            select(Outlet).join(UserOutletAccess, UserOutletAccess.outlet_id == Outlet.id)
            .where(and_(UserOutletAccess.user_id == user_id, Outlet.is_deleted == False))
        )
        outlets = result.scalars().all()
        if outlets:
            return [{"id": o.id, "name": o.name} for o in outlets]
            
        # Fallback to users.outlet_id
        user_res = await db.execute(select(User.outlet_id).where(User.id == user_id))
        user_outlet_id = user_res.scalar_one_or_none()
        if user_outlet_id:
            outlet_res = await db.execute(select(Outlet).where(Outlet.id == user_outlet_id))
            o = outlet_res.scalar_one_or_none()
            if o:
                return [{"id": o.id, "name": o.name}]
                
    return []

async def validate_outlet_access(user_id: int, role: str, outlet_id: int, db) -> bool:
    """Validate if the user has access to the specified outlet_id"""
    accessible = await get_accessible_outlets(user_id, role, db)
    accessible_ids = [o["id"] for o in accessible]
    return outlet_id in accessible_ids

# ═══════════════════════════════════════════════════════════════
# DAY OPEN ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/day/open")
async def open_day(
    request: DayOpenRequest,
    manager: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """Open cash register for the day"""
    try:
        user_id = manager.get("user_id")
        role = manager.get("role")
        
        # Check permissions
        if role not in ["outlet_manager", "area_manager", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to open the register"
            )
            
        # Resolve outlet_id
        outlet_id = request.outlet_id
        if not outlet_id:
            accessible = await get_accessible_outlets(user_id, role, db)
            if not accessible:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User has no assigned outlets"
                )
            outlet_id = accessible[0]["id"]
        else:
            if not await validate_outlet_access(user_id, role, outlet_id, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this outlet"
                )
        
        today = date.today()
        
        # Check if day already open
        result = await db.execute(select(DayClose).where(and_(
            DayClose.date == today,
            DayClose.outlet_id == outlet_id,
            DayClose.closed_at == None
        )))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Register already open for today at this outlet"
            )
            
        # Create day open record
        day_close = DayClose(
            outlet_id=outlet_id,
            date=today,
            opening_float=request.opening_float,
            opened_by=user_id,
            opened_at=datetime.utcnow(),
            notes=request.notes,
            created_at=datetime.utcnow()
        )
        db.add(day_close)
        await db.commit()
        
        logger.info(f"Register opened for outlet {outlet_id} with float ₹{request.opening_float}")
        
        return {
            "success": True,
            "data": {
                "day_id": day_close.id,
                "date": today,
                "outlet_id": outlet_id,
                "opening_float": request.opening_float,
                "opened_by": user_id,
                "opened_at": day_close.opened_at.isoformat(),
                "message": f"Register opened successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Day open error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open register"
        )

# ═══════════════════════════════════════════════════════════════
# DAY CLOSE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/day/close", response_model=DayCloseResponse)
async def close_day(
    request: DayCloseRequest,
    manager: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """Close cash register and reconcile"""
    try:
        user_id = manager.get("user_id")
        role = manager.get("role")
        
        # Check permissions
        if role not in ["outlet_manager", "area_manager", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to close the register"
            )
            
        # Resolve outlet_id
        outlet_id = request.outlet_id
        if not outlet_id:
            accessible = await get_accessible_outlets(user_id, role, db)
            if not accessible:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User has no assigned outlets"
                )
            outlet_id = accessible[0]["id"]
        else:
            if not await validate_outlet_access(user_id, role, outlet_id, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this outlet"
                )
                
        today = date.today()
        
        # Get open record
        result = await db.execute(select(DayClose).where(and_(
            DayClose.date == today,
            DayClose.outlet_id == outlet_id,
            DayClose.closed_at == None
        )))
        day_record = result.scalar_one_or_none()
        if not day_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No open register found for today at this outlet"
            )
            
        # Calculate expected totals for this outlet
        sales_result = await db.execute(text("""
            SELECT 
              COUNT(*) as transaction_count,
              COALESCE(SUM(total_amount), 0) as total_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'upi' THEN total_amount ELSE 0 END), 0) as upi_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_sales
            FROM sales
            WHERE DATE(transaction_date) = CURRENT_DATE AND store_id = :store_id
        """), {"store_id": outlet_id})
        
        sales_data = sales_result.fetchone()
        transaction_count = sales_data[0] or 0
        total_sales = float(sales_data[1] or 0)
        cash_sales = float(sales_data[2] or 0)
        upi_sales = float(sales_data[3] or 0)
        card_sales = float(sales_data[4] or 0)
        # Reconciliation calculations
        expected_cash = day_record.opening_float + cash_sales
        physical_cash = request.physical_cash_count
        variance = physical_cash - expected_cash
        variance_percent = (variance / expected_cash * 100) if expected_cash > 0 else 0.0
        
        if abs(variance) < 1.0:
            reconciliation_status = "matched"
        elif abs(variance) < 50.0:
            reconciliation_status = "small_variance"
        else:
            reconciliation_status = "large_variance"
            
        # Update record
        day_record.closed_at = datetime.utcnow()
        day_record.closing_float = physical_cash
        day_record.closed_by = user_id
        day_record.expected_cash = expected_cash
        day_record.physical_cash = physical_cash
        day_record.variance = variance
        day_record.reconciliation_status = reconciliation_status
        day_record.notes = request.notes
        
        await db.commit()
        logger.info(f"Register closed for outlet {outlet_id}: variance ₹{variance} ({reconciliation_status})")
        
        return DayCloseResponse(
            success=True,
            day_close_id=day_record.id,
            date=today,
            outlet_id=outlet_id,
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
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Day close error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close register"
        )

# ═══════════════════════════════════════════════════════════════
# STATUS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/day/status")
async def get_day_status(
    outlet_id: Optional[int] = None,
    current_user: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """Get current day's register status"""
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        accessible = await get_accessible_outlets(user_id, role, db)
        if not accessible:
            return {
                "success": True,
                "data": {
                    "status": "no_outlets",
                    "message": "User has no outlets assigned"
                },
                "accessible_outlets": []
            }
            
        # Resolve active outlet_id
        if not outlet_id:
            outlet_id = accessible[0]["id"]
        else:
            if not await validate_outlet_access(user_id, role, outlet_id, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this outlet"
                )
                
        today = date.today()
        
        # Get today's record for this outlet
        result = await db.execute(select(DayClose).where(and_(
            DayClose.date == today,
            DayClose.outlet_id == outlet_id
        )).order_by(DayClose.created_at.desc()))
        day_record = result.scalar_one_or_none()
        
        if not day_record:
            # Get current sales for today to display preview
            sales_result = await db.execute(text("""
                SELECT 
                  COUNT(*) as transaction_count,
                  COALESCE(SUM(total_amount), 0) as total_sales,
                  COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_sales,
                  COALESCE(SUM(CASE WHEN payment_method = 'upi' THEN total_amount ELSE 0 END), 0) as upi_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_sales
            FROM sales
            WHERE DATE(transaction_date) = CURRENT_DATE AND store_id = :store_id
        """), {"store_id": outlet_id})
        
        sales_data = sales_result.fetchone()
        
        return {
            "success": True,
            "data": {
                "status": "not_opened",
                    "outlet_id": outlet_id,
                    "date": today,
                    "message": "Register not opened for today",
                    "sales_preview": {
                        "transaction_count": sales_data[0] or 0,
                        "total_sales": float(sales_data[1] or 0),
                        "cash_sales": float(sales_data[2] or 0),
                        "upi_sales": float(sales_data[3] or 0),
                        "card_sales": float(sales_data[4] or 0),
                    }
                },
                "accessible_outlets": accessible
            }
            
        # Get current sales for today
        sales_result = await db.execute(text("""
            SELECT 
              COUNT(*) as transaction_count,
              COALESCE(SUM(total_amount), 0) as total_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'upi' THEN total_amount ELSE 0 END), 0) as upi_sales,
              COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_sales
            FROM sales
            WHERE DATE(transaction_date) = CURRENT_DATE AND store_id = :store_id
        """), {"store_id": outlet_id})
        
        sales_data = sales_result.fetchone()
        
        return {
            "success": True,
            "data": {
                "status": "open" if not day_record.closed_at else "closed",
                "outlet_id": outlet_id,
                "date": today,
                "opening_float": day_record.opening_float,
                "opened_at": day_record.opened_at.isoformat() if day_record.opened_at else None,
                "closed_at": day_record.closed_at.isoformat() if day_record.closed_at else None,
                "closing_float": day_record.closing_float,
                "variance": day_record.variance,
                "reconciliation_status": day_record.reconciliation_status,
                "notes": day_record.notes,
                "sales_summary": {
                    "transaction_count": sales_data[0] or 0,
                    "total_sales": float(sales_data[1] or 0),
                    "cash_sales": float(sales_data[2] or 0),
                    "upi_sales": float(sales_data[3] or 0),
                    "card_sales": float(sales_data[4] or 0)
                }
            },
            "accessible_outlets": accessible
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get day status"
        )

# ═══════════════════════════════════════════════════════════════
# HISTORY ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/day/history")
async def get_day_history(
    outlet_id: Optional[int] = None,
    current_user: Dict = Depends(verify_access_token),
    db=Depends(get_db)
):
    """Get history of register day-close records for the outlet"""
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        # Resolve outlet_id
        if not outlet_id:
            accessible = await get_accessible_outlets(user_id, role, db)
            if not accessible:
                return {"success": True, "history": []}
            outlet_id = accessible[0]["id"]
        else:
            if not await validate_outlet_access(user_id, role, outlet_id, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this outlet"
                )
                
        # Query history
        result = await db.execute(
            select(DayClose, User.first_name, User.last_name)
            .outerjoin(User, DayClose.closed_by == User.id)
            .where(and_(DayClose.outlet_id == outlet_id, DayClose.closed_at != None))
            .order_by(DayClose.date.desc())
        )
        
        history = []
        for row in result.all():
            record = row[0]
            first_name = row[1] or ""
            last_name = row[2] or ""
            submitted_by = f"{first_name} {last_name}".strip() or f"User ID {record.closed_by}"
            
            history.append({
                "id": record.id,
                "date": record.date.isoformat(),
                "opening_float": record.opening_float,
                "expected_cash": record.expected_cash,
                "counted_cash": record.physical_cash,
                "variance": record.variance,
                "reconciliation_status": record.reconciliation_status,
                "submitted_by": submitted_by,
                "notes": record.notes
            })
            
        return {
            "success": True,
            "history": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History fetch error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history"
        )
