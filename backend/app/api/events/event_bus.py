"""
EventBus - Pub/Sub System
Publish-Subscribe pattern for system-wide events.
Enables decoupled communication between anomaly detector and handlers.
"""

import logging
import asyncio
from typing import Callable, Dict, List, Any, Optional
from threading import Lock
from abc import ABC, abstractmethod

from app.api.events.system_events import SystemAlertEvent, EventType

logger = logging.getLogger(__name__)


# ============================================================================
# EVENT LISTENER INTERFACE
# ============================================================================

class EventListener(ABC):
    """Base class for event listeners"""
    
    @abstractmethod
    async def handle(self, event: SystemAlertEvent) -> Any:
        """Handle the event"""
        pass


# ============================================================================
# EVENT BUS IMPLEMENTATION
# ============================================================================

class EventBus:
    """
    Publish-Subscribe Event Bus
    
    Usage:
        event_bus.subscribe('system_alert', handler_function)
        event_bus.publish(SystemAlertEvent(...))
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = Lock()
        logger.info("✅ EventBus initialized")
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        handler_name: str = None
    ) -> str:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to listen for
            handler: Async function to handle events
            handler_name: Optional name for this handler (for logging)
            
        Returns:
            Subscription ID
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            self._subscribers[event_type].append(handler)
            
            handler_id = f"{event_type}:{handler_name or handler.__name__}"
            logger.info(f"📥 Subscribed to {event_type}: {handler_id}")
            
            return handler_id
    
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable
    ) -> bool:
        """Unsubscribe from events."""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    logger.info(f"📤 Unsubscribed from {event_type}")
                    return True
                except ValueError:
                    return False
        
        return False
    
    async def publish(
        self,
        event: SystemAlertEvent,
        wait_for_handlers: bool = False
    ) -> Dict[str, Any]:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
            wait_for_handlers: If True, wait for all handlers to complete
                              If False, fire-and-forget (non-blocking)
        
        Returns:
            Results from handlers
        """
        event_type = event.event_type.value
        
        logger.info(f"📢 Publishing event: {event_type} - {event.title}")
        
        handlers = self._subscribers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"  No subscribers for {event_type}")
            return {"published": True, "handlers_notified": 0}
        
        # Create coroutines for all handlers
        tasks = [
            self._call_handler(handler, event, event_type)
            for handler in handlers
        ]
        
        if wait_for_handlers:
            # Wait for all handlers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"  ✓ {len(results)} handlers executed")
            return {
                "published": True,
                "handlers_notified": len(handlers),
                "results": results
            }
        else:
            # Fire-and-forget
            asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))
            logger.info(f"  ✓ {len(handlers)} handlers notified (async)")
            return {
                "published": True,
                "handlers_notified": len(handlers)
            }
    
    async def _call_handler(
        self,
        handler: Callable,
        event: SystemAlertEvent,
        event_type: str
    ) -> Any:
        """Call a handler function safely."""
        try:
            handler_name = handler.__name__
            logger.debug(f"  → Calling handler: {handler_name}")
            
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                result = await handler(event)
            else:
                result = handler(event)
            
            logger.debug(f"  ✓ {handler_name} completed")
            return {"success": True, "handler": handler_name, "result": result}
        
        except Exception as e:
            logger.error(f"  ✗ Handler {handler.__name__} failed: {e}", exc_info=True)
            return {"success": False, "handler": handler.__name__, "error": str(e)}
    
    def get_subscribers(self, event_type: str = None) -> Dict[str, List[str]]:
        """Get list of subscribers."""
        if event_type:
            handlers = self._subscribers.get(event_type, [])
            return {event_type: [h.__name__ for h in handlers]}
        
        return {
            et: [h.__name__ for h in handlers]
            for et, handlers in self._subscribers.items()
        }


# ============================================================================
# GLOBAL SINGLETON
# ============================================================================

event_bus = EventBus()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def publish_alert(
    title: str,
    message: str,
    severity: str,
    category: str = "system",
    details: Dict[str, Any] = None,
    affected_products: List[int] = None,
    wait_for_handlers: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to create and publish a SystemAlertEvent.
    
    Args:
        title: Alert title
        message: Alert message
        severity: AlertSeverity enum value
        category: Alert category
        details: Additional details dict
        affected_products: List of affected product IDs
        wait_for_handlers: Wait for handlers to complete
        
    Returns:
        Publication result
    """
    from app.api.events.system_events import AlertSeverity
    
    event = SystemAlertEvent(
        title=title,
        message=message,
        severity=AlertSeverity(severity),
        category=category,
        details=details or {},
        related_product_ids=affected_products or []
    )
    
    return await event_bus.publish(event, wait_for_handlers=wait_for_handlers)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test handler
    async def test_handler(event: SystemAlertEvent):
        logger.info(f"Test handler received: {event.title}")
        await asyncio.sleep(0.5)
        return "Processed successfully"
    
    async def main():
        # Subscribe
        event_bus.subscribe('system_alert', test_handler)
        
        # Publish
        from app.api.events.system_events import AlertSeverity
        
        event = SystemAlertEvent(
            title="Test Alert",
            message="This is a test",
            severity=AlertSeverity.WARNING,
            category="test"
        )
        
        result = await event_bus.publish(event, wait_for_handlers=True)
        print(f"\nResult: {result}")
    
    asyncio.run(main())
