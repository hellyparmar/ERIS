"""
Email Notification Service
Fallback for WhatsApp when rate limits are hit
WITH CIRCUIT BREAKER PROTECTION
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.api.utils.circuit_breakers import smtp_circuit_breaker

class EmailService:
    """Email notification service for fallback communication"""
    
    def __init__(self):
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@rdios.com')
        self.from_name = os.getenv('FROM_NAME', 'R-DIOS')
        
        if not self.smtp_user or not self.smtp_password:
            print("⚠️  Email credentials not configured. Email fallback disabled.")
            self.enabled = False
        elif self.enabled:
            print("✅ Email service enabled with circuit breaker protection")
    
    @smtp_circuit_breaker
    def _send_via_smtp(self, msg: MIMEMultipart) -> None:
        """
        Send email via SMTP (protected by circuit breaker)
        
        Automatically retries on failures and opens circuit
        after 5 consecutive failures
        """
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Dict:
        """
        Send email with circuit breaker protection
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
        
        Returns:
            Result dict with status and message
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Email service not configured"
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Add plain text part
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML part if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email (protected by circuit breaker)
            self._send_via_smtp(msg)
            
            return {
                "status": "sent",
                "message": "Email sent successfully",
                "to": to_email,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "to": to_email
            }
    
    def send_invoice_receipt(
        self,
        customer_email: str,
        invoice_number: str,
        total_amount: float,
        amount_paid: float,
        amount_due: float,
        payment_status: str
    ) -> Dict:
        """Send invoice receipt via email (WhatsApp fallback)"""
        
        subject = f"Invoice Receipt - {invoice_number}"
        
        # Plain text version
        body = f"""
R-DIOS Invoice Receipt

Invoice Number: {invoice_number}
Total Amount: ₹{total_amount:,.2f}
Amount Paid: ₹{amount_paid:,.2f}
Amount Due: ₹{amount_due:,.2f}
Status: {payment_status.upper()}

{'Remaining balance: ₹' + f'{amount_due:,.2f}' if amount_due > 0 else 'Invoice fully paid. Thank you!'}

For queries, contact: billing@rdios.com

---
This is an automated email from R-DIOS Transaction Engine.
        """.strip()
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .invoice-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; 
                       border-bottom: 1px solid #eee; }}
        .detail-label {{ font-weight: bold; color: #666; }}
        .detail-value {{ color: #333; }}
        .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; 
                         font-weight: bold; text-transform: uppercase; }}
        .status-paid {{ background: #d4edda; color: #155724; }}
        .status-partial {{ background: #fff3cd; color: #856404; }}
        .status-pending {{ background: #f8d7da; color: #721c24; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 Invoice Receipt</h1>
            <p>R-DIOS Transaction Engine</p>
        </div>
        <div class="content">
            <div class="invoice-details">
                <div class="detail-row">
                    <span class="detail-label">Invoice Number:</span>
                    <span class="detail-value">{invoice_number}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Total Amount:</span>
                    <span class="detail-value">₹{total_amount:,.2f}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Amount Paid:</span>
                    <span class="detail-value">₹{amount_paid:,.2f}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Amount Due:</span>
                    <span class="detail-value">₹{amount_due:,.2f}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="status-badge status-{payment_status.lower()}">{payment_status.upper()}</span>
                </div>
            </div>
            
            {'<p><strong>⚠️ Remaining balance: ₹' + f'{amount_due:,.2f}</strong></p>' 
             if amount_due > 0 else '<p>✅ <strong>Invoice fully paid. Thank you!</strong></p>'}
            
            <p>For any queries, please contact: <a href="mailto:billing@rdios.com">billing@rdios.com</a></p>
        </div>
        <div class="footer">
            <p>This is an automated email from R-DIOS Transaction Engine.</p>
            <p>© 2026 R-DIOS - Enterprise Retail Intelligence System</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(customer_email, subject, body, html_body)
    
    def send_payment_reminder(
        self,
        customer_email: str,
        invoice_number: str,
        amount_due: float,
        days_overdue: int
    ) -> Dict:
        """Send payment reminder via email"""
        
        subject = f"Payment Reminder - Invoice {invoice_number}"
        
        body = f"""
Payment Reminder

Dear Customer,

This is a friendly reminder that payment for Invoice {invoice_number} is overdue by {days_overdue} days.

Outstanding Amount: ₹{amount_due:,.2f}

Please clear your dues at your earliest convenience to avoid any penalties.

For payment assistance, contact: billing@rdios.com

Thank you for your business!
R-DIOS Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f8d7da; color: #721c24; padding: 30px; text-align: center; 
                   border-radius: 10px 10px 0 0; }}
        .content {{ background: #fff; padding: 30px; border-radius: 0 0 10px 10px; 
                    border: 1px solid #f8d7da; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #dc3545; text-align: center; 
                   margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Payment Reminder</h1>
        </div>
        <div class="content">
            <p>Dear Customer,</p>
            <p>This is a friendly reminder that payment for Invoice <strong>{invoice_number}</strong> 
               is overdue by <strong>{days_overdue} days</strong>.</p>
            
            <div class="amount">
                Outstanding: ₹{amount_due:,.2f}
            </div>
            
            <p>Please clear your dues at your earliest convenience to avoid any penalties.</p>
            <p>For payment assistance, contact: 
               <a href="mailto:billing@rdios.com">billing@rdios.com</a></p>
            
            <p>Thank you for your business!<br>R-DIOS Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(customer_email, subject, body, html_body)
    
    def send_bulk_reminders(self, reminders: List[Dict]) -> List[Dict]:
        """Send bulk payment reminders"""
        results = []
        
        for reminder in reminders:
            result = self.send_payment_reminder(
                customer_email=reminder['email'],
                invoice_number=reminder['invoice_number'],
                amount_due=reminder['amount_due'],
                days_overdue=reminder['days_overdue']
            )
            results.append(result)
        
        return results

# Global email service instance
email_service = EmailService()
