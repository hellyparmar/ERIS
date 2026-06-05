"""
Phase 2 Credit Management (Khata) REST API Router
Handles customer credit accounts, payment tracking, and credit decisions
Status: Advanced credit scoring, aging analysis, payment reminders
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.api.db.database import get_db
from app.api.db.phase2_models import (
    CustomerCredit, CreditTransaction, CreditReminder, Invoice
)
from app.api.services.phase2_credit_service import Phase2CreditService
from app.api.utils.jwt_auth import get_current_user

# Initialize router
router = APIRouter(prefix="/api/v1/credit", tags=["credit"])

# Initialize service
credit_service = Phase2CreditService()


# ============================================================================
# DATA MODELS (Pydantic schemas)
# ============================================================================

class CreateCreditAccountRequest:
    """Create new credit account"""
    customer_id: str
    customer_name: str
    initial_credit_limit: Decimal = Decimal("10000")
    business_id: str


class TransactionRequest:
    """Record credit transaction"""
    transaction_type: str  # DEBIT (sale), CREDIT (payment), ADJUSTMENT
    amount: Decimal
    reference_id: Optional[str]
    reference_type: Optional[str]
    due_date: Optional[datetime]
    notes: Optional[str]


class PaymentRequest:
    """Record payment"""
    amount: Decimal
    payment_reference: str
    payment_date: Optional[datetime]
    payment_method: Optional[str]


class AdjustmentRequest:
    """Make adjustment to credit"""
    adjustment_type: str  # CREDIT_LIMIT_INCREASE, PENALTY, REWARD, MANUAL_ADJUSTMENT
    amount: Decimal
    reason: str


class ReminderRequest:
    """Send payment reminder"""
    reminder_type: str  # SMS, EMAIL, WHATSAPP
    custom_message: Optional[str]


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

@router.post("/accounts/create")
async def create_credit_account(
    request: CreateCreditAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize credit account for customer
    
    Features:
    - Set initial credit limit
    - Initialize credit score (75)
    - Create transaction ledger
    
    Returns:
    - New credit account with initial limits
    """
    # Check if account exists
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == request.customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Credit account already exists for this customer"
        )
    
    try:
        # Create account record
        db_account = CustomerCredit(
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            business_id=current_user["business_id"],
            credit_limit=request.initial_credit_limit,
            current_balance=Decimal("0"),
            credit_score=75,  # Starting score
            credit_rating="GOOD",
            on_time_payments=0,
            late_payments=0,
            missed_payments=0,
            total_transactions=0,
            is_active=True,
            is_blocked=False
        )
        
        db.add(db_account)
        db.flush()
        
        # Create initial transaction ledger entry
        initial_transaction = CreditTransaction(
            customer_credit_id=db_account.id,
            transaction_type="CREDIT",
            amount=Decimal("0"),
            balance_after=Decimal("0"),
            reference_id=None,
            reference_type="ACCOUNT_INITIALIZATION",
            notes="Credit account initialized"
        )
        
        db.add(initial_transaction)
        db.commit()
        
        return {
            "success": True,
            "account_id": str(db_account.id),
            "customer_id": request.customer_id,
            "customer_name": request.customer_name,
            "credit_limit": float(request.initial_credit_limit),
            "current_balance": 0.0,
            "available_credit": float(request.initial_credit_limit),
            "credit_score": 75,
            "credit_rating": "GOOD",
            "message": "Credit account created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create credit account: {str(e)}"
        )


@router.get("/accounts/list")
async def list_credit_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    credit_rating: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all credit accounts for business
    
    Query Parameters:
    - credit_rating: EXCELLENT, GOOD, FAIR, POOR
    - is_blocked: Filter blocked accounts
    
    Returns:
    - List of credit accounts with summary
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.business_id == current_user["business_id"]
    )
    
    if credit_rating:
        query = query.filter(CustomerCredit.credit_rating == credit_rating)
    if is_blocked is not None:
        query = query.filter(CustomerCredit.is_blocked == is_blocked)
    
    total = query.count()
    accounts = query.order_by(CustomerCredit.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(accounts),
        "accounts": [
            {
                "account_id": str(acc.id),
                "customer_id": acc.customer_id,
                "customer_name": acc.customer_name,
                "credit_limit": float(acc.credit_limit),
                "current_balance": float(acc.current_balance),
                "available_credit": float(acc.credit_limit - acc.current_balance),
                "credit_score": acc.credit_score,
                "credit_rating": acc.credit_rating,
                "is_active": acc.is_active,
                "is_blocked": acc.is_blocked,
                "total_transactions": acc.total_transactions
            }
            for acc in accounts
        ]
    }


