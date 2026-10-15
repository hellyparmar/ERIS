"""Creating and voiding sales (shared by manual entry and CSV import).

A sale of a menu item draws its ingredients down by the recipe quantities (an item without a recipe draws itself
down). If an ingredient would run short, the dish cannot be made and the bill is refused (manual billing only:
imported history never blocks).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import clock
from app.models import CHANNELS, PAYMENT_METHODS, Customer, Outlet, Product, Recipe, Sale, SaleItem, StockMovement, User
from app.services.inventory import change_stock


@dataclass
class LineInput:
    product_id: int
    quantity: float
    unit_price: float | None = None  # defaults to the product's selling price
    discount: float = 0.0  # absolute amount for the line


@dataclass
class SaleInput:
    outlet_id: int
    lines: list[LineInput]
    sold_at: datetime | None = None
    payment_method: str = "cash"
    channel: str = "dine_in"
    covers: int | None = None
    customer_id: int | None = None
    customer_phone: str | None = None
    customer_name: str | None = None
    bill_discount: float = 0.0  # absolute amount, spread across lines proportionally
    invoice_no: str | None = None
    notes: str | None = None
    extra: dict = field(default_factory=dict)


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[-10:]
    return digits or None


def find_or_create_customer(db: Session, phone: str | None, name: str | None) -> Customer | None:
    raw = phone
    phone = normalize_phone(phone)
    if not phone:
        return None
    if len(phone) != 10:
        raise HTTPException(400, f"'{raw}' is not a valid 10-digit mobile number")
    customer = db.scalar(select(Customer).where(Customer.phone == phone))
    if customer is None:
        customer = Customer(name=(name or "").strip() or f"Customer {phone[-4:]}", phone=phone)
        db.add(customer)
        db.flush()
    return customer


def next_invoice_no(db: Session, outlet: Outlet, when: datetime) -> str:
    prefix = f"{outlet.code.replace('-', '')}-{when:%y%m%d}-"
    last = db.scalar(select(func.max(Sale.invoice_no)).where(Sale.invoice_no.like(f"{prefix}%")))
    seq = int(last.rsplit("-", 1)[1]) + 1 if last and last.rsplit("-", 1)[1].isdigit() else 1
    return f"{prefix}{seq:04d}"


def _ingredient_needs(db: Session, built: list) -> list[tuple[int, float, list[int]]]:
    """What the bill uses up: (stocked item id, quantity, the dishes that need it). Dishes use their recipe's
    ingredients; an item sold without a recipe uses itself."""
    ids = [b[0].id for b in built]
    recipes: dict[int, list[tuple[int, float]]] = {}
    for dish, ing, q in db.execute(select(Recipe.menu_item_id, Recipe.ingredient_id, Recipe.quantity).where(
            Recipe.menu_item_id.in_(ids))).all():
        recipes.setdefault(dish, []).append((ing, q))
    need: dict[int, list] = {}
    for product, qty, *_ in built:
        for item_id, per in recipes.get(product.id, [(product.id, 1.0)]):
            entry = need.setdefault(item_id, [0.0, []])
            entry[0] += round(per * qty, 4)
            if product.id not in entry[1]:
                entry[1].append(product.id)
    return [(item_id, round(q, 4), dishes) for item_id, (q, dishes) in need.items()]


def create_sale(db: Session, data: SaleInput, user: User | None, source: str = "manual",
                update_stock: bool = True, commit: bool = True) -> Sale:
    outlet = db.get(Outlet, data.outlet_id)
    if outlet is None:
        raise HTTPException(404, "Outlet not found")
    if not outlet.is_active:
        raise HTTPException(400, f"Outlet {outlet.name} is inactive")
    if not data.lines:
        raise HTTPException(400, "A sale needs at least one item")
    if data.payment_method not in PAYMENT_METHODS:
        raise HTTPException(400, f"payment_method must be one of {', '.join(PAYMENT_METHODS)}")
    if data.channel not in CHANNELS:
        raise HTTPException(400, f"channel must be one of {', '.join(CHANNELS)}")

    sold_at = data.sold_at or clock.now()
    if sold_at > clock.now() + timedelta(minutes=5):
        raise HTTPException(400, "Sale date/time cannot be in the future")

    customer = None
    if data.customer_id:
        customer = db.get(Customer, data.customer_id)
        if customer is None:
            raise HTTPException(404, "Customer not found")
    elif data.customer_phone:
        customer = find_or_create_customer(db, data.customer_phone, data.customer_name)
    if data.payment_method == "credit" and customer is None:
        raise HTTPException(400, "Credit sales must be linked to a customer")

    # merge duplicate products, validate
    merged: dict[tuple[int, float | None], LineInput] = {}
    for line in data.lines:
        if line.quantity is None or line.quantity <= 0:
            raise HTTPException(400, "Quantities must be greater than zero")
        if line.unit_price is not None and line.unit_price < 0:
            raise HTTPException(400, "Unit price cannot be negative")
        if line.discount < 0:
            raise HTTPException(400, "Discount cannot be negative")
        key = (line.product_id, line.unit_price)
        if key in merged:
            merged[key].quantity += line.quantity
            merged[key].discount += line.discount
        else:
            merged[key] = LineInput(line.product_id, line.quantity, line.unit_price, line.discount)

    built = []
    for line in merged.values():
        product = db.get(Product, line.product_id)
        if product is None:
            raise HTTPException(404, f"Product {line.product_id} not found")
        if not product.is_active:
            raise HTTPException(400, f"{product.name} is not active")
        if product.kind != "menu":
            raise HTTPException(400, f"{product.name} is an ingredient, not a menu item")
        price = float(product.selling_price if line.unit_price is None else line.unit_price)
        gross = round(price * line.quantity, 2)
        if line.discount > gross:
            raise HTTPException(400, f"Discount on {product.name} exceeds the line amount")
        built.append([product, line.quantity, price, gross, float(line.discount)])

    gross_total = sum(b[3] for b in built)
    line_disc_total = sum(b[4] for b in built)
    if data.bill_discount < 0 or data.bill_discount > gross_total - line_disc_total:
        raise HTTPException(400, "Bill discount must be between 0 and the bill amount")
    # spread bill discount proportionally (last line absorbs rounding)
    remaining = round(data.bill_discount, 2)
    base = gross_total - line_disc_total
    for i, b in enumerate(built):
        if remaining <= 0:
            break
        share = remaining if i == len(built) - 1 else round(data.bill_discount * (b[3] - b[4]) / base, 2)
        share = min(share, b[3] - b[4])
        b[4] += share
        remaining = round(remaining - share, 2)

    if not data.invoice_no and commit:
        # one bill number at a time per outlet: simultaneous bills queue here instead of clashing (PostgreSQL).
        # Imports (one long transaction) skip the lock so billing is not blocked; the retry below covers them.
        db.execute(select(Outlet.id).where(Outlet.id == outlet.id).with_for_update())
    invoice_no = data.invoice_no or next_invoice_no(db, outlet, sold_at)
    if data.invoice_no and db.scalar(select(Sale.id).where(Sale.invoice_no == data.invoice_no)):
        raise HTTPException(409, f"Invoice {data.invoice_no} already exists")

    sale = Sale(invoice_no=invoice_no, outlet_id=outlet.id, customer_id=customer.id if customer else None,
                sold_at=sold_at, sale_date=sold_at.date(), channel=data.channel,
                covers=data.covers if data.channel == "dine_in" else None,
                payment_method=data.payment_method, status="completed", source=source,
                created_by=user.id if user else None, notes=data.notes, subtotal=0, total=0)
    subtotal = discount = tax_total = total = qty_total = 0.0
    for product, qty, price, gross, disc in built:
        line_total = round(gross - disc, 2)
        tax = round(line_total * product.tax_rate / (100 + product.tax_rate), 2)
        sale.items.append(SaleItem(product_id=product.id, outlet_id=outlet.id, sale_date=sale.sale_date,
                                   quantity=qty, unit_price=price, discount=round(disc, 2), line_total=line_total,
                                   tax_amount=tax, cost_amount=round(qty * product.cost_price, 2)))
        subtotal += gross
        discount += disc
        tax_total += tax
        total += line_total
        qty_total += qty
    sale.subtotal, sale.discount = round(subtotal, 2), round(discount, 2)
    sale.tax_amount, sale.total, sale.items_count = round(tax_total, 2), round(total, 2), qty_total
    for attempt in range(6):
        try:
            with db.begin_nested():  # savepoint: a number clash only undoes this insert
                db.add(sale)
                db.flush()
            break
        except IntegrityError:
            if data.invoice_no:
                raise HTTPException(409, f"Invoice {data.invoice_no} already exists") from None
            if attempt == 5:
                raise HTTPException(409, "Could not allocate an invoice number, please retry") from None
            # another bill took this number at the same moment - take the next free one
            sale.invoice_no = next_invoice_no(db, outlet, sold_at)

    if update_stock:
        for item_id, qty, dishes in _ingredient_needs(db, built):
            try:
                change_stock(db, outlet.id, item_id, -qty, "sale", user.id if user else None,
                             reference=sale.invoice_no, allow_negative=source == "import")
            except HTTPException as exc:
                if dishes == [item_id]:
                    raise
                names = ", ".join(db.get(Product, d).name for d in dishes)
                raise HTTPException(400, f"Cannot make {names}: {exc.detail}") from None
    if commit:
        db.commit()
        db.refresh(sale)
    return sale


def void_sale(db: Session, sale: Sale, user: User, reason: str | None) -> Sale:
    if sale.status == "void":
        raise HTTPException(400, "Sale is already void")
    sale.status = "void"
    sale.notes = f"VOID: {reason}" if reason else "VOID"
    # Put back exactly what this sale drew down (demo history and imported historical sales drew nothing).
    drawn = db.execute(select(StockMovement.product_id, func.sum(StockMovement.change)).where(
        StockMovement.reference == sale.invoice_no, StockMovement.reason == "sale",
        StockMovement.outlet_id == sale.outlet_id).group_by(StockMovement.product_id)).all()
    for item_id, change in drawn:
        if change:
            change_stock(db, sale.outlet_id, item_id, -change, "sale_void", user.id,
                         reference=sale.invoice_no, note=reason)
    db.commit()
    return sale
