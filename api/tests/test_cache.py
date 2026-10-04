"""The analytics response cache only ever serves answers that are still true for the current data and user."""
from app.db import SessionLocal
from app.models import User


def test_repeat_request_is_served_from_cache_and_a_sale_invalidates_it(client, admin):
    url = "/api/dashboard?period=7d"
    first = client.get(url, headers=admin)
    second = client.get(url, headers=admin)
    assert first.status_code == second.status_code == 200
    assert second.headers.get("x-cache") == "hit" and second.json() == first.json()

    orders_before = second.json()["kpis"]["current"]["orders"]
    sale = client.post("/api/sales", headers=admin, json={"outlet_id": 1, "items": [{"product_id": 3, "quantity": 1}]})
    assert sale.status_code == 201
    after = client.get(url, headers=admin)
    assert after.headers.get("x-cache") == "miss"
    assert after.json()["kpis"]["current"]["orders"] == orders_before + 1 or after.json()["range"] != second.json()["range"]


def test_answers_are_kept_per_user(client, admin, manager):
    url = "/api/analytics/outlets?period=30d"
    all_outlets = client.get(url, headers=admin).json()
    own_outlet = client.get(url, headers=manager).json()
    assert len(all_outlets["outlets"] if isinstance(all_outlets, dict) else all_outlets) > \
        len(own_outlet["outlets"] if isinstance(own_outlet, dict) else own_outlet)


def test_deactivated_user_gets_nothing_from_the_cache(client, viewer):
    url = "/api/alerts"
    assert client.get(url, headers=viewer).status_code == 200
    assert client.get(url, headers=viewer).headers.get("x-cache") == "hit"
    with SessionLocal() as db:
        db.query(User).filter_by(email="analyst@eris.demo").update({"is_active": False})
        db.commit()
    try:
        assert client.get(url, headers=viewer).status_code == 401
    finally:
        with SessionLocal() as db:
            db.query(User).filter_by(email="analyst@eris.demo").update({"is_active": True})
            db.commit()


def test_exports_and_unauthenticated_requests_are_not_cached(client, admin):
    export = client.get("/api/reports/sales-daily/export?format=csv", headers=admin)
    assert export.status_code == 200 and "x-cache" not in export.headers
    assert client.get("/api/dashboard").status_code == 401


def test_prepared_page_requests_are_valid_for_every_demo_role(client):
    """The Docker build stores the answers to WARM_URLS; each must be a request the app really answers."""
    from app.seed.bake import user_warm_urls
    from app.seed.generator import DEMO_LOGINS, DEMO_PASSWORDS

    for _, email, key, _ in DEMO_LOGINS:
        token = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORDS[key]}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/auth/me", headers=headers).json()
        urls = user_warm_urls(me)
        if me["role"] != "admin" and len(me["outlet_ids"]) == 1:  # the web app pins single-outlet users
            assert all(f"outlet_id={me['outlet_ids'][0]}" in u for u in urls)
        for url in urls:
            r = client.get(url, headers=headers)
            assert r.status_code == 200, (email, url, r.status_code, r.text[:200])
