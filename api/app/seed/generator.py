"""Synthetic but realistic demo data for one F&B retail organization with six outlets.

Demand is simulated basket by basket from a structural model:

    baskets/day = base x outlet size x weekday x trend x seasonality x festivals x weather x ramp-up x noise
    basket mix  = product popularity x product-specific seasonality (summer, winter, monsoon, festive, ...)

so the data contains the patterns a retailer would actually see (weekend peaks, summer beverages,
Diwali sweets, monsoon dips, a growing new outlet, a slowly declining outlet, loyal and churned customers),
which makes forecasting and analytics results meaningful.
"""
from __future__ import annotations

import math
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from app.models import (
    Category,
    ChatMessage,
    Customer,
    InventoryItem,
    Organization,
    Outlet,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Sale,
    SaleItem,
    StockMovement,
    Supplier,
    User,
)
from app.security import hash_password
from app.seed import catalog
from app.services.holidays import event_window

DEMO_PASSWORDS = {"admin": "Admin@123", "manager": "Manager@123", "staff": "Staff@123"}

WEEKDAY_FACTOR = np.array([0.88, 0.86, 0.90, 0.95, 1.06, 1.24, 1.16])  # Mon..Sun
HOUR_WEIGHTS_WEEKDAY = np.array([3, 5, 6, 7, 8, 7, 5, 4, 5, 7, 9, 10, 8, 4], dtype=float)  # 08:00..21:00
HOUR_WEIGHTS_WEEKEND = np.array([2, 4, 6, 8, 9, 8, 7, 6, 7, 8, 9, 9, 7, 4], dtype=float)
# Long-run outlet growth per year (Ahmedabad is slowly losing ground to a new competitor).
OUTLET_GROWTH = {"MUM-AND": 0.12, "MUM-BAN": 0.09, "PUN-KOR": 0.16, "BLR-IND": 0.14, "AMD-SGH": -0.07, "BLR-WHF": 0.10}


def _bump(doy: int, center: int, width: float) -> float:
    d = abs(doy - center)
    d = min(d, 365 - d)
    return math.exp(-0.5 * (d / width) ** 2)


def _profile_factor(profile: str, d: date, weekend: bool, event: tuple[str, int] | None) -> float:
    doy = d.timetuple().tm_yday
    f = 1.0
    if profile == "summer":
        f = 1 + 0.6 * _bump(doy, 130, 35) - 0.2 * _bump(doy, 5, 30)
    elif profile == "winter":
        f = 1 + 0.4 * _bump(doy, 1, 40) - 0.2 * _bump(doy, 135, 35)
    elif profile == "monsoon":
        f = 1 + 0.5 * _bump(doy, 210, 35)
    elif profile == "mango":
        f = 0.02 + 1.6 * _bump(doy, 135, 22)
    elif profile == "christmas":
        f = 0.15 + 7 * _bump(doy, 355, 9)
    elif profile == "weekend":
        f = 1.3 if weekend else 0.9
    elif profile == "staple":
        f = 1.3 if d.day <= 5 else 0.96
    elif profile == "party":
        f = 1.15 if weekend else 0.95
    if event:
        name, delta = event
        if profile == "diwali":
            f = 0.12 * f
            if name == "Diwali":
                f *= 1 + 9 * max(0.0, 1 - abs(delta) / 12)
            elif name in ("Raksha Bandhan", "Navratri", "Ganesh Chaturthi", "Holi"):
                f *= 4
        elif profile == "festive":
            f *= 1 + (1.3 * max(0.0, 1 - abs(delta) / 12) if name == "Diwali" else 0.5)
        elif profile == "party" and name in ("New Year", "Christmas", "Holi"):
            f *= 2.0
    elif profile == "diwali":
        f = 0.12
    return f


def _footfall_event_factor(event: tuple[str, int] | None) -> float:
    if not event:
        return 1.0
    name, delta = event
    if name == "Diwali":
        if delta == 0:
            return 0.75  # stores close early on Diwali day
        if delta < 0:
            return 0.7
        return 1 + 0.4 * max(0.0, 1 - delta / 12)
    if name == "Holi":
        return 0.6 if delta == 0 else 1.2
    return 1.15


