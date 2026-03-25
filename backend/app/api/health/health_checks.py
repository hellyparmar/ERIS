"""
Health Check System for Enterprise Retail Intelligence System

Provides comprehensive health monitoring including:
- Individual service health checks
- Database connectivity checks
- Cache/Redis connectivity
- External service status
- Health aggregation
- Readiness and liveness probes
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth:
    """Health check result for a single service"""
    
    def __init__(self, name: str, status: HealthStatus, response_time_ms: float,
                 message: str = "", details: Optional[Dict[str, Any]] = None):
        self.name = name
        self.status = status
        self.response_time_ms = response_time_ms
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


class HealthCheckCache:
    """Cache for health check results with TTL"""
    
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}  # (result, timestamp)
    
    def get(self, key: str) -> Optional[ServiceHealth]:
        """Get cached health check result"""
        if key not in self.cache:
            return None
        
        result, timestamp = self.cache[key]
        if datetime.utcnow() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self.cache[key]
            return None
        
        return result
    
    def set(self, key: str, value: ServiceHealth):
        """Cache health check result"""
        self.cache[key] = (value, datetime.utcnow())
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()


class HealthCheckManager:
    """Central manager for all health checks"""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self.cache = HealthCheckCache()
        self.last_full_check = None
        self.check_history: List[Dict[str, Any]] = []
        self.max_history = 100
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function
        
        Check function should return ServiceHealth object
        """
        self.checks[name] = check_func
    
    async def check_single(self, service_name: str, use_cache: bool = True) -> ServiceHealth:
        """Run a single health check"""
        # Check cache first
        if use_cache:
            cached = self.cache.get(service_name)
            if cached:
                return cached
        
        if service_name not in self.checks:
            return ServiceHealth(
                service_name,
                HealthStatus.UNHEALTHY,
                0,
                f"Check not registered for {service_name}"
            )
        
        try:
            check_func = self.checks[service_name]
            result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
            
            # Cache successful result
            self.cache.set(service_name, result)
            return result
            
        except Exception as e:
            logger.error(f"Error in health check {service_name}: {str(e)}")
            return ServiceHealth(
                service_name,
                HealthStatus.UNHEALTHY,
                0,
                f"Check failed: {str(e)}"
            )
    
    async def check_all(self, use_cache: bool = False) -> Dict[str, Any]:
        """Run all registered health checks"""
        start_time = time.time()
        
        # Run all checks concurrently
        tasks = [
            self.check_single(name, use_cache=use_cache)
            for name in self.checks.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Aggregate results
        check_results = [r.to_dict() for r in results if isinstance(r, ServiceHealth)]
        
        # Determine overall status
        statuses = [r["status"] for r in check_results]
        if "unhealthy" in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif "degraded" in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        response_time = (time.time() - start_time) * 1000
        
        aggregate = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time, 2),
            "checks": {r["name"]: r for r in check_results},
            "summary": {
                "total_checks": len(check_results),
                "healthy": sum(1 for r in check_results if r["status"] == "healthy"),
                "degraded": sum(1 for r in check_results if r["status"] == "degraded"),
                "unhealthy": sum(1 for r in check_results if r["status"] == "unhealthy")
            }
        }
        
        # Store in history
        self.last_full_check = aggregate
        self.check_history.append(aggregate)
        if len(self.check_history) > self.max_history:
            self.check_history.pop(0)
        
        return aggregate
    
    async def readiness_probe(self) -> Dict[str, Any]:
        """Readiness probe - checks if service is ready to accept traffic
        
        Returns unhealthy if critical services are down
        """
        # Run quick checks only
        critical_services = ["database", "api", "auth"]
        
        health_check = await self.check_all(use_cache=True)
        
        # Check critical services
        for service in critical_services:
            if service in health_check["checks"]:
                if health_check["checks"][service]["status"] == "unhealthy":
                    return {
                        "ready": False,
                        "reason": f"Critical service {service} is unhealthy",
                        "check": health_check
                    }
        
        return {
            "ready": True,
            "check": health_check
        }
    
    async def liveness_probe(self) -> Dict[str, Any]:
        """Liveness probe - checks if service is still running
        
        Returns unhealthy if service is completely dead or locked
        """
        # Quick check - just verify API is responding
        check = await self.check_single("api", use_cache=True)
        
        return {
            "alive": check.status != HealthStatus.UNHEALTHY,
            "check": check.to_dict()
        }
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history"""
        return self.check_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get health check statistics"""
        if not self.check_history:
            return {
                "total_checks": 0,
                "avg_response_time_ms": 0,
                "uptime_percentage": 0
            }
        
        # Calculate statistics
        total_checks = len(self.check_history)
        avg_response_time = sum(
            h.get("response_time_ms", 0) for h in self.check_history
        ) / total_checks if total_checks > 0 else 0
        
        healthy_checks = sum(
            1 for h in self.check_history
            if h.get("status") == "healthy"
        )
        uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "total_checks": total_checks,
            "avg_response_time_ms": round(avg_response_time, 2),
            "uptime_percentage": round(uptime_percentage, 2),
            "last_check": self.last_full_check
        }


