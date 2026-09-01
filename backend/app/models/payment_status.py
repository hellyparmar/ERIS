import enum

class PaymentStatus(str, enum.Enum):
    """Payment Status Enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    PARTIALLY_PAID = "partially_paid"
