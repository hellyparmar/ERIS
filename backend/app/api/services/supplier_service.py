"""
Supplier & Purchase Order Service
Business logic for vendor management and procurement workflows
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.db.multitenant_models import Supplier, PurchaseOrder, PurchaseOrderItem, Product, Inventory


class SupplierService:
    def __init__(self, db: Session):
        self.db = db

    # ==================== SUPPLIER CRUD ====================

    def _generate_supplier_code(self) -> str:
        count = self.db.query(Supplier).count()
        return f"SUP{(count + 1):04d}"

    def create_supplier(self, data: dict) -> Supplier:
        supplier = Supplier(
            supplier_code=self._generate_supplier_code(),
            name=data["name"],
            contact_person=data.get("contact_person"),
            email=data.get("email"),
            phone=data.get("phone"),
            gst_number=data.get("gst_number"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country", "India"),
            payment_terms_days=data.get("payment_terms_days", 30),
            organization_id=data.get("organization_id"),
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def get_supplier(self, supplier_id: int) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.is_active == True
        ).first()

    def list_suppliers(
        self,
        search: Optional[str] = None,
        city: Optional[str] = None,
        is_active: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = self.db.query(Supplier).filter(Supplier.is_active == is_active)
        if search:
            query = query.filter(
                (Supplier.name.ilike(f"%{search}%")) |
                (Supplier.contact_person.ilike(f"%{search}%")) |
                (Supplier.email.ilike(f"%{search}%"))
            )
        if city:
            query = query.filter(Supplier.city.ilike(f"%{city}%"))

        total = query.count()
        suppliers = query.order_by(Supplier.name).offset((page - 1) * limit).limit(limit).all()
        return {"items": [self._supplier_dict(s) for s in suppliers], "total": total, "page": page}

    def update_supplier(self, supplier_id: int, data: dict) -> Optional[Supplier]:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return None
        for key in ["name", "contact_person", "email", "phone", "gst_number",
                    "address", "city", "state", "payment_terms_days", "is_active"]:
            if key in data and data[key] is not None:
                setattr(supplier, key, data[key])
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def delete_supplier(self, supplier_id: int) -> bool:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return False
        supplier.is_active = False
        self.db.commit()
        return True

    def _supplier_dict(self, s: Supplier) -> dict:
        return {
            "id": s.id,
            "supplier_code": s.supplier_code,
            "name": s.name,
            "contact_person": s.contact_person,
            "email": s.email,
            "phone": s.phone,
            "gst_number": s.gst_number,
            "address": s.address,
            "city": s.city,
            "state": s.state,
            "country": s.country,
            "payment_terms_days": s.payment_terms_days,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

    def get_supplier_products(self, supplier_id: int) -> List[dict]:
        """Get all products associated with this supplier via purchase order history."""
        pos = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier_id
        ).all()
        product_ids = set()
        for po in pos:
            for item in po.items:
                product_ids.add(item.product_id)

        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        return [{"id": p.id, "name": p.name, "sku": getattr(p, "sku", None), "price": float(p.price)} for p in products]

    def get_supplier_performance(self, supplier_id: int) -> dict:
        """Calculate performance metrics: on-time delivery, order count, total spend."""
        pos = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier_id
        ).all()

        total_orders = len(pos)
        received = [p for p in pos if p.status == "received" or p.status == "paid"]
        on_time = sum(
            1 for p in received
            if p.actual_delivery_date and p.expected_delivery_date
            and p.actual_delivery_date <= p.expected_delivery_date
        )
        total_spend = sum(float(p.total_amount) for p in pos if p.status in ("received", "paid"))
        on_time_pct = round((on_time / len(received)) * 100, 1) if received else 0.0

        return {
            "supplier_id": supplier_id,
            "total_orders": total_orders,
            "completed_orders": len(received),
            "on_time_deliveries": on_time,
            "on_time_percentage": on_time_pct,
            "total_spend": total_spend,
            "pending_orders": sum(1 for p in pos if p.status in ("draft", "sent", "confirmed")),
        }

    # ==================== PURCHASE ORDERS ====================

    def _generate_po_number(self) -> str:
        today = date.today()
        count = self.db.query(PurchaseOrder).filter(
            func.extract("year", PurchaseOrder.created_at) == today.year,
            func.extract("month", PurchaseOrder.created_at) == today.month,
        ).count()
        return f"PO/{today.year}/{today.month:02d}/{(count + 1):04d}"

    def create_purchase_order(self, data: dict) -> PurchaseOrder:
        supplier = self.db.query(Supplier).filter(Supplier.id == data["supplier_id"]).first()
        if not supplier:
            raise ValueError(f"Supplier {data['supplier_id']} not found")

        subtotal = Decimal("0")
        gst_total = Decimal("0")
        item_records = []

        for item in data["items"]:
            qty = item["quantity_ordered"]
            unit_cost = Decimal(str(item["unit_cost"]))
            gst_rate = Decimal(str(item.get("gst_rate", 18.0)))
            taxable = unit_cost * qty
            gst = taxable * (gst_rate / 100)
            line_total = taxable + gst
            subtotal += taxable
            gst_total += gst
            item_records.append({
                "product_id": item["product_id"],
                "quantity_ordered": qty,
                "quantity_received": 0,
                "unit_cost": unit_cost,
                "gst_rate": gst_rate,
                "line_total": line_total,
            })

        po = PurchaseOrder(
            po_number=self._generate_po_number(),
            supplier_id=data["supplier_id"],
            order_date=date.today(),
            expected_delivery_date=data.get("expected_delivery_date"),
            subtotal=subtotal,
            gst_amount=gst_total,
            total_amount=subtotal + gst_total,
            status="draft",
            notes=data.get("notes"),
            organization_id=data.get("organization_id") or supplier.organization_id,
            store_id=data.get("store_id") or supplier.organization_id,  # fallback
        )
        self.db.add(po)
        self.db.flush()

        for ir in item_records:
            poi = PurchaseOrderItem(purchase_order_id=po.id, **ir)
            self.db.add(poi)

        self.db.commit()
        self.db.refresh(po)
        return po

    def list_purchase_orders(
        self,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = self.db.query(PurchaseOrder)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)

        total = query.count()
        orders = query.order_by(PurchaseOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        return {"items": [self._po_dict(o) for o in orders], "total": total, "page": page}

    def get_purchase_order(self, po_id: int) -> Optional[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    def update_po_status(self, po_id: int, status: str, notes: str | None = None) -> PurchaseOrder:
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")
        po.status = status
        if notes:
            po.notes = (po.notes or "") + f"\n[{datetime.now().strftime('%Y-%m-%d')}] {notes}"
        self.db.commit()
        self.db.refresh(po)
        return po

    def receive_goods(self, po_id: int, received_items: list, notes: str | None = None) -> PurchaseOrder:
        """Mark goods as received and update inventory stock levels."""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")

        received_map = {r["product_id"]: r["quantity_received"] for r in received_items}

        all_received = True
        for item in po.items:
            qty_rcv = received_map.get(item.product_id, 0)
            if qty_rcv > 0:
                item.quantity_received = qty_rcv
                # Update inventory if product exists in inventory
                inv = self.db.query(Inventory).filter(
                    Inventory.product_id == item.product_id
                ).first()
                if inv:
                    inv.quantity_in_stock = (inv.quantity_in_stock or 0) + qty_rcv
                    inv.last_updated = datetime.now()

            if item.quantity_received < item.quantity_ordered:
                all_received = False

        po.status = "received" if all_received else "partial"
        po.actual_delivery_date = date.today()
        if notes:
            po.notes = (po.notes or "") + f"\n[Received {date.today()}] {notes}"

        self.db.commit()
        self.db.refresh(po)
        return po

    def _po_dict(self, po: PurchaseOrder) -> dict:
        return {
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "order_date": po.order_date.isoformat() if po.order_date else None,
            "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            "actual_delivery_date": po.actual_delivery_date.isoformat() if po.actual_delivery_date else None,
            "subtotal": float(po.subtotal),
            "gst_amount": float(po.gst_amount),
            "total_amount": float(po.total_amount),
            "status": po.status,
            "notes": po.notes,
            "created_at": po.created_at.isoformat() if po.created_at else None,
            "items": [
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "quantity_ordered": i.quantity_ordered,
                    "quantity_received": i.quantity_received,
                    "unit_cost": float(i.unit_cost),
                    "gst_rate": float(i.gst_rate),
                    "line_total": float(i.line_total),
                } for i in (po.items or [])
            ]
        }

    # ==================== ANALYTICS ====================

    def compare_supplier_prices(self, product_id: int) -> List[dict]:
        """Compare unit costs for a product across different suppliers."""
        items = self.db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.product_id == product_id
        ).all()

        result = {}
        for item in items:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == item.purchase_order_id).first()
            if not po:
                continue
            sid = po.supplier_id
            cost = float(item.unit_cost)
            if sid not in result:
                supplier = self.db.query(Supplier).filter(Supplier.id == sid).first()
                result[sid] = {
                    "supplier_id": sid,
                    "supplier_name": supplier.name if supplier else "Unknown",
                    "prices": [],
                    "latest_price": cost,
                    "min_price": cost,
                    "max_price": cost,
                }
            prices_list = result[sid]["prices"]
            if isinstance(prices_list, list):
                prices_list.append(cost)
            result[sid]["latest_price"] = cost
            result[sid]["min_price"] = min(result[sid]["min_price"], cost)
            result[sid]["max_price"] = max(result[sid]["max_price"], cost)

        return sorted(result.values(), key=lambda x: x["latest_price"])
