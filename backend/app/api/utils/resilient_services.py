"""
Resilient Service Integration Layer
Wraps all external service calls with circuit breaker, retry, and fallback logic
PRIORITY 2 Implementation: Circuit Breaker Integration
"""

import logging
import time
from functools import wraps
from typing import Callable, Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceHealthStatus(Enum):
    """Health status of external services"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    CIRCUIT_OPEN = "circuit_open"


class ResilientServiceCall:
    """
    Wrapper for external service calls with resilience patterns:
    - Circuit breaker (fail fast)
    - Exponential backoff retry
    - Fallback responses
    - Health tracking
    - Metrics collection
    """
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        max_retries: int = 3,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 30.0
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.max_retries = max_retries
        self.initial_backoff_seconds = initial_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        
        # State tracking
        self.failure_count = 0
        self.success_count = 0
        self.circuit_open = False
        self.circuit_opened_at = None
        self.last_failure_at = None
        self.last_error = None
        
        # Metrics
        self.total_calls = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_retries = 0
        self.last_call_duration_ms = 0
    
    def is_circuit_open(self) -> bool:
        """Check if circuit is currently open"""
        if not self.circuit_open:
            return False
        
        # Check if recovery timeout has elapsed
        elapsed = (datetime.utcnow() - self.circuit_opened_at).total_seconds()
        if elapsed >= self.recovery_timeout_seconds:
            logger.info(f"{self.service_name}: Circuit recovery timeout reached, attempting HALF_OPEN")
            self.circuit_open = False
            self.failure_count = 0
            self.success_count = 0
            return False
        
        return True
    
    def record_success(self):
        """Record successful call"""
        self.failure_count = 0
        self.success_count += 1
        self.total_successes += 1
        self.last_error = None
        
        logger.debug(f"{self.service_name}: ✅ Call successful")
    
    def record_failure(self, error: Exception):
        """Record failed call"""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_at = datetime.utcnow()
        self.last_error = str(error)
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.circuit_opened_at = datetime.utcnow()
            logger.error(
                f"{self.service_name}: 🔴 CIRCUIT OPEN after {self.failure_count} failures. "
                f"Recovery in {self.recovery_timeout_seconds}s. Error: {error}"
            )
        else:
            logger.warning(
                f"{self.service_name}: ⚠️  Call failed ({self.failure_count}/{self.failure_threshold}). "
                f"Error: {error}"
            )
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        import random
        
        backoff = self.initial_backoff_seconds * (2 ** attempt)
        backoff = min(backoff, self.max_backoff_seconds)
        # Add jitter (±10%)
        jitter = random.uniform(0.9, 1.1)
        return backoff * jitter
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        fallback_response: Optional[Any] = None,
        **kwargs
    ) -> Tuple[Any, bool]:
        """
        Execute function with retry and circuit breaker protection
        
        Returns:
            Tuple of (result, is_fallback)
        """
        self.total_calls += 1
        
        # Check if circuit is open
        if self.is_circuit_open():
            logger.warning(f"{self.service_name}: Circuit is OPEN. Using fallback.")
            return fallback_response, True
        
        # Attempt calls with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Success!
                duration_ms = (time.time() - start_time) * 1000
                self.last_call_duration_ms = duration_ms
                self.record_success()
                
                logger.info(
                    f"{self.service_name}: ✅ Success (attempt {attempt + 1}, "
                    f"{duration_ms:.1f}ms)"
                )
                
                return result, False
                
            except Exception as e:
                last_error = e
                duration_ms = (time.time() - start_time) * 1000
                self.last_call_duration_ms = duration_ms
                
                # Record failure
                self.record_failure(e)
                
                # Determine if we should retry
                if attempt < self.max_retries - 1:
                    backoff_seconds = self.calculate_backoff(attempt)
                    self.total_retries += 1
                    
                    logger.warning(
                        f"{self.service_name}: Attempt {attempt + 1} failed. "
                        f"Retrying in {backoff_seconds:.2f}s... Error: {e}"
                    )
                    
                    time.sleep(backoff_seconds)
                else:
                    logger.error(
                        f"{self.service_name}: All {self.max_retries} attempts failed. "
                        f"Using fallback. Final error: {e}"
                    )
        
        # All retries exhausted, use fallback
        return fallback_response, True
    
    def call(
        self,
        func: Callable,
        fallback_response: Any = None,
        *args,
        **kwargs
    ) -> Tuple[Any, bool]:
        """
        Execute a function with circuit breaker protection.
        Returns tuple of (response, is_fallback)
        """
        return self.execute_with_retry(func, fallback_response, *args, **kwargs)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status and metrics"""
        success_rate = 0.0
        if self.total_calls > 0:
            success_rate = (self.total_successes / self.total_calls) * 100
        
        return {
            "service": self.service_name,
            "status": ServiceHealthStatus.CIRCUIT_OPEN.value if self.is_circuit_open() else ServiceHealthStatus.HEALTHY.value,
            "circuit_open": self.is_circuit_open(),
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "metrics": {
                "total_calls": self.total_calls,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "total_retries": self.total_retries,
                "success_rate_percent": success_rate,
                "last_call_duration_ms": self.last_call_duration_ms
            }
        }


# Service instances - one per external service
tally_service = ResilientServiceCall(
    "Tally ERP",
    failure_threshold=3,
    recovery_timeout_seconds=120,
    max_retries=3
)

whatsapp_service = ResilientServiceCall(
    "WhatsApp API",
    failure_threshold=5,
    recovery_timeout_seconds=60,
    max_retries=2
)

email_service_resilient = ResilientServiceCall(
    "SMTP Email",
    failure_threshold=5,
    recovery_timeout_seconds=60,
    max_retries=3
)

weather_service = ResilientServiceCall(
    "OpenWeather API",
    failure_threshold=3,
    recovery_timeout_seconds=30,
    max_retries=2
)

ollama_service = ResilientServiceCall(
    "Ollama AI",
    failure_threshold=3,
    recovery_timeout_seconds=30,
    max_retries=1
)

payment_service = ResilientServiceCall(
    "Payment Gateway",
    failure_threshold=2,
    recovery_timeout_seconds=120,
    max_retries=1
)

# Export all services
__all__ = [
    'ResilientServiceCall',
    'ServiceHealthStatus',
    'tally_service',
    'whatsapp_service',
    'email_service_resilient',
    'weather_service',
    'ollama_service',
    'payment_service'
]
