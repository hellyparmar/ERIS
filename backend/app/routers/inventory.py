from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.inventory import ProductCreate, ProductUpdate, ProductResponse, LowStockResponse, StoreResponse
from app.models.multitenant_models import Product, Inventory, User, Store
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])

@router.get("/products", response_model=List[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all products belonging to the user's organization.
    
    Returns a list of products with their current stock levels across all stores.
    """
    products = db.query(Product).filter(
        Product.organization_id == current_user.organization_id
    ).all()
    
    # Enrich with stock levels
    response = []
    for p in products:
        product_data = ProductResponse.model_validate(p)
        inventory = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        product_data.current_stock = inventory.current_stock if inventory else 0
        response.append(product_data)
        
    return response

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details for a specific product by ID.
    
    Includes real-time stock information.
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == current_user.organization_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product_data = ProductResponse.model_validate(product)
    inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    product_data.current_stock = inventory.current_stock if inventory else 0
    return product_data

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product and initialize its inventory record.
    
    - **sku**: Unique identifier for the product.
    - **initial_stock**: Starting stock level to be recorded in the designated store.
    """
    # Check if SKU already exists for this organization
    if db.query(Product).filter(
        Product.sku == product_in.sku,
        Product.organization_id == current_user.organization_id
    ).first():
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    # Create Product
    product_data = product_in.model_dump(exclude={"initial_stock", "store_id", "organization_id"})
    new_product = Product(**product_data, organization_id=current_user.organization_id)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Initialize Inventory
    new_inventory = Inventory(
        product_id=new_product.id,
        current_stock=product_in.initial_stock,
        available_stock=product_in.initial_stock,
        store_id=product_in.store_id
    )
    db.add(new_inventory)
    db.commit()
    
    res = ProductResponse.model_validate(new_product)
    res.current_stock = product_in.initial_stock
    return res

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update attributes of an existing product.
    
    Only provided fields will be updated.
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == current_user.organization_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    update_data = product_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    
    res = ProductResponse.model_validate(product)
    inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    res.current_stock = inventory.current_stock if inventory else 0
    return res

@router.get("/low-stock", response_model=List[LowStockResponse])
def get_low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a list of products where current stock is at or below the reorder point.
    
    Useful for procurement and restocking alerts.
    """
    low_stock_items = db.query(Inventory).join(Product).filter(
        Product.organization_id == current_user.organization_id,
        Inventory.current_stock <= Inventory.reorder_point
    ).all()
    
    response = []
    for item in low_stock_items:
        response.append({
            "product_id": item.product_id,
            "sku": item.product.sku,
            "name": item.product.name,
            "current_stock": item.current_stock,
            "reorder_point": item.reorder_point,
            "store_id": item.store_id
        })
        
    return response

@router.get("/stores", response_model=List[StoreResponse])
def get_stores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all physical/logical stores belonging to the organization.
    """
    return db.query(Store).filter(
        Store.organization_id == current_user.organization_id
    ).all()
