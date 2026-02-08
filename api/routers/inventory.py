"""
Inventory Router - Database Version
Uses repository pattern to access real database
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.db.repositories.inventory_repository import inventory_repository
from pydantic import BaseModel

class ProductCreateRequest(BaseModel):
    sku: str
    name: str
    category: str
    unit_price: float
    cost_price: Optional[float] = 0.0
    current_stock: Optional[int] = 0
    reorder_point: Optional[int] = 10
    warehouse_location: Optional[str] = "Main Warehouse"

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    current_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    warehouse_location: Optional[str] = None

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

@router.get("/list")
async def get_inventory_list(
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    stock_status: Optional[str] = Query(None, regex="^(low|medium|high|out_of_stock)$"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated inventory list from database"""
    items, pagination = inventory_repository.get_inventory_list(
        db=db,
        search=search,
        category=category,
        stock_status=stock_status,
        page=page,
        per_page=per_page
    )
    
    return {
        "success": True,
        "data": {
            "items": items,
            "pagination": pagination,
            "filters_applied": {
                "search": search,
                "category": category,
                "stock_status": stock_status
            }
        }
    }

@router.get("/reorder-recommendations")
async def get_reorder_recommendations(
    limit: int = Query(default=15, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get products that need reordering from database"""
    recommendations = inventory_repository.get_reorder_recommendations(db=db, limit=limit)
    
    return {
        "success": True,
        "data": {
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    }

@router.get("/summary")
async def get_stock_summary(db: Session = Depends(get_db)):
    """Get inventory statistics from database"""
    summary = inventory_repository.get_stock_summary(db=db)
    
    return {
        "success": True,
        "data": summary
    }

@router.post("/create")
async def create_product(
    product: ProductCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new product with initial inventory"""
    try:
        # Split data for repository
        prod_data = {
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "unit_price": product.unit_price,
            "cost_price": product.cost_price
        }
        inv_data = {
            "current_stock": product.current_stock,
            "reorder_point": product.reorder_point,
            "warehouse_location": product.warehouse_location
        }
        
        result = inventory_repository.create_product(db, prod_data, inv_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.put("/update/{product_id}")
async def update_product(
    product_id: int,
    updates: ProductUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update product or inventory details"""
    try:
        update_data = updates.dict(exclude_unset=True)
        result = inventory_repository.update_product(db, product_id, update_data)
        if not result:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.delete("/delete/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    try:
        success = inventory_repository.delete_product(db, product_id)
        if not success:
            return {"success": False, "error": "Deletion failed"}
        return {"success": True, "message": "Product deleted successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}
