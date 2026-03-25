"""
Monitoring Dashboard - Prometheus Export Router
Exposes metrics for visualization in Grafana
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api.db import get_db
from app.api.db.models import Invoice, Message, CommunityListing, Sale
from app.api.middleware.rate_limiter import rate_limiter
from app.api.services.cache_service import cache

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/metrics/prometheus")
async def prometheus_metrics(db: Session = Depends(get_db)):
    """
    Prometheus-compatible metrics endpoint
    Use with Grafana for visualization
    """
    
    # Business metrics
    total_invoices = db.query(Invoice).count()
    paid_invoices = db.query(Invoice).filter(Invoice.payment_status == "paid").count()
    overdue_invoices = db.query(Invoice).filter(Invoice.payment_status == "overdue").count()
    
    total_messages = db.query(Message).count()
    unread_messages = db.query(Message).filter(Message.read_at.is_(None)).count()
    
    active_listings = db.query(CommunityListing).filter(
        CommunityListing.status == "active"
    ).count()
    
    # Rate limiter stats
    rate_stats = rate_limiter.get_stats()
    
    # Cache stats
    cache_stats = cache.get_stats()
    
    # Generate Prometheus format
    metrics = f"""
# HELP rdios_invoices_total Total number of invoices in system
# TYPE rdios_invoices_total gauge
rdios_invoices_total {total_invoices}

# HELP rdios_invoices_paid Number of paid invoices
# TYPE rdios_invoices_paid gauge
rd ios_invoices_paid {paid_invoices}

# HELP rdios_invoices_overdue Number of overdue invoices
# TYPE rdios_invoices_overdue gauge
rdios_invoices_overdue {overdue_invoices}

# HELP rdios_messages_total Total messages in system
# TYPE rdios_messages_total gauge
rdios_messages_total {total_messages}

# HELP rdios_messages_unread Unread messages
# TYPE rdios_messages_unread gauge
rdios_messages_unread {unread_messages}

# HELP rdios_community_listings_active Active community listings
# TYPE rdios_community_listings_active gauge
rdios_community_listings_active {active_listings}

# HELP rdios_whatsapp_sent_today WhatsApp messages sent today
# TYPE rdios_whatsapp_sent_today counter
rdios_whatsapp_sent_today {rate_stats['whatsapp']['sent_today']}

# HELP rdios_whatsapp_cost_today WhatsApp cost today in INR
# TYPE rdios_whatsapp_cost_today gauge
rdios_whatsapp_cost_today {rate_stats['whatsapp']['cost_today']}

# HELP rdios_whatsapp_budget_remaining Remaining WhatsApp budget in INR
# TYPE rdios_whatsapp_budget_remaining gauge
rdios_whatsapp_budget_remaining {rate_stats['whatsapp']['remaining_budget']}

# HELP rdios_cache_enabled Cache system status
# TYPE rdios_cache_enabled gauge
rdios_cache_enabled {1 if cache_stats.get('enabled') else 0}

# HELP rdios_cache_hit_rate Cache hit rate percentage
# TYPE rdios_cache_hit_rate gauge
rdios_cache_hit_rate {cache_stats.get('hit_rate', 0) if cache_stats.get('enabled') else 0}
    """.strip()
    
    return metrics, {"Content-Type": "text/plain; version=0.0.4"}

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive stats for monitoring dashboard
    Returns JSON for custom dashboards
    """
    
    # Time ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Invoice stats
    invoice_stats = {
        "total": db.query(Invoice).count(),
        "paid": db.query(Invoice).filter(Invoice.payment_status == "paid").count(),
        "pending": db.query(Invoice).filter(Invoice.payment_status == "pending").count(),
        "partial": db.query(Invoice).filter(Invoice.payment_status == "partial").count(),
        "overdue": db.query(Invoice).filter(Invoice.payment_status == "overdue").count(),
        "revenue_total": db.query(func.sum(Invoice.total_amount)).scalar() or 0,
        "revenue_outstanding": db.query(func.sum(Invoice.amount_due)).filter(
            Invoice.payment_status.in_(["pending", "partial", "overdue"])
        ).scalar() or 0
    }
    
    # Message stats
    message_stats = {
        "total": db.query(Message).count(),
        "unread": db.query(Message).filter(Message.read_at.is_(None)).count(),
        "by_channel": {},
        "today": db.query(Message).filter(
            func.date(Message.sent_at) == today
        ).count()
    }
    
    # Community stats
    community_stats = {
        "active_listings": db.query(CommunityListing).filter(
            CommunityListing.status == "active"
        ).count(),
        "matched_listings": db.query(CommunityListing).filter(
            CommunityListing.status == "matched"
        ).count()
    }
    
    # Rate limiter stats
    rate_stats = rate_limiter.get_stats()
    
    # Cache stats
    cache_stats = cache.get_stats()
    
    # System health
    system_health = {
        "cache_enabled": cache_stats.get('enabled', False),
        "cache_connected": cache_stats.get('connected', False),
        "cache_hit_rate": cache_stats.get('hit_rate', 0),
        "whatsapp_budget_remaining": rate_stats['whatsapp']['remaining_budget'],
        "whatsapp_messages_remaining": rate_stats['whatsapp']['remaining_count']
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "invoices": invoice_stats,
        "messages": message_stats,
        "community": community_stats,
        "rate_limiting": rate_stats,
        "cache": cache_stats,
        "health": system_health
    }

@router.get("/dashboard/trends")
async def get_trends(days: int = 30, db: Session = Depends(get_db)):
    """
    Get trend data for charts (revenue, messages, invoices over time)
    """
    from datetime import datetime, timedelta
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Daily invoice trends
    invoice_trends = db.query(
        func.date(Invoice.created_at).label('date'),
        func.count(Invoice.id).label('count'),
        func.sum(Invoice.total_amount).label('revenue')
    ).filter(
        func.date(Invoice.created_at) >= start_date
    ).group_by(func.date(Invoice.created_at)).all()
    
    # Daily message trends
    message_trends = db.query(
        func.date(Message.sent_at).label('date'),
        func.count(Message.id).label('count')
    ).filter(
        func.date(Message.sent_at) >= start_date
    ).group_by(func.date(Message.sent_at)).all()
    
    return {
        "period": f"{start_date} to {end_date}",
        "invoices": [
            {
                "date": str(row.date),
                "count": row.count,
                "revenue": float(row.revenue or 0)
            }
            for row in invoice_trends
        ],
        "messages": [
            {
                "date": str(row.date),
                "count": row.count
            }
            for row in message_trends
        ]
    }
