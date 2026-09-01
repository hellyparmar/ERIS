"""
Purchase Order Models
"""

import enum

class PurchaseOrderStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    confirmed = "confirmed"
    delivered = "delivered"
    cancelled = "cancelled"


