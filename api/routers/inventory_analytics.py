"""
Inventory Analytics Router - Stock status, low stock alerts, ABC analysis
Provides comprehensive inventory analytics for the R-DIOS dashboard
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, and_, or_
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from api.db.database import get_db
from api.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics/inventory", tags=["Inventory Analytics"])


# ============================================================
# INVENTORY OVERVIEW
# ============================================================

@router.get("/summary", response_model=Dict[str, Any])
async def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive inventory summary including:
    - Total products, active products
    - Total stock value
    - Low stock count
    - Dead stock count
    """
    query = text("""
        SELECT 
            COUNT(*) as total_products,
            COUNT(CASE WHEN is_active = true THEN 1 END) as active_products,
            COALESCE(SUM(stock_level), 0) as total_units,
            COALESCE(SUM(stock_level * cost_price), 0) as stock_value_cost,
            COALESCE(SUM(stock_level * selling_price), 0) as stock_value_retail,
            COUNT(CASE WHEN stock_level <= reorder_point AND is_active = true THEN 1 END) as low_stock_count,
            COUNT(CASE WHEN stock_level = 0 AND is_active = true THEN 1 END) as out_of_stock_count,
            COUNT(CASE WHEN last_sale_date < CURRENT_DATE - INTERVAL '180 days' OR last_sale_date IS NULL THEN 1 END) as dead_stock_count,
            AVG(CASE WHEN stock_level > 0 THEN (selling_price - cost_price) / NULLIF(cost_price, 0) * 100 END) as avg_margin_percent
        FROM products
        WHERE is_active = true
    """)
    
    result = db.execute(query).fetchone()
    
    return {
        "products": {
            "total": result.total_products or 0,
            "active": result.active_products or 0,
            "total_units": result.total_units or 0
        },
        "value": {
            "cost": float(result.stock_value_cost or 0),
            "retail": float(result.stock_value_retail or 0),
            "potential_profit": float((result.stock_value_retail or 0) - (result.stock_value_cost or 0))
        },
        "alerts": {
            "low_stock": result.low_stock_count or 0,
            "out_of_stock": result.out_of_stock_count or 0,
            "dead_stock": result.dead_stock_count or 0
        },
        "avg_margin_percent": round(float(result.avg_margin_percent or 0), 1)
    }


@router.get("/low-stock", response_model=List[Dict[str, Any]])
async def get_low_stock_products(
    limit: int = Query(20, ge=1, le=100),
    include_out_of_stock: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get products at or below reorder point
    Sorted by urgency (stock_level / reorder_point)
    """
    stock_condition = "stock_level <= reorder_point" if include_out_of_stock else "stock_level > 0 AND stock_level <= reorder_point"
    
    query = text(f"""
        SELECT 
            p.id,
            p.name,
            p.sku,
            p.stock_level,
            p.reorder_point,
            p.min_order_quantity,
            p.cost_price,
            COALESCE(pc.name, 'Uncategorized') as category,
            COALESCE(s.name, 'No Supplier') as supplier_name,
            s.avg_lead_time_days,
            COALESCE(sold.avg_daily_sales, 0) as avg_daily_sales,
            CASE 
                WHEN COALESCE(sold.avg_daily_sales, 0) > 0 
                THEN ROUND(p.stock_level / sold.avg_daily_sales, 1)
                ELSE NULL 
            END as days_of_stock_left,
            CASE 
                WHEN p.reorder_point > 0 
                THEN ROUND(p.stock_level::DECIMAL / p.reorder_point * 100, 1)
                ELSE 0 
            END as stock_percent
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        LEFT JOIN (
            SELECT 
                product_id,
                SUM(quantity) / 30.0 as avg_daily_sales
            FROM sale_items
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY product_id
        ) sold ON p.id = sold.product_id
        WHERE p.is_active = true AND {stock_condition}
        ORDER BY 
            CASE WHEN p.stock_level = 0 THEN 0 ELSE 1 END,
            p.stock_level::DECIMAL / NULLIF(p.reorder_point, 0)
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "sku": row.sku,
            "stock_level": row.stock_level,
            "reorder_point": row.reorder_point,
            "min_order_quantity": row.min_order_quantity,
            "cost_price": float(row.cost_price or 0),
            "category": row.category,
            "supplier": row.supplier_name,
            "lead_time_days": row.avg_lead_time_days or 7,
            "avg_daily_sales": round(float(row.avg_daily_sales or 0), 2),
            "days_of_stock_left": float(row.days_of_stock_left) if row.days_of_stock_left else None,
            "stock_percent": float(row.stock_percent or 0),
            "urgency": "critical" if row.stock_level == 0 else "warning" if row.stock_percent < 50 else "low"
        }
        for row in result.fetchall()
    ]


