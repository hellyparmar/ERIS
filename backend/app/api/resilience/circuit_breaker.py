"""
Phase 7.2: High-Availability - Advanced Circuit Breaker & Cache Protection
Implements resilience patterns for external service failures and cache degradation
"""

import time
import logging
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, block calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout_seconds: int = 60  # Wait before half-open
    expected_exception: type = Exception
    name: str = "circuitbreaker"
    success_threshold: int = 2  # Successes before closing from half-open


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation for fault tolerance
    
    Prevents cascading failures by failing fast when service is down
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_time = None
        self._lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{config.name}' initialized")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.config.name}' transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.config.name}' is OPEN"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.opened_time is None:
            return False
        
        elapsed = (datetime.utcnow() - self.opened_time).total_seconds()
        return elapsed >= self.config.recovery_timeout_seconds
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.config.name}' CLOSED (recovered)")
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            self.success_count = 0
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_time = datetime.utcnow()
                logger.warning(
                    f"Circuit breaker '{self.config.name}' OPEN after {self.failure_count} failures"
                )
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        with self._lock:
            return {
                'name': self.config.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'opened_time': self.opened_time.isoformat() if self.opened_time else None,
            }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


def circuit_breaker(config: Optional[CircuitBreakerConfig] = None):
    """Decorator for circuit breaker protection"""
    if config is None:
        config = CircuitBreakerConfig()
    
    cb = CircuitBreaker(config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        wrapper.circuit_breaker = cb
        return wrapper
    
    return decorator


# ============================================================
# CACHE PROTECTION & DEGRADATION
# ============================================================

@dataclass
class CacheConfig:
    """Configuration for cache protection"""
    ttl_seconds: int = 600  # Cache time-to-live
    max_size: int = 10000  # Maximum entries
    stale_ttl_seconds: int = 3600  # Serve stale data if backend fails
    enable_compression: bool = False


class ResilientCache:
    """
    Cache with degradation support
    Serves stale data when backend service fails
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.cache: Dict[str, tuple] = {}  # {key: (value, timestamp, is_stale)}
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str, backend_func: Optional[Callable] = None) -> Any:
        """
        Get value from cache
        Falls back to backend_func if available and fresh cache expired
        Serves stale data if backend fails
        """
        with self._lock:
            if key in self.cache:
                value, timestamp, is_stale = self.cache[key]
                age = (datetime.utcnow() - timestamp).total_seconds()
                
                # Serve fresh cache
                if age < self.config.ttl_seconds:
                    self.hits += 1
                    return value
                
                # Serve stale cache (if within stale window)
                if is_stale and age < self.config.stale_ttl_seconds:
                    logger.info(f"Serving stale cache for key {key}")
                    self.hits += 1
                    return value
        
        # Try backend
        if backend_func:
            try:
                value = backend_func()
                self.set(key, value, is_stale=False)
                return value
            except Exception as e:
                logger.warning(f"Backend failed for key {key}: {e}")
                
                # Fall back to stale cache if available
                with self._lock:
                    if key in self.cache:
                        value, _, _ = self.cache[key]
                        logger.info(f"Falling back to stale cache for key {key}")
                        self.hits += 1
                        return value
                
                # No cache available, raise
                self.misses += 1
                raise CacheFailoverError(f"Backend unavailable and no cache for key {key}")
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, is_stale: bool = False):
        """Set value in cache"""
        with self._lock:
            if len(self.cache) >= self.config.max_size:
                # Evict oldest entry (LRU)
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (value, datetime.utcnow(), is_stale)
    
    def invalidate(self, key: str):
        """Invalidate cache entry"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        with self._lock:
            to_delete = [k for k in self.cache.keys() if pattern in k]
            for k in to_delete:
                del self.cache[k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                'entries': len(self.cache),
                'max_size': self.config.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.1f}%",
            }


class CacheFailoverError(Exception):
    """Exception when cache failover exhausted"""
    pass


# ============================================================
# BULKHEAD PATTERN (Isolation)
# ============================================================

