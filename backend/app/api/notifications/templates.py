from enum import Enum
from typing import Dict, Any

class TemplateType(str, Enum):
    LOW_STOCK = "low_stock_alert"
    DAILY_SUMMARY = "daily_sales_summary"
    INVOICE_DELIVERY = "invoice_delivery"
    ORDER_CONFIRMATION = "order_confirmation"
    REORDER_REMINDER = "reorder_reminder"

# Mapping of internal template types to MSG91 template IDs/Names
# In a real scenario, these would match the templates approved in MSG91 dashboard.
MSG91_TEMPLATE_MAP = {
    TemplateType.LOW_STOCK: "low_stock_01",
    TemplateType.DAILY_SUMMARY: "sales_summary_01",
    TemplateType.INVOICE_DELIVERY: "invoice_msg_01",
    TemplateType.ORDER_CONFIRMATION: "order_conf_01",
    TemplateType.REORDER_REMINDER: "reorder_msg_01",
}

def get_template_id(template_type: TemplateType) -> str:
    return MSG91_TEMPLATE_MAP.get(template_type, "")
