"""Deterministic synthetic data generator for the ERIS demo company (generator v3).

One organization, five outlets by default (up to seven), ~61 products in 9 categories and two years of
bill-level history. Demand is simulated basket by basket from a documented structural model:

    bills/day  = base x outlet size x weekday x growth trend x season x festival x rain footfall x
                 new-outlet ramp-up x noise x (injected anomaly)
    basket mix = popularity x seasonality x temperature / rain response x promotion uplift x price elasticity
                 + companion items (bread -> butter, chips -> cola, ...)
    stockouts  = random outages per outlet & product; a buyer switches to a substitute (60%) or the sale is lost

Everything is driven by one random seed (default 42), so the same seed and end date reproduce the same
dataset. Ground truth is stored next to the data: promotions, price history, daily weather, stockout events
and labelled anomalies, plus a DatasetInfo provenance row that every synthetic bill references.
See docs/DATASET.md for the full data dictionary.
"""
from __future__ import annotations

import math
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np
from sqlalchemy import delete, insert, text
from sqlalchemy.orm import Session

from app import clock
from app.models import (
    MAX_OUTLETS,
    AnomalyLabel,
    AuditLog,
    Category,
    ChatMessage,
    Customer,
    DatasetInfo,
    ForecastResult,
    ForecastRun,
    ImportJob,
    InventoryItem,
    Invoice,
    Organization,
    Outlet,
    PriceHistory,
    Product,
    Promotion,
    PurchaseOrder,
    PurchaseOrderItem,
    Sale,
    SaleItem,
    StockMovement,
    StockoutEvent,
    Supplier,
    User,
    WeatherDaily,
    user_outlets,
)
from app.security import hash_password
from app.seed import catalog
from app.services.gst import demo_gstin
from app.services.holidays import event_window

GENERATOR_VERSION = "3.0.0"
DEMO_PASSWORDS = {"admin": "Admin@123", "manager": "Manager@123", "staff": "Staff@123", "viewer": "Viewer@123"}

WEEKDAY_FACTOR = np.array([0.88, 0.86, 0.90, 0.95, 1.06, 1.24, 1.16])  # Mon..Sun
HOUR_WEIGHTS_WEEKDAY = np.array([3, 5, 6, 7, 8, 7, 5, 4, 5, 7, 9, 10, 8, 4], dtype=float)  # 08:00..21:00
HOUR_WEIGHTS_WEEKEND = np.array([2, 4, 6, 8, 9, 8, 7, 6, 7, 8, 9, 9, 7, 4], dtype=float)
FUTURE_DAYS = 90  # weather climatology and planned promotions are generated this far ahead (known future inputs)
PROMO_ELASTICITY = 2.0  # demand multiplier = (1 - discount) ^ -elasticity
PRICE_ELASTICITY = 1.0


def _bump(doy: int, center: int, width: float) -> float:
    d = abs(doy - center)
    d = min(d, 365 - d)
    return math.exp(-0.5 * (d / width) ** 2)


def _profile_factor(profile: str, d: date, weekend: bool, event: tuple[str, int] | None,
                    temp: float, rain: float) -> float:
    doy = d.timetuple().tm_yday
    f = 1.0
    if profile == "summer":
        # hot days sell more cold drinks, curd and ice cream; plus a little school-vacation bump
        f = min(1.7, max(0.55, 1 + 0.045 * (temp - 30))) * (1 + 0.12 * _bump(doy, 140, 25))
    elif profile == "winter":
        f = 1 + 0.4 * _bump(doy, 1, 40) - 0.2 * _bump(doy, 135, 35)
    elif profile == "monsoon":
        f = 1 + 0.018 * min(rain, 40) + 0.15 * _bump(doy, 210, 35)
    elif profile == "mango":
        f = 0.02 + 1.6 * _bump(doy, 135, 22)
    elif profile == "christmas":
        f = 0.15 + 7 * _bump(doy, 355, 9)
    elif profile == "weekend":
        f = 1.3 if weekend else 0.9
    elif profile == "staple":
        f = 1.3 if d.day <= 5 else 0.96  # salary-day stock-up
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


