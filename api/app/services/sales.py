"""Creating and voiding sales (shared by manual entry and CSV import)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import clock
from app.models import CHANNELS, PAYMENT_METHODS, Customer, Outlet, Product, Sale, SaleItem, StockMovement, User
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
    channel: str = "in_store"
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

    invoice_no = data.invoice_no or next_invoice_no(db, outlet, sold_at)
    if data.invoice_no and db.scalar(select(Sale.id).where(Sale.invoice_no == data.invoice_no)):
        raise HTTPException(409, f"Invoice {data.invoice_no} already exists")

    sale = Sale(invoice_no=invoice_no, outlet_id=outlet.id, customer_id=customer.id if customer else None,
                sold_at=sold_at, sale_date=sold_at.date(), channel=data.channel,
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
    db.add(sale)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Invoice number conflict, please retry") from None

    if update_stock:
        for product, qty, *_ in built:
            change_stock(db, outlet.id, product.id, -qty, "sale", user.id if user else None, reference=invoice_no,
                         allow_negative=source == "import")
    if commit:
        db.commit()
        db.refresh(sale)
    return sale


def void_sale(db: Session, sale: Sale, user: User, reason: str | None) -> Sale:
    if sale.status == "void":
        raise HTTPException(400, "Sale is already void")
    sale.status = "void"
    sale.notes = f"VOID: {reason}" if reason else "VOID"
    # Only restore stock if this sale actually decremented it (demo history and
    # imported historical sales may not have).
    decremented = db.scalar(select(func.count(StockMovement.id)).where(
        StockMovement.reference == sale.invoice_no, StockMovement.reason == "sale"))
    if decremented:
        for item in sale.items:
            change_stock(db, sale.outlet_id, item.product_id, item.quantity, "sale_void", user.id,
                         reference=sale.invoice_no, note=reason)
    db.commit()
    return sale