@router.get("/accounts/{customer_id}")
async def get_credit_account(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed credit account information
    
    Returns:
    - Account details, credit score factors, payment history
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    query = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    # Get recent transactions
    result = await db.execute(select(CreditTransaction).where(CreditTransaction.customer_credit_id == account.id
    ).order_by(CreditTransaction.created_at.desc()).limit(10))
    account = result.scalars().all()
    # Get outstanding invoices
    result = await db.execute(select(Invoice).where(Invoice.customer_id == customer_id,
        Invoice.payment_status != "PAID"))
    outstanding_invoices = result.scalars().all()
    return {
        "account": {
            "account_id": str(account.id),
            "customer_id": account.customer_id,
            "customer_name": account.customer_name,
            "credit_limit": float(account.credit_limit),
            "current_balance": float(account.current_balance),
            "available_credit": float(account.credit_limit - account.current_balance),
            "credit_score": account.credit_score,
            "credit_rating": account.credit_rating,
            "is_active": account.is_active,
            "is_blocked": account.is_blocked
        },
        "payment_metrics": {
            "on_time_payments": account.on_time_payments,
            "late_payments": account.late_payments,
            "missed_payments": account.missed_payments,
            "total_transactions": account.total_transactions,
            "on_time_payment_ratio": account.on_time_payments / max(account.total_transactions, 1),
            "payment_reliability": "HIGH" if (account.on_time_payments / max(account.total_transactions, 1)) > 0.8 else "MEDIUM" if (account.on_time_payments / max(account.total_transactions, 1)) > 0.6 else "LOW"
        },
        "recent_activity": [
            {
                "transaction_id": str(t.id),
                "transaction_type": t.transaction_type,
                "amount": float(t.amount),
                "balance_after": float(t.balance_after),
                "reference_type": t.reference_type,
                "created_at": t.created_at,
                "notes": t.notes
            }
            for t in recent_transactions
        ],
        "outstanding_invoices": {
            "count": len(outstanding_invoices),
            "total_outstanding": float(sum(inv.grand_total - sum(p.amount for p in inv.payments) for inv in outstanding_invoices)),
            "invoices": [
                {
                    "invoice_number": inv.invoice_number,
                    "amount": float(inv.grand_total),
                    "due_date": inv.due_date,
                    "payment_status": inv.payment_status
                }
                for inv in outstanding_invoices[:5]
            ]
        }
    }


# ============================================================================
# TRANSACTIONS
# ============================================================================

@router.post("/accounts/{customer_id}/transactions")
async def record_transaction(
    customer_id: str,
    request: TransactionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record credit transaction (DEBIT for sales, CREDIT for payments, ADJUSTMENT for manual)
    
    Parameters:
    - transaction_type: DEBIT, CREDIT, ADJUSTMENT
    - amount: Transaction amount
    - reference_id: Link to invoice or payment
    - due_date: Due date for credit transaction
    
    Returns:
    - Transaction recorded, updated balance and credit score
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    recent_transactions = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    if not account.is_active:
        raise HTTPException(status_code=400, detail="Credit account is inactive")
    
    if account.is_blocked:
        raise HTTPException(status_code=400, detail="Credit account is blocked")
    
    try:
        # Validate transaction type
        if request.transaction_type == "DEBIT":
            new_balance = account.current_balance + request.amount
            
            # Check credit limit
            if new_balance > account.credit_limit:
                raise HTTPException(
                    status_code=400,
                    detail=f"Credit limit exceeded. Limit: {account.credit_limit}, New balance would be: {new_balance}"
                )
        elif request.transaction_type == "CREDIT":
            new_balance = max(Decimal("0"), account.current_balance - request.amount)
        elif request.transaction_type == "ADJUSTMENT":
            new_balance = account.current_balance + request.amount
        else:
            raise HTTPException(status_code=400, detail="Invalid transaction type")
        
        # Record transaction
        db_transaction = CreditTransaction(
            customer_credit_id=account.id,
            transaction_type=request.transaction_type,
            amount=request.amount,
            balance_after=new_balance,
            reference_id=request.reference_id,
            reference_type=request.reference_type,
            due_date=request.due_date,
            notes=request.notes
        )
        
        db.add(db_transaction)
        
        # Update account balance
        account.current_balance = new_balance
        account.total_transactions += 1
        
        db.commit()
        
        return {
            "success": True,
            "transaction_id": str(db_transaction.id),
            "customer_id": customer_id,
            "transaction_type": request.transaction_type,
            "amount": float(request.amount),
            "previous_balance": float(account.current_balance - request.amount if request.transaction_type == "CREDIT" else account.current_balance - request.amount),
            "current_balance": float(new_balance),
            "credit_limit": float(account.credit_limit),
            "available_credit": float(account.credit_limit - new_balance),
            "message": "Transaction recorded successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record transaction: {str(e)}"
        )


@router.post("/accounts/{customer_id}/payments")
async def record_payment(
    customer_id: str,
    request: PaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record payment against credit account
    
    Parameters:
    - amount: Payment amount
    - payment_reference: Reference (check number, bank transfer ID, etc.)
    - payment_date: Date of payment
    
    Returns:
    - Payment recorded, updated balance, credit score adjustment
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    try:
        # Record payment
        credit_service.record_payment(
            customer_id=customer_id,
            amount=request.amount,
            payment_reference=request.payment_reference,
            payment_date=request.payment_date or datetime.now()
        )
        
        # Update balance
        new_balance = max(Decimal("0"), account.current_balance - request.amount)
        account.current_balance = new_balance
        
        # Check if payment was on time or late
        result = await db.execute(select(Invoice).where(Invoice.customer_id == customer_id,
            Invoice.due_date <= datetime.now()))
    account = result.scalars().all()
        if outstanding_invoices:
            account.late_payments += 1
        else:
            account.on_time_payments += 1
        
        # Recalculate credit score
        new_score = credit_service.calculate_credit_score(
            total_transactions=account.total_transactions,
            on_time_payments=account.on_time_payments,
            late_payments=account.late_payments,
            missed_payments=account.missed_payments,
            years_as_customer=((datetime.now() - account.created_at).days / 365),
            current_balance=new_balance,
            credit_limit=account.credit_limit
        )
        
        account.credit_score = new_score
        account.credit_rating = credit_service.get_status_from_score(new_score)
        account.last_payment_date = request.payment_date or datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "customer_id": customer_id,
            "payment_amount": float(request.amount),
            "previous_balance": float(account.current_balance + request.amount),
            "current_balance": float(new_balance),
            "available_credit": float(account.credit_limit - new_balance),
            "payment_reference": request.payment_reference,
            "credit_score": account.credit_score,
            "credit_rating": account.credit_rating,
            "message": "Payment recorded successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record payment: {str(e)}"
        )


@router.post("/accounts/{customer_id}/adjustments")
async def make_adjustment(
    customer_id: str,
    request: AdjustmentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Make manual adjustment to credit account
    
    Adjustment Types:
    - CREDIT_LIMIT_INCREASE: Increase credit limit
    - PENALTY: Apply penalty for late/missed payment
    - REWARD: Reward for consistent on-time payment
    - MANUAL_ADJUSTMENT: Manual balance adjustment
    
    Returns:
    - Adjustment applied, updated credit details
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
        outstanding_invoices = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    try:
        old_balance = account.current_balance
        old_credit_limit = account.credit_limit
        old_score = account.credit_score
        
        if request.adjustment_type == "CREDIT_LIMIT_INCREASE":
            account.credit_limit += request.amount
        elif request.adjustment_type == "PENALTY":
            account.current_balance += request.amount
            account.credit_score = max(0, account.credit_score - 10)
        elif request.adjustment_type == "REWARD":
            account.current_balance = max(Decimal("0"), account.current_balance - request.amount)
            account.credit_score = min(100, account.credit_score + 5)
        elif request.adjustment_type == "MANUAL_ADJUSTMENT":
            account.current_balance += request.amount
        else:
            raise HTTPException(status_code=400, detail="Invalid adjustment type")
        
        # Recalculate rating
        account.credit_rating = credit_service.get_status_from_score(account.credit_score)
        account.updated_at = datetime.now()
        
        # Record transaction
        db_transaction = CreditTransaction(
            customer_credit_id=account.id,
            transaction_type="ADJUSTMENT",
            amount=request.amount,
            balance_after=account.current_balance,
            reference_type=request.adjustment_type,
            notes=request.reason
        )
        
        db.add(db_transaction)
        db.commit()
        
        return {
            "success": True,
            "customer_id": customer_id,
            "adjustment_type": request.adjustment_type,
            "adjustment_amount": float(request.amount),
            "reason": request.reason,
            "previous_balance": float(old_balance),
            "current_balance": float(account.current_balance),
            "previous_credit_limit": float(old_credit_limit),
            "current_credit_limit": float(account.credit_limit),
            "previous_credit_score": old_score,
            "current_credit_score": account.credit_score,
            "credit_rating": account.credit_rating,
            "message": "Adjustment applied successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to make adjustment: {str(e)}"
        )


# ============================================================================
# CREDIT ANALYSIS & DECISIONS
# ============================================================================

@router.get("/accounts/{customer_id}/credit-score-analysis")
async def get_credit_score_analysis(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed credit score analysis with factors
    
    Returns:
    - Score breakdown, contributing factors, recommendations
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    # Calculate factors
    years_as_customer = (datetime.now() - account.created_at).days / 365
    on_time_ratio = account.on_time_payments / max(account.total_transactions, 1)
    credit_utilization = account.current_balance / account.credit_limit if account.credit_limit > 0 else 0
    
    return {
        "customer_id": customer_id,
        "credit_score": account.credit_score,
        "credit_rating": account.credit_rating,
        "score_breakdown": {
            "base_score": 75,
            "on_time_payment_factor": on_time_ratio * 20,
            "late_payment_penalty": -(account.late_payments * 3),
            "missed_payment_penalty": -(account.missed_payments * 10),
            "relationship_bonus": min(10, int(years_as_customer * 2)),
            "credit_utilization_bonus": 10 if credit_utilization < 0.5 else 5 if credit_utilization < 0.7 else 0,
            "current_total": account.credit_score
        },
        "factors": {
            "years_as_customer": round(years_as_customer, 2),
            "total_transactions": account.total_transactions,
            "on_time_payments": account.on_time_payments,
            "on_time_payment_ratio": round(on_time_ratio, 2),
            "late_payments": account.late_payments,
            "missed_payments": account.missed_payments,
            "current_balance": float(account.current_balance),
            "credit_limit": float(account.credit_limit),
            "credit_utilization": round(credit_utilization, 2)
        },
        "recommendations": [
            "Increase credit limit" if credit_utilization > 0.8 else None,
            "Monitor for late payments" if account.late_payments > 0 else None,
            "Reward for on-time payments" if on_time_ratio > 0.95 else None,
            "Consider account suspension" if account.missed_payments > 3 else None
        ]
    }


@router.get("/accounts/{customer_id}/can-extend-credit")
async def can_extend_credit(
    customer_id: str,
    amount: Decimal = Query(..., gt=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if credit can be extended to customer
    
    Query Parameters:
    - amount: Requested credit amount
    
    Returns:
    - Approval decision with reasons
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    can_extend = credit_service.can_extend_credit(
        customer_id=customer_id,
        requested_amount=amount,
        business_id=current_user["business_id"]
    )
    
    reasons = []
    if account.is_blocked:
        reasons.append("Account is blocked")
    if account.credit_score < 50:
        reasons.append("Credit score too low")
    if (account.current_balance + amount) > account.credit_limit:
        reasons.append("Would exceed credit limit")
    if account.missed_payments > 2:
        reasons.append("Multiple missed payments on record")
    
    return {
        "customer_id": customer_id,
        "can_extend": can_extend,
        "reasons": reasons if not can_extend else ["Account meets credit extension criteria"],
        "available_credit": float(account.credit_limit - account.current_balance),
        "requested_amount": float(amount),
        "would_exceed_limit": (account.current_balance + amount) > account.credit_limit,
        "credit_score": account.credit_score,
        "credit_rating": account.credit_rating,
        "recommendation": "APPROVE" if can_extend else "REJECT"
    }


# ============================================================================
# AGING ANALYSIS & REPORTING
# ============================================================================

@router.get("/accounts/{customer_id}/aging-report")
async def get_aging_report(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed aging report for customer
    
    Returns:
    - Invoices grouped by overdue days
    - Total outstanding, payment due
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    aging = credit_service.generate_aging_report(
        customer_id=customer_id,
        business_id=current_user["business_id"]
    )
    
    return {
        "customer_id": customer_id,
        "aging_report": aging,
        "total_outstanding": float(account.current_balance),
        "credit_limit": float(account.credit_limit),
        "available_credit": float(account.credit_limit - account.current_balance)
    }


@router.get("/business-credit-analysis")
async def get_business_credit_analysis(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get business-wide credit analysis
    
    Returns:
    - Total credit extended, collected, outstanding
    - Customer credit distribution
    - High-risk customers
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.business_id == current_user["business_id"]))
    account = result.scalars().all()
    total_credit_limit = sum(acc.credit_limit for acc in accounts)
    total_outstanding = sum(acc.current_balance for acc in accounts)
    total_available = total_credit_limit - total_outstanding
    
    # Group by rating
    rating_distribution = {}
    for acc in accounts:
        rating = acc.credit_rating
        if rating not in rating_distribution:
            rating_distribution[rating] = {"count": 0, "outstanding": Decimal("0")}
        rating_distribution[rating]["count"] += 1
        rating_distribution[rating]["outstanding"] += acc.current_balance
    
    # High-risk customers (score < 60 or blocked)
    high_risk = [acc for acc in accounts if acc.credit_score < 60 or acc.is_blocked]
    
    return {
        "summary": {
            "total_customers": len(accounts),
            "total_credit_limit": float(total_credit_limit),
            "total_outstanding": float(total_outstanding),
            "total_available_credit": float(total_available),
            "credit_utilization_ratio": float(total_outstanding / total_credit_limit) if total_credit_limit > 0 else 0
        },
        "rating_distribution": {
            rating: {
                "count": data["count"],
                "outstanding": float(data["outstanding"]),
                "percentage": (data["count"] / len(accounts) * 100) if accounts else 0
            }
            for rating, data in rating_distribution.items()
        },
        "high_risk_customers": [
            {
                "customer_id": acc.customer_id,
                "customer_name": acc.customer_name,
                "credit_score": acc.credit_score,
                "outstanding": float(acc.current_balance),
                "is_blocked": acc.is_blocked,
                "reason": "Low credit score" if acc.credit_score < 60 else "Account blocked"
            }
            for acc in high_risk
        ]
    }


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

@router.post("/accounts/{customer_id}/block")
async def block_account(
    customer_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Block credit account (prevent further credit)
    
    Parameters:
    - reason: Reason for blocking
    
    Returns:
    - Account blocked confirmation
    """
    account = db.query(CustomerCredit).filter(
        CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    accounts = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    account.is_blocked = True
    account.blocked_reason = reason
    account.blocked_at = datetime.now()
    account.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer_id,
        "is_blocked": True,
        "blocked_reason": reason,
        "blocked_at": datetime.now(),
        "message": "Account blocked successfully"
    }


@router.post("/accounts/{customer_id}/unblock")
async def unblock_account(
    customer_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unblock credit account
    
    Parameters:
    - reason: Reason for unblocking
    
    Returns:
    - Account unblocked confirmation
    """
    result = await db.execute(select(CustomerCredit).where(CustomerCredit.customer_id == customer_id,
        CustomerCredit.business_id == current_user["business_id"]))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Credit account not found")
    
    account.is_blocked = False
    account.blocked_reason = None
    account.blocked_at = None
    account.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer_id,
        "is_blocked": False,
        "unblocked_at": datetime.now(),
        "message": "Account unblocked successfully"
    }
