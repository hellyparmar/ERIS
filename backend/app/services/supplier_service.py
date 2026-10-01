"""Organization-scoped supplier CRUD."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.commerce import Supplier


class SupplierService:
    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id

    def _query(self):
        return self.db.query(Supplier).filter(Supplier.organization_id == self.organization_id)

    def create(self, data: dict) -> Supplier:
        supplier = Supplier(organization_id=self.organization_id, **data)
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def get(self, supplier_id: int) -> Optional[Supplier]:
        return self._query().filter(Supplier.id == supplier_id).first()

    def list(self, search: Optional[str], city: Optional[str], is_active: bool, page: int, limit: int) -> dict:
        query = self._query().filter(Supplier.is_active.is_(is_active))
        if search:
            query = query.filter(
                Supplier.name.ilike(f"%{search}%")
                | Supplier.contact_person.ilike(f"%{search}%")
                | Supplier.phone.ilike(f"%{search}%")
            )
        if city:
            query = query.filter(Supplier.city.ilike(f"%{city}%"))
        total = query.count()
        rows = query.order_by(Supplier.name).offset((page - 1) * limit).limit(limit).all()
        return {"items": [self.serialize(row) for row in rows], "total": total, "page": page, "per_page": limit}

    def update(self, supplier_id: int, data: dict) -> Optional[Supplier]:
        supplier = self.get(supplier_id)
        if supplier is None:
            return None
        for key, value in data.items():
            setattr(supplier, key, value)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def deactivate(self, supplier_id: int) -> bool:
        supplier = self.get(supplier_id)
        if supplier is None:
            return False
        supplier.is_active = False
        self.db.commit()
        return True

    @staticmethod
    def serialize(supplier: Supplier) -> dict:
        return {
            "id": supplier.id,
            "name": supplier.name,
            "contact_person": supplier.contact_person,
            "phone": supplier.phone,
            "gst_number": supplier.gst_number,
            "address": supplier.address,
            "city": supplier.city,
            "state": supplier.state,
            "payment_terms_days": supplier.payment_terms_days,
            "quality_rating": float(supplier.quality_rating or 0),
            "on_time_delivery_rate": float(supplier.on_time_delivery_rate or 0),
            "is_active": supplier.is_active,
            "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
        }
