"""
Customer Analytics Router - RFM Segmentation, Customer Insights
Uses materialized views for optimal performance
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import logging

from api.db.database import get_db
from api.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics/customers", tags=["Customer Analytics"])


# ============================================================
# RFM SEGMENTATION
# ============================================================

@router.get("/rfm/summary", response_model=Dict[str, Any])
async def get_rfm_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get RFM segmentation summary with segment distribution
    Uses pre-calculated RFM scores when available
    """
    query = text("""
        WITH customer_rfm AS (
            SELECT 
                c.id,
                c.name,
                c.last_purchase_date,
                c.purchase_count,
                c.total_spent,
                
                -- Recency Score (1-5)
                CASE 
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '7 days' THEN 5
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' THEN 4
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '90 days' THEN 3
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '180 days' THEN 2
                    ELSE 1
                END as recency_score,
                
                -- Frequency Score (1-5)
                CASE 
                    WHEN c.purchase_count >= 20 THEN 5
                    WHEN c.purchase_count >= 10 THEN 4
                    WHEN c.purchase_count >= 5 THEN 3
                    WHEN c.purchase_count >= 2 THEN 2
                    ELSE 1
                END as frequency_score,
                
                -- Monetary Score (1-5)
                CASE 
                    WHEN c.total_spent >= 50000 THEN 5
                    WHEN c.total_spent >= 20000 THEN 4
                    WHEN c.total_spent >= 10000 THEN 3
                    WHEN c.total_spent >= 5000 THEN 2
                    ELSE 1
                END as monetary_score
                
            FROM customers c
            WHERE c.purchase_count > 0
        ),
        segmented AS (
            SELECT 
                *,
                CASE 
                    WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
                    WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 4 THEN 'Loyal'
                    WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New'
                    WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Potential Loyalist'
                    WHEN recency_score <= 2 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'At Risk'
                    WHEN recency_score <= 2 AND frequency_score <= 2 AND monetary_score >= 3 THEN 'Cant Lose'
                    WHEN recency_score <= 2 THEN 'Hibernating'
                    ELSE 'Regular'
                END as segment
            FROM customer_rfm
        )
        SELECT 
            segment,
            COUNT(*) as customer_count,
            ROUND(AVG(total_spent), 2) as avg_lifetime_value,
            ROUND(AVG(purchase_count), 1) as avg_purchases,
            SUM(total_spent) as total_revenue,
            ROUND(AVG(recency_score + frequency_score + monetary_score) / 3, 2) as avg_rfm_score
        FROM segmented
        GROUP BY segment
        ORDER BY avg_rfm_score DESC
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    total_customers = sum(row.customer_count for row in rows)
    total_revenue = sum(float(row.total_revenue or 0) for row in rows)
    
    segments = [
        {
            "segment": row.segment,
            "customer_count": row.customer_count,
            "percentage": round(row.customer_count / total_customers * 100, 1) if total_customers > 0 else 0,
            "avg_lifetime_value": float(row.avg_lifetime_value or 0),
            "avg_purchases": float(row.avg_purchases or 0),
            "total_revenue": float(row.total_revenue or 0),
            "revenue_percentage": round(float(row.total_revenue or 0) / total_revenue * 100, 1) if total_revenue > 0 else 0,
            "avg_rfm_score": float(row.avg_rfm_score or 0)
        }
        for row in rows
    ]
    
    return {
        "total_customers": total_customers,
        "total_revenue": total_revenue,
        "segments": segments,
        "segment_actions": {
            "Champions": "Reward them. They can be early adopters for new products.",
            "Loyal": "Upsell higher value products. Ask for reviews.",
            "Potential Loyalist": "Offer loyalty program, recommend other products.",
            "New": "Provide onboarding support, start building relationship.",
            "At Risk": "Send personalized reactivation campaigns, offer discounts.",
            "Cant Lose": "Win them back with special offers, personal outreach.",
            "Hibernating": "Reconnect with relevant offers, survey for feedback.",
            "Regular": "Create brand awareness, offer free trials."
        }
    }


@router.get("/rfm/customers", response_model=List[Dict[str, Any]])
async def get_rfm_customers(
    segment: Optional[str] = Query(None, description="Filter by segment name"),
    min_rfm_score: Optional[int] = Query(None, ge=3, le=15),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get customers with their RFM scores and segments"""
    
    conditions = ["c.purchase_count > 0"]
    params = {"limit": limit}
    
    if segment:
        # Will filter after calculation
        pass
    
    query = text("""
        WITH customer_rfm AS (
            SELECT 
                c.id,
                c.name,
                c.email,
                c.phone,
                c.city,
                c.last_purchase_date,
                c.purchase_count,
                c.total_spent,
                c.outstanding_amount,
                
                CASE 
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '7 days' THEN 5
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' THEN 4
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '90 days' THEN 3
                    WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '180 days' THEN 2
                    ELSE 1
                END as recency_score,
                
                CASE 
                    WHEN c.purchase_count >= 20 THEN 5
                    WHEN c.purchase_count >= 10 THEN 4
                    WHEN c.purchase_count >= 5 THEN 3
                    WHEN c.purchase_count >= 2 THEN 2
                    ELSE 1
                END as frequency_score,
                
                CASE 
                    WHEN c.total_spent >= 50000 THEN 5
                    WHEN c.total_spent >= 20000 THEN 4
                    WHEN c.total_spent >= 10000 THEN 3
                    WHEN c.total_spent >= 5000 THEN 2
                    ELSE 1
                END as monetary_score
                
            FROM customers c
            WHERE c.purchase_count > 0
        )
        SELECT 
            *,
            recency_score + frequency_score + monetary_score as total_rfm_score,
            CONCAT(recency_score, frequency_score, monetary_score) as rfm_code,
            CASE 
                WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
                WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 4 THEN 'Loyal'
                WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New'
                WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Potential Loyalist'
                WHEN recency_score <= 2 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'At Risk'
                WHEN recency_score <= 2 AND frequency_score <= 2 AND monetary_score >= 3 THEN 'Cant Lose'
                WHEN recency_score <= 2 THEN 'Hibernating'
                ELSE 'Regular'
            END as segment
        FROM customer_rfm
        ORDER BY total_rfm_score DESC, total_spent DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, params)
    customers = []
    
    for row in result.fetchall():
        # Filter by segment if specified
        if segment and row.segment.lower() != segment.lower():
            continue
        
        # Filter by min score if specified
        if min_rfm_score and row.total_rfm_score < min_rfm_score:
            continue
            
        customers.append({
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "city": row.city,
            "last_purchase_date": str(row.last_purchase_date) if row.last_purchase_date else None,
            "purchase_count": row.purchase_count,
            "total_spent": float(row.total_spent or 0),
            "outstanding_amount": float(row.outstanding_amount or 0),
            "rfm_scores": {
                "recency": row.recency_score,
                "frequency": row.frequency_score,
                "monetary": row.monetary_score,
                "total": row.total_rfm_score
            },
            "rfm_code": row.rfm_code,
            "segment": row.segment
        })
    
    return customers[:limit]


@router.get("/rfm/distribution", response_model=Dict[str, Any])
async def get_rfm_distribution(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get RFM score distribution for visualization"""
    
    query = text("""
        WITH customer_scores AS (
            SELECT 
                CASE 
                    WHEN last_purchase_date >= CURRENT_DATE - INTERVAL '7 days' THEN 5
                    WHEN last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' THEN 4
                    WHEN last_purchase_date >= CURRENT_DATE - INTERVAL '90 days' THEN 3
                    WHEN last_purchase_date >= CURRENT_DATE - INTERVAL '180 days' THEN 2
                    ELSE 1
                END as recency_score,
                
                CASE 
                    WHEN purchase_count >= 20 THEN 5
                    WHEN purchase_count >= 10 THEN 4
                    WHEN purchase_count >= 5 THEN 3
                    WHEN purchase_count >= 2 THEN 2
                    ELSE 1
                END as frequency_score,
                
                CASE 
                    WHEN total_spent >= 50000 THEN 5
                    WHEN total_spent >= 20000 THEN 4
                    WHEN total_spent >= 10000 THEN 3
                    WHEN total_spent >= 5000 THEN 2
                    ELSE 1
                END as monetary_score
            FROM customers
            WHERE purchase_count > 0
        )
        SELECT 
            'recency' as dimension,
            recency_score as score,
            COUNT(*) as count
        FROM customer_scores
        GROUP BY recency_score
        
        UNION ALL
        
        SELECT 
            'frequency' as dimension,
            frequency_score as score,
            COUNT(*) as count
        FROM customer_scores
        GROUP BY frequency_score
        
        UNION ALL
        
        SELECT 
            'monetary' as dimension,
            monetary_score as score,
            COUNT(*) as count
        FROM customer_scores
        GROUP BY monetary_score
        
        ORDER BY dimension, score
    """)
    
    result = db.execute(query)
    
    distribution = {"recency": {}, "frequency": {}, "monetary": {}}
    for row in result.fetchall():
        distribution[row.dimension][str(row.score)] = row.count
    
    return {
        "distribution": distribution,
        "score_meanings": {
            "5": "Highest/Best",
            "4": "High",
            "3": "Medium",
            "2": "Low",
            "1": "Lowest/Needs Attention"
        }
    }


# ============================================================
# CUSTOMER INSIGHTS
# ============================================================

@router.get("/top-spenders", response_model=List[Dict[str, Any]])
async def get_top_spenders(
    period_days: Optional[int] = Query(None, ge=7, le=365, description="Limit to recent period"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get top spending customers"""
    
    if period_days:
        query = text("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.phone,
                c.city,
                COUNT(DISTINCT s.id) as orders,
                SUM(s.total_amount) as total_spent,
                AVG(s.total_amount) as avg_order_value,
                MAX(s.sale_date) as last_purchase
            FROM customers c
            JOIN sales s ON c.id = s.customer_id
            WHERE s.sale_date >= CURRENT_DATE - :period_days * INTERVAL '1 day'
            GROUP BY c.id, c.name, c.email, c.phone, c.city
            ORDER BY total_spent DESC
            LIMIT :limit
        """)
        params = {"period_days": period_days, "limit": limit}
    else:
        query = text("""
            SELECT 
                id, name, email, phone, city,
                purchase_count as orders,
                total_spent,
                total_spent / NULLIF(purchase_count, 0) as avg_order_value,
                last_purchase_date as last_purchase
            FROM customers
            WHERE total_spent > 0
            ORDER BY total_spent DESC
            LIMIT :limit
        """)
        params = {"limit": limit}
    
    result = db.execute(query, params)
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "city": row.city,
            "orders": row.orders,
            "total_spent": float(row.total_spent or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2),
            "last_purchase": str(row.last_purchase) if row.last_purchase else None
        }
        for row in result.fetchall()
    ]


@router.get("/at-risk", response_model=List[Dict[str, Any]])
async def get_at_risk_customers(
    days_since_purchase: int = Query(60, ge=30, le=365),
    min_lifetime_value: float = Query(5000, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get at-risk customers who haven't purchased recently but have high lifetime value
    Prime candidates for re-engagement campaigns
    """
    query = text("""
        SELECT 
            c.id,
            c.name,
            c.email,
            c.phone,
            c.city,
            c.last_purchase_date,
            CURRENT_DATE - c.last_purchase_date as days_since_purchase,
            c.purchase_count,
            c.total_spent,
            c.total_spent / NULLIF(c.purchase_count, 0) as avg_order_value,
            c.outstanding_amount
        FROM customers c
        WHERE c.last_purchase_date < CURRENT_DATE - :days_since_purchase * INTERVAL '1 day'
            AND c.total_spent >= :min_lifetime_value
        ORDER BY c.total_spent DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        "days_since_purchase": days_since_purchase,
        "min_lifetime_value": min_lifetime_value,
        "limit": limit
    })
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "city": row.city,
            "last_purchase_date": str(row.last_purchase_date) if row.last_purchase_date else None,
            "days_since_purchase": row.days_since_purchase or 0,
            "purchase_count": row.purchase_count,
            "total_spent": float(row.total_spent or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2),
            "outstanding_amount": float(row.outstanding_amount or 0),
            "win_back_priority": "High" if float(row.total_spent or 0) > 20000 else "Medium"
        }
        for row in result.fetchall()
    ]


