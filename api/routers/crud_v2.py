"""
Enhanced CRUD Router for R-DIOS v6.0
Covers Products, Customers, Sales, Suppliers with full CRUD operations
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import logging

from api.db.database import get_db
from api.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["CRUD Operations v2"])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    sku: Optional[str] = Field(None, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    cost_price: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    mrp: Optional[float] = None
    hsn_code: str = Field(..., max_length=20)
    gst_rate: float = Field(18.0, ge=0, le=28)
    stock_level: int = Field(0, ge=0)
    reorder_point: int = Field(10, ge=0)
    min_order_quantity: int = Field(1, ge=1)
    
class ProductCreate(ProductBase):
    pass
    
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    stock_level: Optional[int] = None
    reorder_point: Optional[int] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    last_sale_date: Optional[date] = None
    total_units_sold: int = 0
    abc_classification: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Customer Schemas
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    whatsapp: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, max_length=10)
    credit_limit: float = Field(0, ge=0)
    date_of_birth: Optional[date] = None
    
class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Optional[float] = None

class CustomerResponse(CustomerBase):
    id: int
    outstanding_amount: float = 0
    credit_score: int = 100
    last_purchase_date: Optional[date] = None
    purchase_count: int = 0
    total_spent: float = 0
    rfm_segment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Supplier Schemas
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    payment_terms_days: int = Field(30, ge=0)

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    payment_terms_days: Optional[int] = None

class SupplierResponse(SupplierBase):
    id: int
    avg_lead_time_days: int = 7
    quality_rating: float = 5.0
    on_time_delivery_rate: float = 100.0
    outstanding_payable: float = 0
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

# Sale Schemas
class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    discount_percent: float = Field(0, ge=0, le=100)

class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[SaleItemCreate]
    payment_method: str = Field("cash", pattern="^(cash|upi|card|credit|mixed)$")
    discount_amount: float = Field(0, ge=0)
    notes: Optional[str] = None
    channel: str = Field("offline", pattern="^(offline|online|whatsapp)$")

class SaleResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: Optional[int]
    sale_date: datetime
    subtotal: float
    gst_amount: float
    discount_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    channel: str
    items_count: int
    
    class Config:
        from_attributes = True


# ============================================================
# PRODUCTS CRUD
# ============================================================

@router.get("/products", response_model=Dict[str, Any])
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    low_stock: bool = False,
    sort_by: str = Query("name", regex="^(name|price|stock|created_at)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List products with filtering, search, and pagination"""
    offset = (page - 1) * size
    
    # Build dynamic query
    conditions = ["is_active = true"]
    params = {"limit": size, "offset": offset}
    
    if category_id:
        conditions.append("category_id = :category_id")
        params["category_id"] = category_id
    
    if search:
        conditions.append("(name ILIKE :search OR sku ILIKE :search OR barcode ILIKE :search)")
        params["search"] = f"%{search}%"
    
    if low_stock:
        conditions.append("stock_level <= reorder_point")
    
    where_clause = " AND ".join(conditions)
    order_clause = f"{sort_by} {'ASC' if order == 'asc' else 'DESC'}"
    
    # Count total
    count_query = text(f"SELECT COUNT(*) FROM products WHERE {where_clause}")
    total = db.execute(count_query, params).scalar()
    
    # Get products
    query = text(f"""
        SELECT 
            p.*,
            pc.name as category_name
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(query, params)
    products = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "items": products,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.post("/products", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new product"""
    # Check for duplicate SKU
    if product.sku:
        existing = db.execute(
            text("SELECT id FROM products WHERE sku = :sku"),
            {"sku": product.sku}
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    query = text("""
        INSERT INTO products (
            name, sku, barcode, description, category_id, supplier_id,
            cost_price, selling_price, mrp, hsn_code, gst_rate,
            stock_level, reorder_point, min_order_quantity, is_active, created_at
        ) VALUES (
            :name, :sku, :barcode, :description, :category_id, :supplier_id,
            :cost_price, :selling_price, :mrp, :hsn_code, :gst_rate,
            :stock_level, :reorder_point, :min_order_quantity, true, NOW()
        ) RETURNING id
    """)
    
    result = db.execute(query, product.dict())
    db.commit()
    product_id = result.fetchone()[0]
    
    return {"id": product_id, "message": "Product created successfully"}


@router.get("/products/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get product by ID with related data"""
    query = text("""
        SELECT 
            p.*,
            pc.name as category_name,
            s.name as supplier_name,
            COALESCE(sold.total_sold, 0) as total_sold_30d,
            COALESCE(sold.revenue, 0) as revenue_30d
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        LEFT JOIN (
            SELECT 
                product_id,
                SUM(quantity) as total_sold,
                SUM(line_total) as revenue
            FROM sale_items
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY product_id
        ) sold ON p.id = sold.product_id
        WHERE p.id = :product_id
    """)
    
    result = db.execute(query, {"product_id": product_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return dict(result._mapping)


@router.put("/products/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update product"""
    # Check exists
    existing = db.execute(
        text("SELECT id FROM products WHERE id = :id"),
        {"id": product_id}
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Build update query dynamically
    updates = []
    params = {"id": product_id}
    
    for field, value in product.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value
    
    if updates:
        updates.append("updated_at = NOW()")
        query = text(f"UPDATE products SET {', '.join(updates)} WHERE id = :id")
        db.execute(query, params)
        db.commit()
    
    return {"message": "Product updated successfully"}


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete product"""
    result = db.execute(
        text("UPDATE products SET is_active = false, updated_at = NOW() WHERE id = :id RETURNING id"),
        {"id": product_id}
    )
    db.commit()
    
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}


# ============================================================
# CUSTOMERS CRUD
# ============================================================

@router.get("/customers", response_model=Dict[str, Any])
async def list_customers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    segment: Optional[str] = None,
    has_credit: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List customers with filtering and pagination"""
    offset = (page - 1) * size
    
    conditions = ["1=1"]
    params = {"limit": size, "offset": offset}
    
    if search:
        conditions.append("(name ILIKE :search OR phone ILIKE :search OR email ILIKE :search)")
        params["search"] = f"%{search}%"
    
    if segment:
        conditions.append("rfm_segment = :segment")
        params["segment"] = segment
    
    if has_credit:
        conditions.append("outstanding_amount > 0")
    
    where_clause = " AND ".join(conditions)
    
    count_query = text(f"SELECT COUNT(*) FROM customers WHERE {where_clause}")
    total = db.execute(count_query, params).scalar()
    
    query = text(f"""
        SELECT * FROM customers
        WHERE {where_clause}
        ORDER BY name
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(query, params)
    customers = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "items": customers,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.post("/customers", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new customer"""
    query = text("""
        INSERT INTO customers (
            name, email, phone, whatsapp, address, city, state, pincode,
            credit_limit, date_of_birth, created_at
        ) VALUES (
            :name, :email, :phone, :whatsapp, :address, :city, :state, :pincode,
            :credit_limit, :date_of_birth, NOW()
        ) RETURNING id
    """)
    
    result = db.execute(query, customer.dict())
    db.commit()
    customer_id = result.fetchone()[0]
    
    return {"id": customer_id, "message": "Customer created successfully"}


@router.get("/customers/{customer_id}", response_model=Dict[str, Any])
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get customer with purchase history summary"""
    query = text("""
        SELECT 
            c.*,
            COALESCE(s.recent_orders, 0) as orders_30d,
            COALESCE(s.recent_revenue, 0) as revenue_30d
        FROM customers c
        LEFT JOIN (
            SELECT 
                customer_id,
                COUNT(*) as recent_orders,
                SUM(total_amount) as recent_revenue
            FROM sales
            WHERE sale_date >= NOW() - INTERVAL '30 days'
            GROUP BY customer_id
        ) s ON c.id = s.customer_id
        WHERE c.id = :customer_id
    """)
    
    result = db.execute(query, {"customer_id": customer_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return dict(result._mapping)


@router.put("/customers/{customer_id}", response_model=Dict[str, Any])
async def update_customer(
    customer_id: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update customer"""
    updates = []
    params = {"id": customer_id}
    
    for field, value in customer.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value
    
    if updates:
        updates.append("updated_at = NOW()")
        query = text(f"UPDATE customers SET {', '.join(updates)} WHERE id = :id RETURNING id")
        result = db.execute(query, params)
        db.commit()
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")
    
    return {"message": "Customer updated successfully"}


# ============================================================
# SUPPLIERS CRUD
# ============================================================

@router.get("/suppliers", response_model=Dict[str, Any])
async def list_suppliers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List suppliers with pagination"""
    offset = (page - 1) * size
    
    conditions = []
    params = {"limit": size, "offset": offset}
    
    if active_only:
        conditions.append("is_active = true")
    
    if search:
        conditions.append("(name ILIKE :search OR contact_person ILIKE :search)")
        params["search"] = f"%{search}%"
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    count_query = text(f"SELECT COUNT(*) FROM suppliers WHERE {where_clause}")
    total = db.execute(count_query, params).scalar()
    
    query = text(f"""
        SELECT 
            s.*,
            COALESCE(p.product_count, 0) as product_count
        FROM suppliers s
        LEFT JOIN (
            SELECT supplier_id, COUNT(*) as product_count
            FROM products WHERE is_active = true
            GROUP BY supplier_id
        ) p ON s.id = p.supplier_id
        WHERE {where_clause}
        ORDER BY name
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(query, params)
    suppliers = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "items": suppliers,
        "total": total,
        "page": page,
        "size": size
    }


@router.post("/suppliers", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new supplier"""
    query = text("""
        INSERT INTO suppliers (
            name, contact_person, email, phone, gst_number,
            address, city, state, payment_terms_days, is_active, created_at
        ) VALUES (
            :name, :contact_person, :email, :phone, :gst_number,
            :address, :city, :state, :payment_terms_days, true, NOW()
        ) RETURNING id
    """)
    
    result = db.execute(query, supplier.dict())
    db.commit()
    supplier_id = result.fetchone()[0]
    
    return {"id": supplier_id, "message": "Supplier created successfully"}


# ============================================================
# SALES CRUD
# ============================================================

@router.get("/sales", response_model=Dict[str, Any])
async def list_sales(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_id: Optional[int] = None,
    payment_status: Optional[str] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List sales with filtering and pagination"""
    offset = (page - 1) * size
    
    conditions = ["1=1"]
    params = {"limit": size, "offset": offset}
    
    if start_date:
        conditions.append("sale_date >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        conditions.append("sale_date < :end_date")
        params["end_date"] = end_date + timedelta(days=1)
    
    if customer_id:
        conditions.append("customer_id = :customer_id")
        params["customer_id"] = customer_id
    
    if payment_status:
        conditions.append("payment_status = :payment_status")
        params["payment_status"] = payment_status
    
    if channel:
        conditions.append("channel = :channel")
        params["channel"] = channel
    
    where_clause = " AND ".join(conditions)
    
    count_query = text(f"SELECT COUNT(*) FROM sales WHERE {where_clause}")
    total = db.execute(count_query, params).scalar()
    
    query = text(f"""
        SELECT 
            s.*,
            c.name as customer_name,
            (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) as items_count
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE {where_clause}
        ORDER BY sale_date DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(query, params)
    sales = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "items": sales,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/sales/{sale_id}", response_model=Dict[str, Any])
async def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sale with all items"""
    # Get sale
    sale_query = text("""
        SELECT 
            s.*,
            c.name as customer_name,
            c.phone as customer_phone
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE s.id = :sale_id
    """)
    
    sale = db.execute(sale_query, {"sale_id": sale_id}).fetchone()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Get items
    items_query = text("""
        SELECT 
            si.*,
            p.name as product_name,
            p.sku as product_sku
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = :sale_id
    """)
    
    items = [dict(row._mapping) for row in db.execute(items_query, {"sale_id": sale_id}).fetchall()]
    
    result = dict(sale._mapping)
    result["items"] = items
    
    return result
