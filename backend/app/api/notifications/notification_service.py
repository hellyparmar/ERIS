import logging
from typing import List, Optional
from .whatsapp_client import MSG91WhatsAppClient
from .templates import TemplateType, get_template_id

logger = logging.getLogger(__name__)

class NotificationService:
    """
    High-level service for handling business-logic notifications.
    """

    def __init__(self):
        self.client = MSG91WhatsAppClient()

    def send_low_stock_alert(self, phone: str, product_name: str, current_stock: int, threshold: int):
        """Send alert when stock falls below threshold."""
        template = get_template_id(TemplateType.LOW_STOCK)
        variables = [product_name, str(current_stock), str(threshold)]
        return self.client.send_template_message(phone, template, variables)

    def send_daily_summary(self, phone: str, date_str: str, total_sales: float, total_orders: int):
        """Send End-of-Day sales summary."""
        template = get_template_id(TemplateType.DAILY_SUMMARY)
        variables = [date_str, f"Rs. {total_sales:.2f}", str(total_orders)]
        return self.client.send_template_message(phone, template, variables)

    def send_invoice_notification(self, phone: str, invoice_no: str, amount: float):
        """Notify customer of a new invoice."""
        template = get_template_id(TemplateType.INVOICE_DELIVERY)
        variables = [invoice_no, f"Rs. {amount:.2f}"]
        return self.client.send_template_message(phone, template, variables)

    def send_reorder_reminder(self, phone: str, product_list: List[str]):
        """Weekly reminder for items to be reordered."""
        template = get_template_id(TemplateType.REORDER_REMINDER)
        items_str = ", ".join(product_list)
        variables = [items_str]
        return self.client.send_template_message(phone, template, variables)
