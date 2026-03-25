import logging
import aiosmtplib
from email.message import EmailMessage
from typing import List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD

    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password)

    async def send_email(self, to: str, subject: str, body: str, attachments: List[str] = None) -> bool:
        """Send email using Gmail SMTP"""
        if not self.is_configured():
            logger.warning("Email service not fully configured (missing SMTP_USER or SMTP_PASSWORD)")
            return False

        message = EmailMessage()
        message["From"] = self.smtp_user
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        # Handle attachments (assuming paths for now)
        if attachments:
            import os
            import mimetypes
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logger.error(f"Attachment not found: {file_path}")
                    continue
                
                ctype, encoding = mimetypes.guess_type(file_path)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                
                with open(file_path, 'rb') as f:
                    message.add_attachment(
                        f.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(file_path)
                    )

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.smtp_port == 465,
                start_tls=self.smtp_port == 587
            )
            logger.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    async def send_invoice(self, customer_email: str, invoice_pdf_path: str) -> bool:
        """Send invoice with PDF attachment"""
        subject = "Your Invoice from R-DIOS"
        body = "Please find your attached invoice. Thank you for your business!"
        return await self.send_email(to=customer_email, subject=subject, body=body, attachments=[invoice_pdf_path])

    async def test_connection(self) -> bool:
        """Test SMTP connection"""
        if not self.is_configured():
            return False
        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host, 
                port=self.smtp_port, 
                use_tls=self.smtp_port == 465,
                start_tls=self.smtp_port == 587
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False

# Singleton Instance
email_service = EmailService()
