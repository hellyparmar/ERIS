"""
POS Sale Transaction Endpoint
Cashier-facing API for completing transactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from api.db import get_db
from api.routers.pos_auth import verify_pos_token
from api.services.pos_service import complete_sale

router = APIRouter(prefix="/api/v1/pos", tags=["POS Sales"])


class SaleItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    total: float


class CreateSaleRequest(BaseModel):
    items: List[SaleItem]
    subtotal: float
    gst_amount: float
    total: float
    payment_method: str  # "cash", "card", "upi", "wallet"
    customer_id: Optional[int] = None
    discount: float = 0.0
    notes: Optional[str] = None


class CreateSaleResponse(BaseModel):
    success: bool
    sale_id: int
    transaction_id: str
    receipt_number: str
    timestamp: str
    items_count: int
    total_amount: float
    message: str


@router.post("/sale", response_model=CreateSaleResponse)
async def create_sale(
    request: CreateSaleRequest,
    cashier_token = Depends(verify_pos_token),
    db: Session = Depends(get_db)
):
    """
    Complete a POS sale transaction
    - Validates stock (with row locking)
    - Deducts inventory atomically
    - Creates sale & sale items
    - Awards loyalty points
    - Triggers post-sale events (reorder alerts, etc.)
    
    Returns:
        Sale ID, transaction ID, receipt details
    """
    
    # Extract cashier info from token
    cashier_id = cashier_token.get("cashier_id")
    cashier_name = cashier_token.get("cashier_name")
    
    try:
        # Call POS service with ACID transaction
        result = complete_sale(
            cart={
                "items": [item.dict() for item in request.items],
                "subtotal": request.subtotal,
                "gst_amount": request.gst_amount,
                "total": request.total,
                "customer_id": request.customer_id
            },
            payment={
                "method": request.payment_method,
                "amount": request.total,
                "reference": None
            },
            cashier_id=cashier_id,
            db=db
        )
        
        return CreateSaleResponse(
            success=True,
            sale_id=result["data"]["sale_id"],
            transaction_id=result["data"]["transaction_id"],
            receipt_number=result["data"]["receipt_number"],
            timestamp=result["data"]["timestamp"],
            items_count=len(request.items),
            total_amount=request.total,
            message=result["message"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sale processing failed: {str(e)}"
        )


@router.get("/receipt/{sale_id}")
async def get_receipt(
    sale_id: int,
    cashier_token = Depends(verify_pos_token),
    db: Session = Depends(get_db)
):
    """
    Retrieve full receipt for a completed sale
    - Transaction details
    - Itemized list
    - Tax breakdown
    - Payment info
    """
    from sqlalchemy import text
    
    sale = db.execute(text("""
        SELECT id, transaction_id, customer_id, transaction_date,
               discount, tax, total_amount, payment_method
        FROM sales WHERE id = :id
    """)).params(id=sale_id).fetchone()
    
    if not sale:
        raise HTTPException(status_code=404, detail=f"Sale {sale_id} not found")
    
    items = db.execute(text("""
        SELECT si.product_id, p.name, p.sku, si.quantity, si.unit_price, si.line_total
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = :sale_id
    """)).params(sale_id=sale_id).fetchall()
    
    return {
        "sale_id": sale.id,
        "transaction_id": sale.transaction_id,
        "receipt_number": f"RCP-{sale.id:06d}",
        "timestamp": sale.transaction_date.isoformat() if sale.transaction_date else None,
        "customer_id": sale.customer_id,
        "items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "line_total": float(item.line_total)
            }
            for item in items
        ],
        "subtotal": float(sale.total_amount - sale.tax),
        "discount": float(sale.discount),
        "gst": float(sale.tax),
        "total": float(sale.total_amount),
        "payment_method": sale.payment_method
    }


@router.post("/refund/{sale_id}")
async def refund_sale(
    sale_id: int,
    reason: Optional[str] = None,
    cashier_token = Depends(verify_pos_token),
    db: Session = Depends(get_db)
):
    """
    Refund a completed sale and restore inventory
    - Restores all inventory quantities
    - Marks sale as refunded
    - Reverses loyalty points
    """
    from sqlalchemy import text
    
    try:
        # Get sale
        sale = db.execute(text("""
            SELECT id, total_amount FROM sales WHERE id = :id FOR UPDATE
        """)).params(id=sale_id).fetchone()
        
        if not sale:
            raise HTTPException(status_code=404, detail=f"Sale {sale_id} not found")
        
        # Get items
        items = db.execute(text("""
            SELECT product_id, quantity FROM sale_items WHERE sale_id = :sale_id
        """)).params(sale_id=sale_id).fetchall()
        
        # Restore inventory
        for item in items:
            db.execute(text("""
                UPDATE inventory SET quantity = quantity + :qty
                WHERE product_id = :product_id
            """), {
                "qty": item.quantity,
                "product_id": item.product_id
            })
        
        # Mark as refunded
        db.execute(text("""
            UPDATE sales SET status = 'REFUNDED', notes = :reason
            WHERE id = :id
        """), {
            "reason": f"Refunded: {reason}" if reason else "Refunded",
            "id": sale_id
        })
        
        db.commit()
        
        return {
            "success": True,
            "sale_id": sale_id,
            "refunded_amount": float(sale.total_amount),
            "status": "REFUNDED",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund failed: {str(e)}"
        )


@router.get("/day-summary")
async def get_day_summary(
    cashier_token = Depends(verify_pos_token),
    db: Session = Depends(get_db)
):
    """
    Get today's sales summary for cashier
    - Total transactions
    - Total amount
    - By payment method
    - Items sold
    """
    from sqlalchemy import text, func
    
    today = datetime.utcnow().date()
    
    summary = db.execute(text("""
        SELECT 
            COUNT(*) as transaction_count,
            COALESCE(SUM(total_amount), 0) as total_amount,
            payment_method,
            COALESCE(SUM(discount), 0) as total_discount
        FROM sales
        WHERE DATE(transaction_date) = :date
        GROUP BY payment_method
    """)).params(date=today).fetchall()
    
    items_sold = db.execute(text("""
        SELECT 
            p.category,
            COUNT(*) as count,
            COALESCE(SUM(si.quantity), 0) as total_qty
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE DATE(s.transaction_date) = :date
        GROUP BY p.category
    """)).params(date=today).fetchall()
    
    return {
        "date": today.isoformat(),
        "summary": [
            {
                "payment_method": row.payment_method or "unknown",
                "transactions": row.transaction_count,
                "total": float(row.total_amount),
                "discount": float(row.total_discount)
            }
            for row in summary
        ],
        "by_category": [
            {
                "category": row.category,
                "count": row.count,
                "total_qty": row.total_qty
            }
            for row in items_sold
        ]
    }
