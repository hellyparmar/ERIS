"""
Direct Data Router - Returns data directly from the database
Bypasses ORM to work with the current schema
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.db import get_db

router = APIRouter(prefix="/api/v1", tags=["Direct Data"])


@router.get("/customers")
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get customers directly from database"""
    try:
        # Raw SQL query matching the current database schema
        query = text("""
            SELECT id, name, email, phone, rfm_segment, customer_type, 
                   total_spent, last_purchase, registration_date
            FROM customers
            LIMIT :limit OFFSET :skip
        """)
        
        results = db.execute(query, {"limit": limit, "skip": skip}).fetchall()
        
        # Count query
        count_query = text("SELECT COUNT(*) FROM customers")
        total = db.execute(count_query).scalar()
        
        customers = [
            {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "segment": row[4],
                "customer_type": row[5],
                "total_spent": float(row[6]) if row[6] else 0,
                "last_purchase": str(row[7]) if row[7] else None,
                "registration_date": str(row[8]) if row[8] else None,
            }
            for row in results
        ]
        
        return {
            "data": customers,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/dashboard-summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary metrics"""
    try:
        # Total customers
        total_customers = db.execute(
            text("SELECT COUNT(*) FROM customers")
        ).scalar()
        
        # VIP customers (using rfm_segment instead of segment)
        vip_customers = db.execute(
            text("SELECT COUNT(*) FROM customers WHERE rfm_segment = 'VIP'")
        ).scalar()
        
        # Total LTV
        total_ltv = db.execute(
            text("SELECT COALESCE(SUM(total_spent), 0) FROM customers")
        ).scalar()
        
        # Avg LTV
        avg_ltv = db.execute(
            text("SELECT COALESCE(AVG(total_spent), 0) FROM customers")
        ).scalar()
        
        # Revenue at risk (at risk segment)
        revenue_at_risk = db.execute(
            text("SELECT COALESCE(SUM(total_spent), 0) FROM customers WHERE rfm_segment = 'At Risk'")
        ).scalar()
        
        # Retention (champions + loyal)
        retention_count = db.execute(
            text("SELECT COUNT(*) FROM customers WHERE rfm_segment IN ('Champions', 'Loyal')")
        ).scalar()
        retention_pct = (retention_count / total_customers * 100) if total_customers > 0 else 0
        
        return {
            "total_customers": total_customers,
            "vip_customers": vip_customers,
            "total_ltv": float(total_ltv),
            "avg_ltv": float(avg_ltv),
            "revenue_at_risk": float(revenue_at_risk),
            "retention_pct": round(retention_pct, 1)
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/transactions")
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get transactions from database"""
    try:
        query = text("""
            SELECT id, customer_id, amount, transaction_date, payment_method
            FROM transactions
            LIMIT :limit OFFSET :skip
        """)
        
        results = db.execute(query, {"limit": limit, "skip": skip}).fetchall()
        
        count_query = text("SELECT COUNT(*) FROM transactions")
        total = db.execute(count_query).scalar()
        
        transactions = [
            {
                "id": row[0],
                "customer_id": row[1],
                "amount": float(row[2]),
                "date": str(row[3]) if row[3] else None,
                "payment_method": row[4],
            }
            for row in results
        ]
        
        return {
            "data": transactions,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/products")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products from database"""
    try:
        query = text("""
            SELECT id, name, category, price, stock_quantity
            FROM products
            LIMIT :limit OFFSET :skip
        """)
        
        results = db.execute(query, {"limit": limit, "skip": skip}).fetchall()
        
        count_query = text("SELECT COUNT(*) FROM products")
        total = db.execute(count_query).scalar()
        
        products = [
            {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "price": float(row[3]),
                "stock": int(row[4]) if row[4] else 0,
            }
            for row in results
        ]
        
        return {
            "data": products,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        return {"error": str(e), "data": []}
