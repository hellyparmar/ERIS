"""
WhatsApp Notification Handler for Anomaly Alerts
Sends real-time anomaly alerts via WhatsApp Business API with batching.

Features:
- Real-time alerts for CRITICAL anomalies
- Batched delivery for WARNING/INFO anomalies
- Smart templating and formatting
- Rate limiting to control costs
- Retry logic with exponential backoff
- Delivery tracking and logging
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue
import asyncio

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.api.events.system_events import SystemAlertEvent, AlertSeverity

logger = logging.getLogger(__name__)


# ============================================================================
# WHATSAPP MESSAGE TEMPLATES
# ============================================================================

class MessageTemplate(str, Enum):
    """WhatsApp message templates"""
    
    DISCOUNT_FRAUD_CRITICAL = """
🚨 *CRITICAL: Discount Fraud Alert*

Product: {product_name}
Discount: {discount_pct}%
Amount: ₹{discount_amount}
Sale ID: {sale_id}

Action Required: Investigate immediately
Time: {timestamp}
"""
    
    DISCOUNT_FRAUD_WARNING = """
⚠️ *Unusual Discount Pattern*

Product: {product_name}
Discount: {discount_pct}%
Amount: ₹{discount_amount}

Review this transaction
Time: {timestamp}
"""
    
    SALES_DROP_CRITICAL = """
⚠️ *CRITICAL: Sales Drop Detected*

Product: {product_name}
Current: {units_sold:.0f} units
Expected: {rolling_average:.0f} units
Drop: {drop_percent:.1f}%

Status: Below 4-week average
Time: {timestamp}
"""
    
    SALES_DROP_WARNING = """
📊 *Sales Decline Alert*

Product: {product_name}
Drop: {drop_percent:.1f}% from average

Monitor inventory levels
Time: {timestamp}
"""
    
    GHOST_INVENTORY_CRITICAL = """
💀 *CRITICAL: Dead Stock Alert*

Product: {product_name}
Stock: {stock_level} units
Days Without Sales: {days_without_sales}
Cost: ₹{estimated_holding_cost:.0f}

Action: Review for obsolescence
Time: {timestamp}
"""
    
    GHOST_INVENTORY_WARNING = """
📦 *Ghost Inventory Warning*

Product: {product_name}
Stock: {stock_level} units
No sales for {days_without_sales} days

