"""
Phase 6 - Task 3: Event-Driven Architecture
Post-sale event system with inventory deduction, loyalty points, reorder alerts,
forecast updates, and anomaly detection

Event Types:
- SaleCreatedEvent: Triggered when a sale is completed
- InventoryUpdatedEvent: Triggered when inventory changes
- CustomerPurchaseEvent: Triggered for loyalty program
- AnomalyDetectedEvent: Triggered by anomaly detection system
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types in the post-sale event chain"""
    SALE_CREATED = "sale_created"
    INVENTORY_DEDUCTED = "inventory_deducted"
    LOW_INVENTORY_ALERT = "low_inventory_alert"
    REORDER_ALERT = "reorder_alert"
    LOYALTY_POINTS_AWARDED = "loyalty_points_awarded"
    FORECAST_UPDATED = "forecast_updated"
    ANOMALY_DETECTED = "anomaly_detected"
    FORECAST_ACCURACY_LOW = "forecast_accuracy_low"


class EventStatus(str, Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Event:
    """
    Base event class for all domain events
    """
    event_type: EventType
    aggregate_id: uuid.UUID  # Usually sale_id or inventory_id
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    data: Dict[str, Any] = field(default_factory=dict)
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "aggregate_id": str(self.aggregate_id),
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "status": self.status.value,
            "retry_count": self.retry_count,
        }


@dataclass
class SaleCreatedEvent(Event):
    """
    Triggered when a sale transaction is completed
    
    Initiates the post-sale event chain:
    1. Inventory deduction
    2. Loyalty points award
    3. Reorder alert check
    4. Forecast update
    5. Anomaly detection
    """
    
    def __post_init__(self):
        self.event_type = EventType.SALE_CREATED
    
    @property
    def sale_id(self) -> uuid.UUID:
        return self.aggregate_id
    
    @property
    def items(self) -> List[Dict]:
        """Sale line items"""
        return self.data.get('items', [])
    
    @property
    def total_amount(self) -> float:
        """Total sale amount"""
        return self.data.get('total_amount', 0.0)
    
    @property
    def customer_id(self) -> Optional[uuid.UUID]:
        """Customer ID if available"""
        cust_id = self.data.get('customer_id')
        return uuid.UUID(cust_id) if cust_id else None
    
    @property
    def store_id(self) -> Optional[uuid.UUID]:
        """Store/location ID"""
        store_id = self.data.get('store_id')
        return uuid.UUID(store_id) if store_id else None


@dataclass
class InventoryDeductedEvent(Event):
    """
    Triggered after inventory is deducted for a sale
    
    Contains details of items removed from stock
    """
    
    def __post_init__(self):
        self.event_type = EventType.INVENTORY_DEDUCTED
    
    @property
    def deductions(self) -> List[Dict]:
        """List of inventory deductions: {product_id, quantity, previous_stock, new_stock}"""
        return self.data.get('deductions', [])
    
    @property
    def sale_id(self) -> uuid.UUID:
        """Source sale ID"""
        return self.aggregate_id


@dataclass
class LoyaltyPointsAwardedEvent(Event):
    """
    Triggered when loyalty points are awarded to customer
    """
    
    def __post_init__(self):
        self.event_type = EventType.LOYALTY_POINTS_AWARDED
    
    @property
    def customer_id(self) -> uuid.UUID:
        cust_id = self.data.get('customer_id')
        return uuid.UUID(cust_id)
    
    @property
    def points_awarded(self) -> int:
        return self.data.get('points_awarded', 0)
    
    @property
    def total_points(self) -> int:
        return self.data.get('total_points', 0)


@dataclass
class ReorderAlertEvent(Event):
    """
    Triggered when product inventory falls below reorder point
    """
    
    def __post_init__(self):
        self.event_type = EventType.REORDER_ALERT
    
    @property
    def product_id(self) -> uuid.UUID:
        prod_id = self.data.get('product_id')
        return uuid.UUID(prod_id)
    
    @property
    def current_stock(self) -> int:
        return self.data.get('current_stock', 0)
    
    @property
    def reorder_point(self) -> int:
        return self.data.get('reorder_point', 0)
    
    @property
    def reorder_quantity(self) -> int:
        return self.data.get('reorder_quantity', 0)


