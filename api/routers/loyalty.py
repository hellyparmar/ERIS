"""
Loyalty Router - Next-Gen Loyalty Module API Endpoints
Referral program and Udhaar (credit) management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from api.db.database import get_db
from api.db.models import User
from api.services.loyalty_service import LoyaltyService
from api.services.whatsapp_service import WhatsAppReceiptService
from api.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/loyalty", tags=["Loyalty Program"])


# ==================== REQUEST/RESPONSE MODELS ====================

class CreateReferralRequest(BaseModel):
    referrer_id: int
    referee_name: str = Field(..., min_length=1, max_length=255)
    referee_email: Optional[str] = None
    referee_phone: Optional[str] = None


class ConvertReferralRequest(BaseModel):
    new_customer_id: Optional[int] = None


class SendReminderRequest(BaseModel):
    customer_id: int
    invoice_id: Optional[int] = None
    channel: str = Field(default="whatsapp", description="whatsapp, sms, or email")


class BulkReminderRequest(BaseModel):
    min_days_overdue: int = Field(default=1, ge=0)
    max_reminders: int = Field(default=10, ge=1, le=100)
    channel: str = Field(default="whatsapp")


# ==================== DASHBOARD STATS ====================

@router.get("/stats")
async def get_loyalty_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get loyalty program dashboard statistics
    
    Returns:
    - Referral counts (total, converted, pending)
    - Reward amounts (total earned, pending)
    - Credit overview (total outstanding, at-risk count)
    """
    service = LoyaltyService(db)
    return service.get_loyalty_stats()


# ==================== REFERRAL ENDPOINTS ====================

