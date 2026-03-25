"""
Invoice Email Service
Sends invoices via email with PDF attachments
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging
from datetime import datetime
from jinja2 import Template

logger = logging.getLogger(__name__)


class InvoiceEmailService:
    """Email service for invoices"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@enterprise-retail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    def send_invoice(self, invoice_data, pdf_file, recipient_email=None):
        """
        Send invoice via email
        
        Args:
            invoice_data: Dict with invoice details
            pdf_file: BytesIO object with PDF
            recipient_email: Email address to send to
            
        Returns:
            Dict with success status
        """
        try:
            recipient = recipient_email or invoice_data.get('customer_email')
            if not recipient:
                logger.error("No recipient email provided")
                return {"success": False, "error": "No recipient email"}
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = f"Invoice {invoice_data.get('invoice_number')} - {invoice_data.get('customer_name')}"
            message['From'] = self.sender_email
            message['To'] = recipient
            
            # Create email body
            html_body = self._generate_email_html(invoice_data)
            
            # Attach HTML
            message.attach(MIMEText(html_body, 'html'))
            
            # Attach PDF
            self._attach_pdf(message, pdf_file, invoice_data.get('invoice_number'))
            
            # Send email
            self._send_message(message, recipient)
            
            logger.info(f"Invoice {invoice_data.get('invoice_number')} sent to {recipient}")
            return {"success": True, "message": f"Invoice sent to {recipient}"}
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_email_html(self, invoice_data):
        """Generate HTML email body"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .title { color: #1f2937; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .subtitle { color: #6b7280; font-size: 14px; }
        .section { margin-bottom: 30px; }
        .section-title { color: #1f2937; font-size: 16px; font-weight: bold; margin-bottom: 10px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .info-label { color: #6b7280; font-weight: bold; }
        .info-value { color: #1f2937; }
        .amount { font-size: 14px; }
        .total { font-size: 18px; font-weight: bold; color: #3b82f6; }
        .footer { background-color: #f9fafb; padding: 20px; border-radius: 8px; text-align: center; color: #6b7280; font-size: 12px; }
        .button { display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .status { display: inline-block; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status-paid { background-color: #d1fae5; color: #065f46; }
        .status-pending { background-color: #fef3c7; color: #92400e; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th { background-color: #f3f4f6; padding: 10px; text-align: left; border-bottom: 2px solid #e5e7eb; }
        td { padding: 10px; border-bottom: 1px solid #e5e7eb; }
        tr:last-child td { border-bottom: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">Invoice {{ invoice_number }}</div>
            <div class="subtitle">Enterprise Retail Intelligence System</div>
        </div>
        
        <div class="section">
            <div class="section-title">Invoice Details</div>
            <div class="info-row">
                <span class="info-label">Invoice Number:</span>
                <span class="info-value">{{ invoice_number }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Invoice Date:</span>
                <span class="info-value">{{ invoice_date }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Due Date:</span>
                <span class="info-value">{{ due_date }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value">
                    {% if payment_status == 'paid' %}
                        <span class="status status-paid">PAID</span>
                    {% else %}
                        <span class="status status-pending">{{ status|upper }}</span>
                    {% endif %}
                </span>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Bill To</div>
            <div class="info-value">
                <strong>{{ customer_name }}</strong><br>
                {{ customer_email }}<br>
                {{ customer_phone }}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Summary</div>
            <table>
                <tr>
                    <th>Description</th>
                    <th style="text-align: right;">Amount</th>
                </tr>
                <tr>
                    <td>Subtotal</td>
                    <td style="text-align: right;">₹{{ '%.2f'|format(subtotal) }}</td>
                </tr>
                {% if gst_amount > 0 %}
                <tr>
                    <td>GST ({{ gst_rate }}%)</td>
                    <td style="text-align: right;">₹{{ '%.2f'|format(gst_amount) }}</td>
                </tr>
                {% endif %}
                {% if tds_amount > 0 %}
                <tr>
                    <td>TDS</td>
                    <td style="text-align: right;">- ₹{{ '%.2f'|format(tds_amount) }}</td>
                </tr>
                {% endif %}
                <tr style="background-color: #f3f4f6;">
                    <td><strong>Total Amount</strong></td>
                    <td style="text-align: right;"><strong>₹{{ '%.2f'|format(total_amount) }}</strong></td>
                </tr>
                {% if amount_paid > 0 %}
                <tr>
                    <td>Amount Paid</td>
                    <td style="text-align: right;">₹{{ '%.2f'|format(amount_paid) }}</td>
                </tr>
                <tr>
                    <td><strong>Balance Due</strong></td>
                    <td style="text-align: right;"><strong style="color: #ef4444;">₹{{ '%.2f'|format(balance_amount) }}</strong></td>
                </tr>
                {% endif %}
            </table>
        </div>
        
        {% if notes %}
        <div class="section">
            <div class="section-title">Notes</div>
            <div class="info-value">{{ notes }}</div>
        </div>
        {% endif %}
        
        <div style="text-align: center;">
            <p>Please find the detailed invoice attached to this email.</p>
            <a href="#" class="button">View Invoice</a>
        </div>
        
        <div class="footer">
            <p>Thank you for your business!</p>
            <p>Enterprise Retail Intelligence System | Confidential</p>
            <p>This is an automated email. Please do not reply to this address.</p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            template = Template(template_str)
            html = template.render(**invoice_data)
            return html
        except Exception as e:
            logger.error(f"Email template error: {e}")
            # Return simple HTML if template fails
            return f"""
<html>
<body>
<h2>Invoice {invoice_data.get('invoice_number')}</h2>
<p>Amount: ₹{invoice_data.get('total_amount', 0)}</p>
<p>Please find the invoice PDF attached.</p>
</body>
</html>
            """
    
    def _attach_pdf(self, message, pdf_file, invoice_number):
        """Attach PDF to email"""
        try:
            # Reset file pointer
            pdf_file.seek(0)
            
            # Create attachment
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(pdf_file.read())
            encoders.encode_base64(attachment)
            
            # Set filename
            filename = f"Invoice_{invoice_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            
            # Attach to message
            message.attach(attachment)
            
            logger.info(f"PDF attached to email: {filename}")
            
        except Exception as e:
            logger.error(f"PDF attachment error: {e}")
            raise
    
    def _send_message(self, message, recipient):
        """Send email message"""
        try:
            # Create session
            session = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            # Enable TLS
            if self.use_tls:
                session.starttls()
            
            # Login
            if self.sender_password:
                session.login(self.sender_email, self.sender_password)
            
            # Send
            session.send_message(message)
            session.quit()
            
            logger.info(f"Email sent successfully to {recipient}")
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            raise Exception("Email authentication failed")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            raise
    
    def send_test_email(self, recipient_email):
        """Send test email to verify configuration"""
        try:
            message = MIMEMultipart()
            message['Subject'] = "Test Email - Enterprise Retail System"
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            body = """
This is a test email from Enterprise Retail Intelligence System.

If you received this email, the email service is working correctly.
            """
            
            message.attach(MIMEText(body, 'plain'))
            self._send_message(message, recipient_email)
            
            return {"success": True, "message": "Test email sent"}
            
        except Exception as e:
            logger.error(f"Test email error: {e}")
            return {"success": False, "error": str(e)}


# Create service instance
email_service = InvoiceEmailService()

def send_invoice_email(invoice_data, pdf_file, recipient_email=None):
    """Send invoice via email"""
    return email_service.send_invoice(invoice_data, pdf_file, recipient_email)

def send_test_email(recipient_email):
    """Send test email"""
    return email_service.send_test_email(recipient_email)