# ------------------------------------------------------------------------------------------ db helpers
def _bulk_insert(db: Session, model, rows: list[dict]) -> None:
    """Fast bulk load: COPY on PostgreSQL, chunked executemany elsewhere."""
    if not rows:
        return
    table = model if isinstance(model, str) else model.__tablename__
    if db.get_bind().dialect.name == "postgresql":
        import csv
        import io

        cols = list(rows[0].keys())
        buf = io.StringIO()
        w = csv.writer(buf)
        for r in rows:
            w.writerow(["\\N" if r[c] is None else r[c] for c in cols])
        buf.seek(0)
        cur = db.connection().connection.cursor()
        cur.copy_expert(f"COPY {table} ({', '.join(cols)}) FROM STDIN WITH (FORMAT csv, NULL '\\N')", buf)
        return
    target = model if not isinstance(model, str) else user_outlets
    for i in range(0, len(rows), 20000):
        db.execute(insert(target), rows[i:i + 20000])


SEQUENCE_TABLES = ("customers", "sales", "sale_items", "purchase_orders", "purchase_order_items", "inventory",
                   "stock_movements", "products", "outlets", "suppliers", "categories", "users", "organization",
                   "promotions", "price_history", "weather_daily", "stockout_events", "anomaly_labels",
                   "dataset_info")


def _sync_sequences(db: Session) -> None:
    """Rows were bulk-inserted with explicit ids; move PostgreSQL id sequences past them."""
    if db.get_bind().dialect.name != "postgresql":
        return
    for table in SEQUENCE_TABLES:
        db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"))
    db.commit()


def reset_all(db: Session) -> None:
    for model in (ChatMessage, AuditLog, Invoice, ForecastResult, ForecastRun, StockMovement, PurchaseOrderItem,
                  PurchaseOrder, SaleItem, Sale, ImportJob, DatasetInfo, InventoryItem, StockoutEvent, AnomalyLabel,
                  Promotion, PriceHistory, WeatherDaily, Customer):
        db.execute(delete(model))
    db.execute(delete(user_outlets))
    for model in (User, Product, Category, Supplier, Outlet, Organization):
        db.execute(delete(model))
    db.commit()


# ------------------------------------------------------------------------------------------ weather
def simulate_weather(rng: np.random.Generator, cities: list[str], start: date, days: int) -> dict:
    """Daily max temperature & rainfall per city from monthly climate normals + persistent noise.

    Returns {city: (temp[days + FUTURE_DAYS], rain[...])}; the future part is climatology (expected values),
    which is what a forecaster could know in advance.
    """
    total = days + FUTURE_DAYS
    out = {}
    for city in cities:
        temps_m, prob_m, amount_m = catalog.CLIMATE[city]
        temp, rain = np.zeros(total), np.zeros(total)
        noise, wet = 0.0, False
        for i in range(total):
            d = start + timedelta(days=i)
            m = d.month - 1
            # smooth monthly normals by blending with the neighbouring month
            frac = (d.day - 15) / 30
            nxt = (m + (1 if frac >= 0 else -1)) % 12
            clim = temps_m[m] * (1 - abs(frac)) + temps_m[nxt] * abs(frac)
            p_rain = prob_m[m] * (1.35 if wet else 0.85)
            if i < days:
                noise = 0.7 * noise + rng.normal(0, 1.1)
                wet = rng.random() < min(p_rain, 0.97)
                amount = rng.gamma(0.8, amount_m[m] / 0.8) if wet else 0.0
                temp[i] = clim + noise - (2.0 if amount > 20 else 0.0)
                rain[i] = round(amount, 1)
            else:
                temp[i] = clim
                rain[i] = round(prob_m[m] * amount_m[m], 1)
        out[city] = (np.round(temp, 1), rain)
    return out


