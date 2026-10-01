"""Deterministic synthetic portfolio data for one organization and five outlets."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import os
import random

import holidays
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gstin import generate_synthetic_gstin
from app.core.security import hash_password
from app.models.customers import Customer
from app.models.inventory import Inventory
from app.models.commerce import Product, ProductCategory, Sale, SaleItem, Supplier
from app.models.organization import Organization
from app.models.outlet import Outlet
from app.models.users import Role, User, UserOutletAccess


logger = logging.getLogger(__name__)
DEMO_DATA_SEED = int(os.getenv("ERIS_DEMO_DATA_SEED", "42"))

OUTLETS = [
    (1, "Mumbai Central", "Mumbai", "MH", 19.0760, 72.8777),
    (2, "Delhi Connaught", "Delhi", "DL", 28.7041, 77.1025),
    (3, "Bengaluru Indiranagar", "Bengaluru", "KA", 12.9716, 77.5946),
    (4, "Chennai T-Nagar", "Chennai", "TN", 13.0827, 80.2707),
    (5, "Jaipur Pink City", "Jaipur", "RJ", 26.9124, 75.7873),
]
CATALOG = {
    "Starters": [
        ("Paneer Tikka", 180, 60),
        ("Veg Spring Rolls", 120, 40),
        ("Chicken Wings", 220, 80),
        ("Crispy Corn", 140, 45),
    ],
    "Mains": [
        ("Butter Chicken", 280, 90),
        ("Dal Makhani", 180, 50),
        ("Palak Paneer", 220, 75),
        ("Kadai Chicken", 300, 100),
    ],
    "Breads": [("Butter Naan", 40, 10), ("Garlic Naan", 50, 12), ("Tandoori Roti", 30, 8), ("Laccha Paratha", 60, 15)],
    "Rice": [
        ("Chicken Biryani", 320, 120),
        ("Veg Biryani", 220, 80),
        ("Jeera Rice", 120, 30),
        ("Steamed Rice", 90, 20),
    ],
    "Beverages": [
        ("Sweet Lassi", 60, 15),
        ("Masala Chai", 30, 5),
        ("Cold Coffee", 120, 30),
        ("Fresh Lime Soda", 50, 10),
    ],
}


def _seed_password() -> str:
    password = os.getenv("ERIS_SEED_PASSWORD", "").strip()
    if not password or password.lower().startswith("change_me"):
        raise RuntimeError("ERIS_SEED_PASSWORD must be set before creating demo users")
    return password


async def _exists(session: AsyncSession, model) -> bool:
    return bool((await session.execute(select(func.count()).select_from(model))).scalar())


async def bootstrap_essentials(session: AsyncSession) -> dict:
    """Create the single demo organization, roles, outlets, and login users idempotently."""
    created: dict[str, int] = {}
    try:
        organization = await session.get(Organization, 1)
        if organization is None:
            session.add(
                Organization(
                    id=1,
                    name="Spice Route Retail (Synthetic Demo)",
                    tax_id=generate_synthetic_gstin("29", DEMO_DATA_SEED),
                    country="India",
                    is_active=True,
                )
            )
            created["organizations"] = 1

        existing_roles = {row.name: row for row in (await session.execute(select(Role))).scalars()}
        for role_id, name in enumerate(("admin", "manager", "viewer"), start=1):
            if name not in existing_roles:
                session.add(Role(id=role_id, name=name, description=f"{name.title()} access", is_system_role=True))
                created["roles"] = created.get("roles", 0) + 1
        await session.flush()

        existing_outlets = set((await session.execute(select(Outlet.id))).scalars())
        for outlet_id, name, city, state, latitude, longitude in OUTLETS:
            if outlet_id not in existing_outlets:
                session.add(
                    Outlet(
                        id=outlet_id,
                        organization_id=1,
                        name=name,
                        code=f"OUT-{outlet_id:02d}",
                        city=city,
                        state=state,
                        country="India",
                        phone=f"+9190000000{outlet_id:02d}",
                        email=f"outlet{outlet_id}@eris.example",
                        latitude=latitude,
                        longitude=longitude,
                        is_active=True,
                    )
                )
                created["outlets"] = created.get("outlets", 0) + 1
        await session.flush()

        if not await _exists(session, User):
            password_hash = hash_password(_seed_password())
            users = [
                User(
                    id=999,
                    organization_id=1,
                    username="admin",
                    email="admin@eris.example",
                    first_name="Demo",
                    last_name="Admin",
                    password_hash=password_hash,
                    role_id=1,
                    is_active=True,
                ),
                User(
                    id=998,
                    organization_id=1,
                    username="manager",
                    email="manager@eris.example",
                    first_name="Demo",
                    last_name="Manager",
                    password_hash=password_hash,
                    role_id=2,
                    is_active=True,
                ),
                User(
                    id=997,
                    organization_id=1,
                    username="viewer",
                    email="viewer@eris.example",
                    first_name="Demo",
                    last_name="Viewer",
                    password_hash=password_hash,
                    role_id=3,
                    is_active=True,
                ),
            ]
            session.add_all(users)
            await session.flush()
            session.add_all([UserOutletAccess(user_id=998, outlet_id=1), UserOutletAccess(user_id=997, outlet_id=1)])
            created["users"] = len(users)
        await session.commit()
        return {"status": "success" if created else "skipped", "records": created, "errors": []}
    except Exception:
        await session.rollback()
        raise


async def generate_historical_data(session: AsyncSession, days: int = 365) -> dict:
    """Generate clearly synthetic customers, catalog, inventory, and sales history."""
    if await _exists(session, Sale):
        return {"status": "skipped", "records": {}, "message": "Sales data already exists"}

    rng = random.Random(DEMO_DATA_SEED)
    india_holidays = holidays.IN(years={datetime.now().year, (datetime.now() - timedelta(days=days)).year})
    suppliers = [
        Supplier(
            id=1,
            organization_id=1,
            name="Demo Wholesale Foods",
            phone="+918000000001",
            city="Mumbai",
            payment_terms_days=30,
        ),
        Supplier(
            id=2,
            organization_id=1,
            name="Demo Fresh Produce",
            phone="+918000000002",
            city="Bengaluru",
            payment_terms_days=15,
        ),
    ]
    session.add_all(suppliers)

    products: list[Product] = []
    product_id = 1
    for category_id, (category_name, items) in enumerate(CATALOG.items(), start=1):
        session.add(
            ProductCategory(
                id=category_id,
                organization_id=1,
                name=category_name,
                hsn_code=f"D{category_id:03d}",
                default_gst_rate=Decimal("5.00"),
            )
        )
        for name, price, cost in items:
            products.append(
                Product(
                    id=product_id,
                    organization_id=1,
                    category_id=category_id,
                    supplier_id=1 if product_id % 2 else 2,
                    sku=f"DEMO-{product_id:04d}",
                    name=name,
                    cost_price=Decimal(cost),
                    selling_price=Decimal(price),
                    mrp=Decimal(price),
                    hsn_code=f"D{category_id:03d}",
                    reorder_level=25,
                    reorder_quantity=100,
                    unit="item",
                    is_active=True,
                    is_deleted=False,
                )
            )
            product_id += 1
    session.add_all(products)

    customers = [
        Customer(
            id=customer_id,
            organization_id=1,
            first_name="Demo",
            last_name=f"Customer {customer_id:03d}",
            email=f"customer{customer_id:03d}@example.test",
            phone=f"70000{customer_id:05d}",
            city=OUTLETS[(customer_id - 1) % len(OUTLETS)][2],
            state=OUTLETS[(customer_id - 1) % len(OUTLETS)][3],
            country="India",
        )
        for customer_id in range(1, 51)
    ]
    session.add_all(customers)
    await session.flush()

    session.add_all(
        [
            Inventory(
                organization_id=1,
                outlet_id=outlet_id,
                product_id=product.id,
                current_stock=rng.randint(100, 300),
                reserved_stock=0,
                last_restocked_at=datetime.now(timezone.utc),
            )
            for outlet_id, *_ in OUTLETS
            for product in products
        ]
    )
    await session.flush()

    customer_totals = {customer.id: [Decimal("0"), 0] for customer in customers}
    sale_id = 1
    sale_item_id = 1
    start = datetime.now(timezone.utc) - timedelta(days=days - 1)
    for day_offset in range(days):
        day = start + timedelta(days=day_offset)
        holiday_factor = 1.5 if day.date() in india_holidays else 1.0
        weekend_factor = 1.25 if day.weekday() >= 5 else 1.0
        for outlet_id, *_ in OUTLETS:
            order_count = max(2, int(rng.randint(4, 8) * holiday_factor * weekend_factor))
            for _ in range(order_count):
                selected = rng.sample(products, k=rng.randint(1, 3))
                item_rows = []
                subtotal = Decimal("0")
                for product in selected:
                    quantity = rng.randint(1, 3)
                    line_total = Decimal(product.selling_price) * quantity
                    subtotal += line_total
                    item_rows.append(
                        SaleItem(
                            id=sale_item_id,
                            organization_id=1,
                            sale_id=sale_id,
                            product_id=product.id,
                            quantity=quantity,
                            unit_price=product.selling_price,
                            discount_percent=Decimal("0"),
                            line_total=line_total,
                        )
                    )
                    sale_item_id += 1
                tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
                total = subtotal + tax
                customer = rng.choice(customers) if rng.random() > 0.2 else None
                sale_time = day.replace(hour=rng.randint(9, 22), minute=rng.randint(0, 59), second=0, microsecond=0)
                session.add(
                    Sale(
                        id=sale_id,
                        organization_id=1,
                        outlet_id=outlet_id,
                        customer_id=customer.id if customer else None,
                        sale_number=f"DEMO-{sale_time:%Y%m%d}-{sale_id:06d}",
                        sale_date=sale_time,
                        subtotal=subtotal,
                        tax_amount=tax,
                        discount_amount=Decimal("0"),
                        total_amount=total,
                        payment_method=rng.choice(("cash", "card", "upi")),
                        payment_status="paid",
                        amount_paid=total,
                        status="completed",
                        channel=rng.choice(("offline", "offline", "online")),
                        notes="Synthetic demonstration transaction",
                    )
                )
                session.add_all(item_rows)
                if customer:
                    customer_totals[customer.id][0] += total
                    customer_totals[customer.id][1] += 1
                sale_id += 1
        if day_offset % 14 == 0:
            await session.flush()

    for customer in customers:
        customer.total_purchases = customer_totals[customer.id][0]
        customer.total_transactions = customer_totals[customer.id][1]
    await session.commit()
    return {
        "status": "success",
        "records": {
            "outlets": len(OUTLETS),
            "products": len(products),
            "customers": len(customers),
            "sales": sale_id - 1,
            "sale_items": sale_item_id - 1,
        },
        "synthetic": True,
        "seed": DEMO_DATA_SEED,
    }


async def seed_database(session: AsyncSession, skip_if_exists: bool = True) -> dict:
    """Canonical seed entry point; existing transactional data is never overwritten."""
    essentials = await bootstrap_essentials(session)
    history = await generate_historical_data(session)
    return {"status": history["status"], "essentials": essentials, **history}


if __name__ == "__main__":
    import asyncio
    from app.database import AsyncSessionLocal

    async def run():
        async with AsyncSessionLocal() as session:
            print(await seed_database(session))

    asyncio.run(run())
