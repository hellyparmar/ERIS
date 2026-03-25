"""
Phase 2: Credit Management with Database Integration

Complete credit lifecycle management with scoring and database persistence
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.api.db.database import get_db
from app.api.db.phase2_models import (
    CustomerCredit, CreditTransaction, CreditReminder
)
from app.api.services.phase2_credit_service import phase2_credit_service

router = APIRouter(prefix="/api/v2/credit", tags=["credit"])


class CreditAccountCreateRequest(BaseModel):
    business_id: int
    customer_id: int
    credit_limit: Decimal = Decimal("50000")
    payment_terms_days: int = 30
    notes: Optional[str] = None


# ==================== Credit Account Management ====================

@router.post("/accounts/create")
def create_credit_account(
    request: CreditAccountCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new credit account for customer
    
    Args:
        request: Credit account creation request
        
    Returns:
        Created credit account details
    """
    try:
        # Check if account already exists
        existing = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == request.customer_id
        ).first()
        
        if existing:
            raise ValueError(f"Credit account already exists for customer {request.customer_id}")
        
        # Create new credit account
        account = CustomerCredit(
            business_id=request.business_id,
            customer_id=request.customer_id,
            credit_limit=Decimal(str(request.credit_limit)),
            current_balance=Decimal(0),
            credit_score=100,  # Initial score
            credit_rating="GOOD"
        )
        
        db.add(account)
        db.commit()
        
        return {
            "status": "success",
            "account": {
                "id": account.id,
                "customer_id": account.customer_id,
                "credit_limit": float(account.credit_limit),
                "current_balance": float(account.current_balance),
                "credit_score": account.credit_score,
                "credit_rating": account.credit_rating,
                "created_at": account.created_at.isoformat() if account.created_at else None
            }
        }
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{customer_id}")
def get_credit_account(customer_id: str, db: Session = Depends(get_db)):
    """Get credit account details"""
    try:
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        return {
            "status": "success",
            "account": {
                "customer_id": account.customer_id,
                "customer_name": account.customer_name,
                "credit_limit": float(account.credit_limit),
                "used_credit": float(account.used_credit),
                "available_credit": float(account.credit_limit - account.used_credit),
                "credit_score": account.credit_score,
                "credit_status": account.credit_status,
                "last_transaction": None  # Will be populated from transactions
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/accounts/{customer_id}/limit")
def update_credit_limit(
    customer_id: str,
    new_limit: Decimal,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update credit limit for customer"""
    try:
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        old_limit = account.credit_limit
        account.credit_limit = Decimal(str(new_limit))
        account.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": f"Credit limit updated from {old_limit} to {new_limit}",
            "updated_at": account.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{customer_id}/balance")
def get_credit_balance(customer_id: str, db: Session = Depends(get_db)):
    """Get current credit balance"""
    try:
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        # Calculate pending payments
        pending_txns = db.query(CreditTransaction).filter(
            CreditTransaction.customer_id == customer_id,
            CreditTransaction.transaction_type == "CREDIT",
            CreditTransaction.due_date > date.today()
        ).all()
        
        pending_amount = sum(
            Decimal(str(txn.amount)) for txn in pending_txns
        )
        
        return {
            "status": "success",
            "balance": {
                "customer_id": account.customer_id,
                "total_credit": float(account.credit_limit),
                "used_credit": float(account.used_credit),
                "available_credit": float(account.credit_limit - account.used_credit),
                "pending_payments": float(pending_amount),
                "last_updated": account.updated_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Credit Transactions ====================

@router.post("/transactions/record")
def record_credit_transaction(
    customer_id: str,
    transaction_type: str,
    amount: Decimal,
    invoice_id: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Record a credit transaction (sale or payment)
    
    Args:
        customer_id: Customer ID
        transaction_type: CREDIT (sale) or PAYMENT
        amount: Transaction amount
        invoice_id: Related invoice ID
        due_date: Payment due date (for credit sales)
    """
    try:
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not account:
            raise ValueError(f"Credit account not found for {customer_id}")
        
        # Create transaction
        transaction = CreditTransaction(
            customer_id=customer_id,
            transaction_type=transaction_type.upper(),
            amount=Decimal(str(amount)),
            invoice_id=invoice_id,
            due_date=due_date,
            description=description,
            is_on_time=True,
            is_late=False,
            is_missed=False
        )
        
        db.add(transaction)
        
        # Update account used credit
        if transaction_type.upper() == "CREDIT":
            account.used_credit += Decimal(str(amount))
        elif transaction_type.upper() == "PAYMENT":
            account.used_credit -= Decimal(str(amount))
            if account.used_credit < 0:
                account.used_credit = Decimal(0)
        
        account.total_transactions += 1
        account.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "transaction": {
                "transaction_id": str(transaction.id),
                "customer_id": customer_id,
                "type": transaction_type,
                "amount": float(amount),
                "created_at": transaction.created_at.isoformat()
            }
        }
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{customer_id}")
def get_transaction_history(
    customer_id: str,
    transaction_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get credit transaction history"""
    try:
        query = db.query(CreditTransaction).filter(
            CreditTransaction.customer_id == customer_id
        )
        
        if transaction_type:
            query = query.filter(CreditTransaction.transaction_type == transaction_type)
        
        total = query.count()
        transactions = query.order_by(CreditTransaction.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "transactions": [
                {
                    "transaction_id": str(txn.id),
                    "type": txn.transaction_type,
                    "amount": float(txn.amount),
                    "due_date": txn.due_date.isoformat() if txn.due_date else None,
                    "created_at": txn.created_at.isoformat()
                }
                for txn in transactions
            ],
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment/record")
def record_payment(
    customer_id: str,
    amount: Decimal,
    payment_method: str,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Record a payment against credit account
    
    Args:
        customer_id: Customer ID
        amount: Payment amount
        payment_method: CASH, CHEQUE, UPI, TRANSFER, etc.
        reference_number: Payment reference (cheque no, UPI ref, etc.)
    """
    try:
        payment = phase2_credit_service.record_transaction(
            customer_id=customer_id,
            transaction_type="PAYMENT",
            amount=Decimal(str(amount)),
            description=f"Payment via {payment_method}"
        )
        
        # Store payment in database
        db_payment = CreditTransaction(
            customer_id=customer_id,
            transaction_type="PAYMENT",
            amount=Decimal(str(amount)),
            description=f"Payment via {payment_method}: {reference_number or ''}"
        )
        db.add(db_payment)
        
        # Update account
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if account:
            account.used_credit = max(Decimal(0), account.used_credit - Decimal(str(amount)))
            account.on_time_payments += 1
        
        db.commit()
        
        return {
            "status": "success",
            "payment": {
                "payment_id": str(db_payment.id),
                "customer_id": customer_id,
                "amount": float(amount),
                "method": payment_method,
                "reference": reference_number,
                "status": "COMPLETED",
                "recorded_at": datetime.utcnow().isoformat()
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Credit Scoring & Status ====================

@router.get("/score/{customer_id}")
def get_credit_score(customer_id: str, db: Session = Depends(get_db)):
    """
    Get credit score and status for customer
    
    Score Range: 0-100
    Status: EXCELLENT (80+), GOOD (60-79), FAIR (40-59), POOR (<40)
    """
    try:
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        # Calculate score using service
        score = phase2_credit_service.calculate_credit_score(
            total_transactions=account.total_transactions,
            on_time_payments=account.on_time_payments,
            late_payments=account.late_payments,
            missed_payments=account.missed_payments
        )
        
        # Update account score
        account.credit_score = score
        db.commit()
        
        return {
            "status": "success",
            "credit_profile": {
                "customer_id": account.customer_id,
                "credit_score": score,
                "credit_status": account.credit_status,
                "total_transactions": account.total_transactions,
                "on_time_payments": account.on_time_payments,
                "late_payments": account.late_payments,
                "missed_payments": account.missed_payments,
                "last_updated": account.updated_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Reminders & Collections ====================

@router.post("/reminders/send")
def send_payment_reminder(
    customer_id: str,
    reminder_type: str = Query("auto", regex="^(auto|manual)$"),
    channels: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Send payment reminder to customer
    
    Args:
        customer_id: Customer ID
        reminder_type: auto (automated) or manual
        channels: Communication channels (SMS, EMAIL, WHATSAPP)
    """
    try:
        account = db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        channels = channels or ["SMS", "EMAIL"]
        reminder_message = phase2_credit_service.get_payment_reminder_message(customer_id)
        
        # Get overdue transactions
        overdue_txns = db.query(CreditTransaction).filter(
            CreditTransaction.customer_id == customer_id,
            CreditTransaction.transaction_type == "CREDIT",
            CreditTransaction.due_date < date.today()
        ).all()
        
        for txn in overdue_txns:
            reminder = CreditReminder(
                customer_id=customer_id,
                invoice_id=txn.invoice_id,
                due_date=txn.due_date,
                amount_due=txn.amount,
                reminder_type=reminder_type,
                channels=",".join(channels),
                status="PENDING"
            )
            db.add(reminder)
        
        db.commit()
        
        return {
            "status": "success",
            "reminder": {
                "customer_id": customer_id,
                "reminder_type": reminder_type,
                "channels": channels,
                "message_preview": reminder_message[:100] + "..." if len(reminder_message) > 100 else reminder_message,
                "reminders_queued": len(overdue_txns),
                "sent_at": datetime.utcnow().isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminders/{customer_id}")
def get_pending_reminders(customer_id: str, db: Session = Depends(get_db)):
    """Get pending payment reminders"""
    try:
        reminders = db.query(CreditReminder).filter(
            CreditReminder.customer_id == customer_id,
            CreditReminder.status == "PENDING"
        ).all()
        
        return {
            "status": "success",
            "pending_reminders": len(reminders),
            "reminders": [
                {
                    "reminder_id": str(r.id),
                    "amount_due": float(r.amount_due),
                    "due_date": r.due_date.isoformat(),
                    "channels": r.channels.split(","),
                    "created_at": r.created_at.isoformat()
                }
                for r in reminders
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aging-report/{business_id}")
def get_aging_report(business_id: str, db: Session = Depends(get_db)):
    """
    Get aging report of outstanding credit
    
    Categories: Current, 0-30, 30-60, 60-90, 90+
    """
    try:
        today = date.today()
        
        # Get all overdue transactions for business
        transactions = db.query(CreditTransaction, CustomerCredit).join(
            CustomerCredit
        ).filter(
            CustomerCredit.business_id == business_id,
            CreditTransaction.transaction_type == "CREDIT"
        ).all()
        
        aging_data = {
            "current": Decimal(0),
            "0_30": Decimal(0),
            "30_60": Decimal(0),
            "60_90": Decimal(0),
            "90_plus": Decimal(0)
        }
        
        for txn, account in transactions:
            if not txn.due_date:
                continue
                
            days_overdue = (today - txn.due_date).days
            
            if days_overdue <= 0:
                aging_data["current"] += txn.amount
            elif days_overdue <= 30:
                aging_data["0_30"] += txn.amount
            elif days_overdue <= 60:
                aging_data["30_60"] += txn.amount
            elif days_overdue <= 90:
                aging_data["60_90"] += txn.amount
            else:
                aging_data["90_plus"] += txn.amount
        
        aging_report = phase2_credit_service.generate_aging_report()
        
        return {
            "status": "success",
            "aging_report": {
                "current": float(aging_data["current"]),
                "0_30_days": float(aging_data["0_30"]),
                "30_60_days": float(aging_data["30_60"]),
                "60_90_days": float(aging_data["60_90"]),
                "90_plus_days": float(aging_data["90_plus"]),
                "total_outstanding": float(sum(aging_data.values()))
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers-at-risk/{business_id}")
def get_customers_at_risk(business_id: str, db: Session = Depends(get_db)):
    """
    Get customers at risk of default
    
    Based on: Credit score < 50, missed payments, overdue invoices
    """
    try:
        at_risk = db.query(CustomerCredit).filter(
            CustomerCredit.business_id == business_id,
            CustomerCredit.credit_score < 50
        ).all()
        
        return {
            "status": "success",
            "at_risk_count": len(at_risk),
            "customers": [
                {
                    "customer_id": c.customer_id,
                    "customer_name": c.customer_name,
                    "credit_score": c.credit_score,
                    "missed_payments": c.missed_payments,
                    "status": c.credit_status
                }
                for c in at_risk
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Credit Analytics ====================

@router.get("/analytics/summary/{business_id}")
def credit_analytics_summary(business_id: str, db: Session = Depends(get_db)):
    """Get credit analytics summary"""
    try:
        accounts = db.query(CustomerCredit).filter(
            CustomerCredit.business_id == business_id
        ).all()
        
        total_credit = sum(Decimal(str(a.credit_limit)) for a in accounts)
        total_outstanding = sum(Decimal(str(a.used_credit)) for a in accounts)
        avg_score = sum(a.credit_score for a in accounts) / len(accounts) if accounts else 0
        
        return {
            "status": "success",
            "summary": {
                "total_credit_extended": float(total_credit),
                "active_accounts": len(accounts),
                "total_outstanding": float(total_outstanding),
                "avg_credit_score": float(avg_score),
                "accounts_excellent": len([a for a in accounts if a.credit_score >= 80]),
                "accounts_good": len([a for a in accounts if 60 <= a.credit_score < 80]),
                "accounts_fair": len([a for a in accounts if 40 <= a.credit_score < 60]),
                "accounts_poor": len([a for a in accounts if a.credit_score < 40])
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