@router.get("/referrals")
async def get_referrals(
    status: Optional[str] = Query(None, description="Filter by status: pending, converted, rewarded"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all referrals with referrer info"""
    service = LoyaltyService(db)
    return service.get_all_referrals(status=status, limit=limit)


@router.get("/referrals/top-referrers")
async def get_top_referrers(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get top customers by successful referrals"""
    service = LoyaltyService(db)
    return service.get_top_referrers(limit=limit)


@router.post("/referrals", status_code=201)
async def create_referral(
    request: CreateReferralRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new referral invite
    
    - **referrer_id**: Customer ID making the referral
    - **referee_name**: Name of the person being referred
    - **referee_email**: Email of the person being referred
    - **referee_phone**: Phone of the person being referred
    """
    try:
        service = LoyaltyService(db)
        referral = service.create_referral(
            referrer_id=request.referrer_id,
            referee_name=request.referee_name,
            referee_email=request.referee_email,
            referee_phone=request.referee_phone
        )
        return {
            "id": referral.id,
            "status": referral.status,
            "message": f"Referral created for {request.referee_name}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/referrals/{referral_id}/convert")
async def convert_referral(
    referral_id: int,
    request: ConvertReferralRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark a referral as converted and award reward to referrer
    """
    try:
        service = LoyaltyService(db)
        referral = service.convert_referral(
            referral_id=referral_id,
            new_customer_id=request.new_customer_id if request else None
        )
        return {
            "id": referral.id,
            "status": referral.status,
            "reward_amount": float(referral.reward_amount or 0),
            "message": "Referral converted and reward processed"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/referrals/customer/{customer_id}")
async def get_customer_referrals(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all referrals made by a specific customer"""
    service = LoyaltyService(db)
    
    # Ensure customer has a referral code
    try:
        referral_code = service.ensure_customer_has_referral_code(customer_id)
    except ValueError:
        referral_code = None
    
    referrals = service.get_customer_referrals(customer_id)
    return {
        "customer_id": customer_id,
        "referral_code": referral_code,
        "referrals": [
            {
                "id": ref.id,
                "referee_name": ref.referee_name,
                "status": ref.status,
                "reward_amount": float(ref.reward_amount or 0),
                "created_at": ref.created_at.isoformat() if ref.created_at else None
            }
            for ref in referrals
        ]
    }


# ==================== CREDIT (UDHAAR) ENDPOINTS ====================

@router.get("/credit/customers")
async def get_credit_customers(
    min_balance: float = Query(0, ge=0),
    risk_level: Optional[str] = Query(None, description="Filter: good, warning, critical"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get customers with credit (udhaar) accounts
    
    Returns customer credit data with:
    - Current balance and credit limit
    - Utilization percentage
    - Credit score
    - Risk status (good/warning/critical)
    """
    service = LoyaltyService(db)
    return service.get_all_credit_customers(
        min_balance=min_balance,
        risk_level=risk_level,
        limit=limit
    )


@router.get("/credit/at-risk")
async def get_at_risk_customers(
    min_utilization: float = Query(80, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customers at high credit risk (>80% utilization by default)"""
    service = LoyaltyService(db)
    all_customers = service.get_all_credit_customers()
    return [c for c in all_customers if c["utilization"] >= min_utilization]


@router.get("/credit/customer/{customer_id}")
async def get_customer_credit_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed credit information for a customer"""
    service = LoyaltyService(db)
    credit = service.get_customer_credit(customer_id)
    risk_analysis = service.calculate_credit_risk(customer_id)
    
    return {
        "customer_id": customer_id,
        "credit_limit": float(credit.credit_limit or 0),
        "current_balance": float(credit.current_balance or 0),
        "credit_score": credit.credit_score,
        "last_payment_date": credit.last_payment_date.isoformat() if credit.last_payment_date else None,
        "risk_analysis": risk_analysis
    }


# ==================== REMINDER ENDPOINTS ====================

@router.get("/reminders/queue")
async def get_reminder_queue(
    min_days_overdue: int = Query(1, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get prioritized queue of customers needing payment reminders
    
    Returns customers with overdue payments, sorted by urgency
    """
    service = LoyaltyService(db)
    return service.get_reminder_queue(min_days_overdue=min_days_overdue, limit=limit)


@router.post("/reminders/send")
async def send_reminder(
    request: SendReminderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a payment reminder to a customer via WhatsApp
    
    - **customer_id**: Customer to send reminder to
    - **invoice_id**: Specific invoice (optional - uses most overdue if not specified)
    - **channel**: Communication channel (whatsapp, sms, email)
    """
    from api.db.models import Customer, Invoice, PaymentStatus
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get invoice
    if request.invoice_id:
        invoice = db.query(Invoice).filter(Invoice.id == request.invoice_id).first()
    else:
        # Get most overdue invoice
        invoice = db.query(Invoice).filter(
            Invoice.customer_id == request.customer_id,
            Invoice.payment_status.in_([PaymentStatus.OVERDUE, PaymentStatus.PENDING]),
            Invoice.amount_due > 0
        ).order_by(Invoice.due_date.asc()).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="No overdue invoice found for this customer")
    
    # Calculate days overdue
    days_overdue = 0
    if invoice.due_date:
        days_overdue = (datetime.now() - invoice.due_date).days
    
    # Send reminder via WhatsApp
    whatsapp_service = WhatsAppReceiptService()
    result = whatsapp_service.send_payment_reminder(
        customer_whatsapp=customer.whatsapp_number or customer.phone or "",
        invoice_number=invoice.invoice_number,
        amount_due=float(invoice.amount_due),
        days_overdue=max(0, days_overdue)
    )
    
    # Record reminder in message history
    service = LoyaltyService(db)
    service.record_reminder_sent(
        customer_id=customer.id,
        invoice_id=invoice.id,
        channel=request.channel
    )
    
    return {
        "status": result.get("status", "sent"),
        "customer_id": customer.id,
        "customer_name": customer.name,
        "invoice_number": invoice.invoice_number,
        "amount_due": float(invoice.amount_due),
        "days_overdue": max(0, days_overdue),
        "channel": request.channel,
        "message": f"Reminder sent to {customer.name}"
    }


@router.post("/reminders/bulk")
async def send_bulk_reminders(
    request: BulkReminderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send bulk payment reminders to overdue customers
    
    - **min_days_overdue**: Minimum days past due date
    - **max_reminders**: Maximum number of reminders to send
    - **channel**: Communication channel
    """
    service = LoyaltyService(db)
    queue = service.get_reminder_queue(
        min_days_overdue=request.min_days_overdue,
        limit=request.max_reminders
    )
    
    if not queue:
        return {
            "sent": 0,
            "failed": 0,
            "message": "No customers in reminder queue"
        }
    
    # Prepare reminder data
    reminders = []
    for item in queue:
        if item.get("whatsapp") or item.get("phone"):
            reminders.append({
                "whatsapp": item.get("whatsapp") or item.get("phone"),
                "invoice_number": item["invoice_number"],
                "amount_due": item["amount_due"],
                "days_overdue": item["days_overdue"]
            })
    
    # Send via WhatsApp service
    whatsapp_service = WhatsAppReceiptService()
    results = whatsapp_service.send_bulk_reminders(reminders)
    
    return {
        "total_in_queue": len(queue),
        "sent": results.get("sent", 0),
        "simulated": results.get("simulated", 0),
        "failed": results.get("failed", 0),
        "channel": request.channel,
        "message": f"Bulk reminders processed for {len(reminders)} customers"
    }


@router.get("/reminders/history")
async def get_reminder_history(
    customer_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get history of payment reminders sent"""
    service = LoyaltyService(db)
    return service.get_reminder_history(
        customer_id=customer_id,
        days=days,
        limit=limit
    )
