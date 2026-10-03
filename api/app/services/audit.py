"""Audit trail.

Every create / update / delete of business records made by a signed-in user is recorded automatically by a
SQLAlchemy `before_flush` hook (who, what, which fields changed). Actions that are not a single ORM change
(imports, bulk clears, password changes) call `audit()` explicitly.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Category,
    Customer,
    InventoryItem,
    Invoice,
    Organization,
    Outlet,
    Product,
    Promotion,
    PurchaseOrder,
    Sale,
    Supplier,
    User,
)

TRACKED = {Sale: "sale", Product: "product", Category: "category", Outlet: "outlet", Supplier: "supplier",
           Customer: "customer", PurchaseOrder: "purchase_order", InventoryItem: "stock_level", User: "user",
           Organization: "organization", Promotion: "promotion", Invoice: "invoice"}
HIDDEN_FIELDS = {"password_hash", "token_version", "updated_at", "created_at", "last_login_at"}
LABEL_FIELDS = ("invoice_no", "po_number", "number", "sku", "code", "email", "name")


def audit(db: Session, user: User | None, action: str, entity: str, entity_id=None, summary: str = "",
          details: dict | None = None, outlet_id: int | None = None) -> None:
    """Record an audit entry in the caller's transaction (it is committed together with the change)."""
    db.add(AuditLog(user_id=user.id if user else None, action=action, entity=entity,
                    entity_id=str(entity_id) if entity_id is not None else None, outlet_id=outlet_id,
                    summary=summary[:255], details=details))


def _plain(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    return str(v)


def _label(obj) -> str:
    for f in LABEL_FIELDS:
        v = getattr(obj, f, None)
        if v:
            return str(v)
    return f"#{getattr(obj, 'id', '?')}"


@event.listens_for(Session, "before_flush")
def _record_changes(session: Session, _flush_context, _instances) -> None:
    uid = session.info.get("user_id")
    if uid is None or session.info.get("audit_bulk"):
        # system work (seeding, background jobs) is not user activity; bulk imports write one summary entry
        return
    entries = []
    for obj in list(session.new):
        name = TRACKED.get(type(obj))
        if name:
            entries.append((obj, "create", name, {}))
    for obj in list(session.dirty):
        name = TRACKED.get(type(obj))
        if not name or not session.is_modified(obj):
            continue
        changes = {}
        for attr in inspect(obj).attrs:
            if attr.key in HIDDEN_FIELDS or not attr.history.has_changes():
                continue
            if attr.key in [r.key for r in inspect(type(obj)).relationships]:
                continue
            old = attr.history.deleted[0] if attr.history.deleted else None
            new = attr.history.added[0] if attr.history.added else None
            changes[attr.key] = {"from": _plain(old), "to": _plain(new)}
        if changes:
            action = "void" if name == "sale" and changes.get("status", {}).get("to") == "void" else "update"
            entries.append((obj, action, name, changes))
    for obj in list(session.deleted):
        name = TRACKED.get(type(obj))
        if name:
            entries.append((obj, "delete", name, {}))
    for obj, action, name, changes in entries:
        outlet_id = obj.id if isinstance(obj, Outlet) else getattr(obj, "outlet_id", None)
        verb = {"create": "Created", "update": "Updated", "delete": "Deleted", "void": "Voided"}[action]
        summary = f"{verb} {name.replace('_', ' ')} {_label(obj)}"
        if name == "stock_level" and "reorder_level" in changes:
            summary = f"Changed reorder level for product {obj.product_id} at outlet {obj.outlet_id}"
        elif name == "stock_level" and action == "update":
            continue  # quantity changes are already recorded as stock movements
        entry = AuditLog(user_id=uid, action=f"{name}.{action}", entity=name,
                         entity_id=str(obj.id) if getattr(obj, "id", None) else None,
                         outlet_id=outlet_id if isinstance(outlet_id, int) else None, summary=summary[:255],
                         details=changes or None)
        session.add(entry)
        if entry.entity_id is None and action == "create":
            session.info.setdefault("_audit_pending", []).append((entry, obj))


@event.listens_for(Session, "after_flush_postexec")
def _fill_new_ids(session: Session, _flush_context) -> None:
    """New records get their primary key during the flush; copy it onto their audit entries (and the outlet id
    for new outlets). Session.commit flushes again until clean, so the update is saved in the same transaction."""
    pending = session.info.pop("_audit_pending", None)
    for entry, obj in pending or ():
        if getattr(obj, "id", None) is not None:
            entry.entity_id = str(obj.id)
            if isinstance(obj, Outlet):
                entry.outlet_id = obj.id
            elif entry.outlet_id is None and isinstance(getattr(obj, "outlet_id", None), int):
                entry.outlet_id = obj.outlet_id
