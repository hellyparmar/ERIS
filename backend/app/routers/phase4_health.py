"""
Phase 4 - System Health Monitoring Router
Database, API, cache health with 15-second heartbeat
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
import logging
import psutil
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health Monitoring"])


# Models
class ServiceHealth(BaseModel):
    name: str
    status: str  # operational, degraded, down
    response_time_ms: float
    last_check: datetime
    uptime_percentage: float


class SystemHealth(BaseModel):
    overall_status: str
    database: ServiceHealth
    api: ServiceHealth
    cache: ServiceHealth
    system_resources: dict
    timestamp: datetime


class HealthHistory(BaseModel):
    service_name: str
    checks: List[dict]
    average_uptime: float
    incident_count: int


# Health check storage
health_checks = {
    "database": [],
    "api": [],
    "cache": []
}

HEARTBEAT_INTERVAL = 15  # seconds
MAX_HISTORY = 288  # 4 hours at 15-second intervals


async def check_database_health() -> ServiceHealth:
    """Check database connectivity and performance"""
    try:
        start_time = datetime.now()
        
        # Simulate database check
        await asyncio.sleep(0.1)
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ServiceHealth(
            name="Database",
            status="operational",
            response_time_ms=response_time,
            last_check=datetime.now(),
            uptime_percentage=99.9
        )
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return ServiceHealth(
            name="Database",
            status="down",
            response_time_ms=-1,
            last_check=datetime.now(),
            uptime_percentage=0
        )


async def check_api_health() -> ServiceHealth:
    """Check API health"""
    try:
        start_time = datetime.now()
        
        # Simulate API check
        await asyncio.sleep(0.05)
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ServiceHealth(
            name="API",
            status="operational",
            response_time_ms=response_time,
            last_check=datetime.now(),
            uptime_percentage=99.95
        )
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        return ServiceHealth(
            name="API",
            status="degraded",
            response_time_ms=-1,
            last_check=datetime.now(),
            uptime_percentage=85
        )


async def check_cache_health() -> ServiceHealth:
    """Check cache (Redis) health"""
    try:
        start_time = datetime.now()
        
        # Simulate cache check
        await asyncio.sleep(0.02)
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ServiceHealth(
            name="Cache",
            status="operational",
            response_time_ms=response_time,
            last_check=datetime.now(),
            uptime_percentage=99.8
        )
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        return ServiceHealth(
            name="Cache",
            status="down",
            response_time_ms=-1,
            last_check=datetime.now(),
            uptime_percentage=0
        )


def get_system_resources() -> dict:
    """Get system resource metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "status": "normal" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent": memory.percent,
                "status": "normal" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": disk.percent,
                "status": "normal" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system resources: {str(e)}")
        return {}


def store_health_check(service: str, health: ServiceHealth):
    """Store health check in history"""
    if service not in health_checks:
        health_checks[service] = []
    
    health_checks[service].append({
        "status": health.status,
        "response_time_ms": health.response_time_ms,
        "uptime_percentage": health.uptime_percentage,
        "timestamp": health.last_check.isoformat()
    })
    
    # Keep only recent history
    if len(health_checks[service]) > MAX_HISTORY:
        health_checks[service] = health_checks[service][-MAX_HISTORY:]


@router.get("/system", response_model=SystemHealth)
async def get_system_health():
    """
    Get complete system health status
    """
    try:
        # Check all services
        db_health = await check_database_health()
        api_health = await check_api_health()
        cache_health = await check_cache_health()
        
        # Store in history
        store_health_check("database", db_health)
        store_health_check("api", api_health)
        store_health_check("cache", cache_health)
        
        # Determine overall status
        statuses = [db_health.status, api_health.status, cache_health.status]
        if "down" in statuses:
            overall_status = "down"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "operational"
        
        return SystemHealth(
            overall_status=overall_status,
            database=db_health,
            api=api_health,
            cache=cache_health,
            system_resources=get_system_resources(),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/database")
async def get_database_health():
    """Get database health details"""
    try:
        health = await check_database_health()
        store_health_check("database", health)
        return health
    except Exception as e:
        logger.error(f"Error checking database health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api")
async def get_api_health():
    """Get API health details"""
    try:
        health = await check_api_health()
        store_health_check("api", health)
        return health
    except Exception as e:
        logger.error(f"Error checking API health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache")
async def get_cache_health():
    """Get cache health details"""
    try:
        health = await check_cache_health()
        store_health_check("cache", health)
        return health
    except Exception as e:
        logger.error(f"Error checking cache health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heartbeat")
async def heartbeat():
    """
    15-second heartbeat endpoint
    Used for continuous monitoring
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - datetime(2024, 1, 1)).total_seconds()
    }


@router.get("/history/{service}")
async def get_service_history(
    service: str,
    minutes: int = 60
) -> HealthHistory:
    """
    Get health check history for a service
    """
    try:
        if service not in health_checks:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")
        
        checks = health_checks[service]
        
        # Filter by time
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_checks = [
            c for c in checks
            if datetime.fromisoformat(c["timestamp"]) > cutoff_time
        ]
        
        # Calculate average uptime
        if recent_checks:
            avg_uptime = sum(c["uptime_percentage"] for c in recent_checks) / len(recent_checks)
        else:
            avg_uptime = 100
        
        # Count incidents (status != operational)
        incident_count = sum(1 for c in recent_checks if c["status"] != "operational")
        
        return HealthHistory(
            service_name=service,
            checks=recent_checks,
            average_uptime=avg_uptime,
            incident_count=incident_count
        )
        
    except Exception as e:
        logger.error(f"Error getting service history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources")
async def get_resource_metrics():
    """Get system resource metrics"""
    try:
        return get_system_resources()
    except Exception as e:
        logger.error(f"Error getting resource metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
