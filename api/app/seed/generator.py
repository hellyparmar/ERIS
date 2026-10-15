"""Deterministic synthetic data generator for the ERIS demo restaurant chain (generator v4).

One organization, five restaurants by default (up to seven), a 50-dish menu in 9 categories made from 38 stocked
ingredients, and two years of bill-level history. Demand is simulated bill by bill from a documented model:

    bills/day  = base x outlet size x weekday x growth trend x season x festival x rain x
                 new-outlet ramp-up x noise x (injected anomaly)
    each bill  = channel (dine-in / takeaway / delivery; rain pushes orders to delivery) and party size (covers);
                 the party orders by course - mains, breads or rice with curries, starters, soups, drinks,
                 desserts - with dishes chosen by popularity x season / weather x promotion x price x the
                 outlet's appetite for non-vegetarian food (lower in Navratri and Shravan)
    ingredients = dishes sold x recipe quantities; ingredient outages take dishes off the menu (86'd):
                 guests pick a similar dish (60%) or the order is lost

Everything is driven by one random seed (default 42), so the same seed and end date reproduce the same
dataset. Ground truth is stored next to the data: promotions, menu prices and ingredient costs over time, daily
weather, dish outages and labelled anomalies, plus a DatasetInfo provenance row that every synthetic bill
references. See docs/DATASET.md for the full data dictionary.
"""
from __future__ import annotations

import ctypes
import gc
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
    Recipe,
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

GENERATOR_VERSION = "4.0.0"  # 4.0: restaurant chain (menu, ingredients, recipes, covers, dine-in/takeaway/delivery)
DEMO_PASSWORDS = {"admin": "Admin@123", "manager": "Manager@123", "staff": "Staff@123", "viewer": "Viewer@123"}
# Sign-in shortcuts shown on the login page of the demo: (role label, email, password key, what they can see)
DEMO_LOGINS = [
    ("Owner / admin", "admin@eris.demo", "admin", "All restaurants, settings and users"),
    ("Restaurant manager", "priya.and@eris.demo", "manager", "Andheri West only"),
    ("Area manager", "arjun.ind@eris.demo", "manager", "Indiranagar + Whitefield"),
    ("Staff", "staff.andheri@eris.demo", "staff", "Billing & stock lookup"),
    ("Analyst (viewer)", "analyst@eris.demo", "viewer", "Read-only, all restaurants"),
]

WEEKDAY_FACTOR = np.array([0.80, 0.78, 0.84, 0.90, 1.10, 1.42, 1.34])  # Mon..Sun: restaurants fill up at weekends
OPEN_HOUR = 11  # kitchens take orders 11:00-23:59
# dine-in & takeaway: a lunch peak (12-15h) and a bigger dinner peak (19-22h); delivery runs later into the night
HOUR_WEIGHTS_DINE = np.array([2, 7, 10, 7, 3, 2, 2, 3, 6, 10, 11, 7, 2], dtype=float)
HOUR_WEIGHTS_DELIVERY = np.array([2, 5, 7, 6, 3, 3, 3, 4, 6, 9, 11, 10, 5], dtype=float)
MIN_DAYS = 90  # price changes, anomalies and churn are placed at least 60 days into the history
WRITE_BATCH_LINES = 50_000  # bill lines held in memory before they are written
FUTURE_DAYS = 90  # weather climatology and planned promotions are generated this far ahead (known future inputs)
PROMO_ELASTICITY = 2.0  # demand multiplier = (1 - discount) ^ -elasticity
PRICE_ELASTICITY = 1.0
BASE_BILLS = 42  # bills per day at an average-size restaurant on an average day
TAKEAWAY_SHARE = 0.12
MAX_OUTAGE_DISHES = 8  # an ingredient used by more dishes than this is a staple that is never allowed to run out
# share of bills that order each course, by channel: (dine-in, takeaway, delivery)
P_STARTER = {"dine_in": 0.62, "takeaway": 0.30, "delivery": 0.40}
P_DESSERT = {"dine_in": 0.30, "takeaway": 0.10, "delivery": 0.14}
P_DRINK = {"dine_in": 0.50, "takeaway": 0.15, "delivery": 0.18}  # per guest
P_SOUP = {"dine_in": 0.13, "takeaway": 0.05, "delivery": 0.07}
PROMO_NAMES = {
    "Cold Beverages": "Happy Hours", "Rice & Biryani": "Biryani Fest", "Starters": "Starters Combo",
    "Desserts": "Dessert Week", "Main Course": "Weekday Lunch Offer", "Indo-Chinese": "Wok Wednesdays",
    "Soups": "Soup Season", "Breads": "Tandoor Treat", "Hot Beverages": "Chai Time",
}


def _bump(doy: int, center: int, width: float) -> float:
    d = abs(doy - center)
    d = min(d, 365 - d)
    return math.exp(-0.5 * (d / width) ** 2)


