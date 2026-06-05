"""
Supplier Models
"""

from sqlalchemy import String, Boolean, Float, Integer, text, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from app.models.base import Base
import uuid
from datetime import datetime

class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    gstin: Mapped[str] = mapped_column(String(20), nullable=True)
    gst_number: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=True)
    average_lead_time_days: Mapped[int] = mapped_column(Integer, default=7, nullable=True)
    payment_terms: Mapped[int] = mapped_column(Integer, default=30, nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=True)