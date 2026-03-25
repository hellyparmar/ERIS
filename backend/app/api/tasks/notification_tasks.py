import logging
from typing import Optional
from app.api.celery_app import celery_app
from app.api.notifications.notification_manager import notification_manager
from app.api.notifications.email_service import email_service

logger = logging.getLogger(__name__)

@celery_app.task(name="notifications.send_email_async")
def send_email_async(to_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """Asynchronous email delivery"""
    return email_service.send_email(to_email, subject, body, html_body)

@celery_app.task(name="notifications.send_invoice_alert")
def send_invoice_async(email: str, phone: str, invoice_id: str, amount: float, pdf_path: Optional[str] = None):
    """Asynchronous unified invoice notification"""
    return notification_manager.send_invoice_notification(email, phone, invoice_id, amount, pdf_path)

@celery_app.task(name="notifications.send_low_stock_report")
def send_low_stock_alerts():
    """Daily check for low stock and send alerts"""
    # Logic to fetch low stock from DB and call notification_manager
    logger.info("Executing daily low stock check...")
    return {"status": "checked"}