@router.get("/upcoming-birthdays", response_model=List[Dict[str, Any]])
async def get_upcoming_birthdays(
    days_ahead: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get customers with birthdays in the next N days for sending offers"""
    
    query = text("""
        SELECT 
            id, name, email, phone, city,
            date_of_birth,
            total_spent,
            purchase_count,
            EXTRACT(DAY FROM date_of_birth) as birth_day,
            EXTRACT(MONTH FROM date_of_birth) as birth_month
        FROM customers
        WHERE date_of_birth IS NOT NULL
            AND (
                (EXTRACT(MONTH FROM date_of_birth) = EXTRACT(MONTH FROM CURRENT_DATE)
                 AND EXTRACT(DAY FROM date_of_birth) >= EXTRACT(DAY FROM CURRENT_DATE)
                 AND EXTRACT(DAY FROM date_of_birth) <= EXTRACT(DAY FROM CURRENT_DATE) + :days_ahead)
                OR
                (EXTRACT(MONTH FROM date_of_birth) = EXTRACT(MONTH FROM CURRENT_DATE) + 1
                 AND EXTRACT(DAY FROM date_of_birth) <= :days_ahead - (
                    EXTRACT(DAY FROM (DATE_TRUNC('MONTH', CURRENT_DATE) + INTERVAL '1 MONTH' - INTERVAL '1 day')) 
                    - EXTRACT(DAY FROM CURRENT_DATE)
                 ))
            )
        ORDER BY birth_month, birth_day
        LIMIT 50
    """)
    
    result = db.execute(query, {"days_ahead": days_ahead})
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "city": row.city,
            "birthday": f"{int(row.birth_day):02d}/{int(row.birth_month):02d}",
            "total_spent": float(row.total_spent or 0),
            "purchase_count": row.purchase_count or 0,
            "suggested_discount": "20%" if float(row.total_spent or 0) > 10000 else "15%" if float(row.total_spent or 0) > 5000 else "10%"
        }
        for row in result.fetchall()
    ]
