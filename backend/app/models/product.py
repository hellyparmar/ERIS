"""
Product Models
"""

from sqlalchemy import String, Boolean, Float, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.models.base import Base
import uuid

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    sku_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    gst_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False)
    max_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sale_items: Mapped[list["SaleItem"]] = relationship("SaleItem", back_populates="product")
