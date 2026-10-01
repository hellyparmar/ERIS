"""CSV import for sales, products, customers, suppliers and stock levels.

Every import can run as a dry run first: rows are fully validated and the caller gets a per-row error report
and a preview, without anything being written. A real run is all-or-nothing per file.
"""
from __future__ import annotations

import csv
import io
import re
from collections import OrderedDict
from datetime import datetime, time

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PAYMENT_METHODS, Category, Customer, Outlet, Product, Sale, Supplier, User
from app.services.inventory import set_stock
from app.services.sales import LineInput, SaleInput, create_sale, normalize_phone

MAX_ROWS = 50_000
MAX_ERRORS = 200

TEMPLATES: dict[str, dict] = {
    "sales": {
        "columns": ["invoice_no", "date", "time", "outlet_code", "sku", "quantity", "unit_price", "discount",
                    "payment_method", "channel", "customer_phone", "customer_name"],
        "required": ["date", "outlet_code", "sku", "quantity"],
        "example": [
            ["INV-1001", "2026-09-30", "10:15", "MUM-AND", "DAI-001", "2", "", "", "upi", "in_store", "9876543210", "Asha Verma"],
            ["INV-1001", "2026-09-30", "10:15", "MUM-AND", "BAK-002", "1", "", "", "upi", "in_store", "9876543210", "Asha Verma"],
            ["INV-1002", "2026-09-30", "11:40", "MUM-AND", "BEV-001", "6", "18", "5", "cash", "in_store", "", ""],
        ],
        "help": "One row per product line. Rows sharing an invoice_no become one bill. outlet_code and sku must "
                "already exist (outlet name and product name also work). unit_price defaults to the product's "
                "selling price; discount is a rupee amount for the line. Dates: YYYY-MM-DD or DD-MM-YYYY.",
    },
    "products": {
        "columns": ["sku", "name", "category", "unit", "cost_price", "selling_price", "tax_rate", "reorder_level",
                    "supplier"],
        "required": ["sku", "name", "category", "cost_price", "selling_price"],
        "example": [["BEV-101", "Ginger Ale 300ml", "Beverages", "can", "35", "60", "18", "12", "Coastal Beverages Distributors"]],
        "help": "Existing SKUs are updated, new SKUs are created. New categories are created automatically; "
                "supplier must match an existing supplier name (or be left empty).",
    },
    "customers": {
        "columns": ["name", "phone", "email", "city", "customer_type"],
        "required": ["name", "phone"],
        "example": [["Asha Verma", "9876543210", "asha@example.com", "Mumbai", "retail"]],
        "help": "Customers are matched on phone number: existing ones are updated. customer_type is retail or business.",
    },
    "suppliers": {
        "columns": ["name", "contact_person", "phone", "email", "city", "lead_time_days", "payment_terms"],
        "required": ["name"],
        "example": [["Fresh Valley Farms", "Rohit Jain", "+91 98000 00000", "orders@freshvalley.example", "Nashik", "2", "Net 15"]],
        "help": "Suppliers are matched on name: existing ones are updated.",
    },
    "inventory": {
        "columns": ["outlet_code", "sku", "quantity", "reorder_level"],
        "required": ["outlet_code", "sku", "quantity"],
        "example": [["MUM-AND", "DAI-001", "120", "40"]],
        "help": "Sets the counted stock level (stock-take). A stock movement is recorded for the difference.",
    },
}


def template_csv(kind: str) -> str:
    t = TEMPLATES.get(kind)
    if not t:
        raise HTTPException(404, "Unknown import type")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(t["columns"])
    w.writerows(t["example"])
    return buf.getvalue()


def _read_csv(content: bytes) -> list[dict]:
    text = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None or not text.strip():
        raise HTTPException(400, "The file is empty or not a text CSV file")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise HTTPException(400, "The CSV file has no header row")
    rows = []
    for raw in reader:
        row = {_norm_key(k): (v or "").strip() for k, v in raw.items() if k is not None}
        if any(row.values()):
            rows.append(row)
        if len(rows) > MAX_ROWS:
            raise HTTPException(400, f"Files are limited to {MAX_ROWS:,} rows; please split the file")
    return rows


