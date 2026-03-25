"""
PRIORITY 4: Service Monitoring & Metrics Collection

Monitors external service health (Tally, Weather, Ollama, WhatsApp, Razorpay, Twilio)
with circuit breaker integration and performance metrics tracking.

Features:
- Real-time service status monitoring
- Circuit breaker state tracking
- Performance metrics (latency, success rate, error rate)
- Alerting thresholds
- Health history and trends
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """External service status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject requests
    HALF_OPEN = "half_open"    # Testing recovery


@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    service_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    
    def average_response_time_ms(self) -> float:
        """Calculate average response time"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time_ms / self.total_requests
    
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        return 100.0 - self.success_rate()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "service_name": self.service_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "average_response_time_ms": round(self.average_response_time_ms(), 2),
            "min_response_time_ms": round(self.min_response_time_ms, 2) if self.min_response_time_ms != float('inf') else None,
            "max_response_time_ms": round(self.max_response_time_ms, 2),
            "success_rate": round(self.success_rate(), 2),
            "error_rate": round(self.error_rate(), 2),
            "consecutive_failures": self.consecutive_failures,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_error": self.last_error
        }


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    service_name: str
    error_rate_threshold: float = 10.0  # % errors
    response_time_threshold_ms: float = 5000.0  # 5 seconds
    consecutive_failures_threshold: int = 3
    unhealthy_duration_seconds: int = 300  # 5 minutes
    
    def to_dict(self) -> dict:
        return asdict(self)


class ServiceMonitor:
    """Comprehensive service monitoring system"""
    
    def __init__(self):
        self._lock = Lock()
        self.services: Dict[str, ServiceMetrics] = {}
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.circuit_states: Dict[str, CircuitState] = {}
        self.health_history: Dict[str, List[Tuple[datetime, ServiceStatus]]] = {}
        self.alerts: List[Dict] = []
        self.max_history_size = 100
        
        # Initialize common external services
        self._init_default_services()
    
    def _init_default_services(self):
        """Initialize default external services"""
        external_services = [
            ("tally", AlertThreshold("tally", error_rate_threshold=5.0, response_time_threshold_ms=3000)),
            ("weather", AlertThreshold("weather", error_rate_threshold=10.0, response_time_threshold_ms=2000)),
            ("ollama", AlertThreshold("ollama", error_rate_threshold=15.0, response_time_threshold_ms=10000)),
            ("whatsapp", AlertThreshold("whatsapp", error_rate_threshold=5.0, response_time_threshold_ms=5000)),
            ("razorpay", AlertThreshold("razorpay", error_rate_threshold=3.0, response_time_threshold_ms=3000)),
            ("twilio", AlertThreshold("twilio", error_rate_threshold=5.0, response_time_threshold_ms=4000)),
            ("database", AlertThreshold("database", error_rate_threshold=1.0, response_time_threshold_ms=500)),
        ]
        
        for service_name, threshold in external_services:
            self.register_service(service_name, threshold)
    
    def register_service(self, service_name: str, threshold: Optional[AlertThreshold] = None) -> None:
        """Register a new service for monitoring"""
        with self._lock:
            if service_name not in self.services:
                self.services[service_name] = ServiceMetrics(service_name=service_name)
                self.circuit_states[service_name] = CircuitState.CLOSED
                self.health_history[service_name] = []
                
                if threshold:
                    self.thresholds[service_name] = threshold
                else:
                    self.thresholds[service_name] = AlertThreshold(service_name)
                
                logger.info(f"Service '{service_name}' registered for monitoring")
    
    def record_request(
        self,
        service_name: str,
        success: bool,
        response_time_ms: float,
        error: Optional[str] = None
    ) -> None:
        """Record a service request outcome"""
        self.register_service(service_name)
        
        with self._lock:
            metrics = self.services[service_name]
            metrics.total_requests += 1
            metrics.last_check = datetime.now()
            metrics.total_response_time_ms += response_time_ms
            metrics.min_response_time_ms = min(metrics.min_response_time_ms, response_time_ms)
            metrics.max_response_time_ms = max(metrics.max_response_time_ms, response_time_ms)
            
            if success:
                metrics.successful_requests += 1
                metrics.consecutive_failures = 0
            else:
                metrics.failed_requests += 1
                metrics.consecutive_failures += 1
                metrics.last_error = error
        
        # Check thresholds and update status
        self._check_and_update_status(service_name)
    
    def _check_and_update_status(self, service_name: str) -> None:
        """Check metrics against thresholds and update service status"""
        with self._lock:
            metrics = self.services[service_name]
            threshold = self.thresholds[service_name]
            
            # Determine status based on metrics
            if metrics.total_requests == 0:
                status = ServiceStatus.UNKNOWN
            elif metrics.error_rate() > threshold.error_rate_threshold:
                status = ServiceStatus.UNHEALTHY
            elif metrics.consecutive_failures >= threshold.consecutive_failures_threshold:
                status = ServiceStatus.UNHEALTHY
            elif metrics.average_response_time_ms() > threshold.response_time_threshold_ms:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.HEALTHY
            
            # Record in history
            if service_name not in self.health_history:
                self.health_history[service_name] = []
            
            history = self.health_history[service_name]
            if len(history) == 0 or history[-1][1] != status:
                history.append((datetime.now(), status))
                
                # Keep history size limited
                if len(history) > self.max_history_size:
                    history.pop(0)
                
                # Generate alert if status changed to unhealthy
                if status == ServiceStatus.UNHEALTHY:
                    self._create_alert(service_name, status, metrics)
    
    def _create_alert(self, service_name: str, status: ServiceStatus, metrics: ServiceMetrics) -> None:
        """Create an alert for service status change"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "status": status.value,
            "error_rate": round(metrics.error_rate(), 2),
            "consecutive_failures": metrics.consecutive_failures,
            "last_error": metrics.last_error,
            "average_response_time_ms": round(metrics.average_response_time_ms(), 2)
        }
        
        self.alerts.append(alert)
        
        # Keep alerts limited
        if len(self.alerts) > 1000:
            self.alerts.pop(0)
        
        logger.warning(f"Alert: {service_name} is {status.value} - {json.dumps(alert)}")
    
    def set_circuit_state(self, service_name: str, state: CircuitState) -> None:
        """Update circuit breaker state"""
        self.register_service(service_name)
        
        with self._lock:
            old_state = self.circuit_states[service_name]
            self.circuit_states[service_name] = state
            
            if old_state != state:
                logger.info(f"Circuit breaker for '{service_name}': {old_state.value} → {state.value}")
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get current status of a service"""
        self.register_service(service_name)
        
        with self._lock:
            if service_name in self.health_history and len(self.health_history[service_name]) > 0:
                return self.health_history[service_name][-1][1]
        
        return ServiceStatus.UNKNOWN
    
    def get_service_metrics(self, service_name: str) -> Optional[Dict]:
        """Get metrics for a service"""
        self.register_service(service_name)
        
        with self._lock:
            if service_name in self.services:
                return self.services[service_name].to_dict()
        
        return None
    
    def get_all_services_report(self) -> Dict:
        """Get comprehensive report of all services"""
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "services": {
                    name: {
                        "metrics": self.services[name].to_dict(),
                        "status": self.get_service_status(name).value,
                        "circuit_breaker_state": self.circuit_states[name].value,
                        "threshold": self.thresholds[name].to_dict()
                    }
                    for name in self.services.keys()
                },
                "active_alerts": [a for a in self.alerts[-10:]],  # Last 10 alerts
                "total_alerts": len(self.alerts)
            }
    
    def get_health_trend(self, service_name: str, hours: int = 1) -> List[Dict]:
        """Get health trend for a service over time"""
        self.register_service(service_name)
        
        with self._lock:
            if service_name not in self.health_history:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            history = self.health_history[service_name]
            
            return [
                {
                    "timestamp": timestamp.isoformat(),
                    "status": status.value
                }
                for timestamp, status in history
                if timestamp >= cutoff_time
            ]
    
    def clear_metrics(self, service_name: str) -> None:
        """Clear metrics for a service (useful for testing)"""
        with self._lock:
            if service_name in self.services:
                self.services[service_name] = ServiceMetrics(service_name=service_name)
                self.health_history[service_name] = []
                logger.info(f"Metrics cleared for '{service_name}'")
    
    def get_alert_summary(self) -> Dict:
        """Get summary of alerts"""
        with self._lock:
            unhealthy_services = [
                service_name
                for service_name, history in self.health_history.items()
                if len(history) > 0 and history[-1][1] == ServiceStatus.UNHEALTHY
            ]
            
            degraded_services = [
                service_name
                for service_name, history in self.health_history.items()
                if len(history) > 0 and history[-1][1] == ServiceStatus.DEGRADED
            ]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "unhealthy_services": unhealthy_services,
                "degraded_services": degraded_services,
                "total_alerts_in_last_hour": len([
                    a for a in self.alerts
                    if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=1)
                ]),
                "total_alerts": len(self.alerts)
            }


# Global service monitor instance
service_monitor = ServiceMonitor()
