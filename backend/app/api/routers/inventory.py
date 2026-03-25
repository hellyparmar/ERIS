"""
Inventory Router - Database Version
Uses repository pattern to access real database
"""

from fastapi import APIRouter, Query, Depends, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.api.db import get_db
from app.api.utils.cache import cache_response
from app.api.db.repositories.inventory_repository import inventory_repository
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
@cache_response(ttl_seconds=1800)
async def get_inventory_list(
    request: Request,
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    stock_status: Optional[str] = Query(None, regex="^(low|medium|high|out_of_stock)$"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated inventory list from database"""
    from sqlalchemy import text, and_, or_
    
    # Use raw SQL to query the actual inventory table with its current schema
    base_query = """
        SELECT 
            i.id, i.product_id, p.sku, p.name, p.category, i.current_stock,
            i.reorder_point, COALESCE(i.max_stock_level, i.reorder_point * 5) AS max_stock,
            p.unit_price, p.cost_price,
            CASE
                WHEN i.current_stock = 0                              THEN 'out_of_stock'
                WHEN i.current_stock <= i.reorder_point               THEN 'low'
                WHEN i.current_stock <= i.reorder_point * 2           THEN 'medium'
                ELSE 'high'
            END AS stock_status,
            i.warehouse_location, i.last_stocked_date
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE 1=1
    """
    
    params = {}
    where_clauses = []
    
    if search:
        where_clauses.append("(p.name ILIKE :search OR p.sku ILIKE :search)")
        params['search'] = f"%{search}%"
    
    if category:
        where_clauses.append("p.category = :category")
        params['category'] = category
    
    if stock_status:
        # Map stock_status filter to the derived CASE condition
        status_map = {
            'out_of_stock': 'i.current_stock = 0',
            'low':    'i.current_stock > 0 AND i.current_stock <= i.reorder_point',
            'medium': 'i.current_stock > i.reorder_point AND i.current_stock <= i.reorder_point * 2',
            'high':   'i.current_stock > i.reorder_point * 2',
        }
        clause = status_map.get(stock_status)
        if clause:
            where_clauses.append(f"({clause})")
    
    # Count query
    count_query = "SELECT COUNT(*) as total FROM inventory i JOIN products p ON i.product_id = p.id WHERE 1=1"
    if where_clauses:
        count_query += " AND " + " AND ".join(where_clauses)
    
    total_result = db.execute(text(count_query), params).fetchone()
    total = total_result[0] if total_result else 0
    
    # Data query with pagination
    data_query = base_query
    if where_clauses:
        data_query += " AND " + " AND ".join(where_clauses)
    data_query += f" ORDER BY i.id LIMIT {per_page} OFFSET {(page - 1) * per_page}"
    
    items = db.execute(text(data_query), params).fetchall()
    
    formatted_items = []
    for row in items:
        formatted_items.append({
            "id": row[0],
            "product_id": row[1],
            "sku": row[2],
            "name": row[3],
            "category": row[4],
            "current_stock": row[5],
            "reorder_point": row[6],
            "max_stock": row[7],
            "unit_price": row[8],
            "cost_price": row[9],
            "stock_status": row[10],
            "warehouse_location": row[11],
            "last_restock_date": row[12]
        })
    
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "success": True,
        "data": {
            "items": formatted_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            },
            "filters_applied": {
                "search": search,
                "category": category,
                "stock_status": stock_status
            }
        }
    }

@router.get("/reorder-recommendations")
@cache_response(ttl_seconds=1800)
async def get_reorder_recommendations(
    request: Request,
    limit: int = Query(default=15, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get products that need reordering from database"""
    from app.api.db.models import Product, Inventory
    
    # Get low stock items
    items = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(
        Inventory.stock_status.in_(['low', 'out_of_stock'])
    ).order_by(Inventory.current_stock.asc()).limit(limit).all()
    
    recommendations = []
    for inv, prod in items:
        reorder_qty = inv.max_stock - inv.current_stock
        recommendations.append({
            "product_id": prod.id,
            "sku": prod.sku,
            "name": prod.name,
            "category": prod.category,
            "current_stock": inv.current_stock,
            "reorder_point": inv.reorder_point,
            "max_stock": inv.max_stock,
            "recommended_order_qty": reorder_qty,
            "unit_price": prod.cost_price,
            "estimated_cost": reorder_qty * prod.cost_price,
            "urgency": "critical" if inv.current_stock == 0 else "high"
        })
    
    return {
        "success": True,
        "data": {
            "recommendations": recommendations,
            "count": len(recommendations),
            "estimated_total_cost": sum(r["estimated_cost"] for r in recommendations)
        }
    }

@router.get("/summary")
@cache_response(ttl_seconds=1800)
async def get_stock_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get inventory statistics from database"""
    from app.api.db.models import Product, Inventory
    from sqlalchemy import func
    
    # Get statistics
    stats = db.query(
        func.count(Inventory.id).label('total_products'),
        func.sum(Inventory.current_stock).label('total_units'),
        func.sum(Inventory.max_stock).label('max_capacity'),
        func.count(Inventory.id).filter(Inventory.stock_status == 'low').label('low_stock_count'),
        func.count(Inventory.id).filter(Inventory.stock_status == 'out_of_stock').label('out_of_stock_count')
    ).first()
    
    # Calculate inventory value
    value_result = db.query(
        func.sum(Inventory.current_stock * Product.cost_price).label('inventory_value'),
        func.sum(Inventory.current_stock * Product.selling_price).label('retail_value')
    ).join(Product, Inventory.product_id == Product.id).first()
    
    # Stock status breakdown
    status_breakdown = db.query(
        Inventory.stock_status,
        func.count(Inventory.id).label('count')
    ).group_by(Inventory.stock_status).all()
    
    return {
        "success": True,
        "data": {
            "total_products": stats.total_products or 0,
            "total_units_in_stock": stats.total_units or 0,
            "max_capacity": stats.max_capacity or 0,
            "stock_utilization": round((stats.total_units or 0) / (stats.max_capacity or 1) * 100, 1) if stats.max_capacity else 0,
            "low_stock_count": stats.low_stock_count or 0,
            "out_of_stock_count": stats.out_of_stock_count or 0,
            "inventory_cost_value": round(value_result.inventory_value or 0, 2),
            "inventory_retail_value": round(value_result.retail_value or 0, 2),
            "status_breakdown": {item[0]: item[1] for item in status_breakdown}
        }
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
