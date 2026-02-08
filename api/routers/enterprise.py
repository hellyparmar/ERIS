"""
Enterprise Router - Multi-Store Analytics
Aggregates data across all stores for the enterprise view.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import logging

from api.db.database import get_db
from api.auth.dependencies import get_current_active_user
from api.db.multitenant_models import Store, User
from api.db.models import Sale

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enterprise", tags=["Enterprise"])

@router.get("/overview")
async def get_enterprise_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get aggregated enterprise metrics by store
    """
    try:
        # Get all stores
        stores = db.query(Store).all()
        
        results = []
        
        # Define region mapping (simple heuristic based on city or metadata)
        # In a real app, Store model would have a 'region' field.
        # We'll map mostly to 'North' as it's Petpooja/India specific for now
        
        for store in stores:
            # Aggregate Sales for this store
            # Note: In production, use a GROUP BY query instead of looping
            metrics = db.query(
                func.sum(Sale.total_amount).label('revenue'),
                func.count(Sale.id).label('orders')
            ).filter(Sale.store_id == store.id).first()
            
            revenue = float(metrics.revenue or 0)
            orders = metrics.orders or 0
            
            # Mock targets/staff for now as they aren't in core schema yet
            # or could be in store_metadata
            target = revenue * 1.1 
            staff = 10 + (orders // 1000) 
            growth = 12.5 # Mock growth for display
            
            results.append({
                "id": store.id,
                "name": store.name,
                "region": store.location.split(',')[0] if store.location else "North", # Fallback
                "location": store.location or "New Delhi, India",
                "revenue": revenue,
                "target": target,
                "orders": orders,
                "staff": staff,
                "growth": growth,
                "status": "excellent" if revenue > 100000 else "good"
            })
            
        return results

    except Exception as e:
        logger.error(f"Error fetching enterprise data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