@router.get("/dead-stock", response_model=List[Dict[str, Any]])
async def get_dead_stock(
    days_threshold: int = Query(180, ge=30, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get products with no sales in specified period (dead stock)
    """
    query = text("""
        SELECT 
            p.id,
            p.name,
            p.sku,
            p.stock_level,
            p.cost_price,
            p.selling_price,
            p.stock_level * p.cost_price as stuck_capital,
            COALESCE(pc.name, 'Uncategorized') as category,
            p.last_sale_date,
            CURRENT_DATE - p.last_sale_date as days_since_last_sale,
            COALESCE(pc.dead_stock_days, 180) as category_threshold
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.is_active = true 
            AND p.stock_level > 0
            AND (p.last_sale_date IS NULL OR p.last_sale_date < CURRENT_DATE - :days_threshold * INTERVAL '1 day')
        ORDER BY stuck_capital DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"days_threshold": days_threshold, "limit": limit})
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "sku": row.sku,
            "stock_level": row.stock_level,
            "cost_price": float(row.cost_price or 0),
            "selling_price": float(row.selling_price or 0),
            "stuck_capital": float(row.stuck_capital or 0),
            "category": row.category,
            "last_sale_date": str(row.last_sale_date) if row.last_sale_date else "Never",
            "days_since_last_sale": row.days_since_last_sale or 999,
            "recommendation": "Discount" if row.stock_level < 10 else "Clearance Sale" if float(row.stuck_capital or 0) > 10000 else "Monitor"
        }
        for row in result.fetchall()
    ]


# ============================================================
# ABC ANALYSIS
# ============================================================

