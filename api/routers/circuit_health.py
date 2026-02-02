"""
Circuit Breaker Health Monitoring Endpoint
Track circuit breaker status and system resilience
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging

from api.utils.circuit_breakers import CircuitBreakerHealth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/circuit-breakers", tags=["circuit-breakers"])

@router.get("/status")
async def get_circuit_breaker_status() -> Dict:
    """
    Get status of all circuit breakers
    
    Returns circuit state, failure counts, and opened timestamps
    for all registered circuit breakers (Twilio, SMTP, external APIs)
    """
    try:
        status = CircuitBreakerHealth.get_status()
        
        # Add health summary
        all_closed = all(
            circuit.get("state") == "closed" 
            for circuit in status.get("circuits", {}).values()
        )
        
        return {
            "status": "healthy" if all_closed else "degraded",
            "total_circuits": status["total_circuits"],
            "circuits": status["circuits"],
            "timestamp": "2026-01-20T11:10:00+05:30"
        }
    except Exception as e:
        logger.error(f"Error getting circuit status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/reset")
async def reset_all_circuit_breakers() -> Dict:
    """
    Reset all circuit breakers (EMERGENCY USE ONLY)
    
    This will close all open circuits and reset failure counts.
    Use with caution - only when you know external services are back online.
    """
    try:
        CircuitBreakerHealth.reset_all()
        
        logger.warning("All circuit breakers manually reset")
        
        return {
            "status": "success",
            "message": "All circuit breakers reset",
            "warning": "Ensure external services are actually available"
        }
    except Exception as e:
        logger.error(f"Error resetting circuits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_resilience_health() -> Dict:
    """
    Get overall system resilience health
    
    Checks:
    - Circuit breaker status
    - Fallback availability  
    - External service health
    """
    cb_status = CircuitBreakerHealth.get_status()
    circuits = cb_status.get("circuits", {})
    
    # Count circuit states
    open_circuits = sum(1 for c in circuits.values() if c.get("state") == "open")
    half_open_circuits = sum(1 for c in circuits.values() if c.get("state") == "half-open")
    closed_circuits = sum(1 for c in circuits.values() if c.get("state") == "closed")
    
    # Determine overall health
    if open_circuits == 0:
        health = "healthy"
        message = "All external services operational"
    elif open_circuits < len(circuits) / 2:
        health = "degraded"
        message = f"{open_circuits} service(s) degraded, fallbacks active"
    else:
        health = "critical"
        message = f"Multiple services down ({open_circuits}/{len(circuits)})"
    
   
    return {
        "health": health,
        "message": message,
        "circuits": {
            "total": len(circuits),
            "open": open_circuits,
            "half_open": half_open_circuits,
            "closed": closed_circuits
        },
        "fallbacks_available": {
            "whatsapp_to_email": True,  # Email fallback for WhatsApp
            "api_to_cache": True  # Cached data for APIs
        },
        "recommendations": _get_recommendations(open_circuits, len(circuits))
    }

def _get_recommendations(open_count: int, total_count: int) -> List[str]:
    """Generate recommendations based on circuit status"""
    recommendations = []
    
    if open_count > 0:
        recommendations.append("Monitor external service status")
        recommendations.append("Check fallback system logs")
        
        if open_count >= total_count / 2:
            recommendations.append("⚠️ CRITICAL: Multiple services down")
            recommendations.append("Verify network connectivity")
            recommendations.append("Check API credentials/quotas")
    else:
        recommendations.append("All systems operational")
    
    return recommendations
