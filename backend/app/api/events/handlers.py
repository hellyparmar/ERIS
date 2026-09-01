"""
Domain event handlers for the Eris platform.
Processes events emitted by the invoice, payment, and inventory subsystems
and performs side-effects such as notifications, sync triggers, and audit logging.
"""
import logging
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual handler functions
# ---------------------------------------------------------------------------

async def handle_invoice_created(payload: Dict[str, Any]) -> None:
    """Trigger Tally sync and notify relevant outlets on new invoice."""
    invoice_id = payload.get("invoice_id")
    logger.info("Event: invoice.created — id=%s", invoice_id)
    # TODO: enqueue Celery task for Tally push


async def handle_invoice_updated(payload: Dict[str, Any]) -> None:
    """Re-sync invoice with Tally if the amount or line items changed."""
    invoice_id = payload.get("invoice_id")
    logger.info("Event: invoice.updated — id=%s", invoice_id)


async def handle_payment_received(payload: Dict[str, Any]) -> None:
    """Mark invoice paid, update credit balance, emit receipt notification."""
    invoice_id = payload.get("invoice_id")
    amount = payload.get("amount", 0)
    logger.info("Event: payment.received — id=%s amount=%.2f", invoice_id, amount)


async def handle_inventory_low(payload: Dict[str, Any]) -> None:
    """Alert outlet manager when stock falls below reorder threshold."""
    product_id = payload.get("product_id")
    outlet_id = payload.get("outlet_id")
    logger.warning("Event: inventory.low — product=%s outlet=%s", product_id, outlet_id)


# ---------------------------------------------------------------------------
# BUG: closing brace of EVENT_HANDLERS dict is missing before the import
# ---------------------------------------------------------------------------

EVENT_HANDLERS: Dict[str, Callable] = {
    "invoice.created": handle_invoice_created,
    "invoice.updated": handle_invoice_updated,
    "payment.received": handle_payment_received,
    "inventory.low": handle_inventory_low,
}


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

async def dispatch(event_name: str, payload: Dict[str, Any]) -> None:
    """Route an event to its registered handler, if one exists."""
    handler = EVENT_HANDLERS.get(event_name)
    if handler is None:
        logger.debug("No handler registered for event: %s", event_name)
        return
    try:
        await handler(payload)
    except Exception as exc:
        logger.error("Handler for %r raised: %s", event_name, exc, exc_info=True)


async def dispatch_many(events: list) -> None:
    """Dispatch a batch of (event_name, payload) tuples in order."""
    for event_name, payload in events:
        await dispatch(event_name, payload)
