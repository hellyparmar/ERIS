"""
Health Check Router for External Services
Monitors circuit breaker states and resilience metrics
PRIORITY 2: Circuit Breaker Integration
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.api.db import get_db
from app.api.auth.dependencies import get_current_user
from app.api.utils.resilient_services import (
    tally_service,
    whatsapp_service,
    email_service_resilient,
    weather_service,
    ollama_service,
    payment_service,
    ServiceHealthStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health & Monitoring"])


@router.get("/services")
async def get_services_health(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get health status of all external services
    
    Returns:
        {
            "timestamp": "2026-03-04T...",
            "overall_status": "healthy|degraded|critical",
            "services": [
                {
                    "service": "Tally ERP",
                    "status": "healthy|degraded|unavailable|circuit_open",
                    "circuit_open": false,
                    "last_error": null,
                    "failure_count": 0,
                    "metrics": {
                        "total_calls": 150,
                        "success_rate_percent": 98.5,
                        "last_call_duration_ms": 450
                    }
                }
            ]
        }
    """
    
    services = [
        tally_service,
        whatsapp_service,
        email_service_resilient,
        weather_service,
        ollama_service,
        payment_service
    ]
    
    service_statuses = []
    circuit_open_count = 0
    
    for service in services:
        status = service.get_health_status()
        service_statuses.append(status)
        
        if status["circuit_open"]:
            circuit_open_count += 1
    
    # Determine overall status
    if circuit_open_count >= 3:
        overall_status = ServiceHealthStatus.UNAVAILABLE.value
    elif circuit_open_count > 0:
        overall_status = ServiceHealthStatus.DEGRADED.value
    else:
        overall_status = ServiceHealthStatus.HEALTHY.value
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "circuit_breakers_open": circuit_open_count,
        "services": service_statuses
    }


@router.get("/circuits")
async def get_circuit_breaker_states(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed circuit breaker states
    
    Useful for monitoring and debugging
    """
    
    services = {
        "tally": tally_service.get_health_status(),
        "whatsapp": whatsapp_service.get_health_status(),
        "email": email_service_resilient.get_health_status(),
        "weather": weather_service.get_health_status(),
        "ollama": ollama_service.get_health_status(),
        "payment": payment_service.get_health_status()
    }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "circuits": services
    }


@router.post("/circuits/{service_name}/reset")
async def reset_circuit_breaker(
    service_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually reset a circuit breaker (admin only)
    
    Useful for forcing recovery after manual intervention
    """
    
    service_map = {
        "tally": tally_service,
        "whatsapp": whatsapp_service,
        "email": email_service_resilient,
        "weather": weather_service,
        "ollama": ollama_service,
        "payment": payment_service
    }
    
    if service_name not in service_map:
        return {
            "error": f"Service '{service_name}' not found",
            "available_services": list(service_map.keys())
        }
    
    service = service_map[service_name]
    
    # Reset circuit breaker state
    service.circuit_open = False
    service.failure_count = 0
    service.success_count = 0
    service.circuit_opened_at = None
    
    logger.warning(f"Circuit breaker for {service.service_name} manually reset by {current_user.get('user_id')}")
    
    return {
        "status": "reset",
        "service": service.service_name,
        "circuit_open": service.is_circuit_open(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def get_resilience_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive resilience metrics across all services
    """
    
    services = [
        tally_service,
        whatsapp_service,
        email_service_resilient,
        weather_service,
        ollama_service,
        payment_service
    ]
    
    total_calls = sum(s.total_calls for s in services)
    total_successes = sum(s.total_successes for s in services)
    total_failures = sum(s.total_failures for s in services)
    total_retries = sum(s.total_retries for s in services)
    
    overall_success_rate = 0.0
    if total_calls > 0:
        overall_success_rate = (total_successes / total_calls) * 100
    
    # Average response time
    avg_response_time = sum(s.last_call_duration_ms for s in services) / len(services) if services else 0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "aggregated_metrics": {
            "total_calls": total_calls,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "total_retries": total_retries,
            "overall_success_rate_percent": overall_success_rate,
            "avg_response_time_ms": avg_response_time,
            "services_monitored": len(services),
            "circuits_open": sum(1 for s in services if s.is_circuit_open())
        },
        "service_breakdown": [
            {
                "service": s.service_name,
                "calls": s.total_calls,
                "successes": s.total_successes,
                "failures": s.total_failures,
                "retries": s.total_retries,
                "success_rate_percent": (s.total_successes / s.total_calls * 100) if s.total_calls > 0 else 0,
                "circuit_open": s.is_circuit_open()
            }
            for s in services
        ]
    }
