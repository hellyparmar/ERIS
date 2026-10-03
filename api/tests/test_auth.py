"""Sessions (refresh-token rotation and revocation), multi-outlet managers, the outlet cap and role limits."""
from app.seed.generator import DEMO_PASSWORDS


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def test_refresh_rotates_and_logout_all_revokes(client):
    s = _login(client, "staff.andheri@eris.demo", DEMO_PASSWORDS["staff"])
    assert s["refresh_token"] and s["access_token"]
    # an access token cannot be used as a refresh token and vice versa
    assert client.post("/api/auth/refresh", json={"refresh_token": s["access_token"]}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {s['refresh_token']}"}).status_code == 401
    r = client.post("/api/auth/refresh", json={"refresh_token": s["refresh_token"]})
    assert r.status_code == 200 and r.json()["user"]["email"] == "staff.andheri@eris.demo"
    new = r.json()
    headers = {"Authorization": f"Bearer {new['access_token']}"}
    assert client.post("/api/auth/logout-all", headers=headers).json()["ok"]
    for token in (s["refresh_token"], new["refresh_token"]):
        assert client.post("/api/auth/refresh", json={"refresh_token": token}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": "garbage"}).status_code == 401


def test_area_manager_sees_both_outlets(client):
    s = _login(client, "arjun.ind@eris.demo", DEMO_PASSWORDS["manager"])
    assert sorted(s["user"]["outlet_names"]) == ["Indiranagar", "Whitefield"]
    h = {"Authorization": f"Bearer {s['access_token']}"}
    names = {o["name"] for o in client.get("/api/dashboard", headers=h).json()["outlets"]}
    assert names == {"Indiranagar", "Whitefield"}
    ids = s["user"]["outlet_ids"]
    for oid in ids:
        assert client.get(f"/api/sales?outlet_id={oid}", headers=h).status_code == 200
    assert client.get("/api/sales?outlet_id=1", headers=h).status_code == 403


def test_user_with_several_outlets_and_viewer_role(client, admin):
    r = client.post("/api/users", headers=admin, json={"email": "multi@eris.demo", "full_name": "Multi Outlet",
                                                         "role": "viewer", "outlet_ids": [1, 2], "password": "Password1"})
    assert r.status_code == 201, r.text
    assert sorted(r.json()["outlet_ids"]) == [1, 2]
    uid = r.json()["id"]
    r = client.patch(f"/api/users/{uid}", headers=admin, json={"outlet_ids": [3]})
    assert r.status_code == 200 and r.json()["outlet_ids"] == [3]
    r = client.post("/api/users", headers=admin, json={"email": "bad@eris.demo", "full_name": "Bad", "role": "staff",
                                                         "outlet_ids": [999], "password": "Password1"})
    assert r.status_code in (400, 404, 422)


def test_outlet_cap(client, admin):
    existing = len(client.get("/api/outlets", headers=admin).json())
    created = []
    for i in range(7 - existing):
        r = client.post("/api/outlets", headers=admin, json={"code": f"CAP-{i}", "name": f"Cap {i}", "city": "Nagpur"})
        assert r.status_code == 201, r.text
        created.append(r.json()["id"])
    r = client.post("/api/outlets", headers=admin, json={"code": "CAP-X", "name": "One too many", "city": "Nagpur"})
    assert r.status_code == 400 and "7" in r.json()["detail"]
    for oid in created:  # leave the other tests' world as it was
        client.delete(f"/api/outlets/{oid}", headers=admin)


def test_viewer_cannot_change_settings_or_stock(client, viewer):
    assert client.post("/api/inventory/adjust", headers=viewer, json={"outlet_id": 1, "product_id": 14, "mode": "set",
                                                                       "quantity": 5}).status_code == 403
    assert client.put("/api/settings/organization", headers=viewer, json={"name": "X"}).status_code in (403, 405)
    assert client.post("/api/imports/sales", headers=viewer,
                       files={"file": ("s.csv", "date,outlet_code,sku,quantity\n", "text/csv")}).status_code == 403


def test_demo_accounts_listed_only_while_they_use_the_published_passwords(client):
    from app.db import SessionLocal
    from app.models import User
    from app.security import hash_password

    accounts = client.get("/api/auth/demo-accounts").json()
    assert [a["email"] for a in accounts][:2] == ["admin@eris.demo", "priya.and@eris.demo"] and len(accounts) == 5
    assert all(client.post("/api/auth/login", json={"email": a["email"], "password": a["password"]}).status_code == 200
               for a in accounts)

    with SessionLocal() as db:  # the analyst changes their password: the shortcut disappears
        user = db.query(User).filter_by(email="analyst@eris.demo").one()
        original, user.password_hash = user.password_hash, hash_password("a-private-password")
        db.commit()
    try:
        assert "analyst@eris.demo" not in {a["email"] for a in client.get("/api/auth/demo-accounts").json()}
    finally:
        with SessionLocal() as db:
            db.query(User).filter_by(email="analyst@eris.demo").update({"password_hash": original})
            db.commit()
    assert len(client.get("/api/auth/demo-accounts").json()) == 5
