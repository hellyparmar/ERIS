"""
Khata Service — Business Logic for Credit Tracking
Handles credit ledger operations, balance validation, and payment recording
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def get_or_create_credit_account(db: Session, customer_id: int) -> Dict[str, Any]:
    """
    Get existing credit account or create one for a customer.
    Returns dict with credit account data.
    """
    result = db.execute(text("""
        SELECT id, customer_id, credit_limit, current_balance,
               last_payment_date, credit_score, notes
        FROM customer_credits
        WHERE customer_id = :cid
        LIMIT 1
    """), {"cid": customer_id}).fetchone()

    if result:
        return {
            "id": result[0],
            "customer_id": result[1],
            "credit_limit": float(result[2] or 0),
            "current_balance": float(result[3] or 0),
            "last_payment_date": result[4],
            "credit_score": result[5],
            "notes": result[6],
        }

    # Create new credit account
    db.execute(text("""
        INSERT INTO customer_credits (customer_id, credit_limit, current_balance, created_at, updated_at)
        VALUES (:cid, 10000.0, 0.0, NOW(), NOW())
    """), {"cid": customer_id})
    db.commit()

    return {
        "id": None,
        "customer_id": customer_id,
        "credit_limit": 10000.0,
        "current_balance": 0.0,
        "last_payment_date": None,
        "credit_score": None,
        "notes": None,
    }


def record_credit_sale(
    db: Session,
    customer_id: int,
    amount: float,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add an amount to the customer's outstanding balance.
    Validates credit limit before adding.
    Returns updated balance info.
    """
    account = get_or_create_credit_account(db, customer_id)
    current = account["credit_limit"]
    balance = account["current_balance"]

    # Validate credit limit
    if current > 0 and (balance + amount) > current:
        raise ValueError(
            f"Credit limit exceeded. Limit: ₹{current}, Current balance: ₹{balance}, "
            f"Requested: ₹{amount}"
        )

    new_balance = balance + amount

    db.execute(text("""
        UPDATE customer_credits
        SET current_balance = :new_balance,
            notes = COALESCE(:notes, notes),
            updated_at = NOW()
        WHERE customer_id = :cid
    """), {"new_balance": new_balance, "cid": customer_id, "notes": notes})
    db.commit()

    logger.info(f"Credit sale recorded: customer={customer_id}, amount={amount}, new_balance={new_balance}")
    return {
        "customer_id": customer_id,
        "amount_added": amount,
        "previous_balance": balance,
        "new_balance": new_balance,
        "credit_limit": current,
        "available_credit": max(0, current - new_balance),
    }


def record_payment(
    db: Session,
    customer_id: int,
    amount: float,
    payment_method: str = "cash",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a payment against outstanding Khata balance.
    Returns updated balance and settlement status.
    """
    account = get_or_create_credit_account(db, customer_id)
    balance = account["current_balance"]

    if balance <= 0:
        raise ValueError("No outstanding balance for this customer")
    if amount > balance:
        raise ValueError(f"Payment ₹{amount} exceeds balance ₹{balance}")

    new_balance = balance - amount

    db.execute(text("""
        UPDATE customer_credits
        SET current_balance = :new_balance,
            last_payment_date = NOW(),
            updated_at = NOW()
        WHERE customer_id = :cid
    """), {"new_balance": new_balance, "cid": customer_id})
    db.commit()

    logger.info(f"Payment recorded: customer={customer_id}, amount={amount}, remaining={new_balance}")
    return {
        "customer_id": customer_id,
        "amount_paid": amount,
        "previous_balance": balance,
        "remaining_balance": new_balance,
        "fully_settled": new_balance <= 0,
        "payment_method": payment_method,
    }


def get_khata_summary(db: Session) -> Dict[str, Any]:
    """Get aggregate summary of all Khata accounts"""
    result = db.execute(text("""
        SELECT
            COUNT(*) as total_accounts,
            COALESCE(SUM(current_balance), 0) as total_outstanding,
            COUNT(CASE WHEN current_balance > 0 THEN 1 END) as accounts_with_balance,
            COALESCE(AVG(CASE WHEN current_balance > 0 THEN current_balance END), 0) as avg_balance
        FROM customer_credits
    """)).fetchone()

    return {
        "total_accounts": int(result[0] or 0),
        "total_outstanding": float(result[1] or 0),
        "accounts_with_balance": int(result[2] or 0),
        "avg_balance": round(float(result[3] or 0), 2),
    }


def get_overdue_accounts(db: Session) -> List[Dict[str, Any]]:
    """Get all customers with outstanding balance"""
    results = db.execute(text("""
        SELECT
            cc.customer_id,
            c.name,
            c.phone,
            cc.current_balance,
            cc.credit_limit,
            cc.last_payment_date
        FROM customer_credits cc
        JOIN customers c ON c.id = cc.customer_id
        WHERE cc.current_balance > 0
        ORDER BY cc.current_balance DESC
    """)).fetchall()

    return [
        {
            "customer_id": r[0],
            "customer_name": r[1],
            "customer_phone": r[2] or "",
            "outstanding_balance": float(r[3] or 0),
            "credit_limit": float(r[4] or 0),
            "last_payment_date": r[5],
        }
        for r in results
    ]


def list_credit_accounts(
    db: Session,
    search: Optional[str] = None,
    has_balance: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """List all credit accounts with optional filters"""
    where_clauses = []
    params: Dict[str, Any] = {"offset": (page - 1) * per_page, "limit": per_page}

    if search:
        where_clauses.append("c.name ILIKE :search")
        params["search"] = f"%{search}%"
    if has_balance is True:
        where_clauses.append("cc.current_balance > 0")
    elif has_balance is False:
        where_clauses.append("cc.current_balance <= 0")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total_result = db.execute(text(f"""
        SELECT COUNT(*) FROM customer_credits cc
        JOIN customers c ON c.id = cc.customer_id
        {where_sql}
    """), params).scalar()

    rows = db.execute(text(f"""
        SELECT cc.id, cc.customer_id, c.name, c.phone,
               cc.credit_limit, cc.current_balance, cc.last_payment_date, cc.credit_score
        FROM customer_credits cc
        JOIN customers c ON c.id = cc.customer_id
        {where_sql}
        ORDER BY cc.current_balance DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    accounts = [
        {
            "id": r[0],
            "customer_id": r[1],
            "customer_name": r[2],
            "customer_phone": r[3] or "",
            "credit_limit": float(r[4] or 0),
            "current_balance": float(r[5] or 0),
            "last_payment_date": r[6],
            "credit_score": r[7],
            "is_overdue": float(r[5] or 0) > 0,
        }
        for r in rows
    ]

    return {
        "data": accounts,
        "total": int(total_result or 0),
        "page": page,
        "per_page": per_page,
    }
