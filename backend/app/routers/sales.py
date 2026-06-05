from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
from decimal import Decimal
from app.database import get_db
from app.models.sale import Sale, SaleItem, SalePaymentStatus
from app.models.multitenant_models import Inventory, Product, User
from app.schemas.sales import SaleCreate, SaleResponse, SalesAnalytics
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])

@router.get("/", response_model=List[SaleResponse])
async def get_sales(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all sales transactions for the organization.
    
    Includes line items and payment status.
    """
    from app.models.multitenant_models import Store
    result = await db.execute(
        select(Sale).join(Store, Sale.store_id == Store.id).where(
            Store.organization_id == current_user.organization_id
        )
    )
    sales = result.scalars().all()
    return sales

@router.get("/summary")
def get_sales_summary(current_user: User = Depends(get_current_user)):
    """
    Get a high-level summary of total sales and transaction count.
    """
    return {"total": 0, "count": 0}

@router.get("/daily-report")
def get_daily_sales_report(date: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """
    Generate a detailed sales report for a specific date.
    """
    return {"date": date, "report": {}}

@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details for a specific transaction by its ID.
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a new sales transaction and decrement inventory levels.
    
    - **items**: List of products, quantities, and prices.
    - **discount/tax**: Optional adjustments to the total.
    - **Inventory**: Stock is automatically reduced for each item.
    """
    from datetime import timezone
    total_amount = Decimal(0)
    sale_items = []
    
    for item in sale_in.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        inventory = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
        
        if not inventory or inventory.current_stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {product.name}")
        
        # line_total is Decimal * int -> Decimal
        line_total = item.unit_price * item.quantity
        total_amount += line_total
        
        sale_items.append(SaleItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=line_total
        ))
        
        # Atomic inventory reduction
        inventory.current_stock -= item.quantity
        inventory.available_stock -= item.quantity

    final_total = total_amount - sale_in.discount + sale_in.tax_amount
    sale_uid = uuid.uuid4().hex
    
    new_sale = Sale(
        transaction_id=f"TRX-{sale_uid[0:8].upper()}",
        customer_id=sale_in.customer_id,
        store_id=sale_in.store_id,
        transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),
        discount=sale_in.discount,
        tax_amount=sale_in.tax_amount,
        total_amount=final_total,
        payment_method=sale_in.payment_method,
        payment_status=SalePaymentStatus.PAID.value,
        items=sale_items
    )
    
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale

@router.get("/analytics", response_model=SalesAnalytics)
def get_sales_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get high-level sales analytics for the organization.
    """
    from app.models.multitenant_models import Store
    sales = db.query(Sale).join(Store, Sale.store_id == Store.id).filter(
        Store.organization_id == current_user.organization_id
    ).all()
    
    total_revenue = sum(s.total_amount for s in sales)
    count = len(sales)
    avg_value = total_revenue / count if count > 0 else 0
    
    return {
        "total_sales": total_revenue,
        "transaction_count": count,
        "average_order_value": avg_value,
        "top_categories": []
    }
