"""
Real-Time Alert System for Retail Operations
Week 14-15: Production-grade alerting with multiple channels

Features:
- Anomaly detection (forecast deviation, stock depletion, sales surge)
- Multi-channel notifications (webhook, email, in-app, SMS)
- Alert aggregation and deduplication
- Alert history and audit trail
- WebSocket support for real-time frontend updates
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import json
from pathlib import Path
import asyncio
import hashlib
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"          # Informational
    WARNING = "warning"    # Needs attention
    CRITICAL = "critical"  # Immediate action needed
    ALERT = "alert"        # Standard alert


class AlertType(str, Enum):
    """Types of alerts"""
    FORECAST_ANOMALY = "forecast_anomaly"      # Forecast deviates significantly
    STOCK_DEPLETION = "stock_depletion"        # Stock running low
    SALES_ANOMALY = "sales_anomaly"            # Sales surge/drop
    WEATHER_IMPACT = "weather_impact"          # Unusual weather affecting sales
    PROMOTION_MISMATCH = "promotion_mismatch"  # Promotion not performing
    DEMAND_SPIKE = "demand_spike"              # Unexpected demand
    OUTLET_UNDERPERFORM = "outlet_underperform" # Outlet underperforming
    MODEL_DRIFT = "model_drift"                # Model accuracy degrading
    DATA_QUALITY = "data_quality"              # Data quality issue
    CUSTOM = "custom"                          # Custom alert


@dataclass
class AlertContext:
    """Context for alert generation"""
    outlet_id: str
    product_id: str
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float  # % deviation
    timestamp: datetime = field(default_factory=datetime.now)
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    context: Dict[str, Any]
    outlet_id: str
    product_id: Optional[str]
    timestamp: datetime
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'context': self.context,
            'outlet_id': self.outlet_id,
            'product_id': self.product_id,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes
        }
    
    def get_hash(self) -> str:
        """Get unique hash for deduplication"""
        key = f"{self.type}{self.outlet_id}{self.product_id}{self.title}"
        return hashlib.md5(key.encode()).hexdigest()


class AnomalyDetector:
    """Detect anomalies in metrics"""
    
    @staticmethod
    def detect_deviation(
        actual: float,
        expected: float,
        threshold_pct: float = 10.0
    ) -> Tuple[bool, float]:
        """
        Detect if actual value deviates from expected
        
        Args:
            actual: Actual value
            expected: Expected/forecast value
            threshold_pct: Deviation threshold in %
        
        Returns:
            (is_anomaly, deviation_pct)
        """
        if expected == 0:
            return actual != 0, 100.0
        
        deviation = abs(actual - expected) / expected * 100
        is_anomaly = deviation > threshold_pct
        
        return is_anomaly, deviation
    
    @staticmethod
    def detect_outlier(
        value: float,
        recent_values: List[float],
        std_threshold: float = 3.0
    ) -> Tuple[bool, float]:
        """
        Detect if value is statistical outlier
        
        Args:
            value: Value to check
            recent_values: Recent historical values
            std_threshold: Number of standard deviations
        
        Returns:
            (is_outlier, z_score)
        """
        if len(recent_values) < 2:
            return False, 0.0
        
        mean = np.mean(recent_values)
        std = np.std(recent_values)
        
        if std == 0:
            return False, 0.0
        
        z_score = abs(value - mean) / std
        is_outlier = z_score > std_threshold
        
        return is_outlier, z_score
    
    @staticmethod
    def detect_trend_change(
        values: List[float],
        window_size: int = 5
    ) -> Tuple[bool, str]:
        """
        Detect significant trend changes
        
        Args:
            values: Time series values
            window_size: Window for trend calculation
        
        Returns:
            (is_trend_change, trend_direction)
        """
        if len(values) < window_size * 2:
            return False, "insufficient_data"
        
        old_trend = np.mean(values[-2*window_size:-window_size])
        new_trend = np.mean(values[-window_size:])
        
        change_pct = abs(new_trend - old_trend) / old_trend * 100 if old_trend != 0 else 0
        
        is_change = change_pct > 20
        direction = "up" if new_trend > old_trend else "down"
        
        return is_change, direction


class NotificationChannel(ABC):
    """Abstract base for notification channels"""
    
    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send alert through channel"""
        pass


