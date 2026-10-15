import os
import tempfile
from datetime import date, timedelta

import pytest

_tmp = tempfile.mkdtemp(prefix="eris-test-")
# Set TEST_DATABASE_URL to run the suite against PostgreSQL (the database is wiped).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_tmp}/test.db"  # empty = unset
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["LLM_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, migrate  # noqa: E402
from app.main import app  # noqa: E402
from app.seed.generator import DEMO_PASSWORDS, generate_demo_data  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded():
    if os.environ.get("TEST_DATABASE_URL", "").startswith("postgresql"):
        from sqlalchemy import text

        from app.db import engine

        with engine.begin() as conn:  # start from an empty schema every run
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
    migrate()
    with SessionLocal() as db:
        generate_demo_data(db, days=200, seed=7, end_date=date.today() - timedelta(days=1), log=lambda *_: None)
    yield


@pytest.fixture(scope="session")
def client(seeded):
    with TestClient(app) as c:
        yield c


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, "admin@eris.demo", DEMO_PASSWORDS["admin"])


@pytest.fixture(scope="session")
def manager(client):
    return _login(client, "priya.and@eris.demo", DEMO_PASSWORDS["manager"])


@pytest.fixture(scope="session")
def staff(client):
    return _login(client, "staff.andheri@eris.demo", DEMO_PASSWORDS["staff"])


@pytest.fixture(scope="session")
def viewer(client):
    return _login(client, "analyst@eris.demo", DEMO_PASSWORDS["viewer"])


def product_id(sku: str) -> int:
    from app.models import Product

    with SessionLocal() as db:
        return db.query(Product.id).filter_by(sku=sku).scalar()


def stock_up(client, headers, outlet_id: int, dish_sku: str, quantity: float = 50) -> int:
    """Give a kitchen plenty of every ingredient a dish needs, so a test bill can be made. Returns the dish id."""
    dish = product_id(dish_sku)
    for line in client.get(f"/api/products/{dish}", headers=headers).json()["recipe"]:
        r = client.post("/api/inventory/adjust", headers=headers, json={
            "outlet_id": outlet_id, "product_id": line["ingredient_id"], "mode": "set", "quantity": quantity})
        assert r.status_code == 200, r.text
    return dish