# Global health check manager instance
health_manager = HealthCheckManager()


# Specific health check implementations

async def check_api_health() -> ServiceHealth:
    """Check API service health"""
    start_time = time.time()
    
    try:
        # Just verify we can reach this function
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "api",
            HealthStatus.HEALTHY,
            response_time,
            "API service is responding"
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "api",
            HealthStatus.UNHEALTHY,
            response_time,
            f"API health check failed: {str(e)}"
        )


async def check_database_health(db_session) -> ServiceHealth:
    """Check database connectivity"""
    start_time = time.time()
    
    try:
        # Simple query to verify database connectivity
        from sqlalchemy import text
        result = db_session.execute(text("SELECT 1"))
        result.close()
        
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "database",
            HealthStatus.HEALTHY,
            response_time,
            "Database connection successful",
            {"type": "PostgreSQL"}
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "database",
            HealthStatus.UNHEALTHY,
            response_time,
            f"Database connection failed: {str(e)}"
        )


async def check_cache_health(redis_client=None) -> ServiceHealth:
    """Check cache/Redis connectivity"""
    start_time = time.time()
    
    try:
        if redis_client is None:
            # Fallback to healthy if no Redis configured
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                "cache",
                HealthStatus.HEALTHY,
                response_time,
                "Cache not configured (in-memory fallback)"
            )
        
        # Test Redis connection
        redis_client.ping()
        
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "cache",
            HealthStatus.HEALTHY,
            response_time,
            "Redis cache connection successful"
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "cache",
            HealthStatus.DEGRADED,
            response_time,
            f"Cache check failed: {str(e)} (using fallback)"
        )


async def check_external_services_health(circuit_breaker_manager=None) -> ServiceHealth:
    """Check status of external services via circuit breaker"""
    start_time = time.time()
    
    try:
        if circuit_breaker_manager is None:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                "external_services",
                HealthStatus.HEALTHY,
                response_time,
                "Circuit breaker not configured"
            )
        
        # Get circuit breaker stats
        services_status = {}
        total_open = 0
        
        for service_name in circuit_breaker_manager.breakers.keys():
            breaker = circuit_breaker_manager.breakers[service_name]
            is_open = breaker.is_open()
            services_status[service_name] = "open" if is_open else "closed"
            if is_open:
                total_open += 1
        
        response_time = (time.time() - start_time) * 1000
        
        if total_open > 0:
            status = HealthStatus.DEGRADED if total_open < len(services_status) else HealthStatus.UNHEALTHY
            message = f"{total_open} service(s) circuit breaker open"
        else:
            status = HealthStatus.HEALTHY
            message = "All external services operational"
        
        return ServiceHealth(
            "external_services",
            status,
            response_time,
            message,
            services_status
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "external_services",
            HealthStatus.UNHEALTHY,
            response_time,
            f"External services check failed: {str(e)}"
        )


async def check_auth_health() -> ServiceHealth:
    """Check authentication service health"""
    start_time = time.time()
    
    try:
        # Verify token blacklist system is operational
        from app.api.utils.token_blacklist import get_blacklist_stats
        
        stats = get_blacklist_stats()
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealth(
            "auth",
            HealthStatus.HEALTHY,
            response_time,
            "Authentication service operational",
            {
                "blacklisted_tokens": stats.get("blacklisted_count", 0),
                "cleaned_tokens": stats.get("cleaned_count", 0)
            }
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            "auth",
            HealthStatus.UNHEALTHY,
            response_time,
            f"Auth health check failed: {str(e)}"
        )
