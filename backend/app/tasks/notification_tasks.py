import logging
from celery import Celery
from app.notifications.notification_manager import notification_manager
from app.config import settings
from datetime import date

# Initialize Celery app (assuming Redis broker as per .env)
celery_app = Celery('eris_tasks', broker=settings.REDIS_URL)

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.send_email_async")
def send_email_async(email_data: dict):
    """Background task for sending emails"""
    import asyncio
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(
        notification_manager.email.send_email(
            to=email_data.get('to'),
            subject=email_data.get('subject'),
            body=email_data.get('body'),
            attachments=email_data.get('attachments')
        )
    )
    return success

@celery_app.task(name="tasks.send_daily_summary")
def send_daily_summary(recipient_email: str, summary_data: dict):
    """Background task for daily EOD summary"""
    subject = f"R-DIOS Daily Retail Summary: {date.today()}"
    body = f"""
    Daily Summary for {date.today()}
    ----------------------------
    Total Sales: Rs. {summary_data.get('total_sales', 0):,.2f}
    Total Orders: {summary_data.get('total_orders', 0)}
    Top Category: {summary_data.get('top_category', 'N/A')}
    
    Check your dashboard for detailed analytics.
    """
    
    import asyncio
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(
        notification_manager.email.send_email(to=recipient_email, subject=subject, body=body)
    )
    return success
