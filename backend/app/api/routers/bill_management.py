"""
Bill Management API Endpoints
Handles vendor bills, payments, GST input credit tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.api.db.database_postgres import get_db
from app.api.services.bill_management_service import BillManagementService, BillReconciliation

router = APIRouter(prefix="/api/v1/bills", tags=["Bill Management"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BillItemInput(BaseModel):
    """Bill line item"""
    category: str
    description: str
    quantity: int
    unit_price: float


class CreateBillRequest(BaseModel):
    """Create new bill"""
    bill_number: str
    supplier_id: int
    bill_date: datetime
    items: List[BillItemInput]
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class RecordPaymentRequest(BaseModel):
    """Record bill payment"""
    amount: float
    payment_date: datetime
    payment_method: str
    notes: Optional[str] = None


class ClaimGSTRequest(BaseModel):
    """Claim GST input"""
    amount: Optional[float] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/create")
async def create_bill(
    request: CreateBillRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new vendor bill
    
    Automatically calculates GST and tracks input credit availability.
    
    Args:
        request: Bill details with line items
        
    Returns:
        Created bill with ID and totals
    """
    result = BillManagementService.create_bill(
        bill_number=request.bill_number,
        supplier_id=request.supplier_id,
        bill_date=request.bill_date,
        items=[item.dict() for item in request.items],
        db=db,
        due_date=request.due_date,
        notes=request.notes
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/")
async def list_bills(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    List vendor bills
    
    Args:
        supplier_id: Optional filter by supplier
        status: Filter by status (draft, approved, paid)
        days: Lookback period (1-365)
        
    Returns:
        List of bills with summary
    """
    result = BillManagementService.get_bills(
        db=db,
        supplier_id=supplier_id,
        status=status,
        days=days
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/{bill_id}")
async def get_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed bill information
    
    Returns bill header, line items, and GST tracking.
    
    Args:
        bill_id: Bill ID
        
    Returns:
        Complete bill details with items
    """
    result = BillManagementService.get_bill_details(bill_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.post("/{bill_id}/payment")
async def record_payment(
    bill_id: int,
    request: RecordPaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Record payment for a bill
    
    Updates payment status and tracks amount paid.
    
    Args:
        bill_id: Bill ID
        request: Payment details
        
    Returns:
        Payment record with updated status
    """
    result = BillManagementService.record_bill_payment(
        bill_id=bill_id,
        amount=request.amount,
        payment_date=request.payment_date,
        payment_method=request.payment_method,
        db=db,
        notes=request.notes
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.post("/{bill_id}/claim-gst")
async def claim_gst_input(
    bill_id: int,
    request: ClaimGSTRequest,
    db: Session = Depends(get_db)
):
    """
    Claim GST input credit
    
    Records GST input credit claim for the bill.
    Reduces available GST, increases claimed GST.
    
    Args:
        bill_id: Bill ID
        request: Claim amount (optional, claims all if not specified)
        
    Returns:
        Updated GST claim status
    """
    result = BillManagementService.claim_gst_input(
        bill_id=bill_id,
        amount=request.amount,
        db=db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/analytics/gst-input-summary")
async def get_gst_input_summary(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get GST input credit summary
    
    Returns total GST available in bills, claimed, and available.
    
    Args:
        days: Analysis period
        
    Returns:
        GST input summary with claims
    """
    result = BillManagementService.get_gst_input_summary(db=db, days=days)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/analytics/vendor")
async def get_vendor_analytics(
    supplier_id: Optional[int] = Query(None),
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get vendor bill analytics
    
    Returns spending, payment metrics, and GST summary.
    
    Args:
        supplier_id: Optional filter by supplier
        days: Analysis period
        
    Returns:
        Vendor analytics and metrics
    """
    result = BillManagementService.get_vendor_analytics(
        db=db,
        supplier_id=supplier_id,
        days=days
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/reconciliation/pending")
async def get_pending_bills(
    days_overdue: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get pending and overdue bills
    
    Lists bills awaiting payment or partially paid.
    Can filter by overdue days.
    
    Args:
        days_overdue: Show only bills overdue by N+ days (0 = all pending)
        
    Returns:
        List of pending bills
    """
    result = BillReconciliation.get_pending_bills(
        db=db,
        days_overdue=days_overdue
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.post("/reconciliation/gst-period")
async def reconcile_gst_period(
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: Session = Depends(get_db)
):
    """
    Generate GST reconciliation report
    
    Creates compliance report for a period showing:
    - Output GST from invoices
    - Input GST from bills
    - GST claims
    - Net GST liability/refund
    
    Args:
        period_start: Period start date
        period_end: Period end date
        
    Returns:
        GST reconciliation data
    """
    result = BillReconciliation.reconcile_gst_for_period(
        db=db,
        period_start=period_start,
        period_end=period_end
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/dashboard/summary")
async def get_bills_dashboard(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get bills dashboard summary
    
    Returns key metrics and pending items for dashboard.
    
    Args:
        days: Analysis period
        
    Returns:
        Dashboard metrics
    """
    vendor_analytics = BillManagementService.get_vendor_analytics(db=db, days=days)
    gst_summary = BillManagementService.get_gst_input_summary(db=db, days=days)
    pending_bills = BillReconciliation.get_pending_bills(db=db)
    
    if vendor_analytics["success"] and gst_summary["success"]:
        return {
            "success": True,
            "data": {
                "period_days": days,
                "bills_count": vendor_analytics["data"]["bill_count"],
                "total_payable": vendor_analytics["data"]["total_amount"],
                "amount_paid": vendor_analytics["data"]["total_paid"],
                "pending_amount": vendor_analytics["data"]["pending_amount"],
                "payment_rate_percent": vendor_analytics["data"]["payment_rate_percent"],
                "gst_input_available": gst_summary["data"]["total_gst_available"],
                "gst_claimed": gst_summary["data"]["total_gst_claimed"],
                "pending_bills_count": pending_bills["data"]["total_bills"]
            }
        }
    
    raise HTTPException(status_code=400, detail="Failed to fetch dashboard data")
