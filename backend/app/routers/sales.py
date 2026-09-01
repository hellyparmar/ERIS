"""
Sales API Router
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select

from app.models.models_v6 import Sale, SaleItem
from app.models.sale import SalePaymentStatus
from app.schemas.sales import SaleCreate, SaleResponse
from app.models.inventory import Inventory
import uuid
from decimal import Decimal

import csv
import io

from app.database import get_db
from app.models.users import User
from app.models.outlet import Outlet
from app.models.sales import SaleTransaction
from app.models.models_v6 import Product
from app.api.deps import get_current_active_user
from app.core.data_isolation import OutletDataAccess, require_outlet_access

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/")
async def list_sales(
    outlet_id: Optional[int] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get paginated sales transactions with filtering.
    Date format: YYYY-MM-DD
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    if outlet_id:
        if not require_outlet_access(current_user, outlet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    # Build statement
    stmt = select(
        SaleTransaction.id,
        SaleTransaction.outlet_id,
        SaleTransaction.product_id,
        SaleTransaction.quantity,
        SaleTransaction.unit_price,
        SaleTransaction.total_amount,
        SaleTransaction.payment_method,
        SaleTransaction.transaction_at,
        Product.name,
        Product.category,
        Outlet.name.label("outlet_name")
    ).join(Product, SaleTransaction.product_id == Product.id).join(
        Outlet, SaleTransaction.outlet_id == Outlet.id
    ).where(SaleTransaction.outlet_id.in_(outlets_filter))

    # Apply filters
    if product_id:
        stmt = stmt.where(SaleTransaction.product_id == product_id)
    if category:
        stmt = stmt.where(Product.category == category)
    if payment_method:
        stmt = stmt.where(SaleTransaction.payment_method == payment_method)
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            stmt = stmt.where(func.date(SaleTransaction.transaction_at) >= from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            stmt = stmt.where(func.date(SaleTransaction.transaction_at) <= to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")

    # Get total count via a subquery
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar() or 0

    # Paginate and order
    offset = (page - 1) * per_page
    items_result = await db.execute(
        stmt.order_by(desc(SaleTransaction.transaction_at)).offset(offset).limit(per_page)
    )
    items = items_result.all()

    sales_list = [
        {
            "id": row[0],
            "outlet_id": row[1],
            "product_id": row[2],
            "quantity": row[3],
            "unit_price": float(row[4]),
            "total_amount": float(row[5]),
            "payment_method": row[6],
            "transaction_at": row[7],
            "product_name": row[8],
            "category": row[9],
            "outlet_name": row[10]
        }
        for row in items
    ]

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "items": sales_list
    }


@router.get("/summary")
async def get_sales_summary(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    outlet_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get sales summary with comparison to previous period.
    Period: daily, weekly, monthly
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    if outlet_id:
        if not require_outlet_access(current_user, outlet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    today = datetime.now().date()

    if period == "daily":
        current_start = today
        current_end = today
        previous_start = today - timedelta(days=1)
        previous_end = today - timedelta(days=1)
    elif period == "weekly":
        current_start = today - timedelta(days=today.weekday())
        current_end = today
        week_start = current_start - timedelta(days=7)
        previous_start = week_start
        previous_end = previous_start + timedelta(days=6)
    else:  # monthly
        current_start = today.replace(day=1)
        current_end = today
        prev_month_end = current_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        previous_start = prev_month_start
        previous_end = prev_month_end

    # Current period
    cur_row = await db.execute(
        select(
            func.sum(SaleTransaction.total_amount).label("revenue"),
            func.count(SaleTransaction.id).label("transactions"),
            func.avg(SaleTransaction.total_amount).label("avg_transaction")
        ).where(
            SaleTransaction.outlet_id.in_(outlets_filter),
            func.date(SaleTransaction.transaction_at) >= current_start,
            func.date(SaleTransaction.transaction_at) <= current_end
        )
    )
    current_result = cur_row.first()

    # Previous period
    prev_row = await db.execute(
        select(
            func.sum(SaleTransaction.total_amount).label("revenue"),
            func.count(SaleTransaction.id).label("transactions")
        ).where(
            SaleTransaction.outlet_id.in_(outlets_filter),
            func.date(SaleTransaction.transaction_at) >= previous_start,
            func.date(SaleTransaction.transaction_at) <= previous_end
        )
    )
    previous_result = prev_row.first()

    current_revenue = float(current_result[0]) if current_result and current_result[0] else 0
    current_transactions = int(current_result[1]) if current_result and current_result[1] else 0
    current_avg = float(current_result[2]) if current_result and current_result[2] else 0
    previous_revenue = float(previous_result[0]) if previous_result and previous_result[0] else 0

    revenue_change = 0
    if previous_revenue > 0:
        revenue_change = ((current_revenue - previous_revenue) / previous_revenue) * 100

    return {
        "period": period,
        "current_period": {
            "revenue": current_revenue,
            "transactions": current_transactions,
            "avg_transaction_value": round(current_avg, 2)
        },
        "previous_period": {
            "revenue": previous_revenue
        },
        "comparison": {
            "revenue_change_pct": round(revenue_change, 2),
            "revenue_change_amount": round(current_revenue - previous_revenue, 2)
        }
    }


@router.get("/by-product")
async def get_sales_by_product(
    period: str = Query("30d", pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get revenue and quantity sold grouped by product.
    Period: 7d, 30d, 90d, 365d
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    if outlet_id:
        if not require_outlet_access(current_user, outlet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    period_days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}.get(period, 30)
    start_date = datetime.now().date() - timedelta(days=period_days)

    stmt = select(
        Product.id,
        Product.name,
        Product.category,
        func.sum(SaleTransaction.quantity).label("qty_sold"),
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.count(SaleTransaction.id).label("transactions")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).where(
        SaleTransaction.outlet_id.in_(outlets_filter),
        func.date(SaleTransaction.transaction_at) >= start_date
    )

    if category:
        stmt = stmt.where(Product.category == category)

    stmt = stmt.group_by(Product.id, Product.name, Product.category).order_by(
        func.sum(SaleTransaction.total_amount).desc()
    )

    result = await db.execute(stmt)
    results = result.all()

    total_revenue = sum(float(row[4]) if row[4] else 0 for row in results)

    products_data = [
        {
            "product_id": row[0],
            "product_name": row[1],
            "category": row[2],
            "quantity_sold": int(row[3]) if row[3] else 0,
            "revenue": float(row[4]) if row[4] else 0,
            "revenue_percentage": (float(row[4]) / total_revenue * 100) if total_revenue > 0 else 0,
            "transactions": int(row[5]) if row[5] else 0
        }
        for row in results
    ]

    return {
        "period": period,
        "total_revenue": round(total_revenue, 2),
        "total_products": len(products_data),
        "items": products_data
    }


@router.get("/by-payment-method")
async def get_sales_by_payment_method(
    period: str = Query("30d", pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get sales breakdown by payment method.
    Returns: cash, card, upi, other with percentages
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    if outlet_id:
        if not require_outlet_access(current_user, outlet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    period_days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}.get(period, 30)
    start_date = datetime.now().date() - timedelta(days=period_days)

    result = await db.execute(
        select(
            SaleTransaction.payment_method,
            func.sum(SaleTransaction.total_amount).label("revenue"),
            func.count(SaleTransaction.id).label("transactions")
        ).where(
            SaleTransaction.outlet_id.in_(outlets_filter),
            func.date(SaleTransaction.transaction_at) >= start_date
        ).group_by(SaleTransaction.payment_method)
    )
    results = result.all()

    total_revenue = sum(float(row[1]) if row[1] else 0 for row in results)

    payment_data = [
        {
            "payment_method": row[0],
            "revenue": float(row[1]) if row[1] else 0,
            "percentage": (float(row[1]) / total_revenue * 100) if total_revenue > 0 else 0,
            "transactions": int(row[2]) if row[2] else 0
        }
        for row in results
    ]

    return {
        "period": period,
        "total_revenue": round(total_revenue, 2),
        "items": sorted(payment_data, key=lambda x: x["revenue"], reverse=True)
    }


@router.get("/export")
async def export_sales(
    outlet_id: Optional[int] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Export sales data as CSV.
    Same filtering options as GET /
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    if outlet_id:
        if not require_outlet_access(current_user, outlet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    stmt = select(
        SaleTransaction.id,
        SaleTransaction.outlet_id,
        SaleTransaction.product_id,
        SaleTransaction.quantity,
        SaleTransaction.unit_price,
        SaleTransaction.total_amount,
        SaleTransaction.payment_method,
        SaleTransaction.transaction_at,
        Product.name,
        Product.category,
        Outlet.name.label("outlet_name")
    ).join(Product, SaleTransaction.product_id == Product.id).join(
        Outlet, SaleTransaction.outlet_id == Outlet.id
    ).where(SaleTransaction.outlet_id.in_(outlets_filter))

    if product_id:
        stmt = stmt.where(SaleTransaction.product_id == product_id)
    if category:
        stmt = stmt.where(Product.category == category)
    if payment_method:
        stmt = stmt.where(SaleTransaction.payment_method == payment_method)
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            stmt = stmt.where(func.date(SaleTransaction.transaction_at) >= from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            stmt = stmt.where(func.date(SaleTransaction.transaction_at) <= to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")

    result = await db.execute(stmt.order_by(desc(SaleTransaction.transaction_at)))
    items = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Transaction ID", "Outlet", "Product", "Category", "Quantity",
        "Unit Price", "Total Amount", "Payment Method", "Date Time"
    ])
    for row in items:
        writer.writerow([
            row[0], row[10], row[8], row[9], row[3],
            f"{row[4]:.2f}", f"{row[5]:.2f}", row[6], row[7]
        ])

    output.seek(0)
    filename = f"sales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return FileResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        filename=filename
    )


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve details for a specific transaction by its ID.
    """
    result = await db.execute(select(Sale).filter(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_in: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Record a new sales transaction and decrement inventory levels.
    """
    from datetime import timezone
    total_amount = Decimal(0)
    sale_items = []
    
    for item in sale_in.items:
        prod_result = await db.execute(select(Product).filter(Product.id == item.product_id))
        product = prod_result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        inv_result = await db.execute(select(Inventory).filter(Inventory.product_id == item.product_id))
        inventory = inv_result.scalar_one_or_none()
        
        if not inventory or inventory.current_stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {product.name}")
        
        line_total = item.unit_price * item.quantity
        total_amount += line_total
        
        sale_items.append(SaleItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=line_total
        ))
        
        # Atomic inventory reduction (simplified for this context)
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
    await db.commit()
    await db.refresh(new_sale)
    return new_sale