def _norm_key(k: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", k.strip().lower()).strip("_")


def _num(value: str, name: str, allow_empty: bool = False, minimum: float | None = 0) -> float | None:
    if value in ("", None):
        if allow_empty:
            return None
        raise ValueError(f"{name} is required")
    try:
        n = float(str(value).replace(",", "").replace("₹", "").strip())
    except ValueError:
        raise ValueError(f"{name} '{value}' is not a number") from None
    if minimum is not None and n < minimum:
        raise ValueError(f"{name} cannot be below {minimum:g}")
    return n


DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d.%m.%Y", "%d-%b-%Y", "%d %b %Y")


def _date(value: str):
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value[:11].strip(), fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise ValueError(f"date '{value}' not recognised (use YYYY-MM-DD or DD-MM-YYYY)") from None


def _time(value: str) -> time:
    if not value:
        return time(12, 0)
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(value.strip().upper() if "M" in value.upper() else value.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"time '{value}' not recognised (use HH:MM)")


def _check_columns(rows: list[dict], kind: str) -> None:
    if not rows:
        raise HTTPException(400, "The file has no data rows")
    present = set(rows[0].keys())
    required = TEMPLATES[kind]["required"]
    aliases = {"outlet_code": {"outlet", "outlet_name"}, "sku": {"product", "product_name"}}
    missing = [c for c in required if c not in present and not (aliases.get(c, set()) & present)]
    if missing:
        raise HTTPException(400, f"Missing required column(s): {', '.join(missing)}. "
                                 f"Expected columns: {', '.join(TEMPLATES[kind]['columns'])}")


class _Lookup:
    def __init__(self, db: Session):
        self.outlets = {}
        for o in db.scalars(select(Outlet)).all():
            self.outlets[o.code.lower()] = o
            self.outlets[o.name.lower()] = o
        self.products = {}
        for p in db.scalars(select(Product)).all():
            self.products[p.sku.lower()] = p
            self.products.setdefault(p.name.lower(), p)
        self.suppliers = {s.name.lower(): s for s in db.scalars(select(Supplier)).all()}

    def outlet(self, row: dict) -> Outlet:
        key = (row.get("outlet_code") or row.get("outlet") or row.get("outlet_name") or "").lower()
        if not key:
            raise ValueError("outlet_code is required")
        o = self.outlets.get(key)
        if not o:
            raise ValueError(f"unknown outlet '{key}'")
        return o

    def product(self, row: dict) -> Product:
        key = (row.get("sku") or row.get("product") or row.get("product_name") or "").lower()
        if not key:
            raise ValueError("sku is required")
        p = self.products.get(key)
        if not p:
            raise ValueError(f"unknown product '{key}' - add it under Products first")
        return p


def run_import(db: Session, kind: str, content: bytes, user: User, dry_run: bool = True,
               update_stock: bool = False) -> dict:
    if kind not in TEMPLATES:
        raise HTTPException(404, "Unknown import type")
    rows = _read_csv(content)
    _check_columns(rows, kind)
    handler = {"sales": _import_sales, "products": _import_products, "customers": _import_customers,
               "suppliers": _import_suppliers, "inventory": _import_inventory}[kind]
    result = {"kind": kind, "dry_run": dry_run, "total_rows": len(rows), "created": 0, "updated": 0,
              "errors": [], "preview": []}
    try:
        handler(db, rows, user, result, update_stock)
        if result["errors"] or dry_run:
            db.rollback()
        else:
            db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    result["error_count"] = len(result["errors"])
    result["errors"] = result["errors"][:MAX_ERRORS]
    result["valid_rows"] = result["total_rows"] - len({e["row"] for e in result["errors"]})
    result["committed"] = not dry_run and not result["errors"]
    if not dry_run and result["errors"]:
        result["message"] = "Nothing was imported because some rows have errors. Fix them and upload again."
    elif dry_run:
        result["message"] = ("All rows look good - run the import to save them." if not result["errors"]
                             else f"{result['error_count']} row(s) need fixing before import.")
    else:
        result["message"] = f"Import complete: {result['created']} created, {result['updated']} updated."
    return result


def _err(result: dict, row_no: int, msg: str) -> None:
    result["errors"].append({"row": row_no, "message": msg})


# ------------------------------------------------------------------------------------------ sales
def _import_sales(db: Session, rows: list[dict], user: User, result: dict, update_stock: bool) -> None:
    lk = _Lookup(db)
    bills: "OrderedDict[str, dict]" = OrderedDict()
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        try:
            outlet = lk.outlet(row)
            if user.role != "admin" and user.outlet_id and outlet.id != user.outlet_id:
                raise ValueError("you can only import sales for your own outlet")
            product = lk.product(row)
            qty = _num(row.get("quantity", ""), "quantity")
            if qty == 0:
                raise ValueError("quantity must be greater than zero")
            price = _num(row.get("unit_price", ""), "unit_price", allow_empty=True)
            disc = _num(row.get("discount", ""), "discount", allow_empty=True) or 0.0
            d = _date(row.get("date", ""))
            t = _time(row.get("time", ""))
            pm = (row.get("payment_method") or "cash").lower().replace(" ", "_")
            pm = {"gpay": "upi", "phonepe": "upi", "paytm": "upi", "debit_card": "card", "credit_card": "card"}.get(pm, pm)
            if pm not in PAYMENT_METHODS:
                raise ValueError(f"payment_method '{pm}' must be one of {', '.join(PAYMENT_METHODS)}")
            channel = (row.get("channel") or "in_store").lower().replace(" ", "_").replace("-", "_")
            channel = {"store": "in_store", "instore": "in_store", "online": "delivery"}.get(channel, channel)
            phone = normalize_phone(row.get("customer_phone"))
            if row.get("customer_phone") and (not phone or len(phone) < 10):
                raise ValueError(f"customer_phone '{row.get('customer_phone')}' is not a valid phone number")
        except ValueError as exc:
            _err(result, i, str(exc))
            continue
        key = row.get("invoice_no") or f"__row{i}"
        bill = bills.setdefault(key, {"row": i, "outlet": outlet, "when": datetime.combine(d, t), "payment": pm,
                                      "channel": channel, "phone": phone, "name": row.get("customer_name"),
                                      "lines": [], "invoice_no": row.get("invoice_no") or None})
        if bill["outlet"].id != outlet.id:
            _err(result, i, f"invoice {key} has rows for different outlets")
            continue
        bill["lines"].append(LineInput(product.id, qty, price, disc))

    existing = set()
    invoice_nos = [b["invoice_no"] for b in bills.values() if b["invoice_no"]]
    for chunk_start in range(0, len(invoice_nos), 900):
        chunk = invoice_nos[chunk_start:chunk_start + 900]
        existing |= set(db.scalars(select(Sale.invoice_no).where(Sale.invoice_no.in_(chunk))).all())

    for bill in bills.values():
        if bill["invoice_no"] in existing:
            _err(result, bill["row"], f"invoice {bill['invoice_no']} already exists - skipped duplicate")
            continue
        try:
            with db.begin_nested():
                sale = create_sale(db, SaleInput(
                    outlet_id=bill["outlet"].id, lines=bill["lines"], sold_at=bill["when"],
                    payment_method=bill["payment"], channel=bill["channel"], customer_phone=bill["phone"],
                    customer_name=bill["name"], invoice_no=bill["invoice_no"]), user, source="import",
                    update_stock=update_stock, commit=False)
            result["created"] += 1
            if len(result["preview"]) < 10:
                result["preview"].append({"invoice_no": sale.invoice_no, "outlet": bill["outlet"].name,
                                          "date": sale.sold_at.isoformat(sep=" "), "items": len(bill["lines"]),
                                          "total": sale.total, "payment_method": sale.payment_method})
        except HTTPException as exc:
            _err(result, bill["row"], str(exc.detail))
    result["bills"] = len(bills)


# ------------------------------------------------------------------------------------------ master data
def _import_products(db: Session, rows: list[dict], user: User, result: dict, _update_stock: bool) -> None:
    lk = _Lookup(db)
    cats = {c.name.lower(): c for c in db.scalars(select(Category)).all()}
    seen = set()
    for i, row in enumerate(rows, start=2):
        try:
            sku = row.get("sku", "").upper()
            if not sku:
                raise ValueError("sku is required")
            if sku in seen:
                raise ValueError(f"duplicate sku {sku} in file")
            seen.add(sku)
            name = row.get("name", "")
            if not name:
                raise ValueError("name is required")
            cost = _num(row.get("cost_price", ""), "cost_price")
            price = _num(row.get("selling_price", ""), "selling_price")
            if price < cost:
                raise ValueError("selling_price is below cost_price")
            tax = _num(row.get("tax_rate", ""), "tax_rate", allow_empty=True)
            if tax is not None and tax > 40:
                raise ValueError("tax_rate looks wrong (should be a percentage like 5 or 18)")
            reorder = _num(row.get("reorder_level", ""), "reorder_level", allow_empty=True)
            supplier = None
            if row.get("supplier"):
                supplier = lk.suppliers.get(row["supplier"].lower())
                if not supplier:
                    raise ValueError(f"unknown supplier '{row['supplier']}' - add the supplier first")
            cat_name = row.get("category", "").strip()
            if not cat_name:
                raise ValueError("category is required")
        except ValueError as exc:
            _err(result, i, str(exc))
            continue
        cat = cats.get(cat_name.lower())
        if cat is None:
            cat = Category(name=cat_name)
            db.add(cat)
            db.flush()
            cats[cat_name.lower()] = cat
        p = lk.products.get(sku.lower())
        fields = {"name": name, "category_id": cat.id, "cost_price": cost, "selling_price": price}
        if row.get("unit"):
            fields["unit"] = row["unit"]
        if tax is not None:
            fields["tax_rate"] = tax
        if reorder is not None:
            fields["reorder_level"] = reorder
        if supplier:
            fields["supplier_id"] = supplier.id
        if p:
            for k, v in fields.items():
                setattr(p, k, v)
            result["updated"] += 1
        else:
            p = Product(sku=sku, **fields)
            db.add(p)
            result["created"] += 1
        if len(result["preview"]) < 10:
            result["preview"].append({"sku": sku, "name": name, "category": cat_name, "selling_price": price})


def _import_customers(db: Session, rows: list[dict], user: User, result: dict, _update_stock: bool) -> None:
    seen = set()
    for i, row in enumerate(rows, start=2):
        name, phone = row.get("name", ""), normalize_phone(row.get("phone"))
        ctype = (row.get("customer_type") or "retail").lower()
        if not name:
            _err(result, i, "name is required")
            continue
        if not phone or len(phone) < 10:
            _err(result, i, f"phone '{row.get('phone', '')}' is not a valid phone number")
            continue
        if ctype not in ("retail", "business"):
            _err(result, i, "customer_type must be retail or business")
            continue
        if phone in seen:
            _err(result, i, f"duplicate phone {phone} in file")
            continue
        seen.add(phone)
        c = db.scalar(select(Customer).where(Customer.phone == phone))
        if c:
            c.name, c.customer_type = name, ctype
            c.email = row.get("email") or c.email
            c.city = row.get("city") or c.city
            result["updated"] += 1
        else:
            db.add(Customer(name=name, phone=phone, email=row.get("email") or None, city=row.get("city") or None,
                            customer_type=ctype))
            result["created"] += 1
        if len(result["preview"]) < 10:
            result["preview"].append({"name": name, "phone": phone, "type": ctype})


def _import_suppliers(db: Session, rows: list[dict], user: User, result: dict, _update_stock: bool) -> None:
    seen = set()
    for i, row in enumerate(rows, start=2):
        name = row.get("name", "")
        if not name:
            _err(result, i, "name is required")
            continue
        if name.lower() in seen:
            _err(result, i, f"duplicate supplier {name} in file")
            continue
        seen.add(name.lower())
        try:
            lead = _num(row.get("lead_time_days", ""), "lead_time_days", allow_empty=True)
        except ValueError as exc:
            _err(result, i, str(exc))
            continue
        s = db.scalar(select(Supplier).where(func.lower(Supplier.name) == name.lower()))
        fields = {k: row[k] for k in ("contact_person", "phone", "email", "city", "payment_terms") if row.get(k)}
        if lead is not None:
            fields["lead_time_days"] = int(lead)
        if s:
            for k, v in fields.items():
                setattr(s, k, v)
            result["updated"] += 1
        else:
            db.add(Supplier(name=name, **fields))
            result["created"] += 1
        if len(result["preview"]) < 10:
            result["preview"].append({"name": name, **fields})


def _import_inventory(db: Session, rows: list[dict], user: User, result: dict, _update_stock: bool) -> None:
    lk = _Lookup(db)
    seen = set()
    for i, row in enumerate(rows, start=2):
        try:
            outlet = lk.outlet(row)
            if user.role != "admin" and user.outlet_id and outlet.id != user.outlet_id:
                raise ValueError("you can only update stock for your own outlet")
            product = lk.product(row)
            qty = _num(row.get("quantity", ""), "quantity")
            reorder = _num(row.get("reorder_level", ""), "reorder_level", allow_empty=True)
            if (outlet.id, product.id) in seen:
                raise ValueError("duplicate outlet/sku row in file")
            seen.add((outlet.id, product.id))
        except ValueError as exc:
            _err(result, i, str(exc))
            continue
        item = set_stock(db, outlet.id, product.id, qty, user.id, reason="import", reference="STOCK-IMPORT",
                         note="Stock count import")
        if reorder is not None:
            item.reorder_level = reorder
        result["updated"] += 1
        if len(result["preview"]) < 10:
            result["preview"].append({"outlet": outlet.name, "sku": product.sku, "quantity": qty})
