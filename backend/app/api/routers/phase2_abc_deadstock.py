"""
Phase 2 - ABC Classification & Dead Stock Routers
Handles ABC analysis and dead stock identification
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.db.database import get_db
from app.api.services.abc_classification import abc_service
from app.api.services.dead_stock import dead_stock_service

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory Analytics"])


# ============================================================================
# ABC CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/abc/analyze")
async def analyze_abc_classification(
    days: int = Query(365, ge=30, le=1095, description="Analysis period in days"),
    db: Session = Depends(get_db)
):
    """
    Perform ABC classification analysis
    
    ABC Classification:
    - A Items: 80% of revenue, ~20% of inventory (high priority)
    - B Items: 15% of revenue, ~30% of inventory (medium priority)
    - C Items: 5% of revenue, ~50% of inventory (low priority)
    """
    try:
        result = abc_service.analyze_inventory(db, days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/abc/items/{classification}")
async def get_items_by_classification(
    classification: str,
    db: Session = Depends(get_db)
):
    """
    Get all items of a specific ABC classification
    """
    if classification not in ['A', 'B', 'C']:
        raise HTTPException(status_code=400, detail="Classification must be A, B, or C")
    
    try:
        items = abc_service.get_items_by_classification(db, classification)
        
        return {
            "status": "success",
            "classification": classification,
            "count": len(items),
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve items: {str(e)}")


@router.get("/abc/metrics")
async def get_abc_metrics(
    db: Session = Depends(get_db)
):
    """
    Get current ABC classification metrics
    """
    try:
        metrics = abc_service.get_classification_metrics(db)
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


# ============================================================================
# DEAD STOCK IDENTIFICATION ENDPOINTS
# ============================================================================

@router.post("/dead-stock/analyze")
async def analyze_dead_stock(
    days: int = Query(90, ge=30, le=365, description="Days without sale to be considered dead stock"),
    db: Session = Depends(get_db)
):
    """
    Identify dead stock items (not sold in specified period)
    
    Returns:
    - List of dead stock items with suggested discounts
    - Stock value at risk
    - Disposal recommendations
    """
    try:
        result = dead_stock_service.identify_dead_stock(db, days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/slow-moving/analyze")
async def analyze_slow_moving(
    days: int = Query(30, ge=7, le=90, description="Days without sale for slow-moving classification"),
    db: Session = Depends(get_db)
):
    """
    Identify slow-moving items
    
    Slow-moving: Items with very low sales velocity (less than 1 unit per month)
    """
    try:
        result = dead_stock_service.identify_slow_moving(db, days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/dead-stock/summary")
async def get_dead_stock_summary(
    db: Session = Depends(get_db)
):
    """
    Get dead stock summary by category
    """
    try:
        summary = dead_stock_service.get_dead_stock_by_category(db)
        
        total_value = sum(cat["total_value"] for cat in summary.values())
        total_items = sum(cat["dead_stock_count"] for cat in summary.values())
        
        return {
            "status": "success",
            "analysis_date": __import__("datetime").datetime.utcnow().isoformat(),
            "summary": summary,
            "totals": {
                "total_categories": len(summary),
                "total_dead_stock_items": total_items,
                "total_value_at_risk": total_value,
                "potential_cash_recovery": total_value * 0.70
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")


@router.get("/dead-stock/export")
async def export_dead_stock(
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Export dead stock analysis (JSON or CSV format)
    """
    try:
        result = dead_stock_service.identify_dead_stock(db)
        
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "product_id", "name", "sku", "current_stock",
                    "cost_price", "stock_value", "days_since_sale",
                    "suggested_discount_percentage", "total_recovery_amount"
                ]
            )
            
            writer.writeheader()
            for item in result["dead_stock_items"]:
                writer.writerow({
                    "product_id": item["product_id"],
                    "name": item["name"],
                    "sku": item["sku"],
                    "current_stock": item["current_stock"],
                    "cost_price": item["cost_price"],
                    "stock_value": item["stock_value"],
                    "days_since_sale": item["days_since_last_sale"],
                    "suggested_discount_percentage": item["suggested_discount_percentage"],
                    "total_recovery_amount": item["total_recovery_amount"]
                })
            
            return {
                "status": "success",
                "format": "csv",
                "data": output.getvalue()
            }
        else:
            return {
                "status": "success",
                "format": "json",
                "data": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
