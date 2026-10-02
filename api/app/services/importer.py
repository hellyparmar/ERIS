"""CSV import for sales, products, customers, suppliers and stock levels.

Flow: inspect (headers, suggested column mapping, sample rows) -> dry run (full validation, per-row errors,
preview, nothing written) -> commit (all-or-nothing per file). Every run is recorded as an ImportJob with its
error report (downloadable as CSV); committed sales carry the job id so an import can be traced afterwards.
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

from app.models import PAYMENT_METHODS, Category, Customer, ImportJob, Outlet, Product, Sale, Supplier, User
from app.services.audit import audit
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


ALLOWED_EXTENSIONS = (".csv", ".txt", ".tsv")

# alternative header names seen in POS exports, mapped to template columns
ALIASES: dict[str, set[str]] = {
    "invoice_no": {"invoice", "invoice_number", "bill_no", "bill_number", "receipt_no", "order_id", "txn_id"},
    "date": {"sale_date", "bill_date", "invoice_date", "order_date", "transaction_date"},
    "time": {"sale_time", "bill_time"},
    "outlet_code": {"outlet", "outlet_name", "store", "store_code", "branch", "location"},
    "sku": {"product", "product_name", "item", "item_code", "product_code", "barcode"},
    "quantity": {"qty", "units", "quantity_sold"},
    "unit_price": {"price", "rate", "mrp", "selling_price"},
    "discount": {"discount_amount", "disc"},
    "payment_method": {"payment", "payment_mode", "mode", "tender"},
    "customer_phone": {"phone", "mobile", "customer_mobile", "contact"},
    "customer_name": {"customer"},
    "cost_price": {"cost", "purchase_price"},
    "tax_rate": {"gst", "gst_rate", "tax"},
    "reorder_level": {"reorder", "min_stock"},
    "lead_time_days": {"lead_time"},
}


def check_file(filename: str | None, content: bytes) -> None:
    """Reject files that are clearly not CSV before parsing them."""
    name = (filename or "").lower()
    if content[:4] == b"PK\x03\x04" or name.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Excel files are not read directly - use File > Save As > CSV (UTF-8) first")
    if name and not name.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(400, f"Only CSV files are accepted ({', '.join(ALLOWED_EXTENSIONS)})")
    if b"\x00" in content[:8192]:
        raise HTTPException(400, "The file looks binary, not a text CSV file")


def suggest_mapping(kind: str, headers: list[str]) -> dict[str, str | None]:
    """{template column: file header or None} using exact names, then known aliases."""
    norm = {_norm_key(h): h for h in headers}
    out = {}
    for col in TEMPLATES[kind]["columns"]:
        if col in norm:
            out[col] = norm[col]
            continue
        hit = next((norm[a] for a in ALIASES.get(col, ()) if a in norm), None)
        out[col] = hit
    return out


def apply_mapping(rows: list[dict], mapping: dict[str, str | None] | None) -> list[dict]:
    """Rename file columns to template columns. Unmapped template columns are left absent."""
    if not mapping:
        return rows
    pairs = [(col, _norm_key(src)) for col, src in mapping.items() if src]
    return [{**{k: v for k, v in r.items()}, **{col: r.get(src, "") for col, src in pairs}} for r in rows]


def inspect_file(kind: str, content: bytes, filename: str | None) -> dict:
    if kind not in TEMPLATES:
        raise HTTPException(404, "Unknown import type")
    check_file(filename, content)
    rows, headers = _read_csv(content, with_headers=True)
    mapping = suggest_mapping(kind, headers)
    missing = [c for c in TEMPLATES[kind]["required"] if not mapping.get(c)]
    return {"kind": kind, "filename": filename, "headers": headers, "rows": len(rows), "mapping": mapping,
            "columns": TEMPLATES[kind]["columns"], "required": TEMPLATES[kind]["required"],
            "missing_required": missing, "sample": rows[:5]}


def _read_csv(content: bytes, with_headers: bool = False):
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
    headers = [h.strip() for h in reader.fieldnames if h and h.strip()]
    rows = []
    for raw in reader:
        row = {_norm_key(k): (v or "").strip() for k, v in raw.items() if k is not None}
        if any(row.values()):
            rows.append(row)
        if len(rows) > MAX_ROWS:
            raise HTTPException(400, f"Files are limited to {MAX_ROWS:,} rows; please split the file")
    return (rows, headers) if with_headers else rows


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
        raw = row.get("outlet_code") or row.get("outlet") or row.get("outlet_name") or ""
        if not raw:
            raise ValueError("outlet_code is required")
        o = self.outlets.get(raw.lower())
        if not o:
            raise ValueError(f"unknown outlet '{raw}'")
        return o

    def product(self, row: dict) -> Product:
        raw = row.get("sku") or row.get("product") or row.get("product_name") or ""
        if not raw:
            raise ValueError("sku is required")
        p = self.products.get(raw.lower())
        if not p:
            raise ValueError(f"unknown product '{raw}' - add it under Products first")
        return p


def run_import(db: Session, kind: str, content: bytes, user: User, dry_run: bool = True,
               update_stock: bool = False, mapping: dict | None = None, filename: str | None = None,
               skip_duplicates: bool = True) -> dict:
    if kind not in TEMPLATES:
        raise HTTPException(404, "Unknown import type")
    check_file(filename, content)
    rows = apply_mapping(_read_csv(content), mapping)
    _check_columns(rows, kind)
    handler = {"sales": _import_sales, "products": _import_products, "customers": _import_customers,
               "suppliers": _import_suppliers, "inventory": _import_inventory}[kind]

    job = ImportJob(kind=kind, filename=(filename or "")[:255] or None, status="running", dry_run=dry_run,
                    total_rows=len(rows), mapping=mapping or None, user_id=user.id)
    db.add(job)
    db.commit()
    job_id = job.id

    committed = False
    result = {"kind": kind, "dry_run": dry_run, "total_rows": len(rows), "created": 0, "updated": 0,
              "errors": [], "warnings": [], "preview": [], "skipped_duplicates": 0, "job_id": job_id}
    db.info["audit_bulk"] = True
    try:
        handler(db, rows, user, result, {"update_stock": update_stock, "skip_duplicates": skip_duplicates,
                                         "import_id": job_id})
        committed = not dry_run and not result["errors"]
        if committed:
            db.flush()  # write the rows while per-row auditing is off
            del db.info["audit_bulk"]
            audit(db, user, f"import.{kind}", "import", job_id,
                  f"Imported {kind} from {filename or 'CSV'}: {result['created']} created, "
                  f"{result['updated']} updated", {"rows": len(rows), "skipped_duplicates":
                                                   result["skipped_duplicates"]})
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        db.info.pop("audit_bulk", None)
        job = db.get(ImportJob, job_id)
        job.status = "failed"
        db.commit()
        raise
    finally:
        db.info.pop("audit_bulk", None)

    result["error_count"] = len(result["errors"])
    result["valid_rows"] = result["total_rows"] - len({e["row"] for e in result["errors"]})
    result["committed"] = committed
    if not dry_run and result["errors"]:
        result["message"] = "Nothing was imported because some rows have errors. Fix them and upload again."
    elif dry_run:
        result["message"] = ("All rows look good - run the import to save them." if not result["errors"]
                             else f"{result['error_count']} row(s) need fixing before import.")
    else:
        result["message"] = f"Import complete: {result['created']} created, {result['updated']} updated."
    if result["skipped_duplicates"]:
        result["message"] += f" {result['skipped_duplicates']} duplicate bill(s) already in ERIS will be skipped." \
            if dry_run else f" {result['skipped_duplicates']} duplicate bill(s) were skipped."

    job = db.get(ImportJob, job_id)
    job.status = "committed" if committed else ("validated" if dry_run and not result["errors"] else "rejected")
    job.created_count, job.updated_count = (result["created"], result["updated"])
    job.error_count = result["error_count"]
    job.errors = (result["errors"] + result["warnings"])[:5000]
    db.commit()
    result["errors"] = result["errors"][:MAX_ERRORS]
    result["warnings"] = result["warnings"][:MAX_ERRORS]
    return result


def error_report_csv(job: ImportJob) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["row", "severity", "message"])
    for e in job.errors or []:
        w.writerow([e.get("row"), e.get("severity", "error"), e.get("message")])
    return buf.getvalue()


def sample_csv(db: Session, kind: str, with_errors: bool = False) -> str:
    """A ready-to-import example built from this database's real outlets and products (with deliberate
    mistakes when `with_errors` is set, to show what validation catches)."""
    from datetime import timedelta

    from app import clock

    if kind not in TEMPLATES:
        raise HTTPException(404, "Unknown import type")
    outlets = db.scalars(select(Outlet).where(Outlet.is_active.is_(True)).order_by(Outlet.id).limit(3)).all()
    products = db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.id).limit(8)).all()
    if not outlets or not products:
        return template_csv(kind)
    day = clock.today() - timedelta(days=1)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(TEMPLATES[kind]["columns"])
    if kind == "sales":
        stamp = clock.now().strftime("%H%M%S")
        for b in range(6):
            o = outlets[b % len(outlets)]
            for k in range(1 + b % 3):
                p = products[(b + k) % len(products)]
                w.writerow([f"SAMPLE-{stamp}-{b + 1}", day.isoformat(), f"{10 + b}:{15 + k:02d}", o.code, p.sku,
                            1 + (b + k) % 3, "", "", ("upi", "cash", "card")[b % 3], "in_store",
                            f"98{b:02d}00{stamp}"[:10] if b % 2 == 0 else "", f"Sample Customer {b + 1}" if b % 2 == 0 else ""])
        if with_errors:
            o, p = outlets[0], products[0]
            w.writerow([f"SAMPLE-{stamp}-E1", day.isoformat(), "12:00", o.code, "NO-SUCH-SKU", 1, "", "", "cash",
                        "in_store", "", ""])
            w.writerow([f"SAMPLE-{stamp}-E2", day.isoformat(), "12:05", o.code, p.sku, -2, "", "", "cash",
                        "in_store", "", ""])
            w.writerow([f"SAMPLE-{stamp}-E3", "31-31-2025", "12:10", o.code, p.sku, 1, "", "", "cash",
                        "in_store", "", ""])
            w.writerow([f"SAMPLE-{stamp}-E4", day.isoformat(), "12:15", "XXX-000", p.sku, 1, "", "", "cheque",
                        "in_store", "", ""])
            w.writerow([f"SAMPLE-{stamp}-E5", day.isoformat(), "12:20", o.code, p.sku, 1, "", "", "upi",
                        "in_store", "12345", ""])
    elif kind == "inventory":
        for o in outlets:
            for p in products[:4]:
                w.writerow([o.code, p.sku, 50, ""])
        if with_errors:
            w.writerow([outlets[0].code, "NO-SUCH-SKU", 10, ""])
            w.writerow([outlets[0].code, products[0].sku, "ten", ""])
    else:
        w.writerows(TEMPLATES[kind]["example"])
        if with_errors:
            bad = {"products": ["", "Nameless SKU", "Snacks", "pcs", "10", "8", "5", "", ""],
                   "customers": ["No Phone", "12", "", "", "retail"],
                   "suppliers": ["Bad Lead Time", "", "", "", "", "soon", ""]}[kind]
            w.writerow(bad)
    return buf.getvalue()


def _err(result: dict, row_no: int, msg: str) -> None:
    result["errors"].append({"row": row_no, "severity": "error", "message": msg})


def _warn(result: dict, row_no: int, msg: str) -> None:
    result["warnings"].append({"row": row_no, "severity": "warning", "message": msg})


# ------------------------------------------------------------------------------------------ sales
def _import_sales(db: Session, rows: list[dict], user: User, result: dict, opts: dict) -> None:
    lk = _Lookup(db)
    bills: "OrderedDict[str, dict]" = OrderedDict()
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        try:
            outlet = lk.outlet(row)
            if user.role != "admin" and outlet.id not in user.outlet_ids:
                raise ValueError("you can only import sales for your own outlets")
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
        if bill["when"].date() != d:
            _err(result, i, f"invoice {key} has rows with different dates")
            continue
        bill["lines"].append(LineInput(product.id, qty, price, disc))

    existing = set()
    invoice_nos = [b["invoice_no"] for b in bills.values() if b["invoice_no"]]
    for chunk_start in range(0, len(invoice_nos), 900):
        chunk = invoice_nos[chunk_start:chunk_start + 900]
        existing |= set(db.scalars(select(Sale.invoice_no).where(Sale.invoice_no.in_(chunk))).all())

    for bill in bills.values():
        if bill["invoice_no"] in existing:
            if opts["skip_duplicates"]:
                result["skipped_duplicates"] += 1
                _warn(result, bill["row"], f"invoice {bill['invoice_no']} is already in ERIS - skipped")
            else:
                _err(result, bill["row"], f"invoice {bill['invoice_no']} already exists")
            continue
        try:
            with db.begin_nested():
                sale = create_sale(db, SaleInput(
                    outlet_id=bill["outlet"].id, lines=bill["lines"], sold_at=bill["when"],
                    payment_method=bill["payment"], channel=bill["channel"], customer_phone=bill["phone"],
                    customer_name=bill["name"], invoice_no=bill["invoice_no"]), user, source="import",
                    update_stock=opts["update_stock"], commit=False)
                sale.import_id = opts["import_id"]
            result["created"] += 1
            if len(result["preview"]) < 10:
                result["preview"].append({"invoice_no": sale.invoice_no, "outlet": bill["outlet"].name,
                                          "date": sale.sold_at.isoformat(sep=" "), "items": len(bill["lines"]),
                                          "total": sale.total, "payment_method": sale.payment_method})
        except HTTPException as exc:
            _err(result, bill["row"], str(exc.detail))
    result["bills"] = len(bills)


# ------------------------------------------------------------------------------------------ master data
def _import_products(db: Session, rows: list[dict], user: User, result: dict, _opts: dict) -> None:
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


def _import_customers(db: Session, rows: list[dict], user: User, result: dict, _opts: dict) -> None:
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


def _import_suppliers(db: Session, rows: list[dict], user: User, result: dict, _opts: dict) -> None:
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


def _import_inventory(db: Session, rows: list[dict], user: User, result: dict, _opts: dict) -> None:
    lk = _Lookup(db)
    seen = set()
    for i, row in enumerate(rows, start=2):
        try:
            outlet = lk.outlet(row)
            if user.role != "admin" and outlet.id not in user.outlet_ids:
                raise ValueError("you can only update stock for your own outlets")
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
