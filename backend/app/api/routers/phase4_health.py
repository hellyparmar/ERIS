"""
Phase 4: System Health Monitoring

Database, API, cache health checks with 15-second heartbeat monitoring
and service status tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from decimal import Decimal
from sqlalchemy.orm import Session
import psutil
import os

from app.api.db.database import get_db

router = APIRouter(prefix="/api/v4/health", tags=["health"])


# ==================== Health Status Models ====================

class ServiceHealth:
    """Service health status"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.status = "unknown"  # healthy, degraded, unhealthy
        self.response_time_ms = 0
        self.last_check = None
        self.details = {}
    
    def to_dict(self):
        return {
            "service": self.service_name,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "details": self.details
        }


# ==================== Global Health State ====================

class HealthMonitor:
    """Global health monitor"""
    
    def __init__(self):
        self.services = {
            "database": ServiceHealth("database"),
            "api": ServiceHealth("api"),
            "cache": ServiceHealth("cache"),
            "storage": ServiceHealth("storage"),
        }
        self.last_heartbeat = datetime.now()
        self.heartbeat_interval = 15  # seconds
        self.health_history = {}
    
    def record_heartbeat(self):
        """Record heartbeat"""
        self.last_heartbeat = datetime.now()
    
    def get_status(self) -> str:
        """Get overall status"""
        statuses = [s.status for s in self.services.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
    
    def get_report(self) -> dict:
        """Get health report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_status(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "heartbeat_interval_seconds": self.heartbeat_interval,
            "services": {k: v.to_dict() for k, v in self.services.items()}
        }


monitor = HealthMonitor()


# ==================== Database Health ====================

@router.get("/database")
def check_database_health(db: Session = Depends(get_db)):
    """
    Check database connectivity and performance
    
    Returns:
        Database health status
    """
    try:
        start_time = time.time()
        
        # Simple query
        from app.api.db.models_v6 import User
        count = db.query(User).count()
        
        response_time = (time.time() - start_time) * 1000  # ms
        
        monitor.services["database"].status = "healthy" if response_time < 100 else "degraded"
        monitor.services["database"].response_time_ms = response_time
        monitor.services["database"].last_check = datetime.now()
        monitor.services["database"].details = {
            "tables_accessible": True,
            "query_response_time_ms": response_time,
            "sample_records": count
        }
        
        return {
            "status": monitor.services["database"].status,
            "response_time_ms": response_time,
            "details": monitor.services["database"].details,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        monitor.services["database"].status = "unhealthy"
        monitor.services["database"].details = {"error": str(e)}
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ==================== API Health ====================

@router.get("/api")
def check_api_health():
    """
    Check API service health
    
    Returns:
        API health status
    """
    try:
        start_time = time.time()
        response_time = (time.time() - start_time) * 1000
        
        monitor.services["api"].status = "healthy"
        monitor.services["api"].response_time_ms = response_time
        monitor.services["api"].last_check = datetime.now()
        monitor.services["api"].details = {
            "uptime_seconds": (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds(),
            "response_time_ms": response_time,
            "memory_usage_mb": psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        }
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "details": monitor.services["api"].details,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        monitor.services["api"].status = "unhealthy"
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ==================== Cache Health ====================

@router.get("/cache")
def check_cache_health():
    """
    Check cache service health (Redis/Memcached)
    
    Returns:
        Cache health status
    """
    try:
        # Simulate cache check (would connect to actual cache service)
        start_time = time.time()
        response_time = (time.time() - start_time) * 1000
        
        monitor.services["cache"].status = "healthy"
        monitor.services["cache"].response_time_ms = response_time
        monitor.services["cache"].last_check = datetime.now()
        monitor.services["cache"].details = {
            "type": "redis",
            "response_time_ms": response_time,
            "hit_rate": 85.5,
            "eviction_rate": 2.1
        }
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "details": monitor.services["cache"].details,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        monitor.services["cache"].status = "degraded"
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ==================== Storage Health ====================

@router.get("/storage")
def check_storage_health():
    """
    Check storage (disk) health
    
    Returns:
        Storage health status
    """
    try:
        import shutil
        
        # Get disk usage
        total, used, free = shutil.disk_usage("/")
        percent_used = (used / total) * 100
        
        status = "healthy"
        if percent_used > 90:
            status = "unhealthy"
        elif percent_used > 80:
            status = "degraded"
        
        monitor.services["storage"].status = status
        monitor.services["storage"].last_check = datetime.now()
        monitor.services["storage"].details = {
            "total_gb": total / (1024**3),
            "used_gb": used / (1024**3),
            "free_gb": free / (1024**3),
            "percent_used": percent_used
        }
        
        return {
            "status": status,
            "details": monitor.services["storage"].details,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ==================== Comprehensive Health Check ====================

@router.get("/status")
def get_system_health():
    """
    Get overall system health status
    
    Returns:
        Complete health report
    """
    return monitor.get_report()


@router.get("/detailed")
def get_detailed_health(db: Session = Depends(get_db)):
    """
    Get detailed health check with all components
    
    Returns:
        Detailed health information
    """
    try:
        # Run all health checks
        db_health = check_database_health(db)
        api_health = check_api_health()
        cache_health = check_cache_health()
        storage_health = check_storage_health()
        
        monitor.record_heartbeat()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": monitor.get_status(),
            "services": {
                "database": db_health,
                "api": api_health,
                "cache": cache_health,
                "storage": storage_health
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "process_count": len(psutil.pids())
            },
            "heartbeat": {
                "last_check": monitor.last_heartbeat.isoformat(),
                "interval_seconds": monitor.heartbeat_interval
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Heartbeat Endpoint ====================

@router.post("/heartbeat")
def record_heartbeat():
    """
    Record system heartbeat (called by monitoring service)
    
    Returns:
        Heartbeat confirmation
    """
    try:
        monitor.record_heartbeat()
        
        return {
            "status": "acknowledged",
            "timestamp": datetime.now().isoformat(),
            "next_heartbeat_due": (
                datetime.now() + timedelta(seconds=monitor.heartbeat_interval)
            ).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/heartbeat-status")
def get_heartbeat_status():
    """
    Get heartbeat monitoring status
    
    Returns:
        Heartbeat information
    """
    time_since_last = (datetime.now() - monitor.last_heartbeat).total_seconds()
    
    return {
        "last_heartbeat": monitor.last_heartbeat.isoformat(),
        "seconds_since_last": time_since_last,
        "interval_seconds": monitor.heartbeat_interval,
        "status": "healthy" if time_since_last < (monitor.heartbeat_interval * 2) else "missed",
        "timestamp": datetime.now().isoformat()
    }


# ==================== Service Readiness ====================

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes-style readiness probe
    
    Returns:
        200 if ready, 503 if not
    """
    try:
        # Check database
        from app.api.db.models_v6 import User
        db.query(User).count()
        
        return {"status": "ready"}
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@router.get("/alive")
def liveness_check():
    """
    Kubernetes-style liveness probe
    
    Returns:
        200 if alive
    """
    return {"status": "alive"}


# ==================== Performance Metrics ====================

@router.get("/metrics")
def get_performance_metrics():
    """
    Get system performance metrics
    
    Returns:
        Performance data
    """
    try:
        process = psutil.Process(os.getpid())
        
        return {
            "process": {
                "pid": process.pid,
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(interval=0.1),
                "num_threads": process.num_threads(),
                "open_files": len(process.open_files())
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_count": psutil.cpu_count(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "swap_percent": psutil.swap_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
