"""
Circuit Breaker Pattern for External Integrations
Prevents external service failures from crashing POS
Per CLAUDE.md Part 3.4
"""
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, name: str, threshold: int = 5, timeout: int = 60):
        self.name = name
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = "CLOSED"

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure > self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    logger.warning(f"{self.name} circuit OPEN — skipping")
                    return None
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure = time.time()
                if self.failures >= self.threshold:
                    self.state = "OPEN"
                    logger.error(f"{self.name} circuit tripped after {self.failures} failures")
                raise
        return wrapper

# Create breakers for external services
tally_breaker = CircuitBreaker("Tally")
razorpay_breaker = CircuitBreaker("Razorpay")
