"""
POS Router - Point of Sale Operations
Handles checkout, cart management, and order creation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.api.db.database_postgres import get_db
from app.api.db.models import Sale, Product, Customer, Invoice, Inventory

router = APIRouter(prefix="/api/v1/pos", tags=["POS"])

class CartItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    customer_id: Optional[int] = None
    payment_method: str = "cash"
    discount: float = 0.0

@router.post("/checkout")
async def checkout(request: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Process POS checkout with ACID guarantees
    - Row-level inventory locking
    - Stock validation before commit
    - Atomic inventory deduction
    - Loyalty points award
    - Post-sale event chain
    """
    from app.api.services.pos_service import complete_sale
    
    # Build cart structure
    cart = {
        "items": [],
        "subtotal": 0.0,
        "gst_amount": 0.0,
        "total": 0.0,
        "customer_id": request.customer_id
    }
    
    # Calculate totals and build cart items
    for item in request.items:
        item_total = item.unit_price * item.quantity
        gst_amount = item_total * 0.18  # 18% GST
        
        cart["items"].append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item_total,
            "gst_rate": 18.0,
            "gst_amount": gst_amount
        })
        
        cart["subtotal"] += item_total
        cart["gst_amount"] += gst_amount
    
    cart["total"] = cart["subtotal"] + cart["gst_amount"] - request.discount
    
    # Build payment structure
    payment = {
        "method": request.payment_method,
        "amount": cart["total"],
        "reference": None
    }
    
    # Complete sale (ACID transaction)
    # Cashier ID should come from auth token - for now use 1
    cashier_id = 1  # TODO: Get from current_user dependency
    
    return complete_sale(cart, payment, cashier_id, db)

@router.get("/products")
async def get_pos_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get products available for POS with stock info"""
    query = db.query(Product, Inventory).join(
        Inventory, Product.id == Inventory.product_id
    ).filter(Inventory.current_stock > 0)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Product.category == category)
    
    results = query.all()
    
    products = []
    for product, inventory in results:
        products.append({
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "category": product.category,
            "price": float(product.unit_price),
            "stock": inventory.current_stock,
            "image": f"/api/placeholder/100/100"  # Placeholder
        })
    
    return {"success": True, "data": products}