class WebhookChannel(NotificationChannel):
    """Send alerts via webhook"""
    
    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
    
    async def send(self, alert: Alert) -> bool:
        """Send alert via POST to webhook"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json=alert.to_dict(),
                    timeout=self.timeout
                ) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"✓ Alert {alert.id} sent to webhook")
                    else:
                        logger.warning(f"Webhook returned {response.status}")
                    return success
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return False


class EmailChannel(NotificationChannel):
    """Send alerts via email"""
    
    def __init__(self, smtp_server: str, sender_email: str, recipients: List[str]):
        self.smtp_server = smtp_server
        self.sender_email = sender_email
        self.recipients = recipients
    
    async def send(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            import aiosmtplib
            
            message = f"""
            Alert: {alert.title}
            Severity: {alert.severity.value.upper()}
            Type: {alert.type.value}
            
            {alert.message}
            
            Outlet: {alert.outlet_id}
            Product: {alert.product_id}
            
            Timestamp: {alert.timestamp.isoformat()}
            """
            
            async with aiosmtplib.SMTP(hostname=self.smtp_server) as smtp:
                await smtp.sendmail(
                    self.sender_email,
                    self.recipients,
                    f"Subject: {alert.title}\n\n{message}"
                )
            
            logger.info(f"✓ Alert {alert.id} sent via email")
            return True
        except Exception as e:
            logger.warning(f"Email send failed: {str(e)}")
            return False


class InAppChannel(NotificationChannel):
    """Store alerts for in-app display"""
    
    def __init__(self, storage_dir: str = "./alerts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def send(self, alert: Alert) -> bool:
        """Store alert for in-app display"""
        try:
            filepath = self.storage_dir / f"{alert.id}.json"
            with open(filepath, 'w') as f:
                json.dump(alert.to_dict(), f)
            
            logger.info(f"✓ Alert {alert.id} stored in-app")
            return True
        except Exception as e:
            logger.error(f"In-app storage error: {str(e)}")
            return False


class AlertService:
    """
    Central alert management service
    Handles detection, deduplication, storage, and notification
    """
    
    def __init__(self, max_alerts: int = 10000):
        """
        Args:
            max_alerts: Maximum alerts to keep in memory
        """
        self.alerts: Dict[str, Alert] = {}
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.channels: List[NotificationChannel] = []
        self.anomaly_detector = AnomalyDetector()
        self.max_alerts = max_alerts
        self.alert_history: List[str] = []  # Alert IDs in order
        self.dedup_window = timedelta(hours=1)
        self.recent_alerts: Dict[str, datetime] = {}  # For deduplication
        
        logger.info("Initialized AlertService")
    
    def add_channel(self, channel: NotificationChannel) -> None:
        """Add notification channel"""
        self.channels.append(channel)
        logger.info(f"Added notification channel: {channel.__class__.__name__}")
    
    def add_webhook(self, url: str) -> None:
        """Add webhook channel"""
        self.add_channel(WebhookChannel(url))
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        context: Dict[str, Any],
        outlet_id: str,
        product_id: Optional[str] = None
    ) -> Alert:
        """
        Create and register alert
        
        Args:
            alert_type: Type of alert
            severity: Severity level
            title: Alert title
            message: Alert message
            context: Additional context
            outlet_id: Outlet identifier
            product_id: Product identifier (optional)
        
        Returns:
            Created Alert object
        """
        alert_id = self._generate_alert_id()
        
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            context=context,
            outlet_id=outlet_id,
            product_id=product_id,
            timestamp=datetime.now()
        )
        
        # Check for duplicates
        if self._is_duplicate(alert):
            logger.info(f"Skipped duplicate alert: {title}")
            return None
        
        # Store alert
        self.alerts[alert_id] = alert
        self.alert_history.append(alert_id)
        self.recent_alerts[alert.get_hash()] = datetime.now()
        
        # Trim old alerts if needed
        if len(self.alerts) > self.max_alerts:
            oldest_id = self.alert_history.pop(0)
            del self.alerts[oldest_id]
        
        logger.info(f"Created alert: {alert_type.value} - {title}")
        return alert
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if alert is duplicate of recent alert"""
        alert_hash = alert.get_hash()
        
        if alert_hash not in self.recent_alerts:
            return False
        
        last_time = self.recent_alerts[alert_hash]
        return (datetime.now() - last_time) < self.dedup_window
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert through all channels
        
        Args:
            alert: Alert to send
        
        Returns:
            True if sent successfully to at least one channel
        """
        if not alert:
            return False
        
        results = []
        for channel in self.channels:
            try:
                result = await channel.send(alert)
                results.append(result)
            except Exception as e:
                logger.error(f"Channel error: {str(e)}")
                results.append(False)
        
        success = any(results)
        if success:
            logger.info(f"✓ Alert {alert.id} sent through {sum(results)} channels")
        
        return success
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Mark alert as acknowledged
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged
            notes: Optional notes
        
        Returns:
            True if successful
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True
    
    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Mark alert as resolved
        
        Args:
            alert_id: Alert ID
            resolution_notes: How the alert was resolved
        
        Returns:
            True if successful
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()
        alert.resolution_notes = resolution_notes
        
        logger.info(f"Alert {alert_id} resolved")
        return True
    
    def get_active_alerts(
        self,
        outlet_id: Optional[str] = None,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get active (unresolved) alerts with optional filtering
        
        Args:
            outlet_id: Filter by outlet
            alert_type: Filter by type
            severity: Filter by severity
        
        Returns:
            List of matching alerts
        """
        alerts = [a for a in self.alerts.values() if not a.resolved]
        
        if outlet_id:
            alerts = [a for a in alerts if a.outlet_id == outlet_id]
        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp (newest first)
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_summary(self, outlet_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of alerts
        
        Args:
            outlet_id: Optional outlet filter
        
        Returns:
            Summary statistics
        """
        alerts = self.get_active_alerts(outlet_id=outlet_id)
        
        severity_counts = {s.value: 0 for s in AlertSeverity}
        type_counts = {t.value: 0 for t in AlertType}
        
        for alert in alerts:
            severity_counts[alert.severity.value] += 1
            type_counts[alert.type.value] += 1
        
        return {
            'total_active': len(alerts),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'critical_count': severity_counts[AlertSeverity.CRITICAL.value],
            'requires_attention': len([a for a in alerts if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.WARNING]])
        }
    
    def save_alerts(self, filepath: str) -> None:
        """Save alerts to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        alerts_data = [a.to_dict() for a in self.alerts.values()]
        with open(filepath, 'w') as f:
            json.dump(alerts_data, f, indent=2)
        logger.info(f"Saved {len(alerts_data)} alerts to {filepath}")
    
    def load_alerts(self, filepath: str) -> None:
        """Load alerts from file"""
        if not Path(filepath).exists():
            return
        
        with open(filepath, 'r') as f:
            alerts_data = json.load(f)
        
        for data in alerts_data:
            alert = Alert(
                id=data['id'],
                type=AlertType(data['type']),
                severity=AlertSeverity(data['severity']),
                title=data['title'],
                message=data['message'],
                context=data['context'],
                outlet_id=data['outlet_id'],
                product_id=data['product_id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                created_at=datetime.fromisoformat(data['created_at']),
                acknowledged=data['acknowledged'],
                acknowledged_by=data['acknowledged_by'],
                resolved=data['resolved']
            )
            self.alerts[alert.id] = alert
        
        logger.info(f"Loaded {len(alerts_data)} alerts from {filepath}")


# Convenience functions for common alerts
class AlertFactory:
    """Factory for creating common alert types"""
    
    @staticmethod
    def forecast_deviation(
        outlet_id: str,
        product_id: str,
        actual: float,
        forecast: float,
        service: AlertService
    ) -> Optional[Alert]:
        """Create forecast deviation alert"""
        is_anomaly, deviation = AnomalyDetector.detect_deviation(actual, forecast, threshold_pct=15)
        
        if not is_anomaly:
            return None
        
        return service.create_alert(
            alert_type=AlertType.FORECAST_ANOMALY,
            severity=AlertSeverity.WARNING if deviation < 30 else AlertSeverity.CRITICAL,
            title=f"Forecast Deviation: {product_id}",
            message=f"Actual sales ({actual:.0f}) deviated {deviation:.1f}% from forecast ({forecast:.0f})",
            context={
                'actual': actual,
                'forecast': forecast,
                'deviation_pct': deviation
            },
            outlet_id=outlet_id,
            product_id=product_id
        )
    
    @staticmethod
    def stock_depletion(
        outlet_id: str,
        product_id: str,
        stock: float,
        reorder_point: float,
        service: AlertService
    ) -> Optional[Alert]:
        """Create low stock alert"""
        if stock > reorder_point:
            return None
        
        return service.create_alert(
            alert_type=AlertType.STOCK_DEPLETION,
            severity=AlertSeverity.CRITICAL,
            title=f"Low Stock Alert: {product_id}",
            message=f"Stock level ({stock:.0f}) below reorder point ({reorder_point:.0f})",
            context={
                'stock': stock,
                'reorder_point': reorder_point,
                'urgency': 'immediate' if stock < reorder_point * 0.5 else 'soon'
            },
            outlet_id=outlet_id,
            product_id=product_id
        )


# Example usage
if __name__ == "__main__":
    print("✓ Real-Time Alert System ready for integration")
    print("\nExample usage:")
    print("""
    service = AlertService()
    service.add_webhook("https://your-webhook-url.com/alerts")
    
    # Create alert
    alert = AlertFactory.forecast_deviation(
        outlet_id="outlet_1",
        product_id="coffee",
        actual=150,
        forecast=120,
        service=service
    )
    
    # Send alert
    await service.send_alert(alert)
    
    # Get summary
    summary = service.get_alert_summary()
    """)
