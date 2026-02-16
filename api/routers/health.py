"""
Health Check Endpoints
Provides system health monitoring for uptime tracking and alerting
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import psutil
import os

from api.db import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """
    Basic health check - fast response
    Use this for load balancer health checks
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "5.0.0",
        "service": "R-DIOS API"
    }

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - validates dependencies
    Returns 503 if not ready to serve traffic
    """
    checks = {}
    all_ready = True
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ready", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "not_ready", "error": str(e)}
        all_ready = False
    
    # Check Redis (if available)
    try:
        from redis import Redis
        redis = Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, socket_timeout=1)
        redis.ping()
        checks["redis"] = {"status": "ready"}
    except:
        checks["redis"] = {"status": "not_configured"}
    
    status_code = 200 if all_ready else 503
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }, status_code

@router.get("/live")
async def liveness_check():
    """
    Liveness check - is the application running?
    Use for Kubernetes liveness probes
    """
    try:
        # Check if we can allocate memory
        test = [i for i in range(1000)]
        
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        }
    except:
        raise HTTPException(status_code=503, detail="Application not responsive")

@router.get("/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """
    Detailed health check with system metrics
    Use for monitoring dashboards
    """
    checks = {}
    
    # Database check
    try:
        start = datetime.now()
        result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        latency = (datetime.now() - start).total_seconds() * 1000
        
        checks["database"] = {
            "status": "ok",
            "latency_ms": round(latency, 2),
            "connection_pool": "healthy"
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Redis check
    try:
        from redis import Redis
        redis = Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, socket_timeout=1)
        info = redis.info()
        checks["redis"] = {
            "status": "ok",
            "used_memory_mb": round(info['used_memory'] / 1024 / 1024, 2),
            "connected_clients": info['connected_clients']
        }
    except:
        checks["redis"] = {
            "status": "not_configured",
            "message": "Redis not available (caching disabled)"
        }
    
    # System metrics
    try:
        checks["system"] = {
            "status": "ok",
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    except:
        checks["system"] = {"status": "unavailable"}
    
    # Determine overall status
    all_critical_ok = checks.get("database", {}).get("status") == "ok"
    overall_status = "healthy" if all_critical_ok else "degraded"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": get_uptime()
    }

@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint
    """
    from api.middleware.rate_limiter import rate_limiter
    
    stats = rate_limiter.get_stats()
    
    metrics = f"""
# HELP whatsapp_messages_sent_today Total WhatsApp messages sent today
# TYPE whatsapp_messages_sent_today counter
whatsapp_messages_sent_today {stats['whatsapp']['sent_today']}

# HELP whatsapp_cost_today Total WhatsApp cost today in INR
# TYPE whatsapp_cost_today gauge
whatsapp_cost_today {stats['whatsapp']['cost_today']}

# HELP whatsapp_budget_remaining Remaining WhatsApp budget today in INR
# TYPE whatsapp_budget_remaining gauge
whatsapp_budget_remaining {stats['whatsapp']['remaining_budget']}

# HELP api_requests_total Total API requests (approximation)
# TYPE api_requests_total counter
api_requests_total {sum(len(v) for v in rate_limiter.usage.values())}
    """.strip()
    
    return metrics, {"Content-Type": "text/plain; version=0.0.4"}

# Helper functions
_start_time = datetime.now()

def get_uptime():
    """Get application uptime in seconds"""
    return (datetime.now() - _start_time).total_seconds()
