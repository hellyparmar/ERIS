"""
Extended Analytics Router
Additional endpoints for advanced analytics features
"""

from fastapi import APIRouter, Query
from typing import Optional
from app.api.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/category-breakdown")
async def get_category_breakdown(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get sales breakdown by product category
    
    Returns category-wise sales, orders, and percentage distribution
    """
    data = analytics_service.get_category_breakdown(days=days)
    return {
        "success": True,
        "data": data
    }

@router.get("/top-products")
async def get_top_products(
    limit: int = Query(default=10, ge=1, le=50, description="Number of products to return"),
    metric: str = Query(default="revenue", regex="^(revenue|units|profit)$", description="Sorting metric")
):
    """
    Get top performing products
    
    Can be sorted by revenue, units sold, or profit
    """
    products = analytics_service.get_top_products(limit=limit, metric=metric)
    return {
        "success": True,
        "data": {
            "products": products,
            "count": len(products),
            "sort_by": metric
        }
    }

@router.get("/trend-analysis")
async def get_trend_analysis(
    days: int = Query(default=90, ge=7, le=365, description="Number of days to analyze")
):
    """
    Analyze sales trends over time
    
    Returns daily and weekly aggregations with trend metrics
    """
    data = analytics_service.get_trend_analysis(days=days)
    return {
        "success": True,
        "data": data
    }