class BulkheadConfig:
    """Configuration for bulkhead pattern"""
    def __init__(self, max_concurrent: int = 10, queue_size: int = 100, timeout_seconds: int = 30):
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        self.timeout_seconds = timeout_seconds


class Bulkhead:
    """
    Bulkhead pattern: Isolate resources to prevent total system failure
    Limits concurrent requests to a critical resource
    """
    
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.semaphore = threading.Semaphore(config.max_concurrent)
        self.active_count = 0
        self.rejected_count = 0
        self._lock = threading.Lock()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with resource isolation"""
        acquired = self.semaphore.acquire(timeout=self.config.timeout_seconds)
        
        if not acquired:
            with self._lock:
                self.rejected_count += 1
            raise BulkheadRejectedException("Too many concurrent requests")
        
        try:
            with self._lock:
                self.active_count += 1
            
            return func(*args, **kwargs)
        finally:
            with self._lock:
                self.active_count -= 1
            self.semaphore.release()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics"""
        with self._lock:
            return {
                'active': self.active_count,
                'max': self.config.max_concurrent,
                'rejected': self.rejected_count,
            }


class BulkheadRejectedException(Exception):
    """Exception when bulkhead rejects request"""
    pass


# ============================================================
# RETRY WITH EXPONENTIAL BACKOFF
# ============================================================

class RetryConfig:
    """Configuration for retry logic"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 0.1,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryWithBackoff:
    """Retry with exponential backoff and jitter"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random())  # Add 0-50% random jitter
        
        return delay


def retry(config: Optional[RetryConfig] = None):
    """Decorator for retry with backoff"""
    if config is None:
        config = RetryConfig()
    
    retry_logic = RetryWithBackoff(config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_logic.execute(func, *args, **kwargs)
        return wrapper
    
    return decorator


# ============================================================
# TIMEOUT PROTECTION
# ============================================================

import signal

class TimeoutException(Exception):
    """Exception raised on timeout"""
    pass


def timeout(seconds: int):
    """Decorator to add timeout to function"""
    def decorator(func: Callable) -> Callable:
        def handler(signum, frame):
            raise TimeoutException(f"Function {func.__name__} timed out after {seconds}s")
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set signal handler
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)  # Cancel alarm
            
            return result
        return wrapper
    return decorator


# ============================================================
# HEALTH CHECK & MONITORING
# ============================================================

class HealthCheckRegistry:
    """Registry for health checks"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, check_func: Callable):
        """Register a health check function"""
        with self._lock:
            self.checks[name] = check_func
        logger.info(f"Health check '{name}' registered")
    
    def run_all(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks"""
        results = {}
        
        with self._lock:
            checks_copy = self.checks.copy()
        
        for name, check_func in checks_copy.items():
            try:
                start_time = time.time()
                result = check_func()
                elapsed = (time.time() - start_time) * 1000  # Convert to ms
                
                results[name] = {
                    'status': 'healthy',
                    'message': result,
                    'elapsed_ms': f"{elapsed:.1f}",
                }
            except Exception as e:
                results[name] = {
                    'status': 'unhealthy',
                    'message': str(e),
                    'error': type(e).__name__,
                }
        
        # Overall health
        overall = 'healthy' if all(r['status'] == 'healthy' for r in results.values()) else 'unhealthy'
        
        return {
            'overall': overall,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results,
        }


# Global registries
circuit_breakers: Dict[str, CircuitBreaker] = {}
caches: Dict[str, ResilientCache] = {}
bulkheads: Dict[str, Bulkhead] = {}
health_checks = HealthCheckRegistry()


def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create circuit breaker"""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(config or CircuitBreakerConfig(name=name))
    return circuit_breakers[name]


def get_cache(name: str, config: CacheConfig = None) -> ResilientCache:
    """Get or create cache"""
    if name not in caches:
        caches[name] = ResilientCache(config or CacheConfig())
    return caches[name]


def get_bulkhead(name: str, config: BulkheadConfig = None) -> Bulkhead:
    """Get or create bulkhead"""
    if name not in bulkheads:
        bulkheads[name] = Bulkhead(config or BulkheadConfig())
    return bulkheads[name]