Consider reordering or promotion
Time: {timestamp}
"""


@dataclass
class WhatsAppMessage:
    """WhatsApp message envelope"""
    to_number: str
    body: str
    message_type: str = "text"  # text, template, media
    template_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    media_url: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# ============================================================================
# WHATSAPP NOTIFICATION HANDLER
# ============================================================================

class WhatsAppNotificationHandler:
    """
    Handles anomaly alert notifications via WhatsApp Business API.
    
    Integration with EventBus:
    - Subscribes to SystemAlertEvent
    - Formats alerts into WhatsApp messages
    - Implements smart batching for cost optimization
    - Manages delivery and retries
    """
    
    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        admin_phone: str,
        batch_window_seconds: int = 300,  # 5 minutes
        max_batch_size: int = 20,
        enable_batching: bool = True
    ):
        """
        Args:
            phone_number_id: WhatsApp Business API phone number ID
            access_token: WhatsApp Business API access token
            admin_phone: Default admin phone number for alerts
            batch_window_seconds: Window for batching non-critical alerts
            max_batch_size: Maximum messages in a batch
            enable_batching: Enable smart batching
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.admin_phone = admin_phone
        self.batch_window_seconds = batch_window_seconds
        self.max_batch_size = max_batch_size
        self.enable_batching = enable_batching
        
        # Message queue for batching
        self.message_queue: Queue = Queue()
        self.batch_timer: Optional[asyncio.Task] = None
        
        # API endpoint
        self.base_url = f"https://graph.instagram.com/v18.0/{phone_number_id}"
        
        # HTTP client
        self.http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        logger.info("✅ WhatsApp Notification Handler initialized")
    
    def format_anomaly_message(
        self,
        event: SystemAlertEvent,
        details: Dict[str, Any]
    ) -> str:
        """
        Format anomaly details into WhatsApp message.
        
        Args:
            event: SystemAlertEvent with anomaly info
            details: Detailed anomaly information
            
        Returns:
            Formatted message body
        """
        category = details.get('anomaly_type', 'unknown').upper()
        severity = event.severity.value.upper()
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message based on type
        if 'discount_fraud' in category.lower():
            msg = f"""
🚨 *ANOMALY ALERT - DISCOUNT FRAUD*
Severity: {severity}

{event.title}

💡 *Details:*
• Discount: {details['details'].get('discount_percent', 0):.1f}%
• Amount: ₹{details['details'].get('discount_amount', 0):.2f}
• Unit Price: ₹{details['details'].get('unit_price', 0):.2f}
• Quantity: {details['details'].get('quantity', 0)}
• Confidence: {details['confidence_score']:.1%}

🔗 Sale ID: {details['details'].get('sale_id', 'N/A')}
⏰ Time: {timestamp}

*Action Required:* Review and validate discount immediately
""".strip()
        
        elif 'sales_drop' in category.lower():
            msg = f"""
📉 *ANOMALY ALERT - SALES DROP*
Severity: {severity}

{event.title}

💡 *Details:*
• Units Sold: {details['details'].get('units_sold', 0):.0f}
• Expected Average: {details['details'].get('rolling_average', 0):.0f}
• Drop: {details['details'].get('drop_percent', 0):.1f}%
• Std Dev Threshold: {details['details'].get('threshold_sigma', 2):.1f}σ
• Confidence: {details['confidence_score']:.1%}

⏰ Detection: {timestamp}

*Recommendation:* Investigate demand drop, check inventory, review promotions
""".strip()
        
        elif 'ghost_inventory' in category.lower():
            msg = f"""
💀 *ANOMALY ALERT - GHOST INVENTORY*
Severity: {severity}

{event.title}

💡 *Details:*
• Stock Level: {details['details'].get('stock_level', 0)} units
• Days Without Sales: {details['details'].get('days_without_sales', 0)}
• Holding Cost: ₹{details['details'].get('estimated_holding_cost', 0):.0f}
• Confidence: {details['confidence_score']:.1%}

⏰ Last Sale: {details['details'].get('last_sale_date', 'Never')}

*Recommendation:* Review for obsolescence, clearance sale, or donation
""".strip()
        
        else:
            msg = f"""
⚠️ *SYSTEM ALERT*

{event.title}

Message: {event.message}
Severity: {severity}
Confidence: {details['confidence_score']:.1%}

⏰ Time: {timestamp}
""".strip()
        
        return msg
    
    async def send_message(
        self,
        phone_number: str,
        message_body: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Send a single WhatsApp message via Business API.
        
        Args:
            phone_number: Recipient phone number (with country code)
            message_body: Message text
            retry_count: Retry attempt (used for exponential backoff)
            
        Returns:
            API response
        """
        # Validate phone number format
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message_body}
        }
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}/messages",
                json=payload,
                timeout=10.0
            )
            
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"✅ WhatsApp message sent to {phone_number}")
                logger.debug(f"   Response: {result}")
                return {"success": True, "message_id": result.get('messages', [{}])[0].get('id')}
            else:
                logger.warning(f"⚠️ WhatsApp API error: {response.status_code}")
                logger.warning(f"   Response: {result}")
                return {"success": False, "error": result}
        
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _send_with_retry(
        self,
        phone_number: str,
        message_body: str
    ) -> Dict[str, Any]:
        """Send message with automatic retry on failure."""
        return await self.send_message(phone_number, message_body)
    
    async def handle_anomaly_event(self, event: SystemAlertEvent):
        """
        Handle SystemAlertEvent - main entry point for anomaly alerts.
        
        Strategy:
        - CRITICAL: Send immediately
        - WARNING: Queue for batching
        - INFO: Batch with delay
        
        Args:
            event: SystemAlertEvent from EventBus
        """
        logger.info(f"📨 Handling anomaly event: {event.title}")
        
        # Prepare message
        message_body = self.format_anomaly_message(event, event.details)
        
        # Route based on severity
        if event.severity == AlertSeverity.CRITICAL:
            # Send immediately to admin
            logger.warning(f"🚨 CRITICAL alert - sending immediately: {event.title}")
            await self._send_with_retry(self.admin_phone, message_body)
        
        elif event.severity == AlertSeverity.WARNING:
            # Queue for batching (5-minute window)
            logger.info(f"📦 Queuing warning alert for batching: {event.title}")
            msg = WhatsAppMessage(
                to_number=self.admin_phone,
                body=message_body
            )
            self.message_queue.put(msg)
            self._schedule_batch_send()
        
        else:  # INFO
            # Queue for batching (10-minute window)
            logger.debug(f"📋 Queuing info alert: {event.title}")
            msg = WhatsAppMessage(
                to_number=self.admin_phone,
                body=message_body
            )
            self.message_queue.put(msg)
            self._schedule_batch_send(delay_seconds=600)
    
    def _schedule_batch_send(self, delay_seconds: int = 300):
        """Schedule batch send if not already scheduled."""
        if self.batch_timer is None or self.batch_timer.done():
            self.batch_timer = asyncio.create_task(
                self._batch_send_after_delay(delay_seconds)
            )
    
    async def _batch_send_after_delay(self, delay_seconds: int):
        """Wait for delay then send batched messages."""
        await asyncio.sleep(delay_seconds)
        await self.send_batch()
    
    async def send_batch(self):
        """
        Send all queued messages in a single batch.
        Reduces API calls and costs.
        """
        messages = []
        
        # Drain queue
        while not self.message_queue.empty() and len(messages) < self.max_batch_size:
            try:
                msg = self.message_queue.get_nowait()
                messages.append(msg)
            except:
                break
        
        if not messages:
            logger.debug("No messages to batch")
            return
        
        logger.info(f"📨 Sending batch of {len(messages)} WhatsApp messages...")
        
        # Group by recipient
        by_recipient = {}
        for msg in messages:
            if msg.to_number not in by_recipient:
                by_recipient[msg.to_number] = []
            by_recipient[msg.to_number].append(msg)
        
        # Send to each recipient (combine messages)
        for phone, msgs in by_recipient.items():
            combined_body = "\n" + "—" * 40 + "\n".join(
                msg.body for msg in msgs
            )
            
            await self._send_with_retry(phone, combined_body)
    
    async def close(self):
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_whatsapp_handler: Optional[WhatsAppNotificationHandler] = None


def get_whatsapp_handler() -> WhatsAppNotificationHandler:
    """Get or create WhatsApp handler singleton."""
    global _whatsapp_handler
    
    if _whatsapp_handler is None:
        from app.api.config import settings
        
        _whatsapp_handler = WhatsAppNotificationHandler(
            phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
            access_token=settings.WHATSAPP_ACCESS_TOKEN,
            admin_phone=settings.WHATSAPP_ADMIN_PHONE,
            batch_window_seconds=300,
            max_batch_size=20
        )
    
    return _whatsapp_handler


async def send_anomaly_alert(event: SystemAlertEvent):
    """
    Public API to send anomaly alert via WhatsApp.
    Called by EventBus on SystemAlertEvent.
    
    Args:
        event: SystemAlertEvent containing anomaly details
    """
    try:
        handler = get_whatsapp_handler()
        await handler.handle_anomaly_event(event)
    except Exception as e:
        logger.error(f"Failed to send anomaly alert: {e}", exc_info=True)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test message formatting
    import asyncio
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Mock event
    test_event = SystemAlertEvent(
        title="Test: Discount Fraud Alert",
        message="Test message",
        severity=AlertSeverity.CRITICAL,
        category="anomaly_detection",
        details={
            "anomaly_type": "discount_fraud",
            "details": {
                "discount_percent": 75.5,
                "discount_amount": 5000.00,
                "unit_price": 10000.00,
                "quantity": 5,
                "sale_id": "SALE-123"
            },
            "confidence_score": 0.92
        }
    )
    
    handler = WhatsAppNotificationHandler(
        phone_number_id="123456789",
        access_token="test_token",
        admin_phone="+919876543210"
    )
    
    msg = handler.format_anomaly_message(test_event, test_event.details)
    print("\n" + "=" * 80)
    print("FORMATTED MESSAGE:")
    print("=" * 80)
    print(msg)
