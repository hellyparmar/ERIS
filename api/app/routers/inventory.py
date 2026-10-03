"""Stock levels, adjustments, transfers, purchase orders and reorder suggestions."""
from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import clock
from app.db import get_db
from app.models import (
    OPEN_PO_STATUSES,
    Category,
    InventoryItem,
    Organization,
    Outlet,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    StockMovement,
    Supplier,
    User,
)
from app.routers.common import csv_response, get_or_404, page_response, paginate
from app.schemas import PurchaseOrderIn, ReceiveIn, ReorderCreateIn, ReorderLevelIn, StockAdjustIn, TransferIn
from app.security import ensure_outlet_access, get_current_user, require_manager, scoped_outlet_ids
from app.services import analytics as A
from app.services import forecasting as F
from app.services.inventory import change_stock, set_stock, stock_status

router = APIRouter(prefix="/api", tags=["inventory & purchasing"])


@router.get("/inventory")
def list_inventory(outlet_id: int | None = None, category_id: int | None = None, status: str | None = None,
                   search: str | None = None, page: int = 1, page_size: int = Query(50, le=500),
                   sort: str = "cover", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    q = select(InventoryItem, Product, Outlet, Category.name).join(Product, Product.id == InventoryItem.product_id).join(
        Outlet, Outlet.id == InventoryItem.outlet_id).join(Category, Category.id == Product.category_id).where(
        Product.is_active.is_(True))
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    if category_id:
        q = q.where(Product.category_id == category_id)
    if search:
        q = q.where(or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%")))
    if status == "out_of_stock":
        q = q.where(InventoryItem.quantity <= 0, InventoryItem.reorder_level > 0)
    elif status == "low":
        q = q.where(InventoryItem.quantity > 0, InventoryItem.quantity <= InventoryItem.reorder_level)
    elif status == "attention":
        q = q.where(InventoryItem.reorder_level > 0, InventoryItem.quantity <= InventoryItem.reorder_level)
    elif status == "ok":
        q = q.where(InventoryItem.quantity > InventoryItem.reorder_level)

    demand = A.avg_daily_units_by_outlet_product(db, 28)
    rows = db.execute(q).all()
    items = []
    for inv, p, o, cat in rows:
        rate = demand.get((o.id, p.id), 0.0)
        items.append({
            "id": inv.id, "outlet_id": o.id, "outlet": o.name, "product_id": p.id, "sku": p.sku, "product": p.name,
            "category": cat, "unit": p.unit, "quantity": inv.quantity, "reorder_level": inv.reorder_level,
            "cost_price": p.cost_price, "stock_value": round(inv.quantity * p.cost_price, 2),
            "avg_daily_demand": round(rate, 2), "days_of_cover": round(inv.quantity / rate, 1) if rate > 0 else None,
            "status": stock_status(inv.quantity, inv.reorder_level),
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        })
    keyf = {
        "cover": lambda r: (r["days_of_cover"] if r["days_of_cover"] is not None else 1e9, r["product"]),
        "product": lambda r: (r["product"], r["outlet"]),
        "quantity": lambda r: r["quantity"],
        "value": lambda r: -r["stock_value"],
        "outlet": lambda r: (r["outlet"], r["product"]),
    }.get(sort, lambda r: r["product"])
    items.sort(key=keyf)
    total = len(items)
    summary = {
        "lines": total, "stock_value": round(sum(i["stock_value"] for i in items), 2),
        "out_of_stock": sum(1 for i in items if i["status"] == "out_of_stock"),
        "low": sum(1 for i in items if i["status"] == "low"),
    }
    page = max(1, page)
    start = (page - 1) * page_size
    return {**page_response(items[start:start + page_size], total, page, page_size), "summary": summary}


@router.get("/inventory/export")
def export_inventory(outlet_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    q = select(Outlet.code, Product.sku, Product.name, InventoryItem.quantity, InventoryItem.reorder_level).join(
        Product, Product.id == InventoryItem.product_id).join(Outlet, Outlet.id == InventoryItem.outlet_id).order_by(
        Outlet.code, Product.sku)
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    return csv_response("inventory.csv", ["outlet_code", "sku", "product", "quantity", "reorder_level"],
                        [list(r) for r in db.execute(q).all()])


@router.post("/inventory/adjust")
def adjust_stock(body: StockAdjustIn, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    ensure_outlet_access(user, body.outlet_id)
    get_or_404(db, Outlet, body.outlet_id, "Outlet")
    get_or_404(db, Product, body.product_id, "Product")
    reason = "damage" if body.reason == "damage" else body.reason
    if body.mode == "set":
        item = set_stock(db, body.outlet_id, body.product_id, body.quantity, user.id, reason, "MANUAL", body.note)
    else:
        if body.quantity <= 0:
            raise HTTPException(400, "Quantity must be greater than zero")
        change = body.quantity if body.mode == "add" else -body.quantity
        item = change_stock(db, body.outlet_id, body.product_id, change, reason, user.id, "MANUAL", body.note)
    db.commit()
    return {"ok": True, "quantity": item.quantity, "status": stock_status(item.quantity, item.reorder_level)}


@router.post("/inventory/transfer")
def transfer_stock(body: TransferIn, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    if body.from_outlet_id == body.to_outlet_id:
        raise HTTPException(400, "Choose two different outlets")
    ensure_outlet_access(user, body.from_outlet_id)
    src = get_or_404(db, Outlet, body.from_outlet_id, "Outlet")
    dst = get_or_404(db, Outlet, body.to_outlet_id, "Outlet")
    get_or_404(db, Product, body.product_id, "Product")
    ref = f"TRF-{src.code}-{dst.code}"
    change_stock(db, src.id, body.product_id, -body.quantity, "transfer_out", user.id, ref, body.note or f"To {dst.name}")
    change_stock(db, dst.id, body.product_id, body.quantity, "transfer_in", user.id, ref, body.note or f"From {src.name}")
    db.commit()
    return {"ok": True}


@router.patch("/inventory/{item_id}")
def set_reorder_level(item_id: int, body: ReorderLevelIn, user: User = Depends(require_manager),
                      db: Session = Depends(get_db)):
    item = get_or_404(db, InventoryItem, item_id, "Stock item")
    ensure_outlet_access(user, item.outlet_id)
    item.reorder_level = body.reorder_level
    db.commit()
    return {"ok": True, "status": stock_status(item.quantity, item.reorder_level)}


@router.get("/inventory/movements")
def list_movements(outlet_id: int | None = None, product_id: int | None = None, reason: str | None = None,
                   page: int = 1, page_size: int = Query(50, le=500), user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    q = select(StockMovement, Product.name, Outlet.name, User.full_name).join(
        Product, Product.id == StockMovement.product_id).join(Outlet, Outlet.id == StockMovement.outlet_id).outerjoin(
        User, User.id == StockMovement.user_id)
    if outlet_ids:
        q = q.where(StockMovement.outlet_id.in_(outlet_ids))
    if product_id:
        q = q.where(StockMovement.product_id == product_id)
    if reason:
        q = q.where(StockMovement.reason == reason)
    rows, total = paginate(db, q.order_by(StockMovement.id.desc()), page, page_size)
    items = [{"id": m.id, "outlet": o, "product": p, "change": m.change, "balance_after": m.balance_after,
              "reason": m.reason, "reference": m.reference, "note": m.note, "user": u,
              "created_at": m.created_at.isoformat() if m.created_at else None} for m, p, o, u in rows]
    return page_response(items, total, page, page_size)


@router.get("/inventory/reorder-suggestions")
def reorder_suggestions(outlet_id: int | None = None, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    rows = F.reorder_suggestions(db, scoped_outlet_ids(user, outlet_id))
    return {"items": rows, "total_cost": round(sum(r["estimated_cost"] for r in rows), 2),
            "critical": sum(1 for r in rows if r["urgency"] == "critical")}


@router.post("/inventory/reorder", status_code=201)
def create_orders_from_suggestions(body: ReorderCreateIn, user: User = Depends(require_manager),
                                   db: Session = Depends(get_db)):
    """Turn selected suggestions into purchase orders, one per outlet & supplier."""
    groups: dict[tuple[int, int], list] = defaultdict(list)
    skipped: list[str] = []
    for line in body.lines:
        try:
            outlet_id, product_id, qty = int(line["outlet_id"]), int(line["product_id"]), float(line["quantity"])
        except (KeyError, TypeError, ValueError):
            raise HTTPException(400, "Each line needs outlet_id, product_id and quantity") from None
        if qty <= 0:
            continue
        ensure_outlet_access(user, outlet_id)
        p = get_or_404(db, Product, product_id, "Product")
        if not p.supplier_id:
            skipped.append(p.name)  # can't be ordered until a supplier is set - the rest still goes ahead
            continue
        groups[(outlet_id, p.supplier_id)].append((p, qty))
    if not groups:
        if skipped:
            raise HTTPException(400, f"No supplier is set for {', '.join(sorted(set(skipped)))} - set one on the "
                                     "product first")
        raise HTTPException(400, "Nothing to order")
    created = []
    for (outlet_id, supplier_id), lines in groups.items():
        po = _create_po(db, PurchaseOrderIn(supplier_id=supplier_id, outlet_id=outlet_id, items=[
            {"product_id": p.id, "quantity": q, "unit_cost": p.cost_price} for p, q in lines],
            notes="Created from reorder suggestions"), user)
        created.append(po.po_number)
    db.commit()
    return {"created": created, "skipped_no_supplier": sorted(set(skipped))}


# ------------------------------------------------------------------------------------------ purchase orders
def po_dict(po: PurchaseOrder, detail: bool = False) -> dict:
    d = {"id": po.id, "po_number": po.po_number, "supplier_id": po.supplier_id, "supplier": po.supplier.name,
         "outlet_id": po.outlet_id, "outlet": po.outlet.name, "status": po.status,
         "order_date": po.order_date.isoformat(), "expected_date": po.expected_date.isoformat() if po.expected_date else None,
         "received_date": po.received_date.isoformat() if po.received_date else None, "total_cost": po.total_cost,
         "notes": po.notes, "items_count": len(po.items),
         "received_value": round(sum((i.received_quantity or 0) * i.unit_cost for i in po.items), 2),
         "overdue": po.status in OPEN_PO_STATUSES and po.expected_date is not None and po.expected_date < clock.today()}
    if detail:
        d["items"] = [{"product_id": i.product_id, "sku": i.product.sku, "product": i.product.name, "unit": i.product.unit,
                       "quantity": i.quantity, "received_quantity": i.received_quantity or 0.0,
                       "outstanding": i.outstanding if po.status in OPEN_PO_STATUSES else 0.0,
                       "unit_cost": i.unit_cost, "line_total": round(i.quantity * i.unit_cost, 2)}
                      for i in po.items]
    return d


def _create_po(db: Session, body: PurchaseOrderIn, user: User) -> PurchaseOrder:
    ensure_outlet_access(user, body.outlet_id)
    supplier = get_or_404(db, Supplier, body.supplier_id, "Supplier")
    get_or_404(db, Outlet, body.outlet_id, "Outlet")
    today = clock.today()
    # PO numbers run across the organisation: allocate one at a time (simultaneous orders queue here)
    db.execute(select(Organization.id).with_for_update())

    def next_number() -> str:
        count = db.scalar(select(func.count(PurchaseOrder.id))) or 0
        number = f"PO-{today:%y%m}-{count + 1:05d}"
        while db.scalar(select(PurchaseOrder.id).where(PurchaseOrder.po_number == number)):
            count += 1
            number = f"PO-{today:%y%m}-{count + 1:05d}"
        return number

    po = PurchaseOrder(po_number=next_number(), supplier_id=supplier.id, outlet_id=body.outlet_id,
                       status="ordered", order_date=today,
                       expected_date=body.expected_date or today + timedelta(days=supplier.lead_time_days),
                       notes=body.notes, created_by=user.id)
    total = 0.0
    merged: dict[int, list] = {}
    for line in body.items:
        p = get_or_404(db, Product, line.product_id, "Product")
        cost = p.cost_price if line.unit_cost is None else line.unit_cost
        if p.id in merged:
            merged[p.id][1] += line.quantity
        else:
            merged[p.id] = [p, line.quantity, cost]
    for p, qty, cost in merged.values():
        po.items.append(PurchaseOrderItem(product_id=p.id, quantity=qty, unit_cost=cost))
        total += qty * cost
    po.total_cost = round(total, 2)
    for attempt in range(6):
        try:
            with db.begin_nested():  # a PO number taken at the same moment only undoes this insert
                db.add(po)
                db.flush()
            break
        except IntegrityError:
            if attempt == 5:
                raise HTTPException(409, "Could not allocate a purchase order number, please retry") from None
            po.po_number = next_number()
    return po


@router.get("/purchase-orders")
def list_pos(status: str | None = None, supplier_id: int | None = None, outlet_id: int | None = None,
             page: int = 1, page_size: int = Query(50, le=500), user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    q = select(PurchaseOrder)
    if outlet_ids:
        q = q.where(PurchaseOrder.outlet_id.in_(outlet_ids))
    if status == "overdue":
        q = q.where(PurchaseOrder.status.in_(OPEN_PO_STATUSES), PurchaseOrder.expected_date < clock.today())
    elif status == "open":
        q = q.where(PurchaseOrder.status.in_(OPEN_PO_STATUSES))
    elif status:
        q = q.where(PurchaseOrder.status == status)
    if supplier_id:
        q = q.where(PurchaseOrder.supplier_id == supplier_id)
    rows, total = paginate(db, q.order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.id.desc()), page, page_size)
    return page_response([po_dict(r[0]) for r in rows], total, page, page_size)


@router.get("/purchase-orders/{po_id}")
def get_po(po_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    po = get_or_404(db, PurchaseOrder, po_id, "Purchase order")
    ensure_outlet_access(user, po.outlet_id)
    return po_dict(po, detail=True)


@router.post("/purchase-orders", status_code=201)
def create_po(body: PurchaseOrderIn, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    po = _create_po(db, body, user)
    db.commit()
    db.refresh(po)
    return po_dict(po, detail=True)


@router.post("/purchase-orders/{po_id}/receive")
def receive_po(po_id: int, body: ReceiveIn, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    """Record a delivery. `items` are the quantities arriving now (default: everything still outstanding).
    A short delivery leaves the order open as 'partial'; it is complete when nothing is outstanding."""
    po = get_or_404(db, PurchaseOrder, po_id, "Purchase order")
    ensure_outlet_access(user, po.outlet_id)
    if po.status not in OPEN_PO_STATUSES:
        raise HTTPException(400, f"Only open orders can be received (this one is {po.status})")
    lines = {i.product_id: i for i in po.items}
    if body.items is None:
        arriving = {pid: item.outstanding for pid, item in lines.items()}
    else:
        arriving: dict[int, float] = {}
        for line in body.items:
            if line.product_id not in lines:
                raise HTTPException(400, "Received items must be on the purchase order")
            arriving[line.product_id] = arriving.get(line.product_id, 0.0) + line.quantity
        for pid, qty in arriving.items():
            item = lines[pid]
            if qty > item.outstanding + 1e-9:
                raise HTTPException(400, f"{item.product.name}: {qty:g} received but only {item.outstanding:g} "
                                         "still outstanding - create a new order for extra goods")
    if not any(q > 0 for q in arriving.values()):
        raise HTTPException(400, "Enter the quantity that arrived for at least one item")
    for pid, qty in arriving.items():
        if qty > 0:
            item = lines[pid]
            item.received_quantity = round((item.received_quantity or 0.0) + qty, 3)
            change_stock(db, po.outlet_id, pid, qty, "purchase", user.id, po.po_number, "Goods received")
    po.received_date = clock.today()
    po.status = "received" if all(i.outstanding <= 0 for i in po.items) else "partial"
    db.commit()
    db.refresh(po)
    return po_dict(po, detail=True)


@router.post("/purchase-orders/{po_id}/cancel")
def cancel_po(po_id: int, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    """Cancel an open order. If part of it was already delivered, the order is closed instead: the delivered
    goods stay in stock and the outstanding quantity is no longer expected."""
    po = get_or_404(db, PurchaseOrder, po_id, "Purchase order")
    ensure_outlet_access(user, po.outlet_id)
    if po.status not in OPEN_PO_STATUSES:
        raise HTTPException(400, f"Only open orders can be cancelled (this one is {po.status})")
    po.status = "closed" if po.status == "partial" else "cancelled"
    db.commit()
    return po_dict(po)