@router.get("/abc-analysis", response_model=Dict[str, Any])
async def get_abc_analysis(
    period_days: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ABC Analysis - Pareto classification of products by revenue contribution
    A: Top 20% products contributing ~80% revenue
    B: Next 30% products contributing ~15% revenue
    C: Remaining 50% products contributing ~5% revenue
    """
    query = text("""
        WITH product_revenue AS (
            SELECT 
                p.id,
                p.name,
                p.sku,
                p.stock_level,
                p.cost_price,
                p.selling_price,
                COALESCE(pc.name, 'Uncategorized') as category,
                COALESCE(SUM(si.line_total), 0) as revenue,
                COALESCE(SUM(si.quantity), 0) as units_sold
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN sale_items si ON p.id = si.product_id 
                AND si.created_at >= CURRENT_DATE - :period_days * INTERVAL '1 day'
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.sku, p.stock_level, p.cost_price, p.selling_price, pc.name
        ),
        ranked AS (
            SELECT 
                *,
                SUM(revenue) OVER () as total_revenue,
                SUM(revenue) OVER (ORDER BY revenue DESC) as cumulative_revenue,
                ROW_NUMBER() OVER (ORDER BY revenue DESC) as rank,
                COUNT(*) OVER () as total_products
            FROM product_revenue
        ),
        classified AS (
            SELECT 
                *,
                cumulative_revenue / NULLIF(total_revenue, 0) * 100 as cumulative_percent,
                CASE 
                    WHEN cumulative_revenue / NULLIF(total_revenue, 0) <= 0.80 THEN 'A'
                    WHEN cumulative_revenue / NULLIF(total_revenue, 0) <= 0.95 THEN 'B'
                    ELSE 'C'
                END as abc_class
            FROM ranked
        )
        SELECT 
            abc_class,
            COUNT(*) as product_count,
            SUM(revenue) as total_revenue,
            SUM(units_sold) as total_units,
            SUM(stock_level * cost_price) as stock_value,
            AVG(revenue) as avg_revenue_per_product
        FROM classified
        GROUP BY abc_class
        ORDER BY abc_class
    """)
    
    result = db.execute(query, {"period_days": period_days})
    rows = result.fetchall()
    
    classes = {}
    total_revenue = sum(float(row.total_revenue or 0) for row in rows)
    
    for row in rows:
        classes[row.abc_class] = {
            "product_count": row.product_count,
            "revenue": float(row.total_revenue or 0),
            "revenue_percent": round(float(row.total_revenue or 0) / total_revenue * 100, 1) if total_revenue > 0 else 0,
            "units_sold": row.total_units or 0,
            "stock_value": float(row.stock_value or 0),
            "avg_revenue_per_product": round(float(row.avg_revenue_per_product or 0), 2)
        }
    
    # Ensure all classes exist
    for c in ['A', 'B', 'C']:
        if c not in classes:
            classes[c] = {
                "product_count": 0, "revenue": 0, "revenue_percent": 0,
                "units_sold": 0, "stock_value": 0, "avg_revenue_per_product": 0
            }
    
    return {
        "period_days": period_days,
        "total_revenue": total_revenue,
        "classes": classes,
        "insights": [
            f"Class A ({classes['A']['product_count']} products) generates {classes['A']['revenue_percent']:.0f}% of revenue",
            f"Class C ({classes['C']['product_count']} products) may need review or clearance",
            f"Stock value in Class C: ₹{classes['C']['stock_value']:,.0f}"
        ]
    }


@router.get("/abc-products", response_model=List[Dict[str, Any]])
async def get_abc_products(
    abc_class: str = Query("A", regex="^[ABC]$"),
    period_days: int = Query(90, ge=30, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get products by ABC classification"""
    query = text("""
        WITH product_revenue AS (
            SELECT 
                p.id,
                p.name,
                p.sku,
                p.stock_level,
                p.cost_price,
                p.selling_price,
                COALESCE(pc.name, 'Uncategorized') as category,
                COALESCE(SUM(si.line_total), 0) as revenue,
                COALESCE(SUM(si.quantity), 0) as units_sold
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN sale_items si ON p.id = si.product_id 
                AND si.created_at >= CURRENT_DATE - :period_days * INTERVAL '1 day'
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.sku, p.stock_level, p.cost_price, p.selling_price, pc.name
        ),
        ranked AS (
            SELECT 
                *,
                SUM(revenue) OVER () as total_revenue,
                SUM(revenue) OVER (ORDER BY revenue DESC) as cumulative_revenue
            FROM product_revenue
        ),
        classified AS (
            SELECT 
                *,
                CASE 
                    WHEN cumulative_revenue / NULLIF(total_revenue, 0) <= 0.80 THEN 'A'
                    WHEN cumulative_revenue / NULLIF(total_revenue, 0) <= 0.95 THEN 'B'
                    ELSE 'C'
                END as abc_class
            FROM ranked
        )
        SELECT * FROM classified
        WHERE abc_class = :abc_class
        ORDER BY revenue DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        "period_days": period_days,
        "abc_class": abc_class,
        "limit": limit
    })
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "sku": row.sku,
            "category": row.category,
            "stock_level": row.stock_level,
            "cost_price": float(row.cost_price or 0),
            "selling_price": float(row.selling_price or 0),
            "revenue": float(row.revenue or 0),
            "units_sold": row.units_sold or 0,
            "abc_class": row.abc_class
        }
        for row in result.fetchall()
    ]


# ============================================================
# STOCK TURNOVER
# ============================================================

@router.get("/turnover", response_model=Dict[str, Any])
async def get_inventory_turnover(
    period_days: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate inventory turnover metrics
    Turnover = Cost of Goods Sold / Average Inventory
    Higher turnover = faster selling inventory
    """
    query = text("""
        WITH category_turnover AS (
            SELECT 
                COALESCE(pc.name, 'Uncategorized') as category,
                SUM(si.quantity * p.cost_price) as cogs,
                AVG(p.stock_level * p.cost_price) as avg_inventory,
                SUM(si.quantity) as units_sold,
                AVG(p.stock_level) as avg_stock
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN sale_items si ON p.id = si.product_id 
                AND si.created_at >= CURRENT_DATE - :period_days * INTERVAL '1 day'
            WHERE p.is_active = true
            GROUP BY pc.name
        )
        SELECT 
            category,
            cogs,
            avg_inventory,
            units_sold,
            avg_stock,
            CASE 
                WHEN avg_inventory > 0 THEN ROUND((cogs / avg_inventory)::DECIMAL, 2)
                ELSE 0 
            END as turnover_ratio,
            CASE 
                WHEN cogs > 0 AND avg_inventory > 0 
                THEN ROUND((:period_days / (cogs / avg_inventory))::DECIMAL, 1)
                ELSE NULL 
            END as days_of_inventory
        FROM category_turnover
        WHERE cogs > 0
        ORDER BY turnover_ratio DESC
    """)
    
    result = db.execute(query, {"period_days": period_days})
    rows = result.fetchall()
    
    categories = [
        {
            "category": row.category,
            "cogs": float(row.cogs or 0),
            "avg_inventory": float(row.avg_inventory or 0),
            "units_sold": row.units_sold or 0,
            "turnover_ratio": float(row.turnover_ratio or 0),
            "days_of_inventory": float(row.days_of_inventory) if row.days_of_inventory else None
        }
        for row in rows
    ]
    
    # Calculate overall metrics
    total_cogs = sum(c["cogs"] for c in categories)
    total_inventory = sum(c["avg_inventory"] for c in categories)
    overall_turnover = total_cogs / total_inventory if total_inventory > 0 else 0
    
    return {
        "period_days": period_days,
        "overall": {
            "total_cogs": total_cogs,
            "avg_inventory_value": total_inventory,
            "turnover_ratio": round(overall_turnover, 2),
            "days_of_inventory": round(period_days / overall_turnover, 1) if overall_turnover > 0 else None
        },
        "by_category": categories,
        "insights": [
            f"Overall inventory turns {overall_turnover:.1f}x in {period_days} days",
            f"Best performing: {categories[0]['category']}" if categories else "No data",
            f"Slowest: {categories[-1]['category']}" if len(categories) > 1 else "N/A"
        ]
    }
