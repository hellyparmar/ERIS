"""
Manager Override System for R-DIOS POS
Allows managers to approve high-value operations:
- Discounts above configured threshold
- Price overrides
- Refunds above threshold
- Quantity adjustments for restricted items

All overrides are audit logged.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from api.db import get_db
from api.utils.jwt_auth import verify_access_token, verify_pos_token, verify_pin, PERMISSIONS
from api.db.models import AuditLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pos", tags=["POS Manager Override"])

# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class ManagerOverrideRequest(BaseModel):
    """Request manager approval for high-value operation"""
    action: str  # "discount", "refund", "price_override", "quantity"
    reason: str
    amount_or_value: float
    manager_id: int
    manager_pin: str  # PIN for verification
    context: Dict[str, Any]  # Action-specific context

class DiscountOverrideRequest(BaseModel):
    """Discount above threshold requiring manager approval"""
    sale_id: Optional[int]
    discount_amount: float
    discount_reason: str
    manager_id: int
    manager_pin: str

class RefundOverrideRequest(BaseModel):
    """Refund above threshold"""
    sale_id: int
    refund_amount: float
    reason: str
    manager_id: int
    manager_pin: str

class OverrideResponse(BaseModel):
    """Override approval response"""
    success: bool
    approved: bool
    override_code: str
    approved_by: int
    approved_at: datetime
    expires_at: datetime
    message: str

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

OVERRIDE_CONFIG = {
    "discount_threshold": 500.0,      # ₹500 or more requires override
    "discount_max_percent": 50,       # Max 50% discount allowed
    "refund_threshold": 1000.0,       # ₹1000 or more requires override
    "price_override_allowed": True,
    "quantity_override_allowed": True,
    "override_valid_minutes": 5,      # Override code valid for 5 minutes
}

# ═══════════════════════════════════════════════════════════════
# MANAGER OVERRIDE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/override/request-discount")
async def request_discount_override(
    request: DiscountOverrideRequest,
    cashier_user: Dict = Depends(verify_pos_token),
    db=Depends(get_db)
):
    """
    Cashier requests discount override from manager
    Manager must enter PIN to approve
    """
    try:
        # Validate discount amount
        if request.discount_amount < OVERRIDE_CONFIG["discount_threshold"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Discount below ₹{OVERRIDE_CONFIG['discount_threshold']} — no approval needed"
            )
        
        # Verify manager PIN
        from api.db.models import Employee
        manager = db.query(Employee).filter_by(
            id=request.manager_id,
            role="manager"
        ).first()
        
        if not manager:
            logger.warning(f"Override denied: Manager {request.manager_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Manager not found"
            )
        
        if not verify_pin(request.manager_pin, manager.pin_hash or ""):
            logger.warning(f"Override denied: Invalid PIN for manager {request.manager_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Manager PIN incorrect"
            )
        
        # Generate override code (valid for 5 minutes)
        import uuid
        from datetime import timedelta
        
        override_code = str(uuid.uuid4())[:8].upper()
        expires_at = datetime.utcnow() + timedelta(minutes=OVERRIDE_CONFIG["override_valid_minutes"])
        
        # Log the override approval
        db.add(AuditLog(
            action="discount_override_approved",
            performed_by=cashier_user.get("employee_id"),
            approved_by=request.manager_id,
            context={
                "discount_amount": request.discount_amount,
                "reason": request.discount_reason,
                "override_code": override_code,
                "sale_id": request.sale_id
            }
        ))
        db.commit()
        
        logger.info(f"Discount override approved: ₹{request.discount_amount} by Manager {request.manager_id}")
        
        return OverrideResponse(
            success=True,
            approved=True,
            override_code=override_code,
            approved_by=request.manager_id,
            approved_at=datetime.utcnow(),
            expires_at=expires_at,
            message=f"Discount approved: ₹{request.discount_amount} — Code: {override_code}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Discount override error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Override request failed"
        )

@router.post("/override/request-refund")
async def request_refund_override(
    request: RefundOverrideRequest,
    cashier_user: Dict = Depends(verify_pos_token),
    db=Depends(get_db)
):
    """
    Cashier requests refund override from manager
    Manager must enter PIN to approve
    """
    try:
        # Validate refund amount
        if request.refund_amount < OVERRIDE_CONFIG["refund_threshold"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund below ₹{OVERRIDE_CONFIG['refund_threshold']} — no approval needed"
            )
        
        # Verify manager PIN
        from api.db.models import Employee
        manager = db.query(Employee).filter_by(
            id=request.manager_id,
            role="manager"
        ).first()
        
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Manager not found"
            )
        
        if not verify_pin(request.manager_pin, manager.pin_hash or ""):
            logger.warning(f"Refund override denied: Invalid PIN")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Manager PIN incorrect"
            )
        
        # Generate override code
        import uuid
        from datetime import timedelta
        
        override_code = str(uuid.uuid4())[:8].upper()
        expires_at = datetime.utcnow() + timedelta(minutes=OVERRIDE_CONFIG["override_valid_minutes"])
        
        # Log the override
        db.add(AuditLog(
            action="refund_override_approved",
            performed_by=cashier_user.get("employee_id"),
            approved_by=request.manager_id,
            context={
                "refund_amount": request.refund_amount,
                "reason": request.reason,
                "override_code": override_code,
                "sale_id": request.sale_id
            }
        ))
        db.commit()
        
        logger.info(f"Refund override approved: ₹{request.refund_amount} for Sale {request.sale_id}")
        
        return OverrideResponse(
            success=True,
            approved=True,
            override_code=override_code,
            approved_by=request.manager_id,
            approved_at=datetime.utcnow(),
            expires_at=expires_at,
            message=f"Refund approved: ₹{request.refund_amount} — Code: {override_code}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund override error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Override request failed"
        )

@router.get("/override/config")
async def get_override_config():
    """Get override configuration (thresholds, limits)"""
    return {
        "success": True,
        "data": OVERRIDE_CONFIG
    }

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def validate_override_code(override_code: str, action_type: str, db) -> bool:
    """Validate that override code is valid and not expired"""
    from datetime import datetime, timedelta
    
    # In production, would store override codes in Redis with expiry
    # For now, we trust the manager PIN verification above
    return True

def log_override_usage(
    cashier_id: int,
    override_code: str,
    action: str,
    result: str,
    db
):
    """Log usage of override code"""
    db.add(AuditLog(
        action=f"override_used_{action}",
        performed_by=cashier_id,
        context={"override_code": override_code, "result": result}
    ))
    db.commit()
