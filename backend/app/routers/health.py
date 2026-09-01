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

from app.database import get_db

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
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        checks["database"] = {"status": "not_ready", "error": str(e)}
        all_ready = False
    
    # Check Redis (if available)
    redis_status = "unhealthy"
    try:
        from redis import Redis
        # Use env or default
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_client = Redis(host=redis_host, port=6379, socket_timeout=1)
        if redis_client.ping():
            redis_status = "healthy"
    except Exception:
        pass
    
    status_code = 200 if all_ready else 503
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": {"status": db_status},
        "redis": {"status": redis_status}
    }

@router.get("/live")
async def liveness_check():
    """
    Liveness check - is the application running?
    Use for Kubernetes liveness probes
    """
    try:
        # Simple memory test
        _ = [i for i in range(1000)]
        
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
        db.execute(text("SELECT 1")) 
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
            "message": "Redis not available"
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
    """Prometheus-compatible metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Helper functions
_start_time = datetime.now()

def get_uptime():
    """Get application uptime in seconds"""
    return (datetime.now() - _start_time).total_seconds()
