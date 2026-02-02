"""
Enhanced WhatsApp Service with Circuit Breaker
Resilient WhatsApp messaging with automatic failover
"""

import os
import logging
from typing import Optional, List, Dict
from datetime import datetime

# Circuit breaker imports
from api.utils.circuit_breakers import twilio_circuit_breaker, FallbackHandler

# Twilio imports
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed")

# Service imports
from api.middleware.rate_limiter import rate_limiter
from api.services.email_service import email_service

logger = logging.getLogger(__name__)

class WhatsAppReceiptService:
    """Send invoice receipts via WhatsApp with circuit breaker protection"""
    
    def __init__(self):
        self.client = None
        self.from_number = None
        
        if TWILIO_AVAILABLE:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.from_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
            
            if account_sid and auth_token:
                self.client = Client(account_sid, auth_token)
                logger.info("Twilio WhatsApp client initialized with circuit breaker protection")
            else:
                logger.warning("Twilio credentials not found")
    
    @twilio_circuit_breaker
    def _send_twilio_message(self, to_number: str, message_body: str, media_url: Optional[str] = None) -> dict:
        """
        Send message via Twilio (protected by circuit breaker)
        
        This method will automatically retry on failures and
        open the circuit after 5 consecutive failures
        """
        if not self.client:
            raise ConnectionError("Twilio client not initialized")
        
        message = self.client.messages.create(
            from_=self.from_number,
            body=message_body,
            to=to_number,
            media_url=[media_url] if media_url else None
        )
        
        return {
            "status": "sent",
            "message_sid": message.sid,
            "to": to_number,
            "timestamp": datetime.now().isoformat()
        }
    
    def send_invoice_receipt(
        self,
        customer_whatsapp: str,
        invoice_number: str,
        total_amount: float,
        amount_due: float,
        payment_status: str,
        customer_id: Optional[int] = None,
        customer_email: Optional[str] = None,
        pdf_url: Optional[str] = None
    ) -> dict:
        """
        Send invoice receipt with automatic fallback
        
        Protection layers:
        1. Rate limiting (3/day per customer, 1000/day system, ₹500/day budget)
        2. Circuit breaker (5 failures → open for 60s)
        3. Email fallback (automatic)
        """
        # Layer 1: Rate limiting
        if customer_id:
            allowed, reason = rate_limiter.check_whatsapp_limit(customer_id)
            if not allowed:
                logger.warning(f"Rate limit: {reason}")
                return FallbackHandler.whatsapp_fallback(
                    customer_email=customer_email,
                    message_type="invoice_receipt",
                    invoice_number=invoice_number,
                    total_amount=total_amount,
                    amount_paid=total_amount - amount_due,
                    amount_due=amount_due,
                    payment_status=payment_status
                )
        
        # Prepare message
        to_number = f"whatsapp:{customer_whatsapp}" if not customer_whatsapp.startswith('whatsapp:') else customer_whatsapp
        message_body = self._compose_receipt_message(invoice_number, total_amount, amount_due, payment_status)
        
        # Layer 2: Circuit breaker protected send
        try:
            result = self._send_twilio_message(to_number, message_body, pdf_url)
            
            # Record success for rate limiting
            if customer_id:
                rate_limiter.record_whatsapp_sent(customer_id, cost=0.50)
            
            logger.info(f"Receipt sent: {result['message_sid']}")
            return result
            
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            
            # Layer 3: Email fallback
            return FallbackHandler.whatsapp_fallback(
                customer_email=customer_email,
                message_type="invoice_receipt",
                invoice_number=invoice_number,
                total_amount=total_amount,
                amount_paid=total_amount - amount_due,
                amount_due=amount_due,
                payment_status=payment_status
            )
    
    def send_payment_reminder(
        self,
        customer_whatsapp: str,
        invoice_number: str,
        amount_due: float,
        days_overdue: int,
        customer_id: Optional[int] = None,
        customer_email: Optional[str] = None
    ) -> dict:
        """Send payment reminder with circuit breaker protection"""
        to_number = f"whatsapp:{customer_whatsapp}" if not customer_whatsapp.startswith('whatsapp:') else customer_whatsapp
        message_body = self._compose_reminder_message(invoice_number, amount_due, days_overdue)
        
        try:
            result = self._send_twilio_message(to_number, message_body)
            if customer_id:
                rate_limiter.record_whatsapp_sent(customer_id, cost=0.50)
            return result
        except Exception as e:
            logger.error(f"Reminder send failed: {e}")
            return FallbackHandler.whatsapp_fallback(
                customer_email=customer_email,
                message_type="payment_reminder",
                invoice_number=invoice_number,
                amount_due=amount_due,
                days_overdue=days_overdue
            )
    
    def send_bulk_reminders(self, reminders: List[Dict]) -> List[Dict]:
        """Send bulk reminders with circuit breaker protection"""
        results = []
        for reminder in reminders:
            result = self.send_payment_reminder(
                customer_whatsapp=reminder['whatsapp'],
                invoice_number=reminder['invoice_number'],
                amount_due=reminder['amount_due'],
                days_overdue=reminder.get('days_overdue', 0),
                customer_id=reminder.get('customer_id'),
                customer_email=reminder.get('customer_email')
            )
            results.append(result)
        return results
    
    def _compose_receipt_message(self, invoice_number: str, total: float, due: float, status: str) -> str:
        """Compose receipt message"""
        status_emoji = {"paid": "✅", "partial": "⚠️", "pending": "⏳"}.get(status.lower(), "📄")
        return f"""{status_emoji} Invoice Receipt

Invoice: #{invoice_number}
Total: ₹{total:,.2f}
Amount Due: ₹{due:,.2f}
Status: {status.upper()}

Thank you for your business!"""
    
    def _compose_reminder_message(self, invoice_number: str, amount_due: float, days_overdue: int) -> str:
        """Compose payment reminder"""
        return f"""⏰ Payment Reminder

Invoice: #{invoice_number}
Amount Due: ₹{amount_due:,.2f}
Overdue by: {days_overdue} days

Please clear this payment at your earliest convenience."""
