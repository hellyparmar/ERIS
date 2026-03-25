import logging
from typing import List, Dict, Any, Optional
from .email_service import email_service
from .whatsapp_service import whatsapp_service
from app.config import settings

logger = logging.getLogger(__name__)

class NotificationManager:
    """Unified interface for dispatching notifications across multiple channels"""

    def __init__(self):
        self.email = email_service
        self.whatsapp = whatsapp_service

    async def send_notification(
        self,
        notification_type: str,
        recipients: Dict[str, str], # {"email": "...", "phone": "..."}
        data: Dict[str, Any],
        channels: List[str] = ['email']
    ) -> Dict[str, Any]:
        """Route to appropriate channel based on settings and availability"""
        results = {}
        
        if 'email' in channels and settings.ENABLE_EMAIL:
            results['email'] = await self.email.send_email(
                to=recipients.get('email'),
                subject=data.get('subject', 'Notification from R-DIOS'),
                body=data.get('body', ''),
                attachments=data.get('attachments')
            )
        
        if 'whatsapp' in channels and settings.ENABLE_WHATSAPP:
            results['whatsapp'] = await self.whatsapp.send_template_message(
                phone=recipients.get('phone'),
                template_id=data.get('template_id'),
                variables=data.get('variables', {})
            )
            
        return results

    async def send_low_stock_alert(self, product_data: Dict[str, Any], manager_contacts: Dict[str, str]):
        """Send alert when product is low"""
        subject = f"Low Stock Alert: {product_data.get('name')}"
        body = f"The product {product_data.get('name')} (ID: {product_data.get('id')}) is low on stock. Current: {product_data.get('stock')}"
        
        await self.send_notification(
            notification_type="low_stock",
            recipients=manager_contacts,
            data={"subject": subject, "body": body},
            channels=['email']
        )

    async def send_invoice_notification(self, invoice_data: Dict[str, Any], customer: Dict[str, str], pdf_path: str):
        """Send invoice via email (primary) and WhatsApp (if enabled)"""
        # Email
        await self.email.send_invoice(customer_email=customer.get('email'), invoice_pdf_path=pdf_path)
        
        # WhatsApp (optional)
        if settings.ENABLE_WHATSAPP:
            await self.whatsapp.send_template_message(
                phone=customer.get('phone'),
                template_id="invoice_delivery_v1",
                variables={"invoice_id": invoice_data.get('id'), "amount": str(invoice_data.get('amount'))}
            )

# Singleton Instance
notification_manager = NotificationManager()
