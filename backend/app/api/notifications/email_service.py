import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Gmail SMTP based email service (Free/Student Friendly)"""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.enabled = settings.EMAIL_ENABLED and bool(self.user) and bool(self.password)

    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send an email via SMTP"""
        if not self.enabled:
            logger.warning("Email service disabled or credentials missing.")
            return {"success": False, "error": "Email service not configured"}

        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
                return {"success": True}
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {"success": False, "error": str(e)}

# Singleton Instance
email_service = EmailService()
