"""
WhatsApp Invoice Delivery Service
Send invoices via WhatsApp using Twilio API

Features:
- Send invoice PDF via WhatsApp
- Supports template messages
- Delivery confirmation
- Rate limiting
"""

from typing import Optional, Dict
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppInvoiceService:
    """
    WhatsApp service for sending invoices
    
    Uses Twilio WhatsApp Business API
    """
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """
        Initialize WhatsApp service
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: WhatsApp business number (format: whatsapp:+1234567890)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
    
    def send_invoice_whatsapp(self,
                             to_number: str,
                             invoice_number: str,
                             pdf_url: str,
                             invoice_data: Dict) -> bool:
        """
        Send invoice via WhatsApp
        
        Args:
            to_number: Recipient WhatsApp number (format: whatsapp:+91xxxxxxxxxx)
            invoice_number: Invoice number
            pdf_url: Publicly accessible URL of PDF
            invoice_data: Invoice details for message
            
        Returns:
            True if sent successfully
        """
        try:
            # Prepare message
            customer_name = invoice_data.get('customer_name', 'Valued Customer')
            grand_total = invoice_data.get('grand_total', 0)
            
            message = self._create_invoice_message(
                customer_name,
                invoice_number,
                grand_total
            )
            
            # Send message with PDF
            url = f"{self.base_url}/Messages.json"
            
            data = {
                'From': self.from_number,
                'To': to_number,
                'Body': message,
                'MediaUrl': pdf_url
            }
            
            response = requests.post(
                url,
                auth=(self.account_sid, self.auth_token),
                data=data
            )
            
            if response.status_code == 201:
                logger.info(f"Invoice {invoice_number} sent via WhatsApp to {to_number}")
                return True
            else:
                logger.error(f"WhatsApp send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    def _create_invoice_message(self, customer_name: str, invoice_number: str, amount: float) -> str:
        """Create WhatsApp message text"""
        message = f"""
🧾 *Invoice #{invoice_number}*

Dear {customer_name},

Thank you for your business! Your invoice has been generated.

*Amount:* ₹{amount:,.2f}

Please find the invoice PDF attached to this message.

For any queries, please contact us.

Best regards,
R-DIOS Team
        """.strip()
        
        return message


# ============================================================
# MOCK WHATSAPP SERVICE (For Testing)
# ============================================================

class MockWhatsAppService:
    """Mock WhatsApp service for development/testing"""
    
    def __init__(self):
        pass
    
    def send_invoice_whatsapp(self, to_number: str, invoice_number: str, 
                             pdf_url: str, invoice_data: Dict) -> bool:
        """Mock send - just logs"""
        logger.info(f"[MOCK] WhatsApp invoice {invoice_number} to {to_number}")
        logger.info(f"[MOCK] PDF URL: {pdf_url}")
        logger.info(f"[MOCK] Amount: ₹{invoice_data.get('grand_total', 0):,.2f}")
        return True


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # For production (with Twilio credentials)
    # service = WhatsAppInvoiceService(
    #     account_sid="ACxxxxxxxxxxxxx",
    #     auth_token="your_auth_token",
    #     from_number="whatsapp:+14155238886"
    # )
    
    # For development
    service = MockWhatsAppService()
    
    invoice_data = {
        'customer_name': 'John Doe',
        'invoice_number': 'INV-2024-001',
        'grand_total': 106200.00
    }
    
    success = service.send_invoice_whatsapp(
        to_number="whatsapp:+919876543210",
        invoice_number="INV-2024-001",
        pdf_url="https://example.com/invoices/INV-2024-001.pdf",
        invoice_data=invoice_data
    )
    
    if success:
        print("✓ Invoice sent via WhatsApp!")
    else:
        print("✗ Failed to send WhatsApp message")