@dataclass
class ForecastUpdatedEvent(Event):
    """
    Triggered when demand forecast is updated with new sale data
    """
    
    def __post_init__(self):
        self.event_type = EventType.FORECAST_UPDATED
    
    @property
    def product_id(self) -> uuid.UUID:
        prod_id = self.data.get('product_id')
        return uuid.UUID(prod_id)
    
    @property
    def forecast_data(self) -> Dict:
        return self.data.get('forecast_data', {})


@dataclass
class AnomalyDetectedEvent(Event):
    """
    Triggered when unusual patterns are detected in sales/inventory
    
    Anomalies can include:
    - Unusual sales volume for a product
    - Suspicious price points
    - Unusual customer behavior
    - Inventory discrepancies
    """
    
    def __post_init__(self):
        self.event_type = EventType.ANOMALY_DETECTED
    
    @property
    def anomaly_type(self) -> str:
        return self.data.get('anomaly_type', 'unknown')
    
    @property
    def anomaly_score(self) -> float:
        """Anomaly severity: 0.0 to 1.0"""
        return self.data.get('anomaly_score', 0.0)
    
    @property
    def details(self) -> Dict:
        return self.data.get('details', {})
    
    @property
    def recommendation(self) -> str:
        return self.data.get('recommendation', '')


class EventBus:
    """
    Central event bus for publishing and subscribing to events
    Manages event handlers and executes event processing pipeline
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[callable]] = {}
        self._event_store: List[Event] = []
        self._failed_events: List[Event] = []
    
    def subscribe(self, event_type: EventType, handler: callable):
        """
        Register an event handler for a specific event type
        
        Usage:
        ```python
        event_bus = EventBus()
        event_bus.subscribe(EventType.SALE_CREATED, handle_inventory_deduction)
        event_bus.subscribe(EventType.SALE_CREATED, handle_loyalty_points)
        ```
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__name__} for {event_type.value}")
    
    async def publish(self, event: Event) -> bool:
        """
        Publish an event to all registered handlers
        Returns True if all handlers succeeded
        """
        try:
            event.status = EventStatus.PROCESSING
            self._event_store.append(event)
            
            logger.info(f"Publishing event: {event.event_type.value} ({event.event_id})")
            
            handlers = self._handlers.get(event.event_type, [])
            
            if not handlers:
                logger.warning(f"No handlers registered for {event.event_type.value}")
                event.status = EventStatus.COMPLETED
                return True
            
            # Execute all handlers
            results = []
            for handler in handlers:
                try:
                    if hasattr(handler, '__self__'):
                        # Async method
                        result = await handler(event)
                    else:
                        # Try async first
                        import inspect
                        if inspect.iscoroutinefunction(handler):
                            result = await handler(event)
                        else:
                            result = handler(event)
                    
                    results.append(result)
                    logger.debug(f"Handler {handler.__name__} completed")
                    
                except Exception as e:
                    logger.error(f"Handler {handler.__name__} failed: {e}")
                    results.append(False)
            
            # All succeeded?
            success = all(results)
            
            if success:
                event.status = EventStatus.COMPLETED
                logger.info(f"Event {event.event_id} completed successfully")
            else:
                event.status = EventStatus.FAILED
                event.retry_count += 1
                
                if event.retry_count < event.max_retries:
                    event.status = EventStatus.RETRY
                    logger.warning(f"Event {event.event_id} will be retried")
                else:
                    self._failed_events.append(event)
                    logger.error(f"Event {event.event_id} failed after {event.max_retries} retries")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            event.status = EventStatus.FAILED
            self._failed_events.append(event)
            return False
    
    def get_events(self, event_type: Optional[EventType] = None, status: Optional[EventStatus] = None):
        """Retrieve events from store"""
        events = self._event_store
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if status:
            events = [e for e in events if e.status == status]
        
        return events
    
    def get_failed_events(self):
        """Get list of failed events for manual intervention"""
        return self._failed_events
    
    def retry_failed_event(self, event_id: uuid.UUID) -> bool:
        """Manually retry a failed event"""
        event = next((e for e in self._failed_events if e.event_id == event_id), None)
        
        if not event:
            logger.warning(f"Failed event {event_id} not found")
            return False
        
        event.status = EventStatus.PENDING
        event.retry_count = 0
        self._failed_events.remove(event)
        
        import asyncio
        return asyncio.run(self.publish(event))


# Global event bus instance
_event_bus_instance: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Get or create global event bus"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance
