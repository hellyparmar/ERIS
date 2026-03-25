"""
Phase 6 - Task 3: Event-Driven Architecture Module
Provides event publishing and handling framework for post-sale event chains
"""

from .events import (
    Event,
    EventBus,
    EventType,
    EventStatus,
    SaleCreatedEvent,
    InventoryDeductedEvent,
    LoyaltyPointsAwardedEvent,
    ReorderAlertEvent,
    ForecastUpdatedEvent,
    AnomalyDetectedEvent,
    get_event_bus,
)

from .handlers import (
    InventoryDeductionHandler,
    LoyaltyPointsHandler,
    ReorderAlertHandler,
    ForecastUpdateHandler,
    AnomalyDetectionHandler,
    register_event_handlers,
)

__all__ = [
    # Events
    "Event",
    "EventBus",
    "EventType",
    "EventStatus",
    "SaleCreatedEvent",
    "InventoryDeductedEvent",
    "LoyaltyPointsAwardedEvent",
    "ReorderAlertEvent",
    "ForecastUpdatedEvent",
    "AnomalyDetectedEvent",
    "get_event_bus",
    # Handlers
    "InventoryDeductionHandler",
    "LoyaltyPointsHandler",
    "ReorderAlertHandler",
    "ForecastUpdateHandler",
    "AnomalyDetectionHandler",
    "register_event_handlers",
]
