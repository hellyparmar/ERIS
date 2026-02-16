"""
Inventory Control Router
Barcode scanning, stock alerts, reorder suggestions, stock adjustments
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from api.db import get_db
from api.services.barcode_scanner import lookup_barcode, update_product_barcode
from api.services.stock_alerts import get_active_alerts, acknowledge_alert, check_stock_levels
from api.services.reorder_automation import get_reorder_suggestions

router = APIRouter(prefix="/inventory", tags=["Inventory Control"])

class BarcodeUpdateRequest(BaseModel):
    product_id: int
    barcode: str

class AcknowledgeAlertRequest(BaseModel):
    user_id: int

@router.get("/scan/{barcode}")
async def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    Lookup product by barcode
    Supports EAN-13, UPC-A, Code128, EAN-8
    """
    result = lookup_barcode(barcode, db)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'data': {
            'product': result['product'],
            'inventory': result['inventory'],
            'barcode_type': result['barcode_type']
        }
    }

@router.post("/barcode/update")
async def update_barcode(request: BarcodeUpdateRequest, db: Session = Depends(get_db)):
    """
    Update product barcode
    """
    result = update_product_barcode(request.product_id, request.barcode, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return {'success': True, 'message': 'Barcode updated successfully'}

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, warning, info"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get active low stock alerts
    Returns alerts with severity counts and pagination
    """
    result = get_active_alerts(db, severity, category, limit, offset)
    
    return {
        'success': True,
        'data': result
    }

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert_endpoint(
    alert_id: int,
    request: AcknowledgeAlertRequest,
    db: Session = Depends(get_db)
):
    """
    Mark alert as acknowledged
    """
    result = acknowledge_alert(alert_id, request.user_id, db)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {'success': True, 'message': 'Alert acknowledged'}

@router.post("/alerts/check")
async def check_stock_endpoint(db: Session = Depends(get_db)):
    """
    Manually trigger stock level check
    Generates alerts for low stock items
    """
    alerts = check_stock_levels(db)
    
    return {
        'success': True,
        'message': f'Generated {len(alerts)} new alerts',
        'alerts': alerts
    }

@router.get("/reorder-suggestions")
async def get_reorder_suggestions_endpoint(
    min_confidence: int = Query(50, ge=0, le=100, description="Minimum confidence score"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get AI-driven reorder suggestions
    Based on sales velocity and stock levels
    Sorted by urgency
    """
    suggestions = get_reorder_suggestions(db, min_confidence, limit)
    
    return {
        'success': True,
        'data': {
            'suggestions': suggestions,
            'total': len(suggestions)
        }
    }
