"""
Inventory Router - Database Version
Uses repository pattern to access real database
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from api.db.database_postgres import get_db
from api.db.repositories.inventory_repository import inventory_repository

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