def _profile_factor(profile: str, d: date, weekend: bool, event: tuple[str, int] | None,
                    temp: float, rain: float) -> float:
    """Demand multiplier for a dish with this profile on day d (1 = its usual level)."""
    doy = d.timetuple().tm_yday
    f = 1.0
    if profile == "summer":  # cold drinks, lassi, ice cream follow the temperature
        f = min(1.8, max(0.5, 1 + 0.05 * (temp - 30)))
    elif profile == "winter":  # soups, halwa, coffee
        f = 1 + 0.55 * _bump(doy, 5, 40) - 0.3 * _bump(doy, 140, 35)
    elif profile == "monsoon":  # pakoras, chai, manchurian on rainy days
        f = 1 + 0.025 * min(rain, 40) + 0.2 * _bump(doy, 205, 30)
    elif profile == "mango":
        f = 0.05 + 1.8 * _bump(doy, 130, 22)
    elif profile == "weekend":
        f = 1.25 if weekend else 0.88
    elif profile == "date":  # desserts for two around Valentine's Day and New Year's Eve
        f = 1 + 1.2 * _bump(doy, 45, 2) + 0.8 * _bump(doy, 365, 3)
    if event and profile == "festive":
        name, delta = event
        f *= 2.2 if name in ("Diwali", "Raksha Bandhan", "Eid") else 1.4
    return f


def _nonveg_factor(d: date, event: tuple[str, int] | None) -> float:
    """Many guests skip meat in Navratri, Shravan (late July - August) and around Ganesh Chaturthi."""
    doy = d.timetuple().tm_yday
    f = 1 - 0.22 * _bump(doy, 218, 14)  # Shravan
    if event:
        name, _ = event
        f *= {"Navratri": 0.55, "Ganesh Chaturthi": 0.75, "Eid": 1.45, "New Year": 1.15}.get(name, 1.0)
    return f


def _footfall_event_factor(event: tuple[str, int] | None) -> float:
    if not event:
        return 1.0
    name, delta = event
    if name == "Diwali":
        if delta == 0:
            return 0.5  # families eat at home on Diwali night
        if delta < 0:
            return 1.25  # get-togethers in the days after
        return 0.95
    if name == "Holi":
        return 0.55 if delta == 0 else 1.0
    if name == "New Year":
        return {0: 1.75, -1: 1.3}.get(delta, 1.2)  # New Year's Eve parties, then New Year's Day
    if name == "Christmas":
        return 1.3 if delta == 0 else 1.1
    if name == "Navratri":
        return 0.95
    if name in ("Eid", "Raksha Bandhan"):
        return 1.2
    if name == "Valentine's Day":
        return 1.35 if delta == 0 else 1.0
    return 1.05


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


SEQUENCE_TABLES = ("recipes", "customers", "sales", "sale_items", "purchase_orders", "purchase_order_items", "inventory",
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
                  Promotion, PriceHistory, WeatherDaily, Customer, Recipe):
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
def _group_order(picks: np.ndarray, keep: int) -> np.ndarray:
    """Fold a course's picks onto its first `keep` distinct dishes (the same count, fewer dishes in bulk)."""
    first = list(dict.fromkeys(picks.tolist()))[:keep]
    if len(first) <= 1:
        return np.full(len(picks), first[0]) if first else picks
    return np.array([x if x in first else first[k % len(first)] for k, x in enumerate(picks.tolist())], dtype=int)


def _split(values: np.ndarray, counts: np.ndarray) -> list[np.ndarray]:
    return np.split(values, np.cumsum(counts)[:-1]) if len(counts) else []


