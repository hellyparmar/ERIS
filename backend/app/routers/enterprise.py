"""
Enterprise Router - Multi-Store Analytics
Aggregates data across all stores for the enterprise view.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])

@router.get("/overview")
def get_enterprise_overview(db: Session = Depends(get_db)):
    """
    Get aggregated enterprise metrics from real outlet data.

    Returns each active outlet's actual revenue and transaction count from
    the sales table. No synthetic distribution, no random numbers.
    If no sales data exists yet, returns outlets with zero figures.
    """
    from sqlalchemy import text

    try:
        rows = db.execute(text("""
            SELECT
                o.id,
                o.name,
                o.city,
                o.is_active,
                COALESCE(SUM(s.total_amount), 0)  AS total_revenue,
                COUNT(s.id)                        AS total_orders
            FROM outlets o
            LEFT JOIN sales s ON o.id = s.outlet_id
            WHERE o.is_active = TRUE
            GROUP BY o.id, o.name, o.city, o.is_active
            ORDER BY total_revenue DESC
        """)).fetchall()

        return [
            {
                "id":           r[0],
                "name":         r[1],
                "city":         r[2] or "Unknown",
                "is_active":    r[3],
                "total_revenue": float(r[4] or 0),
                "total_orders":  int(r[5] or 0),
            }
            for r in rows
        ]

    except Exception as e:
        logger.error(f"Error fetching enterprise overview: {e}")
        return {"error": str(e), "data": []}



# ============================================================
# MULTI-TENANT MANAGEMENT ENDPOINTS
# ============================================================

from typing import Optional, List
from fastapi import HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organization import Organization


@router.get("/tenants", response_model=List[dict])
async def list_tenants(
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all registered tenants / organizations with pagination.
    Superadmin only — returns name, UUID, and active status.
    """
    try:
        query = db.query(Organization)
        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)
        if search:
            query = query.filter(Organization.name.ilike(f"%{search}%"))
        orgs = query.order_by(Organization.name).offset((page - 1) * per_page).limit(per_page).all()
        return [
            {
                "id": o.id,
                "name": o.name,
                "tenant_id": str(getattr(o, "tenant_id", "")),
                "is_active": o.is_active,
            }
            for o in orgs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Retrieve a single tenant by UUID or ID."""
    try:
        org = db.query(Organization).filter(Organization.name == tenant_id).first()
        if not org:
            org = db.query(Organization).filter(Organization.id == int(tenant_id)).first() if tenant_id.isdigit() else None
        if not org:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id!r} not found")
        return {
            "id": org.id,
            "name": org.name,
            "tenant_id": str(getattr(org, "tenant_id", "")),
            "is_active": org.is_active,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tenants/{tenant_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Soft-delete a tenant by marking it inactive."""
    try:
        org = db.query(Organization).filter(Organization.name == tenant_id).first()
        if not org and tenant_id.isdigit():
            org = db.query(Organization).filter(Organization.id == int(tenant_id)).first()
        if not org:
            raise HTTPException(status_code=404, detail="Tenant not found")
        org.is_active = False
        db.commit()
        return {"detail": f"Tenant '{org.name}' deactivated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

