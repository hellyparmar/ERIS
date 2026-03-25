"""
EventBus Event Definitions - System Alerts
Defines event types and structures for anomaly detection alerts.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate action required
    WARNING = "warning"    # Review needed
    INFO = "info"          # Informational only


class EventType(str, Enum):
    """System event types"""
    SYSTEM_ALERT = "system_alert"
    ANOMALY_DETECTED = "anomaly_detected"
    FRAUD_ALERT = "fraud_alert"
    INVENTORY_ALERT = "inventory_alert"


@dataclass
class SystemAlertEvent:
    """
    System Alert Event - Published to EventBus
    Triggered when anomalies are detected.
    
    Can be consumed by:
    - WhatsApp notification handler
    - Email alerting system
    - Mobile push notifications
    - Slack/Teams webhooks
    - Dashboard real-time updates
    """
    
    # Basic identification
    title: str
    message: str
    severity: AlertSeverity
    category: str  # e.g., "anomaly_detection", "fraud", "inventory"
    
    # Event metadata
    event_type: EventType = EventType.SYSTEM_ALERT
    triggered_at: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: f"ALERT-{datetime.now().timestamp()}")
    
    # Related entities
    related_product_ids: List[int] = field(default_factory=list)
    related_user_ids: List[int] = field(default_factory=list)
    related_tenant_id: Optional[int] = None
    
    # Detailed information
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Action & resolution
    action_required: bool = True
    action_type: Optional[str] = None  # e.g., "review", "investigate", "remediate"
    action_deadline: Optional[datetime] = None
    
    # Acknowledgment tracking
    acknowledged: bool = False
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Convert enums to strings
        data['severity'] = self.severity.value
        data['event_type'] = self.event_type.value
        
        # Convert datetimes to ISO format
        data['triggered_at'] = self.triggered_at.isoformat()
        if self.action_deadline:
            data['action_deadline'] = self.action_deadline.isoformat()
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemAlertEvent':
        """Create instance from dictionary."""
        # Convert string enums back to Enum
        if isinstance(data.get('severity'), str):
            data['severity'] = AlertSeverity(data['severity'])
        if isinstance(data.get('event_type'), str):
            data['event_type'] = EventType(data['event_type'])
        
        # Convert ISO strings back to datetime
        for field_name in ['triggered_at', 'action_deadline', 'acknowledged_at']:
            if isinstance(data.get(field_name), str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)


@dataclass
class DiscountFraudAlert(SystemAlertEvent):
    """Specialized alert for discount fraud detection"""
    
    event_type: EventType = field(default=EventType.FRAUD_ALERT)
    category: str = field(default="discount_fraud")
    
    # Additional fraud-specific fields
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    unit_price: float = 0.0
    sale_id: Optional[int] = None
    sale_date: Optional[datetime] = None


@dataclass
class SalesDropAlert(SystemAlertEvent):
    """Specialized alert for sales drop detection"""
    
    event_type: EventType = field(default=EventType.ANOMALY_DETECTED)
    category: str = field(default="sales_drop")
    
    # Sales metrics
    units_sold: float = 0.0
    rolling_average: float = 0.0
    drop_percent: float = 0.0
    lookback_days: int = 28


@dataclass
class GhostInventoryAlert(SystemAlertEvent):
    """Specialized alert for ghost inventory detection"""
    
    event_type: EventType = field(default=EventType.INVENTORY_ALERT)
    category: str = field(default="ghost_inventory")
    
    # Inventory metrics
    stock_level: int = 0
    days_without_sales: int = 0
    holding_cost: float = 0.0
    last_sale_date: Optional[datetime] = None


# ============================================================================
# EVENT HANDLER REGISTRY
# ============================================================================

class EventHandlerRegistry:
    """
    Registry for EventBus handlers.
    Maps event types to their handlers.
    """
    
    _handlers = {}
    
    @classmethod
    def register(cls, event_type: str, handler_name: str, handler_func):
        """Register a handler for an event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = {}
        
        cls._handlers[event_type][handler_name] = handler_func
    
    @classmethod
    def get_handlers(cls, event_type: str) -> Dict[str, Any]:
        """Get all handlers for an event type."""
        return cls._handlers.get(event_type, {})
    
    @classmethod
    def get_handler(cls, event_type: str, handler_name: str):
        """Get specific handler."""
        return cls._handlers.get(event_type, {}).get(handler_name)


# ============================================================================
# BUILT-IN HANDLERS (REGISTRATION)
# ============================================================================

# These will be registered by the EventBus initialization
# See: api/events/event_bus.py

HANDLER_REGISTRY = {
    'system_alert': {
        'whatsapp': 'api.handlers.whatsapp_anomaly_handler:send_anomaly_alert',
        'database_logger': 'api.handlers.alert_logger:log_alert_to_database',
        'slack_webhook': 'api.handlers.slack_handler:send_to_slack',
        'mobile_push': 'api.handlers.push_notifier:send_push_notification',
    }
}
