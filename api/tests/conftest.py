import os
import tempfile
from datetime import date, timedelta

import pytest

_tmp = tempfile.mkdtemp(prefix="eris-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["LLM_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, create_tables  # noqa: E402
from app.main import app  # noqa: E402
from app.seed.generator import DEMO_PASSWORDS, generate_demo_data  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded():
    create_tables()
    with SessionLocal() as db:
        generate_demo_data(db, days=130, seed=7, end_date=date.today() - timedelta(days=1), log=lambda *_: None)
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
