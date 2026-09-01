import logging
import os
from celery import Celery, shared_task
from datetime import datetime, timedelta
from api.notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Fallback in case CELERY_BROKER_URL is missing
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("notification_tasks", broker=CELERY_BROKER_URL)

@shared_task(name="notifications.send_eod_sales_summary")
def send_eod_sales_summary():
    """
    Task to send end-of-day sales summary to the admin.
    """
    service = NotificationService()
    admin_phone = os.getenv("ADMIN_PHONE_NUMBER")
    
    if not admin_phone:
        logger.error("ADMIN_PHONE_NUMBER not set for EOD summary.")
        return False
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Mock totals - in a real app, query the database
    total_sales = 45500.25 
    total_orders = 112
    
    logger.info(f"Sending EOD summary to {admin_phone}")
    return service.send_daily_summary(admin_phone, date_str, total_sales, total_orders)

@shared_task(name="notifications.check_low_stock")
def check_low_stock_and_alert():
    """
    Check for items below threshold and alert the manager.
    """
    service = NotificationService()
    manager_phone = os.getenv("MANAGER_PHONE_NUMBER")
    
    if not manager_phone:
        logger.error("MANAGER_PHONE_NUMBER not set for low stock alerts.")
        return False
        
    # Mock low stock item - in a real app, query current inventory
    product_name = "Premium Coffee Beans"
    current_stock = 3
    threshold = 10
    
    logger.info(f"Sending low stock alert for {product_name} to {manager_phone}")
    return service.send_low_stock_alert(manager_phone, product_name, current_stock, threshold)

@shared_task(name="notifications.weekly_reorder_reminder")
def send_reorder_reminders():
    """
    Send weekly reminder for reordering essentials.
    """
    service = NotificationService()
    manager_phone = os.getenv("MANAGER_PHONE_NUMBER")
    
    if not manager_phone:
        logger.error("MANAGER_PHONE_NUMBER not set for reorder reminders.")
        return False
        
    # Mock list
    product_list = ["Milk", "Sugar", "Paper Cups", "Stirrer Sticks"]
    
    logger.info(f"Sending reorder reminder to {manager_phone}")
    return service.send_reorder_reminder(manager_phone, product_list)
