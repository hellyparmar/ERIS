"""
POS Router - Point of Sale Operations
Handles checkout, cart management, and order creation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.db.database_postgres import get_db
from api.db.models import Sale, Product, Customer, Invoice, Inventory

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
    Process POS checkout - Create sales records, update inventory, generate invoice
    """
    try:
        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in request.items)
        tax_amount = subtotal * 0.18  # 18% GST
        total = subtotal + tax_amount - request.discount
        
        # Generate transaction ID
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create sales records
        sales_created = []
        for item in request.items:
            # Verify product exists and has stock
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            inventory = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
            if not inventory or inventory.current_stock < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for {product.name}"
                )
            
            # Create sale record
            sale = Sale(
                transaction_id=f"{transaction_id}_{item.product_id}",
                product_id=item.product_id,
                customer_id=request.customer_id,
                transaction_date=datetime.now(),
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=request.discount / len(request.items),  # Distribute discount
                tax=tax_amount / len(request.items),
                total_amount=item.unit_price * item.quantity,
                payment_method=request.payment_method,
                payment_status="paid"
            )
            db.add(sale)
            
            # Update inventory
            inventory.current_stock -= item.quantity
            inventory.available_stock = inventory.current_stock - inventory.reserved_stock
            
            sales_created.append({
                "product_name": product.name,
                "quantity": item.quantity,
                "amount": item.unit_price * item.quantity
            })
        
        # Commit transaction
        db.commit()
        
        return {
            "success": True,
            "data": {
                "transaction_id": transaction_id,
                "total_amount": round(total, 2),
                "tax_amount": round(tax_amount, 2),
                "items_sold": len(request.items),
                "sales": sales_created,
                "message": "Checkout completed successfully"
            }
        }
        
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

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
