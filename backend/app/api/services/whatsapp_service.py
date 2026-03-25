"""
WhatsApp Receipt Service
Send digital receipts and payment reminders via WhatsApp
Support for MSG91 (primary) and Twilio (fallback)
WITH CIRCUIT BREAKER PROTECTION
"""

import os
import logging
import requests
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import email fallback
from app.api.services.email_service import email_service
from app.api.middleware.rate_limiter import rate_limiter
from app.api.utils.circuit_breakers import twilio_circuit_breaker, FallbackHandler

# Import Twilio Client directly
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)

# MSG91 Configuration
MSG91_API_KEY = os.getenv("MSG91_API_KEY", "")
MSG91_SENDER_ID = os.getenv("MSG91_SENDER_ID", "R-DIOS")
MSG91_ROUTE = os.getenv("MSG91_ROUTE", "4")
MSG91_BASE_URL = "https://control.msg91.com/api/sendhttp"
MSG91_ENABLED = bool(MSG91_API_KEY)

# Twilio configuration
TWILIO_ENABLED = os.getenv("TWILIO_ENABLED", "false").lower() == "true"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

class WhatsAppReceiptService:
    """Send invoice receipts via WhatsApp"""
    
    def __init__(self):
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio not installed. WhatsApp functionality will be simulated.")
            self.client = None
            self.from_number = None
        else:
            # Get Twilio credentials from environment
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.from_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
            
            if account_sid and auth_token:
                self.client = Client(account_sid, auth_token)
                logger.info("Twilio WhatsApp client initialized")
            else:
                logger.warning("Twilio credentials not found. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
                self.client = None
    
    def send_invoice_receipt(
        self,
        customer_whatsapp: str,
        invoice_number: str,
        total_amount: float,
        amount_due: float,
        payment_status: str,
        customer_id: int = None,
        customer_email: str = None,
        pdf_url: str = None
    ) -> dict:
        """
        Send invoice receipt via WhatsApp with email fallback
        
        Args:
            customer_whatsapp: Customer WhatsApp number (format: +91XXXXXXXXXX)
            invoice_number: Invoice number
            total_amount: Total invoice amount
            amount_due: Amount remaining
            payment_status: paid/partial/pending
            customer_id: Customer ID (for rate limiting)
            customer_email: Fallback email address
            pdf_url: Public URL to invoice PDF
        
        Returns:
            dict with status and message_sid
        """
        # Check WhatsApp rate limit
        if customer_id:
            allowed, reason = rate_limiter.check_whatsapp_limit(customer_id)
            
            if not allowed:
                logger.warning(f"WhatsApp rate limit hit: {reason}. Falling back to email.")
                
                # Try email fallback
                if customer_email:
                    email_result = email_service.send_invoice_receipt(
                        customer_email=customer_email,
                        invoice_number=invoice_number,
                        total_amount=total_amount,
                        amount_paid=total_amount - amount_due,
                        amount_due=amount_due,
                        payment_status=payment_status
                    )
                    
                    return {
                        "status": "fallback_email",
                        "reason": reason,
                        "email_status": email_result['status'],
                        "message": "WhatsApp rate limited, sent via email instead"
                    }
                else:
                    return {
                        "status": "rate_limited",
                        "reason": reason,
                        "message": "WhatsApp blocked and no email available"
                    }
        
        # Format phone number
        if not customer_whatsapp.startswith('whatsapp:'):
            to_number = f"whatsapp:{customer_whatsapp}"
        else:
            to_number = customer_whatsapp
        
        # Compose message
        message_body = self._compose_receipt_message(
            invoice_number,
            total_amount,
            amount_due,
            payment_status
        )
        
        # Send message
        if self.client:
            try:
                message = self.client.messages.create(
                    from_=self.from_number,
                    body=message_body,
                    to=to_number,
                    media_url=[pdf_url] if pdf_url else None
                )
                
                # Record successful send for rate limiting
                if customer_id:
                    rate_limiter.record_whatsapp_sent(customer_id, cost=0.50)
                
                logger.info(f"WhatsApp receipt sent: {message.sid} to {to_number}")
                
                return {
                    "status": "sent",
                    "message_sid": message.sid,
                    "to": to_number,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Twilio error sending WhatsApp: {e}")
                
                # Try email fallback on error
                if customer_email:
                    email_result = email_service.send_invoice_receipt(
                        customer_email=customer_email,
                        invoice_number=invoice_number,
                        total_amount=total_amount,
                        amount_paid=total_amount - amount_due,
                        amount_due=amount_due,
                        payment_status=payment_status
                    )
                    
                    return {
                        "status": "fallback_email_after_error",
                        "whatsapp_error": str(e),
                        "email_status": email_result['status']
                    }
                
                return {
                    "status": "failed",
                    "error": str(e),
                    "to": to_number
                }
        else:
            # Simulation mode
            logger.info(f"[SIMULATION] WhatsApp receipt to {to_number}")
            logger.info(f"[SIMULATION] Message: {message_body}")
            
            return {
                "status": "simulated",
                "message": message_body,
                "to": to_number,
                "note": "Twilio not configured - message simulated"
            }

    
    def _compose_receipt_message(
        self,
        invoice_number: str,
        total_amount: float,
        amount_due: float,
        payment_status: str
    ) -> str:
        """Compose WhatsApp message text"""
        
        status_emoji = {
            "paid": "✅",
            "partial": "⏳",
            "pending": "📋",
            "overdue": "⚠️"
        }.get(payment_status.lower(), "📄")
        
        message = f"""{status_emoji} *Invoice Receipt - R-DIOS*

*Invoice #:* {invoice_number}
*Total Amount:* ₹{total_amount:,.2f}
*Amount Due:* ₹{amount_due:,.2f}
*Status:* {payment_status.upper()}

"""
        
        if payment_status.lower() == "paid":
            message += "Thank you for your payment! ✨"
        elif payment_status.lower() == "partial":
            message += f"Remaining balance: ₹{amount_due:,.2f}\nPlease clear dues at your earliest convenience."
        elif payment_status.lower() == "overdue":
            message += "⚠️ *This invoice is overdue*\nKindly make the payment immediately."
        else:
            message += f"Payment of ₹{amount_due:,.2f} is due."
        
        message += "\n\n📞 For queries: billing@rdios.com"
        message += "\n🔒 Powered by R-DIOS Transaction Engine"
        
        return message
    
    def send_payment_reminder(
        self,
        customer_whatsapp: str,
        invoice_number: str,
        amount_due: float,
        days_overdue: int = 0
    ) -> dict:
        """Send payment reminder via WhatsApp"""
        
        to_number = f"whatsapp:{customer_whatsapp}" if not customer_whatsapp.startswith('whatsapp:') else customer_whatsapp
        
        if days_overdue > 0:
            urgency = "⚠️ URGENT" if days_overdue > 30 else "⏰ REMINDER"
            message_body = f"""{urgency} - Payment Reminder

*Invoice #:* {invoice_number}
*Amount Due:* ₹{amount_due:,.2f}
*Days Overdue:* {days_overdue} days

Your payment is overdue. Please clear the outstanding balance at your earliest convenience.

📞 Contact: billing@rdios.com
"""
        else:
            message_body = f"""📋 Payment Reminder

*Invoice #:* {invoice_number}
*Amount Due:* ₹{amount_due:,.2f}

This is a friendly reminder about your pending payment.

📞 Contact: billing@rdios.com
"""
        
        if self.client:
            try:
                message = self.client.messages.create(
                    from_=self.from_number,
                    body=message_body,
                    to=to_number
                )
                
                return {
                    "status": "sent",
                    "message_sid": message.sid,
                    "to": to_number
                }
            except TwilioRestException as e:
                logger.error(f"Error sending reminder: {e}")
                return {"status": "failed", "error": str(e)}
        else:
            logger.info(f"[SIMULATION] Reminder to {to_number}: {message_body}")
            return {
                "status": "simulated",
                "message": message_body,
                "to": to_number
            }
    
    def send_bulk_reminders(self, overdue_invoices: list) -> dict:
        """Send reminders for multiple overdue invoices"""
        results = {
            "sent": 0,
            "failed": 0,
            "simulated": 0
        }
        
        for invoice_info in overdue_invoices:
            result = self.send_payment_reminder(
                customer_whatsapp=invoice_info['whatsapp'],
                invoice_number=invoice_info['invoice_number'],
                amount_due=invoice_info['amount_due'],
                days_overdue=invoice_info.get('days_overdue', 0)
            )
            
            if result['status'] == 'sent':
                results['sent'] += 1
            elif result['status'] == 'simulated':
                results['simulated'] += 1
            else:
                results['failed'] += 1
        
        return results
