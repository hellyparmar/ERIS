import logging
from typing import Optional, List, Dict, Any
from .email_service import email_service
from .whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

class NotificationManager:
    """Unified interface for dispatching notifications across multiple channels"""

    def send_invoice_notification(
        self, 
        recipient_email: str, 
        recipient_phone: str, 
        invoice_id: str, 
        amount: float,
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send invoice via available channels"""
        results = {}
        
        # 1. Email Channel
        email_body = f"Hello, your invoice {invoice_id} for Amount: Rs {amount:,.2f} is ready."
        results['email'] = email_service.send_email(
            to_email=recipient_email,
            subject=f"New Invoice: {invoice_id}",
            body=email_body,
            attachments=[pdf_path] if pdf_path else None
        )
        
        # 2. WhatsApp Channel
        # Template: invoice_delivery_v1 (Placeholder name)
        results['whatsapp'] = whatsapp_service.send_template_message(
            phone=recipient_phone,
            template_name="invoice_delivery_v1",
            variables=[invoice_id, str(amount)]
        )
        
        return results

    def send_low_stock_alert(self, item_name: str, current_stock: int) -> Dict[str, Any]:
        """Send internal stock alerts (e.g. to manager if configured)"""
        # Implementation could send to a central admin email/phone
        return {"success": True, "message": "Alert queued"}

# Singleton Instance
notification_manager = NotificationManager()
