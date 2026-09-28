"""
Enterprise Router - Multi-Store Analytics
Aggregates data across all stores for the enterprise view.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.api.deps import require_role
from app.models.users import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])

@router.get("/overview")
def get_enterprise_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "area_manager")),
):
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



