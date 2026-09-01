"""
Circuit Breaker Utilities
Prevent cascading failures from external service outages
"""

from functools import wraps
from typing import Callable, Optional
import logging
from circuitbreaker import circuit
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

# ==================== CIRCUIT BREAKER DECORATORS ====================

def twilio_circuit_breaker(func: Callable) -> Callable:
    """
    Circuit breaker for Twilio WhatsApp service
    
    - Opens circuit after 5 consecutive failures
    - Recovers after 60 seconds
    - Retries up to 3 times with exponential backoff
    """
    @circuit(failure_threshold=5, recovery_timeout=60, name="twilio")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Twilio service error: {e}")
            raise
    
    return wrapper

def api_circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    max_attempts: int = 3
) -> Callable:
    """
    Generic circuit breaker for external APIs
    
    Args:
        service_name: Name of the service (for logging)
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds before trying again
        max_attempts: Maximum retry attempts
    
    Usage:
        @api_circuit_breaker("OpenWeatherMap")
        def fetch_weather():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @circuit(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            name=service_name
        )
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{service_name} API error: {e}")
                raise
        
        return wrapper
    
    return decorator

# ==================== FALLBACK HANDLERS ====================

class FallbackHandler:
    """Handle graceful degradation when circuit is open"""
    
    @staticmethod
    def api_fallback(
        service_name: str,
        use_cached: bool = True,
        cache_key: Optional[str] = None
    ) -> dict:
        """
        Fallback when external API fails
        
        - Return cached data if available
        - Use default values
        - Degrade gracefully
        """
        logger.warning(f"{service_name} circuit open, using fallback")
        
        if use_cached and cache_key:
            try:
                from app.services.cache_service import cache_service
                cached_data = cache_service.get(cache_key)
                
                if cached_data:
                    logger.info(f"Using cached data for {service_name}")
                    return {
                        "status": "cached",
                        "data": cached_data,
                        "message": "Using cached data due to service unavailability"
                    }
            except Exception as e:
                logger.error(f"Cache fallback failed: {e}")
        
        # Return default/empty data
        return {
            "status": "unavailable",
            "data": None,
            "message": f"{service_name} temporarily unavailable"
        }

# ==================== HEALTH CHECK ====================

class CircuitBreakerHealth:
    """Monitor circuit breaker status"""
    
    @staticmethod
    def get_status() -> dict:
        """Get status of all circuit breakers"""
        from circuitbreaker import CircuitBreaker
        
        circuits = CircuitBreaker.all_circuits()
        
        return {
            "total_circuits": len(circuits),
            "circuits": {
                str(cb): {
                    "state": cb.current_state,
                    "failure_count": cb.failure_count,
                    "opened_at": cb.opened_at.isoformat() if cb.opened_at else None
                }
                for cb in circuits
            }
        }
    
    @staticmethod
    def reset_all():
        """Reset all circuit breakers (emergency use)"""
        from circuitbreaker import CircuitBreaker
        
        for cb in CircuitBreaker.all_circuits():
            cb.close()
        
        logger.info("All circuit breakers reset")

# ==================== EXAMPLE USAGE ====================

"""
# In external API calls:
@api_circuit_breaker("OpenWeatherMap", failure_threshold=3)
def fetch_weather_data(city):
    response = requests.get(f"https://api.openweathermap.org/...")
    return response.json()
"""
