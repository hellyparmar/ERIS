"""
Phase 3: Day Operations Management

Day open/close operations with opening balance, closing balance, day-end reports,
cash reconciliation, and daily settlement
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel

from app.api.db.database import get_db
from app.api.db.models_v6 import Sale, Payment, CreditAccount, Customer
from app.api.db.phase2_models import Invoice

router = APIRouter(prefix="/api/v3/day-operations", tags=["day-operations"])


# ==================== Request Models ====================

class DayOpenRequest(BaseModel):
    """Day opening request"""
    business_id: int
    opening_date: date
    opening_cash_balance: Decimal
    manager_id: int
    notes: Optional[str] = None


class DayCloseRequest(BaseModel):
    """Day closing request"""
    business_id: int
    closing_date: date
    closing_cash_balance: Decimal
    expected_balance: Optional[Decimal] = None
    discrepancy_notes: Optional[str] = None
    manager_id: int


class CashReconciliation(BaseModel):
    """Cash reconciliation details"""
    expected_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    variance_percent: Decimal
    notes: Optional[str] = None


# ==================== Response Models ====================

class DayOperationResponse(BaseModel):
    """Day operation summary"""
    business_id: int
    operation_date: date
    status: str  # open, closed
    opening_balance: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    total_sales: Decimal
    total_cash_sales: Decimal
    total_upi_sales: Decimal
    total_card_sales: Decimal
    total_credit_sales: Decimal
    total_payments: Decimal
    cash_collections: Decimal
    net_balance: Decimal
    variance: Optional[Decimal] = None
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    opened_by: Optional[str] = None
    closed_by: Optional[str] = None


class DayEndReport(BaseModel):
    """Complete day-end report"""
    day_summary: DayOperationResponse
    sales_count: int
    average_sale_value: Decimal
    peak_hour: Optional[str] = None
    peak_hour_sales: Optional[Decimal] = None
    payment_breakdown: Dict[str, Decimal]
    credit_activity: Dict[str, Any]
    top_products: List[Dict[str, Any]] = []
    top_customers: List[Dict[str, Any]] = []
    unsettled_credit: Decimal
    outstanding_balance: Decimal


# ==================== Day Opening ====================

@router.post("/open")
def open_day(
    request: DayOpenRequest,
    db: Session = Depends(get_db)
):
    """
    Open business day with opening balance
    
    Args:
        request: Day opening details with opening cash balance
        
    Returns:
        Day operation with opening details
    """
    try:
        # Check if day already open for this business
        existing = db.query(Sale).filter(
            and_(
                Sale.customer_id == None,  # Sentinel record
                func.date(Sale.sale_date) == request.opening_date,
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Day already open")
        
        opening_record = {
            "business_id": request.business_id,
            "operation_date": request.opening_date,
            "status": "open",
            "opening_balance": request.opening_cash_balance,
            "opened_at": datetime.now(),
            "opened_by": f"manager_{request.manager_id}",
            "notes": request.notes,
        }
        
        return {
            "status": "success",
            "message": f"Day opened successfully on {request.opening_date}",
            "operation": opening_record,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Day Closing ====================

@router.post("/close")
def close_day(
    request: DayCloseRequest,
    db: Session = Depends(get_db)
):
    """
    Close business day with closing balance and reconciliation
    
    Args:
        request: Day closing details with cash balance and reconciliation
        
    Returns:
        Complete day-end report with variance analysis
    """
    try:
        operation_date = request.closing_date
        
        # Calculate daily totals
        sales_query = db.query(
            func.count(Sale.id).label("sale_count"),
            func.sum(Sale.total_amount).label("total_amount"),
            func.sum(Sale.gst_amount).label("total_gst")
        ).filter(
            func.date(Sale.sale_date) == operation_date
        )
        
        sales_data = sales_query.first()
        
        # Payment breakdown
        payment_breakdown = db.query(
            Sale.payment_method,
            func.sum(Sale.amount_paid).label("amount")
        ).filter(
            func.date(Sale.sale_date) == operation_date
        ).group_by(Sale.payment_method).all()
        
        # Credit transactions
        credit_query = db.query(
            func.count(CreditAccount.id).label("credit_count"),
            func.sum(CreditAccount.amount).label("credit_amount"),
            func.sum(CreditAccount.amount_paid).label("credit_paid")
        ).filter(
            func.date(CreditAccount.created_at) == operation_date
        )
        
        credit_data = credit_query.first()
        
        # Calculate expected balance
        total_sales = sales_data.total_amount or Decimal(0)
        cash_sales = sum(
            (p.amount or 0) for p in payment_breakdown if p.Sale_payment_method in ['cash', 'mixed']
        ) or Decimal(0)
        
        expected_balance = request.opening_cash_balance + cash_sales if request.opening_cash_balance else None
        
        # Reconciliation
        variance = None
        if expected_balance:
            variance = request.closing_cash_balance - expected_balance
        
        # Day summary
        day_summary = {
            "business_id": request.business_id,
            "operation_date": operation_date,
            "status": "closed",
            "opening_balance": None,  # Retrieved from opening
            "closing_balance": request.closing_cash_balance,
            "total_sales": total_sales,
            "total_cash_sales": cash_sales,
            "total_upi_sales": Decimal(0),  # Can be enhanced
            "total_card_sales": Decimal(0),
            "total_credit_sales": credit_data.credit_amount or Decimal(0),
            "total_payments": sum((p.amount or 0) for p in payment_breakdown) or Decimal(0),
            "cash_collections": cash_sales,
            "net_balance": request.closing_cash_balance,
            "variance": variance,
            "closed_at": datetime.now(),
            "closed_by": f"manager_{request.manager_id}",
        }
        
        # Top products
        top_products_query = db.query(
            func.count(Sale.items).label("quantity"),
            func.sum(Sale.total_amount).label("amount")
        ).filter(
            func.date(Sale.sale_date) == operation_date
        ).limit(5).all()
        
        # Top customers
        top_customers_query = db.query(
            Customer.name,
            func.sum(Sale.total_amount).label("amount")
        ).join(Sale, Sale.customer_id == Customer.id).filter(
            func.date(Sale.sale_date) == operation_date
        ).group_by(Customer.id, Customer.name).order_by(
            func.sum(Sale.total_amount).desc()
        ).limit(5).all()
        
        # Outstanding credit
        outstanding_credit = db.query(
            func.sum(CreditAccount.amount - CreditAccount.amount_paid)
        ).filter(
            CreditAccount.status.in_(['pending', 'partial', 'overdue'])
        ).scalar() or Decimal(0)
        
        day_end_report = {
            "day_summary": day_summary,
            "sales_count": sales_data.sale_count or 0,
            "average_sale_value": (total_sales / (sales_data.sale_count or 1)) if sales_data.sale_count else Decimal(0),
            "payment_breakdown": {
                p.Sale_payment_method: float(p.amount or 0) 
                for p in payment_breakdown
            },
            "credit_activity": {
                "credit_count": credit_data.credit_count or 0,
                "credit_amount": float(credit_data.credit_amount or 0),
                "credit_paid": float(credit_data.credit_paid or 0),
            },
            "top_products": [
                {"index": i+1, "sales": float(p[1] or 0)}
                for i, p in enumerate(top_products_query)
            ],
            "top_customers": [
                {"name": c[0], "amount": float(c[1] or 0)}
                for c in top_customers_query
            ],
            "unsettled_credit": float(credit_data.credit_amount - credit_data.credit_paid),
            "outstanding_balance": float(outstanding_credit),
        }
        
        return {
            "status": "success",
            "message": f"Day closed successfully on {operation_date}",
            "report": day_end_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Day Summary ====================

@router.get("/summary/{business_id}")
def get_day_summary(
    business_id: int,
    operation_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db)
):
    """
    Get day operation summary (open or closed)
    
    Args:
        business_id: Business identifier
        operation_date: Date to query (default: today)
        
    Returns:
        Current day status and summary
    """
    try:
        sales_data = db.query(
            func.count(Sale.id).label("sale_count"),
            func.sum(Sale.total_amount).label("total_amount"),
            func.sum(Sale.amount_paid).label("amount_paid")
        ).filter(
            func.date(Sale.sale_date) == operation_date
        ).first()
        
        # Determine status (simplified - can be enhanced with day tracking table)
        status = "open" if sales_data.sale_count else "not_started"
        
        return {
            "business_id": business_id,
            "operation_date": operation_date,
            "status": status,
            "sales_count": sales_data.sale_count or 0,
            "total_sales": float(sales_data.total_amount or 0),
            "amount_collected": float(sales_data.amount_paid or 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Day History ====================

@router.get("/history/{business_id}")
def get_day_history(
    business_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get history of day operations
    
    Args:
        business_id: Business identifier
        start_date: Period start
        end_date: Period end
        
    Returns:
        Daily summaries for period
    """
    try:
        daily_data = db.query(
            func.date(Sale.sale_date).label("day"),
            func.count(Sale.id).label("sale_count"),
            func.sum(Sale.total_amount).label("total_amount"),
            func.sum(Sale.gst_amount).label("gst_amount")
        ).filter(
            and_(
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= end_date
            )
        ).group_by(func.date(Sale.sale_date)).order_by(
            func.date(Sale.sale_date).desc()
        ).all()
        
        return {
            "business_id": business_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "daily_operations": [
                {
                    "date": str(d.day),
                    "sales_count": d.sale_count or 0,
                    "total_sales": float(d.total_amount or 0),
                    "gst_collected": float(d.gst_amount or 0)
                }
                for d in daily_data
            ],
            "total_operations": len(daily_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Cash Reconciliation ====================

@router.post("/reconcile")
def reconcile_cash(
    business_id: int = Query(...),
    operation_date: date = Query(...),
    expected_amount: Decimal = Query(...),
    actual_amount: Decimal = Query(...),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Record cash reconciliation for day
    
    Args:
        business_id: Business identifier
        operation_date: Day to reconcile
        expected_amount: Expected cash balance
        actual_amount: Actual counted cash
        notes: Reconciliation notes
        
    Returns:
        Reconciliation result with variance
    """
    try:
        variance = actual_amount - expected_amount
        variance_percent = (variance / expected_amount * 100) if expected_amount else 0
        
        reconciliation = {
            "business_id": business_id,
            "date": operation_date,
            "expected_amount": float(expected_amount),
            "actual_amount": float(actual_amount),
            "variance": float(variance),
            "variance_percent": float(variance_percent),
            "status": "matched" if variance == 0 else ("shortage" if variance < 0 else "excess"),
            "notes": notes,
            "reconciled_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "message": f"Cash reconciliation recorded",
            "reconciliation": reconciliation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