def generate_demo_data(db: Session, days: int = 730, seed: int = 42, end_date: date | None = None,
                       n_outlets: int = 5, log=print) -> dict:
    """Wipe the database and generate the demo restaurant chain. Returns row counts."""
    if days < MIN_DAYS:
        raise ValueError(f"The demo needs at least {MIN_DAYS} days of history (got {days})")
    t0 = time.time()
    n_outlets = max(1, min(MAX_OUTLETS, n_outlets))
    rng = np.random.default_rng(seed)
    fixed_end = end_date is not None
    end_date = end_date or (clock.today() - timedelta(days=1))
    start_date = end_date - timedelta(days=days - 1)
    reset_all(db)

    dataset = DatasetInfo(data_source="synthetic", generator_version=GENERATOR_VERSION, random_seed=seed,
                          generated_at=clock.now(), period_start=start_date, period_end=end_date,
                          parameters={"days": days, "outlets": n_outlets, "future_days": FUTURE_DAYS,
                                      "promo_elasticity": PROMO_ELASTICITY, "price_elasticity": PRICE_ELASTICITY,
                                      "fixed_end_date": fixed_end})
    db.add(dataset)
    org = Organization(**catalog.ORGANIZATION, low_stock_cover_days=3,
                       tax_id=demo_gstin(catalog.ORGANIZATION["state_code"], seed), tax_id_is_demo=True)
    db.add(org)
    db.flush()

    # --- master data: suppliers, ingredients, menu and recipes ---------------------------------
    suppliers = []
    for name, contact, phone, email, city, lead, terms in catalog.SUPPLIERS:
        s = Supplier(name=name, contact_person=contact, phone=phone, email=email, city=city,
                     lead_time_days=lead, payment_terms=terms)
        db.add(s)
        suppliers.append(s)
    categories: dict[str, Category] = {}
    for cat in [r[2] for r in catalog.MENU] + [r[2] for r in catalog.INGREDIENTS]:
        if cat not in categories:
            categories[cat] = Category(name=cat)
            db.add(categories[cat])
    db.flush()
    ingredients: list[Product] = []
    for sku, name, cat, unit, cost, sup, _profile in catalog.INGREDIENTS:
        p = Product(kind="ingredient", sku=sku, name=name, category_id=categories[cat].id,
                    supplier_id=suppliers[sup].id, unit=unit, cost_price=float(cost), selling_price=0.0,
                    tax_rate=0.0, reorder_level=0)
        db.add(p)
        ingredients.append(p)
    ing_index = {r[0]: i for i, r in enumerate(catalog.INGREDIENTS)}
    n_menu, n_ing = len(catalog.MENU), len(catalog.INGREDIENTS)
    recipe = np.zeros((n_menu, n_ing))  # ingredient quantity per portion
    for m_idx, row in enumerate(catalog.MENU):
        for ing_sku, qty in row[8].items():
            recipe[m_idx, ing_index[ing_sku]] = qty
    ing_cost = np.array([float(r[4]) for r in catalog.INGREDIENTS])
    menu: list[Product] = []
    for m_idx, (sku, name, cat, unit, price, _w, _profile, _veg, _r) in enumerate(catalog.MENU):
        p = Product(kind="menu", sku=sku, name=name, category_id=categories[cat].id, supplier_id=None, unit=unit,
                    cost_price=round(float(recipe[m_idx] @ ing_cost), 2), selling_price=float(price),
                    tax_rate=catalog.MENU_TAX_RATE, reorder_level=0, hsn_code=catalog.RESTAURANT_SAC)
        db.add(p)
        menu.append(p)
    db.flush()
    db.execute(insert(Recipe), [{"menu_item_id": menu[m].id, "ingredient_id": ingredients[i].id,
                                 "quantity": float(recipe[m, i])}
                                for m in range(n_menu) for i in range(n_ing) if recipe[m, i] > 0])

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
        outlet_meta.append({"code": code, "city": city, "size": size, "growth": growth, "opened": opened,
                            **catalog.OUTLET_TASTE[code]})
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

    base_w = np.array([row[5] for row in catalog.MENU])
    profiles = [row[6] for row in catalog.MENU]
    is_veg = np.array([row[7] for row in catalog.MENU])
    menu_cat = [row[2] for row in catalog.MENU]
    final_price = np.array([float(row[4]) for row in catalog.MENU])
    taxes = np.full(n_menu, catalog.MENU_TAX_RATE)
    menu_ids = [p.id for p in menu]
    course = np.array([catalog.COURSE_OF[c] for c in menu_cat])
    is_curry = np.array([c == "Main Course" for c in menu_cat])
    sku_index = {row[0]: i for i, row in enumerate(catalog.MENU)}
    water_idx = sku_index["CBV-005"]
    rice_sides = np.array([sku_index[s] for s in catalog.RICE_SIDES])
    pools = {c: np.where(course == c)[0] for c in ("soup", "starter", "main", "bread", "dessert", "drink")}
    pools["main"] = np.array([i for i in pools["main"] if i not in rice_sides])  # plain rice comes with curries
    pools["drink"] = pools["drink"][pools["drink"] != water_idx]
    horizon = days + FUTURE_DAYS

    # --- weather ---------------------------------------------------------------------------------
    cities = sorted({m["city"] for m in outlet_meta})
    weather = simulate_weather(rng, cities, start_date, days)
    weather_rows = [{"city": c, "day": start_date + timedelta(days=i), "temp_max_c": float(weather[c][0][i]),
                     "rain_mm": float(weather[c][1][i]), "is_forecast": i >= days}
                    for c in cities for i in range(horizon)]

    # --- ingredient costs (inflation + seasonal vegetable prices) and menu price revisions ---------
    ing_mult = np.ones((n_ing, horizon))
    years = np.arange(horizon) / 365.0
    doys = np.array([(start_date + timedelta(days=i)).timetuple().tm_yday for i in range(horizon)])
    for i, row in enumerate(catalog.INGREDIENTS):
        drift = math.exp(rng.uniform(0.04, 0.08) * 1.0)  # yearly inflation of this ingredient
        level = drift ** (years - years[days - 1])  # equals the catalogue cost on the last day of data
        seasonal = np.ones(horizon)
        if row[6] == "tomato":  # monsoon supply shocks
            seasonal = 1 + 1.6 * np.exp(-0.5 * ((np.minimum(abs(doys - 200), 365 - abs(doys - 200))) / 22) ** 2)
        elif row[6] == "onion":
            seasonal = 1 + 1.1 * np.exp(-0.5 * ((np.minimum(abs(doys - 290), 365 - abs(doys - 290))) / 25) ** 2)
        elif row[6] == "carrot":
            seasonal = 1.35 - 0.45 * np.exp(-0.5 * ((np.minimum(abs(doys - 15), 365 - abs(doys - 15))) / 45) ** 2)
        ing_mult[i] = level * seasonal / seasonal[days - 1]
    menu_mult = np.ones(horizon)
    revisions = sorted(int(x) for x in rng.choice(np.arange(min(75, days // 2), days - 20), 2 if days > 400 else 1,
                                                  replace=False))
    incs = rng.uniform(0.05, 0.08, len(revisions))
    menu_level = 1 / float(np.prod(1 + incs))  # the latest price equals today's menu price
    menu_mult[:] = menu_level
    for day_i, inc in zip(revisions, incs, strict=True):
        menu_level *= 1 + inc
        menu_mult[day_i:] = menu_level
    price_rows = []
    for m_idx in range(n_menu):
        for day_i in [0] + revisions:
            price_rows.append({"product_id": menu_ids[m_idx], "effective_from": start_date + timedelta(days=day_i),
                               "selling_price": float(round(final_price[m_idx] * menu_mult[day_i])),
                               "cost_price": round(float(recipe[m_idx] @ (ing_cost * ing_mult[:, day_i])), 2)})
    for i in range(n_ing):  # ingredient purchase prices, first of each month
        for day_i in range(days):
            d = start_date + timedelta(days=day_i)
            if day_i == 0 or d.day == 1:
                price_rows.append({"product_id": ingredients[i].id, "effective_from": d, "selling_price": 0.0,
                                   "cost_price": round(float(ing_cost[i] * ing_mult[i, day_i]), 2)})

    # --- promotions (history + 30 days of planned promotions) -----------------------------------
    promo_rows = []
    promo_disc = np.zeros((n_outlets, n_menu, horizon))
    promo_ref = np.zeros((n_outlets, n_menu, horizon), dtype=np.int32)
    cat_names = list(dict.fromkeys(menu_cat))
    day_i = int(rng.integers(5, 15))
    while day_i < days + 30:
        disc = float(rng.choice([10, 15, 20]))
        length = int(rng.integers(4, 10))
        scope_outlet = None if rng.random() < 0.7 else int(rng.integers(0, n_outlets))
        if rng.random() < 0.6:
            cat = cat_names[int(rng.integers(0, len(cat_names)))]
            target = [i for i in range(n_menu) if menu_cat[i] == cat]
            name = f"{PROMO_NAMES.get(cat, cat)}: {int(disc)}% off {cat}"
            fields = {"category_id": categories[cat].id, "product_id": None}
        else:
            m_idx = int(rng.choice(n_menu, p=base_w / base_w.sum()))
            target = [m_idx]
            name = f"Chef's Special: {int(disc)}% off {menu[m_idx].name}"
            fields = {"category_id": None, "product_id": menu_ids[m_idx]}
        pid = len(promo_rows) + 1
        s_d, e_d = start_date + timedelta(days=day_i), start_date + timedelta(days=day_i + length - 1)
        promo_rows.append({"id": pid, "name": name + ("" if scope_outlet is None else f" ({outlets[scope_outlet].name})"),
                           "outlet_id": outlets[scope_outlet].id if scope_outlet is not None else None,
                           "discount_pct": disc, "start_date": s_d, "end_date": e_d, **fields,
                           "created_at": datetime.combine(s_d - timedelta(days=7), datetime.min.time())})
        o_range = [scope_outlet] if scope_outlet is not None else range(n_outlets)
        for o_idx in o_range:
            for m_idx in target:
                promo_disc[o_idx, m_idx, day_i:day_i + length] = disc / 100
                promo_ref[o_idx, m_idx, day_i:day_i + length] = pid
        day_i += int(rng.integers(10, 19))

    # --- ingredient outages: the dishes that need the ingredient come off the menu (86'd) ----------
    substitute = {}
    for i in range(n_menu):
        same = [j for j in range(n_menu) if j != i and menu_cat[j] == menu_cat[i] and is_veg[j] == is_veg[i]]
        same = same or [j for j in range(n_menu) if j != i and menu_cat[j] == menu_cat[i]]
        substitute[i] = min(same, key=lambda j: abs(final_price[j] - final_price[i])) if same else None
    available = np.ones((n_outlets, n_menu, days), dtype=bool)
    # Specialty ingredients run out (meat, fish, paneer and fresh dairy most often); staples that nearly every dish
    # needs (onion, oil, masala, flour...) are bought locally the same day, so they never stop the kitchen.
    uses = (recipe > 0).sum(axis=0)
    outage_w = np.array([3.0 if r[2] == "Meat & Seafood" else 2.0 if r[0] in ("ING-001", "ING-002", "ING-007")
                         else 0.6 if r[2] == "Dry Store" else 1.0 for r in catalog.INGREDIENTS])
    outage_w = np.where((uses >= 1) & (uses <= MAX_OUTAGE_DISHES), outage_w * np.sqrt(uses.clip(min=1)), 0.0)
    stockout_rows = []
    for o_idx in range(n_outlets):
        for _ in range(int(rng.poisson(days / 30 * 1.4))):
            i = int(rng.choice(n_ing, p=outage_w / outage_w.sum()))
            s_i = int(rng.integers(0, days - 1))
            length = 1 + int(rng.poisson(0.6))
            for m_idx in np.where(recipe[:, i] > 0)[0]:
                available[o_idx, m_idx, s_i:s_i + length] = False
                sub = substitute[int(m_idx)]
                stockout_rows.append({"outlet_id": outlets[o_idx].id, "product_id": menu_ids[m_idx],
                                      "start_date": start_date + timedelta(days=s_i),
                                      "end_date": start_date + timedelta(days=min(days - 1, s_i + length - 1)),
                                      "substitute_product_id": menu_ids[sub] if sub is not None else None})

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

    # --- guests (customers who leave a phone number for loyalty points or delivery) -------------
    n_customers = 3000
    sizes = np.array([m["size"] for m in outlet_meta])
    home = rng.choice(n_outlets, n_customers, p=sizes / sizes.sum())
    loyalty = rng.lognormal(0, 1.0, n_customers)
    loyalty = np.minimum(loyalty, np.quantile(loyalty, 0.99))  # regulars come weekly, not every day
    join_offset = (rng.beta(1.2, 2.2, n_customers) * days).astype(int)
    churned = rng.random(n_customers) < 0.25
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

    # bills reference promotions, so the demand-driver tables go in first
    db.execute(insert(WeatherDaily), weather_rows)
    db.execute(insert(PriceHistory), price_rows)
    db.execute(insert(Promotion), promo_rows)
    if stockout_rows:
        db.execute(insert(StockoutEvent), stockout_rows)

    # --- sales simulation ----------------------------------------------------------------------
    units_sold = np.zeros((n_outlets, n_menu, days))
    day_revenue = np.zeros((n_outlets, days))
    sale_rows, item_rows = [], []
    sale_id = item_id = 0
    lost_lines = substituted_lines = 0
    p_dine = HOUR_WEIGHTS_DINE / HOUR_WEIGHTS_DINE.sum()
    p_deliv = HOUR_WEIGHTS_DELIVERY / HOUR_WEIGHTS_DELIVERY.sum()
    channels = np.array(["dine_in", "takeaway", "delivery"])

    for d_i in range(days):
        d = start_date + timedelta(days=d_i)
        wd = d.weekday()
        weekend = wd >= 5
        event = event_window(d)
        years_from_start = d_i / 365.0
        doy = d.timetuple().tm_yday
        # December party season; a quieter late spring when families travel
        season = 1 + 0.14 * _bump(doy, 355, 14) - 0.07 * _bump(doy, 135, 25)
        cust_active = (join_offset <= d_i) & (churn_offset > d_i)
        price_today = np.round(final_price * menu_mult[d_i])
        cost_today = recipe @ (ing_cost * ing_mult[:, d_i])
        nonveg_today = _nonveg_factor(d, event)

        for o_idx, meta in enumerate(outlet_meta):
            if d < meta["opened"]:
                continue
            anomaly = anomalies.get((o_idx, d_i))
            if anomaly and anomaly[0] == "closure":
                continue
            temp = float(weather[meta["city"]][0][d_i])
            rain = float(weather[meta["city"]][1][d_i])
            disc_today = promo_disc[o_idx, :, d_i]
            mix = base_w * np.array([_profile_factor(pr, d, weekend, event, temp, rain) for pr in profiles])
            mix = mix * (1 - disc_today) ** -PROMO_ELASTICITY * menu_mult[d_i] ** -PRICE_ELASTICITY
            mix = np.where(is_veg, mix, mix * meta["nonveg"] * nonveg_today)
            age = (d - meta["opened"]).days
            ramp = 0.35 + 0.65 * (1 - math.exp(-age / 50)) if age < 400 else 1.0
            trend = math.exp(meta["growth"] * years_from_start)
            lam = (BASE_BILLS * meta["size"] * WEEKDAY_FACTOR[wd] * trend * season * _footfall_event_factor(event)
                   * (1 - 0.003 * min(rain, 60)) * ramp * rng.lognormal(0, 0.07))
            if anomaly and anomaly[0] in ("pos_outage", "local_event"):
                lam *= anomaly[1]
            n = int(rng.poisson(lam))
            if n == 0:
                continue

            # channel and party size
            p_delivery = min(0.75, meta["delivery"] * (1 + 0.015 * min(rain, 40)) * (0.9 if weekend else 1.0))
            r = rng.random(n)
            is_business = (rng.random(n) < 0.015) & bool(business_by_outlet[o_idx])
            chan = np.where(r < p_delivery, 2, np.where(r < p_delivery + TAKEAWAY_SHARE, 1, 0))
            chan = np.where(is_business, np.where(rng.random(n) < 0.6, 1, 2), chan)
            covers = np.where(chan == 0, 1 + rng.poisson(1.5 + (0.4 if weekend else 0.0), n),
                              1 + rng.poisson(np.where(chan == 1, 0.7, 0.9)))
            covers = np.minimum(covers, 10)
            covers = np.where(is_business, 8 + rng.poisson(6, n), covers)
            ch_names = channels[chan]

            # courses: how many of each the party orders
            n_main = np.maximum(1, np.rint(covers * 0.72 + rng.normal(0, 0.45, n))).astype(int)
            p_start = np.array([P_STARTER[c] for c in ch_names])
            n_start = np.where(rng.random(n) < p_start, np.ceil(covers / 2.2), 0).astype(int)
            soup_boost = float(np.mean([_profile_factor(profiles[i], d, weekend, event, temp, rain)
                                        for i in pools["soup"]]))
            p_soup = np.array([P_SOUP[c] for c in ch_names]) * soup_boost
            n_soup = np.where(rng.random(n) < p_soup, np.ceil(covers / 2), 0).astype(int)
            p_des = np.array([P_DESSERT[c] for c in ch_names])
            n_des = np.where(rng.random(n) < p_des, np.ceil(covers / 2.5), 0).astype(int)
            n_drink = rng.binomial(covers, np.array([P_DRINK[c] for c in ch_names]))
            n_water = np.where((chan == 0) & (rng.random(n) < 0.42), 1 + (covers >= 4), 0)

            def draw(pool_name: str, counts: np.ndarray, mix: np.ndarray = mix) -> list[np.ndarray]:
                pool = pools[pool_name]
                w = mix[pool]
                return _split(rng.choice(pool, int(counts.sum()), p=w / w.sum()), counts)

            mains = draw("main", n_main)
            curries = np.array([int(is_curry[m].sum()) for m in mains])
            n_bread = np.where(curries > 0, np.maximum(1, np.rint(covers * 0.6 + curries * 0.6
                                                                   + rng.normal(0, 0.5, n))), 0).astype(int)
            n_rice = np.where((curries > 0) & (rng.random(n) < 0.45), 1, 0)
            starters, soups, desserts = draw("starter", n_start), draw("soup", n_soup), draw("dessert", n_des)
            drinks, breads = draw("drink", n_drink), draw("bread", n_bread)
            rice_w = mix[rice_sides]
            rice = _split(rng.choice(rice_sides, int(n_rice.sum()), p=rice_w / rice_w.sum()), n_rice)

            p_hour = np.where(chan[:, None] == 2, p_deliv, p_dine)
            hours = OPEN_HOUR + (rng.random(n)[:, None] > np.cumsum(p_hour, axis=1)).sum(axis=1)
            hours = np.minimum(hours, 23)
            minutes = rng.integers(0, 60, n)
            seconds = rng.integers(0, 60, n)
            order = np.lexsort((seconds, minutes, hours))
            pay_r = rng.random(n)
            disc_r = rng.random(n)
            cust_r = rng.random(n)
            pool = by_outlet_customers[o_idx]
            pool = pool[cust_active[pool]]
            pool_p = loyalty[pool] / loyalty[pool].sum() if len(pool) else None
            upi_share = 0.45 + 0.1 * years_from_start
            avail = available[o_idx, :, d_i]

            extra_bills = []
            if anomaly and anomaly[0] == "bulk_order" and business_by_outlet[o_idx]:
                extra_bills.append("bulk")
            if anomaly and anomaly[0] == "entry_error":
                extra_bills.append("error")

            seq = 0
            bills = [("normal", b) for b in order] + [(x, None) for x in extra_bills]
            for kind, b in bills:
                if kind == "normal":
                    parts = [mains[b], breads[b], rice[b], starters[b], soups[b], desserts[b], drinks[b]]
                    if is_business[b]:  # a company orders a few dishes per course, in bulk
                        parts = [_group_order(x, k) for x, k in zip(parts, (3, 2, 1, 2, 1, 1, 2), strict=True)]
                    lines = np.concatenate(parts + [np.full(int(n_water[b]), water_idx)]).astype(int)
                    kept = []
                    for m_idx in lines:
                        if avail[m_idx]:
                            kept.append(m_idx)
                        elif substitute[m_idx] is not None and avail[substitute[m_idx]] and rng.random() < 0.6:
                            kept.append(substitute[m_idx])
                            substituted_lines += 1
                        else:
                            lost_lines += 1
                    if not kept:
                        continue
                    prods, counts = np.unique(kept, return_counts=True)
                    qtys = counts.astype(float)
                    business = bool(is_business[b])
                    channel = str(ch_names[b])
                    party = int(covers[b])
                    hh, mm, ss = int(hours[b]), int(minutes[b]), int(seconds[b])
                elif kind == "bulk":  # a company's one-off party order (ground-truth anomaly)
                    big = np.array([sku_index[s] for s in ("RIC-004", "RIC-003", "MNC-001", "MNC-007", "MNC-003",
                                                           "BRD-001", "STR-001", "STR-004", "DST-001")])
                    prods = big
                    qtys = rng.integers(20, 50, len(prods)).astype(float)
                    qtys[list(big).index(sku_index["BRD-001"])] *= 2  # about two naan a head
                    business, channel, party, hh, mm, ss = True, "takeaway", int(qtys.max()), 12, 5, 0
                else:  # entry error: an extra "00" typed into a quantity (ground-truth anomaly)
                    m_idx = int(rng.choice(np.where(final_price > 250)[0]))
                    prods, qtys = np.array([m_idx]), np.array([float(rng.choice([200, 300]))])
                    business, channel, party, hh, mm, ss = False, "dine_in", 2, 20, 40, 0
                seq += 1
                sale_id += 1
                customer_id = None
                if business:
                    customer_id = int(rng.choice(business_by_outlet[o_idx])) if business_by_outlet[o_idx] else None
                elif kind == "normal" and len(pool) and cust_r[b] < {"dine_in": 0.3, "takeaway": 0.35,
                                                                     "delivery": 0.55}[channel]:
                    customer_id = int(pool[rng.choice(len(pool), p=pool_p)]) + 1
                if kind != "normal":
                    payment, disc_rate = "credit" if business else "card", 0.0
                else:
                    if business:
                        payment = "credit" if pay_r[b] < 0.7 else "upi"
                    elif channel == "delivery":  # paid online through the delivery app
                        payment = "upi" if pay_r[b] < 0.68 else "card"
                    else:
                        payment = "upi" if pay_r[b] < upi_share else ("card" if pay_r[b] < upi_share + 0.3 else "cash")
                    disc_rate = 0.1 if disc_r[b] < 0.03 else (0.05 if disc_r[b] < 0.07 else 0.0)

                subtotal = discount = tax_total = total = qty_total = 0.0
                for m_idx, qty in zip(prods, qtys, strict=True):
                    qty = float(qty)
                    list_price = float(price_today[m_idx])
                    promo = float(disc_today[m_idx])
                    price = float(round(list_price * (1 - promo))) if promo else list_price
                    gross = qty * price
                    line_disc = round(gross * disc_rate, 2)
                    line_total = round(gross - line_disc, 2)
                    tax = round(line_total * taxes[m_idx] / (100 + taxes[m_idx]), 2)
                    item_id += 1
                    item_rows.append({
                        "id": item_id, "sale_id": sale_id, "product_id": menu_ids[m_idx],
                        "outlet_id": outlets[o_idx].id, "sale_date": d, "quantity": qty, "unit_price": price,
                        "list_price": list_price if promo else None,
                        "promotion_id": int(promo_ref[o_idx, m_idx, d_i]) if promo else None,
                        "discount": line_disc, "line_total": line_total, "tax_amount": tax,
                        "cost_amount": round(qty * float(cost_today[m_idx]), 2),
                    })
                    units_sold[o_idx, m_idx, d_i] += qty
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
                    "channel": channel, "covers": party if channel == "dine_in" else None,
                    "payment_method": payment, "subtotal": round(subtotal, 2),
                    "discount": round(discount, 2), "tax_amount": round(tax_total, 2), "total": round(total, 2),
                    "items_count": qty_total, "status": "completed", "source": "synthetic", "dataset_id": dataset.id,
                    "created_at": sold_at,
                })
        if len(item_rows) >= WRITE_BATCH_LINES:  # write whole days in batches to keep memory flat
            _bulk_insert(db, Sale, sale_rows)
            _bulk_insert(db, SaleItem, item_rows)
            sale_rows, item_rows = [], []
        if d_i and d_i % 180 == 0:
            log(f"  simulated {d_i}/{days} days ({time.time() - t0:.1f}s)")

    _bulk_insert(db, Sale, sale_rows)
    _bulk_insert(db, SaleItem, item_rows)
    del sale_rows, item_rows
    log(f"  simulated {sale_id:,} bills / {item_id:,} lines ({time.time() - t0:.1f}s)")
    db.commit()
    log(f"  sales written ({time.time() - t0:.1f}s)")

    # --- anomaly labels (magnitude measured against the same weekday's median at that outlet) ------
    label_rows = []
    descriptions = {
        "pos_outage": "Billing system outage - most of the day's orders were not recorded",
        "bulk_order": "One-off party order from a corporate customer",
        "entry_error": "Data-entry error: an extra '00' typed into a quantity",
        "local_event": "Concert or match nearby drove unusual footfall",
        "closure": "Restaurant closed for the day (kitchen maintenance)",
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

    # --- ingredient stock -------------------------------------------------------------------------
    # daily ingredient use = dishes sold x recipe quantities
    usage = np.einsum("omd,mi->oid", units_sold, recipe)
    recent = usage[:, :, -28:].mean(axis=2)
    lead = {s.id: s.lead_time_days for s in suppliers}
    admin_id = db.query(User.id).filter(User.role == "admin").scalar()
    inv_rows, mov_rows = [], []
    stamp = datetime.combine(end_date, datetime.min.time()) + timedelta(hours=23, minutes=30)
    for o_idx, o in enumerate(outlets):
        for i, ing in enumerate(ingredients):
            avg = recent[o_idx, i]
            lt = lead[ing.supplier_id]
            reorder = round(avg * (lt + 1), 2) if avg > 0 else 0.0  # enough for the delivery wait plus a day
            qty = round(avg * rng.uniform(lt + 0.8, lt + 5), 2) if avg > 0 else 0.0
            r = rng.random()
            if reorder and r < 0.12:
                qty = round(float(rng.uniform(0, reorder * 0.9)), 2)
            if reorder and r < 0.02:
                qty = 0.0
            unit_qty = math.ceil if ing.unit in ("pcs",) else (lambda x: round(x, 2))
            qty, reorder = float(unit_qty(qty)), float(unit_qty(reorder))
            inv_rows.append({"outlet_id": o.id, "product_id": ing.id, "quantity": qty, "reorder_level": reorder,
                             "updated_at": stamp})
            mov_rows.append({"outlet_id": o.id, "product_id": ing.id, "change": qty, "balance_after": qty,
                             "reason": "adjustment", "reference": "OPENING", "note": "Opening stock (synthetic data)",
                             "user_id": admin_id, "created_at": stamp})
    db.execute(insert(InventoryItem), inv_rows)
    db.execute(insert(StockMovement), mov_rows)
    for i, ing in enumerate(ingredients):
        ing.reorder_level = round(float(recent[:, i].mean() * (lead[ing.supplier_id] + 1)), 2)
    db.commit()

    # --- purchase orders (last ~12 weeks): fresh suppliers deliver every few days, the rest weekly ----
    po_rows, po_item_rows = [], []
    po_item_id = 0
    supplier_items = defaultdict(list)
    for i, ing in enumerate(ingredients):
        supplier_items[ing.supplier_id].append(i)
    for o_idx, o in enumerate(outlets):
        for s in suppliers:
            every = 3 if s.lead_time_days <= 1 else 7
            order_day = days - 84 + int(rng.integers(0, every))
            while order_day < days + 1:
                order_date = start_date + timedelta(days=order_day)
                if order_date >= outlet_meta[o_idx]["opened"] and order_day >= 14:
                    window = usage[o_idx, :, max(0, order_day - 14):order_day].mean(axis=1) * every
                    lines = [(i, window[i] * 1.08) for i in supplier_items[s.id] if window[i] > 0]
                    if lines:
                        po_id = len(po_rows) + 1
                        expected = order_date + timedelta(days=s.lead_time_days)
                        if expected <= end_date:
                            status, received = ("cancelled", None) if rng.random() < 0.02 else ("received", expected)
                            if status == "received" and rng.random() < 0.1:
                                received = expected + timedelta(days=int(rng.integers(1, 3)))  # late deliveries
                        else:
                            status, received = "ordered", None
                        total = 0.0
                        for i, q in lines:
                            q = float(math.ceil(q)) if ingredients[i].unit == "pcs" else round(max(q, 0.5), 1)
                            po_item_id += 1
                            unit_cost = round(float(ing_cost[i] * ing_mult[i, min(order_day, days - 1)]), 2)
                            total += q * unit_cost
                            po_item_rows.append({"id": po_item_id, "order_id": po_id, "product_id": ingredients[i].id,
                                                 "quantity": q, "unit_cost": unit_cost,
                                                 "received_quantity": q if status == "received" else 0.0})
                        po_rows.append({
                            "id": po_id, "po_number": f"PO-{order_date:%y%m}-{po_id:05d}", "supplier_id": s.id,
                            "outlet_id": o.id, "status": status, "order_date": order_date, "expected_date": expected,
                            "received_date": received, "total_cost": round(total, 2), "created_by": admin_id,
                            "created_at": datetime.combine(order_date, datetime.min.time()) + timedelta(hours=9),
                        })
                order_day += every
    # number POs in date order, as a real system would have issued them
    po_rows.sort(key=lambda r: (r["order_date"], r["outlet_id"], r["supplier_id"]))
    renumber = {r["id"]: k + 1 for k, r in enumerate(po_rows)}
    for r in po_rows:
        r["id"] = renumber[r["id"]]
        r["po_number"] = f"PO-{r['order_date']:%y%m}-{r['id']:05d}"
    for r in po_item_rows:
        r["order_id"] = renumber[r["order_id"]]
    db.execute(insert(PurchaseOrder), po_rows)
    db.execute(insert(PurchaseOrderItem), po_item_rows)

    counts = {
        "outlets": len(outlets), "menu_items": n_menu, "ingredients": n_ing, "recipe_lines": int((recipe > 0).sum()),
        "suppliers": len(suppliers), "customers": len(customer_rows), "sales": sale_id, "sale_items": item_id,
        "purchase_orders": len(po_rows), "promotions": len(promo_rows), "menu_price_revisions": len(revisions),
        "stockout_events": len(stockout_rows), "lost_lines_due_to_stockout": lost_lines,
        "substituted_lines": substituted_lines, "anomaly_labels": len(label_rows), "weather_days": len(weather_rows),
    }
    dataset.row_counts = counts
    db.commit()
    _sync_sequences(db)
    counts.update(start_date=start_date.isoformat(), end_date=end_date.isoformat(), seconds=round(time.time() - t0, 1))
    log(f"  done: {counts}")
    return counts


def release_memory() -> None:
    """Hand the memory used while generating back to the OS (keeps a small hosted demo within its RAM limit)."""
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)  # glibc keeps freed memory otherwise
    except (OSError, AttributeError):  # not glibc (macOS, Windows, musl)
        pass