def reset_all(db: Session) -> None:
    for model in (
        ChatMessage,
        StockMovement,
        PurchaseOrderItem,
        PurchaseOrder,
        SaleItem,
        Sale,
        InventoryItem,
        Customer,
        Product,
        Category,
        Supplier,
        User,
        Outlet,
        Organization,
    ):
        db.execute(delete(model))
    db.commit()


def create_organization(db: Session) -> Organization:
    org = Organization(**catalog.ORGANIZATION, low_stock_cover_days=7)
    db.add(org)
    db.flush()
    return org


def generate_demo_data(db: Session, days: int = 540, seed: int = 42, end_date: date | None = None, log=print) -> dict:
    """Wipe the database and generate the demo organization. Returns row counts."""
    t0 = time.time()
    rng = np.random.default_rng(seed)
    end_date = end_date or (date.today() - timedelta(days=1))
    start_date = end_date - timedelta(days=days - 1)

    reset_all(db)
    create_organization(db)

    # --- master data -------------------------------------------------------------------------
    suppliers = []
    for name, contact, phone, email, city, lead, terms in catalog.SUPPLIERS:
        s = Supplier(name=name, contact_person=contact, phone=phone, email=email, city=city,
                     lead_time_days=lead, payment_terms=terms)
        db.add(s)
        suppliers.append(s)

    categories: dict[str, Category] = {}
    for row in catalog.PRODUCTS:
        if row[2] not in categories:
            categories[row[2]] = Category(name=row[2])
            db.add(categories[row[2]])
    db.flush()

    products: list[Product] = []
    for sku, name, cat, unit, cost, price, tax, _w, _profile, sup in catalog.PRODUCTS:
        p = Product(sku=sku, name=name, category_id=categories[cat].id, supplier_id=suppliers[sup].id, unit=unit,
                    cost_price=float(cost), selling_price=float(price), tax_rate=float(tax), reorder_level=10)
        db.add(p)
        products.append(p)

    outlets: list[Outlet] = []
    outlet_meta = []
    for code, name, city, address, manager, size, monsoon, opened_days_ago in catalog.OUTLETS:
        opened = end_date - timedelta(days=opened_days_ago) if opened_days_ago else date(2019 + len(outlets) % 4, 6, 1)
        o = Outlet(code=code, name=name, city=city, address=address, manager_name=manager,
                   phone=f"+91 9{rng.integers(100000000, 999999999)}", opened_on=opened)
        db.add(o)
        outlets.append(o)
        outlet_meta.append({"code": code, "size": size, "monsoon": monsoon, "opened": opened})
    db.flush()

    db.add(User(email="admin@eris.demo", full_name="Aditi Rao (Owner)", role="admin",
                password_hash=hash_password(DEMO_PASSWORDS["admin"])))
    for o, (code, *_rest) in zip(outlets, catalog.OUTLETS, strict=False):
        first = (o.manager_name or "manager").split()[0].lower()
        db.add(User(email=f"{first}.{code.split('-')[1].lower()}@eris.demo", full_name=o.manager_name or o.name,
                    role="manager", outlet_id=o.id, password_hash=hash_password(DEMO_PASSWORDS["manager"])))
    db.add(User(email="staff.andheri@eris.demo", full_name="Ravi Kumar", role="staff", outlet_id=outlets[0].id,
                password_hash=hash_password(DEMO_PASSWORDS["staff"])))
    db.commit()
    log(f"  master data ready ({time.time() - t0:.1f}s)")

    # --- customers -----------------------------------------------------------------------------
    n_customers = 2600
    sizes = np.array([m["size"] for m in outlet_meta])
    home = rng.choice(len(outlets), n_customers, p=sizes / sizes.sum())
    loyalty = rng.lognormal(0, 1.0, n_customers)
    join_offset = (rng.beta(1.2, 2.2, n_customers) * days).astype(int)
    churned = rng.random(n_customers) < 0.22
    churn_offset = np.where(churned, join_offset + rng.integers(60, 300, n_customers), days + 10)
    used_phones: set[str] = set()
    customer_rows = []
    for i in range(n_customers):
        while True:
            phone = f"9{rng.integers(100000000, 999999999)}"
            if phone not in used_phones:
                used_phones.add(phone)
                break
        first, last = rng.choice(catalog.FIRST_NAMES), rng.choice(catalog.LAST_NAMES)
        customer_rows.append({
            "id": i + 1, "name": f"{first} {last}", "phone": phone,
            "email": f"{first.lower()}.{last.lower().replace(chr(39), '')}{i}@mail.example" if rng.random() < 0.6 else None,
            "city": catalog.OUTLETS[home[i]][2], "customer_type": "retail",
            "created_at": datetime.combine(start_date + timedelta(days=int(join_offset[i])), datetime.min.time()),
        })
    business_ids = []
    for j, bname in enumerate(catalog.BUSINESS_NAMES):
        cid = n_customers + j + 1
        o_idx = j % len(outlets)
        customer_rows.append({
            "id": cid, "name": bname, "phone": f"8{rng.integers(100000000, 999999999)}",
            "email": f"accounts@{bname.lower().replace(' ', '').replace('&', '').replace('.', '')}.example",
            "city": catalog.OUTLETS[o_idx][2], "customer_type": "business",
            "created_at": datetime.combine(start_date, datetime.min.time()),
        })
        business_ids.append((cid, o_idx))
    db.execute(insert(Customer), customer_rows)
    db.commit()
    by_outlet_customers = [np.where(home == k)[0] for k in range(len(outlets))]
    business_by_outlet = defaultdict(list)
    for cid, o_idx in business_ids:
        business_by_outlet[o_idx].append(cid)

    # --- sales simulation ----------------------------------------------------------------------
    n_products = len(products)
    base_w = np.array([row[7] for row in catalog.PRODUCTS])
    profiles = [row[8] for row in catalog.PRODUCTS]
    prices = np.array([p.selling_price for p in products])
    costs = np.array([p.cost_price for p in products])
    taxes = np.array([p.tax_rate for p in products])
    bulk_units = np.array([p.unit in ("kg", "pack", "loaf", "dozen") for p in products])
    product_ids = [p.id for p in products]
    sku_index = {p.sku: i for i, p in enumerate(products)}
    companions: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for a, b, prob in catalog.COMPANIONS:
        companions[sku_index[a]].append((sku_index[b], prob))
    units_sold = np.zeros((len(outlets), n_products, days))

    sale_rows, item_rows = [], []
    sale_id, item_id = 0, 0
    closure = {(1, end_date - timedelta(days=k)) for k in (228, 229, 230)}  # Bandra refurbishment

    for day_idx in range(days):
        d = start_date + timedelta(days=day_idx)
        wd = d.weekday()
        weekend = wd >= 5
        event = event_window(d)
        years_from_start = day_idx / 365.0
        years_to_end = (days - 1 - day_idx) / 365.0
        price_index = 1 - 0.055 * years_to_end  # ~5.5% yearly inflation
        doy = d.timetuple().tm_yday
        mix = base_w * np.array([_profile_factor(pr, d, weekend, event) for pr in profiles])
        mix = mix / mix.sum()
        season = 1 + 0.08 * _bump(doy, 130, 40) + 0.12 * _bump(doy, 300, 25)  # summer + festive season
        hour_w = HOUR_WEIGHTS_WEEKEND if weekend else HOUR_WEIGHTS_WEEKDAY
        hour_p = hour_w / hour_w.sum()
        cust_active = (join_offset <= day_idx) & (churn_offset > day_idx)

        for o_idx, meta in enumerate(outlet_meta):
            if d < meta["opened"] or (o_idx, d) in closure:
                continue
            age = (d - meta["opened"]).days
            ramp = 0.35 + 0.65 * (1 - math.exp(-age / 50)) if age < 400 else 1.0
            weather = 1 - 0.12 * _bump(doy, 200, 28) if meta["monsoon"] else 1.0
            trend = math.exp(OUTLET_GROWTH[meta["code"]] * years_from_start)
            lam = (58 * meta["size"] * WEEKDAY_FACTOR[wd] * trend * season * _footfall_event_factor(event)
                   * weather * ramp * rng.lognormal(0, 0.07))
            n_baskets = int(rng.poisson(lam))
            if n_baskets == 0:
                continue

            delivery = rng.random(n_baskets) < 0.12
            is_business = (rng.random(n_baskets) < 0.02) & bool(business_by_outlet[o_idx])
            k = 1 + rng.poisson(np.where(delivery, 3.4, 2.1))
            k = np.where(is_business, 6 + rng.poisson(4, n_baskets), k)
            if event:
                k = k + rng.poisson(0.8, n_baskets)
            picks = rng.choice(n_products, int(k.sum()), p=mix)
            hours = 8 + rng.choice(14, n_baskets, p=hour_p)
            minutes = rng.integers(0, 60, n_baskets)
            seconds = rng.integers(0, 60, n_baskets)
            order = np.lexsort((seconds, minutes, hours))
            pay_r = rng.random(n_baskets)
            disc_r = rng.random(n_baskets)
            cust_r = rng.random(n_baskets)
            pool = by_outlet_customers[o_idx]
            pool = pool[cust_active[pool]]
            pool_p = loyalty[pool] / loyalty[pool].sum() if len(pool) else None
            upi_share = 0.42 + 0.12 * years_from_start  # UPI adoption grows over time

            offsets = np.concatenate([[0], np.cumsum(k)])
            for seq, b in enumerate(order, start=1):
                lines = list(picks[offsets[b]:offsets[b + 1]])
                for anchor_idx in list(lines):
                    for comp, prob in companions.get(anchor_idx, ()):
                        if comp not in lines and rng.random() < prob:
                            lines.append(comp)
                prods, counts = np.unique(lines, return_counts=True)
                sale_id += 1
                customer_id = None
                if is_business[b]:
                    customer_id = int(rng.choice(business_by_outlet[o_idx]))
                elif len(pool) and cust_r[b] < (0.45 if delivery[b] else 0.36):
                    customer_id = int(pool[rng.choice(len(pool), p=pool_p)]) + 1
                if is_business[b]:
                    payment = "credit" if pay_r[b] < 0.6 else "upi"
                elif delivery[b]:
                    payment = "upi" if pay_r[b] < 0.72 else ("card" if pay_r[b] < 0.95 else "cash")
                else:
                    payment = "upi" if pay_r[b] < upi_share else ("card" if pay_r[b] < upi_share + 0.24 else "cash")
                disc_rate = 0.1 if disc_r[b] < 0.025 else (0.05 if disc_r[b] < 0.075 else 0.0)

                subtotal = discount = tax_total = total = qty_total = 0.0
                for p_idx, cnt in zip(prods, counts, strict=False):
                    qty = float(cnt)
                    if is_business[b]:
                        qty += float(rng.integers(1, 6))
                    elif bulk_units[p_idx] and rng.random() < 0.18:
                        qty += 1
                    price = round(prices[p_idx] * price_index)
                    gross = qty * price
                    line_disc = round(gross * disc_rate, 2)
                    line_total = round(gross - line_disc, 2)
                    tax = round(line_total * taxes[p_idx] / (100 + taxes[p_idx]), 2)
                    item_id += 1
                    item_rows.append({
                        "id": item_id, "sale_id": sale_id, "product_id": product_ids[p_idx],
                        "outlet_id": outlets[o_idx].id, "sale_date": d, "quantity": qty, "unit_price": float(price),
                        "discount": line_disc, "line_total": line_total, "tax_amount": tax,
                        "cost_amount": round(qty * costs[p_idx] * price_index, 2),
                    })
                    units_sold[o_idx, p_idx, day_idx] += qty
                    subtotal += gross
                    discount += line_disc
                    tax_total += tax
                    total += line_total
                    qty_total += qty
                sold_at = datetime(d.year, d.month, d.day, int(hours[b]), int(minutes[b]), int(seconds[b]))
                sale_rows.append({
                    "id": sale_id,
                    "invoice_no": f"{meta['code'].replace('-', '')}-{d:%y%m%d}-{seq:04d}",
                    "outlet_id": outlets[o_idx].id, "customer_id": customer_id, "sold_at": sold_at, "sale_date": d,
                    "channel": "delivery" if delivery[b] else "in_store", "payment_method": payment,
                    "subtotal": round(subtotal, 2), "discount": round(discount, 2), "tax_amount": round(tax_total, 2),
                    "total": round(total, 2), "items_count": qty_total, "status": "completed", "source": "demo",
                    "created_at": sold_at,
                })

    log(f"  simulated {len(sale_rows):,} sales / {len(item_rows):,} line items ({time.time() - t0:.1f}s)")
    chunk = 20000
    for i in range(0, len(sale_rows), chunk):
        db.execute(insert(Sale), sale_rows[i:i + chunk])
    for i in range(0, len(item_rows), chunk):
        db.execute(insert(SaleItem), item_rows[i:i + chunk])
    db.commit()
    log(f"  sales written ({time.time() - t0:.1f}s)")

    # --- inventory -------------------------------------------------------------------------------
    recent = units_sold[:, :, -28:].mean(axis=2)
    lead = {s.id: s.lead_time_days for s in suppliers}
    admin_id = db.query(User.id).filter(User.role == "admin").scalar()
    inv_rows, mov_rows = [], []
    now = datetime.combine(end_date, datetime.min.time()) + timedelta(hours=22)
    for o_idx, o in enumerate(outlets):
        for p_idx, p in enumerate(products):
            avg = recent[o_idx, p_idx]
            reorder = math.ceil(avg * (lead[p.supplier_id] + 2)) if avg >= 0.15 else 0
            qty = float(math.ceil(avg * rng.uniform(4, 16))) if avg > 0 else 0.0
            r = rng.random()
            if reorder and r < 0.12:
                qty = float(rng.integers(0, max(1, int(reorder * 0.8)) + 1))
            if reorder and r < 0.025:
                qty = 0.0
            inv_rows.append({"outlet_id": o.id, "product_id": p.id, "quantity": qty, "reorder_level": float(reorder),
                             "updated_at": now})
            mov_rows.append({"outlet_id": o.id, "product_id": p.id, "change": qty, "balance_after": qty,
                             "reason": "adjustment", "reference": "OPENING", "note": "Opening stock (demo data)",
                             "user_id": admin_id, "created_at": now})
    db.execute(insert(InventoryItem), inv_rows)
    db.execute(insert(StockMovement), mov_rows)
    for p_idx, p in enumerate(products):
        p.reorder_level = float(max(2, math.ceil(recent[:, p_idx].mean() * 4)))
    db.commit()

    # --- purchase orders (last ~16 weeks, weekly per outlet & supplier) --------------------------
    po_count = 0
    po_rows, po_item_rows = [], []
    po_item_id = 0
    supplier_products = defaultdict(list)
    for p_idx, p in enumerate(products):
        supplier_products[p.supplier_id].append(p_idx)
    for week in range(16, -1, -1):
        for o_idx, o in enumerate(outlets):
            for s in suppliers:
                order_date = end_date - timedelta(days=week * 7 + int(rng.integers(0, 3)))
                if order_date < outlet_meta[o_idx]["opened"]:
                    continue
                window = units_sold[o_idx, :, max(0, (order_date - start_date).days - 14):(order_date - start_date).days]
                weekly = window.mean(axis=1) * 7 if window.size else np.zeros(n_products)
                lines = [(p_idx, math.ceil(weekly[p_idx] * 1.1)) for p_idx in supplier_products[s.id] if weekly[p_idx] >= 1]
                if not lines:
                    continue
                po_count += 1
                expected = order_date + timedelta(days=s.lead_time_days)
                if expected <= end_date:
                    status, received = ("cancelled", None) if rng.random() < 0.02 else ("received", expected)
                else:
                    status, received = "ordered", None
                total = 0.0
                for p_idx, q in lines:
                    po_item_id += 1
                    unit_cost = round(costs[p_idx], 2)
                    total += q * unit_cost
                    po_item_rows.append({"id": po_item_id, "order_id": po_count, "product_id": products[p_idx].id,
                                         "quantity": float(q), "unit_cost": unit_cost})
                po_rows.append({
                    "id": po_count, "po_number": f"PO-{order_date:%y%m}-{po_count:05d}", "supplier_id": s.id,
                    "outlet_id": o.id, "status": status, "order_date": order_date, "expected_date": expected,
                    "received_date": received, "total_cost": round(total, 2), "created_by": admin_id,
                    "created_at": datetime.combine(order_date, datetime.min.time()) + timedelta(hours=9),
                })
    db.execute(insert(PurchaseOrder), po_rows)
    db.execute(insert(PurchaseOrderItem), po_item_rows)
    db.commit()

    counts = {
        "outlets": len(outlets), "products": len(products), "suppliers": len(suppliers),
        "customers": len(customer_rows), "sales": len(sale_rows), "sale_items": len(item_rows),
        "purchase_orders": len(po_rows), "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
        "seconds": round(time.time() - t0, 1),
    }
    log(f"  done: {counts}")
    return counts