# ------------------------------------------------------------------------------------------ main
def generate_demo_data(db: Session, days: int = 730, seed: int = 42, end_date: date | None = None,
                       n_outlets: int = 5, log=print) -> dict:
    """Wipe the database and generate the demo organization. Returns row counts."""
    t0 = time.time()
    n_outlets = max(1, min(MAX_OUTLETS, n_outlets))
    rng = np.random.default_rng(seed)
    end_date = end_date or (clock.today() - timedelta(days=1))
    start_date = end_date - timedelta(days=days - 1)
    reset_all(db)

    dataset = DatasetInfo(data_source="synthetic", generator_version=GENERATOR_VERSION, random_seed=seed,
                          generated_at=clock.now(), period_start=start_date, period_end=end_date,
                          parameters={"days": days, "outlets": n_outlets, "future_days": FUTURE_DAYS,
                                      "promo_elasticity": PROMO_ELASTICITY, "price_elasticity": PRICE_ELASTICITY})
    db.add(dataset)
    org = Organization(**catalog.ORGANIZATION, low_stock_cover_days=7,
                       tax_id=demo_gstin(catalog.ORGANIZATION["state_code"], seed), tax_id_is_demo=True)
    db.add(org)
    db.flush()

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
                    cost_price=float(cost), selling_price=float(price), tax_rate=float(tax), reorder_level=10,
                    hsn_code=catalog.HSN.get(sku))
        db.add(p)
        products.append(p)

    outlets: list[Outlet] = []
    outlet_meta = []
    for idx, (code, name, city, state, state_code, address, manager, size, growth, opened_days_ago) in enumerate(
            catalog.OUTLETS[:n_outlets]):
        opened = end_date - timedelta(days=opened_days_ago) if opened_days_ago else date(2019 + idx % 4, 6, 1)
        o = Outlet(organization_id=org.id, code=code, name=name, city=city, state=state, state_code=state_code,
                   address=address, manager_name=manager, phone=f"+91 9{rng.integers(100000000, 999999999)}",
                   opened_on=opened)
        db.add(o)
        outlets.append(o)
        outlet_meta.append({"code": code, "city": city, "size": size, "growth": growth, "opened": opened})
    db.flush()

    db.add(User(email="admin@eris.demo", full_name="Aditi Rao (Owner)", role="admin",
                password_hash=hash_password(DEMO_PASSWORDS["admin"])))
    manager_pw = hash_password(DEMO_PASSWORDS["manager"])
    by_manager: dict[str, list[Outlet]] = defaultdict(list)
    for o in outlets:
        by_manager[o.manager_name].append(o)
    # Arjun Rao is the Bengaluru area manager: he also runs the newer Whitefield outlet (multi-outlet access).
    if "Arjun Rao" in by_manager and "Vikram Nair" in by_manager:
        by_manager["Arjun Rao"] += by_manager["Vikram Nair"]
    for manager, mine in by_manager.items():
        first = manager.split()[0].lower()
        db.add(User(email=f"{first}.{mine[0].code.split('-')[1].lower()}@eris.demo", full_name=manager,
                    role="manager", outlets=mine, password_hash=manager_pw))
    db.add(User(email="staff.andheri@eris.demo", full_name="Ravi Kumar", role="staff", outlets=[outlets[0]],
                password_hash=hash_password(DEMO_PASSWORDS["staff"])))
    db.add(User(email="analyst@eris.demo", full_name="Meera Iyer (Analyst)", role="viewer", outlets=list(outlets),
                password_hash=hash_password(DEMO_PASSWORDS["viewer"])))
    db.commit()
    log(f"  master data ready ({time.time() - t0:.1f}s)")

    n_products = len(products)
    base_w = np.array([row[7] for row in catalog.PRODUCTS])
    profiles = [row[8] for row in catalog.PRODUCTS]
    cat_of = np.array([products[i].category_id for i in range(n_products)])
    final_price = np.array([p.selling_price for p in products])
    final_cost = np.array([p.cost_price for p in products])
    taxes = np.array([p.tax_rate for p in products])
    bulk_units = np.array([p.unit in ("kg", "pack", "loaf", "dozen") for p in products])
    product_ids = [p.id for p in products]
    sku_index = {p.sku: i for i, p in enumerate(products)}
    companions: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for a, b, prob in catalog.COMPANIONS:
        companions[sku_index[a]].append((sku_index[b], prob))
    horizon = days + FUTURE_DAYS

    # --- weather ---------------------------------------------------------------------------------
    cities = sorted({m["city"] for m in outlet_meta})
    weather = simulate_weather(rng, cities, start_date, days)
    weather_rows = [{"city": c, "day": start_date + timedelta(days=i), "temp_max_c": float(weather[c][0][i]),
                     "rain_mm": float(weather[c][1][i]), "is_forecast": i >= days}
                    for c in cities for i in range(horizon)]

    # --- price changes (step increases, recorded as price history) --------------------------------
    price_mult = np.ones((n_products, horizon))
    price_rows = []
    for p_idx in range(n_products):
        changes = sorted(int(x) for x in rng.integers(60, days - 20, 1 + int(rng.random() < 0.6)))
        incs = rng.uniform(0.04, 0.09, len(changes))
        cum = float(np.prod(1 + incs))
        base = 1 / cum  # the latest price equals today's catalogue price
        level = base
        price_mult[p_idx, :] = base
        price_rows.append({"product_id": product_ids[p_idx], "effective_from": start_date,
                           "selling_price": float(round(final_price[p_idx] * base)),
                           "cost_price": round(float(final_cost[p_idx] * base), 2)})
        for day_i, inc in zip(changes, incs, strict=True):
            level *= 1 + inc
            price_mult[p_idx, day_i:] = level
            price_rows.append({"product_id": product_ids[p_idx], "effective_from": start_date + timedelta(days=day_i),
                               "selling_price": float(round(final_price[p_idx] * level)),
                               "cost_price": round(float(final_cost[p_idx] * level), 2)})

    # --- promotions (history + 30 days of planned promotions) -----------------------------------
    promo_rows = []
    promo_disc = np.zeros((n_outlets, n_products, horizon))
    promo_ref = np.zeros((n_outlets, n_products, horizon), dtype=np.int32)
    cat_names = list(categories)
    day_i = int(rng.integers(5, 15))
    while day_i < days + 30:
        disc = float(rng.choice([10, 15, 20]))
        length = int(rng.integers(4, 10))
        scope_outlet = None if rng.random() < 0.7 else int(rng.integers(0, n_outlets))
        if rng.random() < 0.55:
            cat = cat_names[int(rng.integers(0, len(cat_names)))]
            target = [i for i in range(n_products) if cat_of[i] == categories[cat].id]
            name = f"{int(disc)}% off {cat}"
            fields = {"category_id": categories[cat].id, "product_id": None}
        else:
            p_idx = int(rng.choice(n_products, p=base_w / base_w.sum()))
            target = [p_idx]
            name = f"{int(disc)}% off {products[p_idx].name}"
            fields = {"category_id": None, "product_id": product_ids[p_idx]}
        pid = len(promo_rows) + 1
        s_d, e_d = start_date + timedelta(days=day_i), start_date + timedelta(days=day_i + length - 1)
        promo_rows.append({"id": pid, "name": name + ("" if scope_outlet is None else f" ({outlets[scope_outlet].name})"),
                           "outlet_id": outlets[scope_outlet].id if scope_outlet is not None else None,
                           "discount_pct": disc, "start_date": s_d, "end_date": e_d, **fields,
                           "created_at": datetime.combine(s_d - timedelta(days=7), datetime.min.time())})
        o_range = [scope_outlet] if scope_outlet is not None else range(n_outlets)
        for o_idx in o_range:
            for p_idx in target:
                promo_disc[o_idx, p_idx, day_i:day_i + length] = disc / 100
                promo_ref[o_idx, p_idx, day_i:day_i + length] = pid
        day_i += int(rng.integers(10, 19))

    # --- stockouts (with a substitute in the same category) --------------------------------------
    substitute = {}
    for i in range(n_products):
        same = [j for j in range(n_products) if j != i and cat_of[j] == cat_of[i]]
        substitute[i] = min(same, key=lambda j: abs(final_price[j] - final_price[i])) if same else None
    available = np.ones((n_outlets, n_products, days), dtype=bool)
    stockout_rows = []
    for o_idx in range(n_outlets):
        for _ in range(int(rng.poisson(days / 7 * 1.1))):
            p_idx = int(rng.choice(n_products, p=base_w / base_w.sum()))
            s_i = int(rng.integers(0, days - 1))
            length = 1 + int(rng.poisson(1.3))
            available[o_idx, p_idx, s_i:s_i + length] = False
            sub = substitute[p_idx]
            stockout_rows.append({"outlet_id": outlets[o_idx].id, "product_id": product_ids[p_idx],
                                  "start_date": start_date + timedelta(days=s_i),
                                  "end_date": start_date + timedelta(days=min(days - 1, s_i + length - 1)),
                                  "substitute_product_id": product_ids[sub] if sub is not None else None})

    # --- injected anomalies with ground-truth labels ----------------------------------------------
    anomalies: dict[tuple[int, int], tuple[str, float]] = {}
    candidates = [(o, d_i) for o in range(n_outlets) for d_i in range(60, days - 3)
                  if event_window(start_date + timedelta(days=d_i)) is None
                  and start_date + timedelta(days=d_i) >= outlet_meta[o]["opened"] + timedelta(days=120)]
    picks = rng.choice(len(candidates), min(26, len(candidates)), replace=False)
    kinds = ["pos_outage"] * 7 + ["bulk_order"] * 6 + ["entry_error"] * 5 + ["local_event"] * 5 + ["closure"] * 3
    for kind, pick in zip(kinds, picks, strict=False):
        o_idx, d_i = candidates[int(pick)]
        mult = {"pos_outage": rng.uniform(0.2, 0.45), "local_event": rng.uniform(1.6, 2.1),
                "closure": 0.0}.get(kind, 1.0)
        anomalies[(o_idx, d_i)] = (kind, float(mult))

    # --- customers -----------------------------------------------------------------------------
    n_customers = 2600
    sizes = np.array([m["size"] for m in outlet_meta])
    home = rng.choice(n_outlets, n_customers, p=sizes / sizes.sum())
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
            "city": outlet_meta[home[i]]["city"], "customer_type": "retail", "gstin": None,
            "state_code": catalog.OUTLETS[home[i]][4],
            "created_at": datetime.combine(start_date + timedelta(days=int(join_offset[i])), datetime.min.time()),
        })
    business_ids = []
    for j, bname in enumerate(catalog.BUSINESS_NAMES):
        cid = n_customers + j + 1
        o_idx = j % n_outlets
        state_code = catalog.OUTLETS[o_idx][4]
        customer_rows.append({
            "id": cid, "name": bname, "phone": f"8{rng.integers(100000000, 999999999)}",
            "email": f"accounts@{bname.lower().replace(' ', '').replace('&', '').replace('.', '')}.example",
            "city": outlet_meta[o_idx]["city"], "customer_type": "business",
            "gstin": demo_gstin(state_code, seed * 1000 + j), "state_code": state_code,
            "created_at": datetime.combine(start_date, datetime.min.time()),
        })
        business_ids.append((cid, o_idx))
    db.execute(insert(Customer), customer_rows)
    db.commit()
    by_outlet_customers = [np.where(home == k)[0] for k in range(n_outlets)]
    business_by_outlet = defaultdict(list)
    for cid, o_idx in business_ids:
        business_by_outlet[o_idx].append(cid)

    # --- sales simulation ----------------------------------------------------------------------
    units_sold = np.zeros((n_outlets, n_products, days))
    day_revenue = np.zeros((n_outlets, days))
    sale_rows, item_rows = [], []
    sale_id = item_id = 0
    lost_lines = substituted_lines = 0

    for d_i in range(days):
        d = start_date + timedelta(days=d_i)
        wd = d.weekday()
        weekend = wd >= 5
        event = event_window(d)
        years_from_start = d_i / 365.0
        doy = d.timetuple().tm_yday
        season = 1 + 0.06 * _bump(doy, 130, 40) + 0.12 * _bump(doy, 300, 25)
        hour_w = HOUR_WEIGHTS_WEEKEND if weekend else HOUR_WEIGHTS_WEEKDAY
        hour_p = hour_w / hour_w.sum()
        cust_active = (join_offset <= d_i) & (churn_offset > d_i)
        price_today = np.round(final_price * price_mult[:, d_i])
        cost_today = final_cost * price_mult[:, d_i]
        elasticity = price_mult[:, d_i] ** -PRICE_ELASTICITY

        for o_idx, meta in enumerate(outlet_meta):
            if d < meta["opened"]:
                continue
            anomaly = anomalies.get((o_idx, d_i))
            if anomaly and anomaly[0] == "closure":
                continue
            temp = float(weather[meta["city"]][0][d_i])
            rain = float(weather[meta["city"]][1][d_i])
            mix = base_w * np.array([_profile_factor(pr, d, weekend, event, temp, rain) for pr in profiles])
            disc_today = promo_disc[o_idx, :, d_i]
            mix = mix * (1 - disc_today) ** -PROMO_ELASTICITY * elasticity
            mix = mix / mix.sum()
            age = (d - meta["opened"]).days
            ramp = 0.35 + 0.65 * (1 - math.exp(-age / 50)) if age < 400 else 1.0
            rain_footfall = 1 - 0.005 * min(rain, 60)
            trend = math.exp(meta["growth"] * years_from_start)
            lam = (58 * meta["size"] * WEEKDAY_FACTOR[wd] * trend * season * _footfall_event_factor(event)
                   * rain_footfall * ramp * rng.lognormal(0, 0.07))
            if anomaly and anomaly[0] in ("pos_outage", "local_event"):
                lam *= anomaly[1]
            n_baskets = int(rng.poisson(lam))
            if n_baskets == 0:
                continue

            delivery = rng.random(n_baskets) < (0.12 + 0.004 * min(rain, 50))
            is_business = (rng.random(n_baskets) < 0.02) & bool(business_by_outlet[o_idx])
            k = 1 + rng.poisson(np.where(delivery, 3.4, 2.1))
            k = np.where(is_business, 6 + rng.poisson(4, n_baskets), k)
            if event:
                k = k + rng.poisson(0.8, n_baskets)
            picks_all = rng.choice(n_products, int(k.sum()), p=mix)
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
            upi_share = 0.42 + 0.12 * years_from_start
            avail = available[o_idx, :, d_i]

            extra_bills = []
            if anomaly and anomaly[0] == "bulk_order" and business_by_outlet[o_idx]:
                extra_bills.append("bulk")
            if anomaly and anomaly[0] == "entry_error":
                extra_bills.append("error")

            offsets = np.concatenate([[0], np.cumsum(k)])
            seq = 0
            bills = [("normal", b) for b in order] + [(x, None) for x in extra_bills]
            for kind, b in bills:
                if kind == "normal":
                    lines = list(picks_all[offsets[b]:offsets[b + 1]])
                    for anchor_idx in list(lines):
                        for comp, prob in companions.get(anchor_idx, ()):
                            if comp not in lines and rng.random() < prob:
                                lines.append(comp)
                    kept = []
                    for p_idx in lines:
                        if avail[p_idx]:
                            kept.append(p_idx)
                        elif substitute[p_idx] is not None and avail[substitute[p_idx]] and rng.random() < 0.6:
                            kept.append(substitute[p_idx])
                            substituted_lines += 1
                        else:
                            lost_lines += 1
                    if not kept:
                        continue
                    prods, counts = np.unique(kept, return_counts=True)
                    qtys = counts.astype(float)
                    business = bool(is_business[b])
                    hh, mm, ss = int(hours[b]), int(minutes[b]), int(seconds[b])
                elif kind == "bulk":  # a caterer's one-off party order (ground-truth anomaly)
                    prods = rng.choice(n_products, 14, replace=False, p=base_w / base_w.sum())
                    qtys = rng.integers(15, 45, len(prods)).astype(float)
                    business, hh, mm, ss = True, 11, 5, 0
                else:  # entry error: an extra "00" typed into a quantity (ground-truth anomaly)
                    p_idx = int(rng.choice(np.where(final_price > 150)[0]))
                    prods, qtys = np.array([p_idx]), np.array([float(rng.choice([300, 500]))])
                    business, hh, mm, ss = False, 16, 40, 0
                seq += 1
                sale_id += 1
                customer_id = None
                if business:
                    customer_id = int(rng.choice(business_by_outlet[o_idx])) if business_by_outlet[o_idx] else None
                elif kind == "normal" and len(pool) and cust_r[b] < (0.45 if delivery[b] else 0.36):
                    customer_id = int(pool[rng.choice(len(pool), p=pool_p)]) + 1
                if kind != "normal":
                    payment, channel, disc_rate = "credit" if business else "cash", "in_store", 0.0
                else:
                    if business:
                        payment = "credit" if pay_r[b] < 0.6 else "upi"
                    elif delivery[b]:
                        payment = "upi" if pay_r[b] < 0.72 else ("card" if pay_r[b] < 0.95 else "cash")
                    else:
                        payment = "upi" if pay_r[b] < upi_share else ("card" if pay_r[b] < upi_share + 0.24 else "cash")
                    channel = "delivery" if delivery[b] else "in_store"
                    disc_rate = 0.1 if disc_r[b] < 0.02 else (0.05 if disc_r[b] < 0.06 else 0.0)

                subtotal = discount = tax_total = total = qty_total = 0.0
                for p_idx, qty in zip(prods, qtys, strict=True):
                    qty = float(qty)
                    if kind == "normal":
                        if business:
                            qty += float(rng.integers(1, 6))
                        elif bulk_units[p_idx] and rng.random() < 0.18:
                            qty += 1
                    list_price = float(price_today[p_idx])
                    promo = float(disc_today[p_idx])
                    price = float(round(list_price * (1 - promo))) if promo else list_price
                    gross = qty * price
                    line_disc = round(gross * disc_rate, 2)
                    line_total = round(gross - line_disc, 2)
                    tax = round(line_total * taxes[p_idx] / (100 + taxes[p_idx]), 2)
                    item_id += 1
                    item_rows.append({
                        "id": item_id, "sale_id": sale_id, "product_id": product_ids[p_idx],
                        "outlet_id": outlets[o_idx].id, "sale_date": d, "quantity": qty, "unit_price": price,
                        "list_price": list_price if promo else None,
                        "promotion_id": int(promo_ref[o_idx, p_idx, d_i]) if promo else None,
                        "discount": line_disc, "line_total": line_total, "tax_amount": tax,
                        "cost_amount": round(qty * float(cost_today[p_idx]), 2),
                    })
                    units_sold[o_idx, p_idx, d_i] += qty
                    subtotal += gross
                    discount += line_disc
                    tax_total += tax
                    total += line_total
                    qty_total += qty
                day_revenue[o_idx, d_i] += total
                sold_at = datetime(d.year, d.month, d.day, hh, mm, ss)
                sale_rows.append({
                    "id": sale_id, "invoice_no": f"{meta['code'].replace('-', '')}-{d:%y%m%d}-{seq:04d}",
                    "outlet_id": outlets[o_idx].id, "customer_id": customer_id, "sold_at": sold_at, "sale_date": d,
                    "channel": channel, "payment_method": payment, "subtotal": round(subtotal, 2),
                    "discount": round(discount, 2), "tax_amount": round(tax_total, 2), "total": round(total, 2),
                    "items_count": qty_total, "status": "completed", "source": "synthetic", "dataset_id": dataset.id,
                    "created_at": sold_at,
                })
        if d_i and d_i % 180 == 0:
            log(f"  simulated {d_i}/{days} days ({time.time() - t0:.1f}s)")

    log(f"  simulated {len(sale_rows):,} bills / {len(item_rows):,} lines ({time.time() - t0:.1f}s)")
    db.execute(insert(WeatherDaily), weather_rows)
    db.execute(insert(PriceHistory), price_rows)
    db.execute(insert(Promotion), promo_rows)
    if stockout_rows:
        db.execute(insert(StockoutEvent), stockout_rows)
    _bulk_insert(db, Sale, sale_rows)
    _bulk_insert(db, SaleItem, item_rows)
    db.commit()
    log(f"  sales written ({time.time() - t0:.1f}s)")

    # --- anomaly labels (magnitude measured against the same weekday's median at that outlet) ------
    label_rows = []
    descriptions = {
        "pos_outage": "Billing system outage - most of the day's sales were not recorded",
        "bulk_order": "One-off bulk order from a catering customer",
        "entry_error": "Data-entry error: an extra '00' typed into a quantity",
        "local_event": "Local event nearby drove unusual footfall",
        "closure": "Outlet closed for the day (maintenance)",
    }
    for (o_idx, d_i), (kind, _mult) in sorted(anomalies.items(), key=lambda kv: kv[0][1]):
        same_wd = [day_revenue[o_idx, j] for j in range(max(0, d_i - 56), min(days, d_i + 57), 7)
                   if j != d_i and (o_idx, j) not in anomalies]
        typical = float(np.median(same_wd)) if same_wd else 0.0
        magnitude = round(day_revenue[o_idx, d_i] / typical, 2) if typical else 0.0
        label_rows.append({"day": start_date + timedelta(days=d_i), "outlet_id": outlets[o_idx].id, "kind": kind,
                           "direction": "down" if kind in ("pos_outage", "closure") else "up",
                           "description": descriptions[kind], "magnitude": magnitude})
    db.execute(insert(AnomalyLabel), label_rows)

    # --- inventory -------------------------------------------------------------------------------
    recent = units_sold[:, :, -28:].mean(axis=2)
    lead = {s.id: s.lead_time_days for s in suppliers}
    admin_id = db.query(User.id).filter(User.role == "admin").scalar()
    inv_rows, mov_rows = [], []
    stamp = datetime.combine(end_date, datetime.min.time()) + timedelta(hours=22)
    for o_idx, o in enumerate(outlets):
        for p_idx, p in enumerate(products):
            avg = recent[o_idx, p_idx]
            reorder = math.ceil(avg * (lead[p.supplier_id] + 2)) if avg >= 0.15 else 0
            qty = float(math.ceil(avg * rng.uniform(4, 16))) if avg > 0 else 0.0
            r = rng.random()
            if reorder and r < 0.10:
                qty = float(rng.integers(0, max(1, int(reorder * 0.8)) + 1))
            if reorder and (r < 0.02 or not available[o_idx, p_idx, -1]):
                qty = 0.0  # still in an active stockout
            inv_rows.append({"outlet_id": o.id, "product_id": p.id, "quantity": qty, "reorder_level": float(reorder),
                             "updated_at": stamp})
            mov_rows.append({"outlet_id": o.id, "product_id": p.id, "change": qty, "balance_after": qty,
                             "reason": "adjustment", "reference": "OPENING", "note": "Opening stock (synthetic data)",
                             "user_id": admin_id, "created_at": stamp})
    db.execute(insert(InventoryItem), inv_rows)
    db.execute(insert(StockMovement), mov_rows)
    for p_idx, p in enumerate(products):
        p.reorder_level = float(max(2, math.ceil(recent[:, p_idx].mean() * 4)))
    db.commit()

    # --- purchase orders (last ~16 weeks, weekly per outlet & supplier) --------------------------
    po_rows, po_item_rows = [], []
    po_item_id = 0
    supplier_products = defaultdict(list)
    for p_idx, p in enumerate(products):
        supplier_products[p.supplier_id].append(p_idx)
    for week in range(16, -1, -1):
        for o_idx, o in enumerate(outlets):
            for s in suppliers:
                order_date = end_date - timedelta(days=week * 7 + int(rng.integers(0, 3)))
                if order_date < outlet_meta[o_idx]["opened"] or (order_date - start_date).days < 14:
                    continue
                o_i = (order_date - start_date).days
                weekly = units_sold[o_idx, :, max(0, o_i - 14):o_i].mean(axis=1) * 7
                lines = [(p_idx, math.ceil(weekly[p_idx] * 1.1)) for p_idx in supplier_products[s.id] if weekly[p_idx] >= 1]
                if not lines:
                    continue
                po_id = len(po_rows) + 1
                expected = order_date + timedelta(days=s.lead_time_days)
                if expected <= end_date:
                    status, received = ("cancelled", None) if rng.random() < 0.02 else ("received", expected)
                    if status == "received" and rng.random() < 0.12:
                        received = expected + timedelta(days=int(rng.integers(1, 4)))  # late deliveries
                else:
                    status, received = "ordered", None
                total = 0.0
                for p_idx, q in lines:
                    po_item_id += 1
                    unit_cost = round(float(final_cost[p_idx] * price_mult[p_idx, o_i]), 2)
                    total += q * unit_cost
                    po_item_rows.append({"id": po_item_id, "order_id": po_id, "product_id": products[p_idx].id,
                                         "quantity": float(q), "unit_cost": unit_cost,
                                         "received_quantity": float(q) if status == "received" else 0.0})
                po_rows.append({
                    "id": po_id, "po_number": f"PO-{order_date:%y%m}-{po_id:05d}", "supplier_id": s.id,
                    "outlet_id": o.id, "status": status, "order_date": order_date, "expected_date": expected,
                    "received_date": received, "total_cost": round(total, 2), "created_by": admin_id,
                    "created_at": datetime.combine(order_date, datetime.min.time()) + timedelta(hours=9),
                })
    db.execute(insert(PurchaseOrder), po_rows)
    db.execute(insert(PurchaseOrderItem), po_item_rows)

    counts = {
        "outlets": len(outlets), "products": n_products, "suppliers": len(suppliers), "customers": len(customer_rows),
        "sales": len(sale_rows), "sale_items": len(item_rows), "purchase_orders": len(po_rows),
        "promotions": len(promo_rows), "price_changes": len(price_rows) - n_products,
        "stockout_events": len(stockout_rows), "lost_lines_due_to_stockout": lost_lines,
        "substituted_lines": substituted_lines, "anomaly_labels": len(label_rows), "weather_days": len(weather_rows),
    }
    dataset.row_counts = counts
    db.commit()
    _sync_sequences(db)
    counts.update(start_date=start_date.isoformat(), end_date=end_date.isoformat(), seconds=round(time.time() - t0, 1))
    log(f"  done: {counts}")
    return counts
