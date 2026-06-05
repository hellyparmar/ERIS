"""
Inventory Models
"""

from sqlalchemy import ForeignKey, DateTime, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from app.models.base import Base
import uuid

class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    outlet_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("outlets.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_restocked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_expiry_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_inventory_outlet_product", "outlet_id", "product_id"),
    )

    @property
    def available_stock(self) -> int:
        return self.current_stock - self.reserved_stock