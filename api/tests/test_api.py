"""End-to-end API tests against a small generated demo database."""
from datetime import date

from app.db import SessionLocal
from app.models import InventoryItem, Product


def stock_of(outlet_id: int, product_id: int) -> float:
    with SessionLocal() as db:
        return db.query(InventoryItem).filter_by(outlet_id=outlet_id, product_id=product_id).one().quantity


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_login_rejects_bad_password(client):
    r = client.post("/api/auth/login", json={"email": "admin@eris.demo", "password": "wrong"})
    assert r.status_code == 401


def test_requires_auth(client):
    assert client.get("/api/dashboard").status_code == 401


def test_dashboard(client, admin):
    r = client.get("/api/dashboard?period=30d", headers=admin)
    assert r.status_code == 200
    d = r.json()
    assert d["kpis"]["current"]["revenue"] > 0
    assert len(d["trend"]) == 30
    assert len(d["outlets"]) == 6
    assert d["forecast"] and len(d["forecast"]["forecast"]) == 14


def test_manager_is_scoped_to_own_outlet(client, manager):
    d = client.get("/api/dashboard", headers=manager).json()
    assert [o["name"] for o in d["outlets"]] == ["Andheri West"]
    assert client.get("/api/sales?outlet_id=2", headers=manager).status_code == 403
    assert client.get("/api/users", headers=manager).status_code == 403


def test_manual_sale_updates_stock_and_void_restores(client, admin):
    product_id = 14  # Toned Milk 1L
    client.post("/api/inventory/adjust", headers=admin,
                json={"outlet_id": 1, "product_id": product_id, "mode": "set", "quantity": 50})
    before = stock_of(1, product_id)
    r = client.post("/api/sales", headers=admin, json={
        "outlet_id": 1, "payment_method": "upi", "customer_phone": "+91 98765 43210", "customer_name": "Test Buyer",
        "items": [{"product_id": product_id, "quantity": 3}, {"product_id": 22, "quantity": 1, "discount": 5}],
        "bill_discount": 10})
    assert r.status_code == 201, r.text
    sale = r.json()
    milk_price = next(i["unit_price"] for i in sale["items"] if i["product_id"] == product_id)
    bread = next(i for i in sale["items"] if i["product_id"] == 22)
    assert sale["subtotal"] == round(3 * milk_price + bread["unit_price"], 2)
    assert sale["discount"] == 15
    assert sale["total"] == round(sale["subtotal"] - 15, 2)
    assert sale["customer"] == "Test Buyer"
    assert stock_of(1, product_id) == before - 3

    r = client.post(f"/api/sales/{sale['id']}/void", headers=admin, json={"reason": "entered twice"})
    assert r.status_code == 200 and r.json()["status"] == "void"
    assert stock_of(1, product_id) == before
    assert client.post(f"/api/sales/{sale['id']}/void", headers=admin, json={"reason": "again"}).status_code == 400


def test_sale_rejects_overselling(client, admin):
    client.post("/api/inventory/adjust", headers=admin,
                json={"outlet_id": 1, "product_id": 5, "mode": "set", "quantity": 2})
    r = client.post("/api/sales", headers=admin, json={"outlet_id": 1, "items": [{"product_id": 5, "quantity": 5}]})
    assert r.status_code == 400 and "Not enough stock" in r.json()["detail"]


def test_credit_sale_needs_customer(client, admin):
    r = client.post("/api/sales", headers=admin,
                    json={"outlet_id": 1, "payment_method": "credit", "items": [{"product_id": 14, "quantity": 1}]})
    assert r.status_code == 400


def test_staff_cannot_backdate(client, staff):
    r = client.post("/api/sales", headers=staff, json={
        "outlet_id": 1, "sold_at": "2024-01-01T10:00:00", "items": [{"product_id": 14, "quantity": 1}]})
    assert r.status_code == 403


def test_transfer_and_movements(client, admin):
    client.post("/api/inventory/adjust", headers=admin, json={"outlet_id": 1, "product_id": 30, "mode": "set", "quantity": 20})
    client.post("/api/inventory/adjust", headers=admin, json={"outlet_id": 2, "product_id": 30, "mode": "set", "quantity": 0})
    r = client.post("/api/inventory/transfer", headers=admin,
                    json={"from_outlet_id": 1, "to_outlet_id": 2, "product_id": 30, "quantity": 8})
    assert r.status_code == 200
    assert stock_of(1, 30) == 12 and stock_of(2, 30) == 8
    moves = client.get("/api/inventory/movements?product_id=30", headers=admin).json()["items"]
    assert {m["reason"] for m in moves[:2]} == {"transfer_in", "transfer_out"}


def test_purchase_order_receive_adds_stock(client, admin):
    client.post("/api/inventory/adjust", headers=admin, json={"outlet_id": 3, "product_id": 36, "mode": "set", "quantity": 4})
    r = client.post("/api/purchase-orders", headers=admin, json={
        "supplier_id": 6, "outlet_id": 3, "items": [{"product_id": 36, "quantity": 10}]})
    assert r.status_code == 201
    po = r.json()
    assert po["status"] == "ordered" and po["total_cost"] > 0
    r = client.post(f"/api/purchase-orders/{po['id']}/receive", headers=admin,
                    json={"items": [{"product_id": 36, "quantity": 9}]})
    assert r.status_code == 200 and r.json()["status"] == "received"
    assert stock_of(3, 36) == 13
    assert client.post(f"/api/purchase-orders/{po['id']}/cancel", headers=admin).status_code == 400


def test_reorder_suggestions_create_pos(client, admin):
    sugg = client.get("/api/inventory/reorder-suggestions", headers=admin).json()
    assert "items" in sugg
    if sugg["items"]:
        line = sugg["items"][0]
        r = client.post("/api/inventory/reorder", headers=admin, json={"lines": [
            {"outlet_id": line["outlet_id"], "product_id": line["product_id"], "quantity": line["suggested_qty"]}]})
        assert r.status_code == 201 and len(r.json()["created"]) == 1


def test_sales_import_dry_run_then_commit(client, admin):
    today = date.today().isoformat()
    csv = ("invoice_no,date,time,outlet_code,sku,quantity,unit_price,discount,payment_method,customer_phone\n"
           f"IMP-1,{today},09:30,MUM-BAN,DAI-001,2,,,upi,9000000001\n"
           f"IMP-1,{today},09:30,MUM-BAN,BAK-002,1,,,upi,9000000001\n"
           f"IMP-2,{today},10:00,Bandra,Cola 750ml,3,45,5,gpay,\n")
    files = {"file": ("sales.csv", csv, "text/csv")}
    r = client.post("/api/imports/sales?dry_run=true", headers=admin, files=files)
    res = r.json()
    assert r.status_code == 200 and res["error_count"] == 0 and res["created"] == 2 and not res["committed"]
    r = client.post("/api/imports/sales?dry_run=false", headers=admin, files={"file": ("sales.csv", csv, "text/csv")})
    assert r.json()["committed"] and r.json()["created"] == 2, r.json()["errors"]
    # importing the same file again is rejected as duplicates and nothing is written
    r = client.post("/api/imports/sales?dry_run=false", headers=admin, files={"file": ("sales.csv", csv, "text/csv")})
    assert not r.json()["committed"] and r.json()["error_count"] == 2


def test_sales_import_reports_row_errors(client, admin):
    csv = "date,outlet_code,sku,quantity\n2026-01-01,NOPE,DAI-001,1\nnot-a-date,MUM-AND,DAI-001,1\n2026-01-01,MUM-AND,XXX,1\n"
    res = client.post("/api/imports/sales", headers=admin, files={"file": ("s.csv", csv, "text/csv")}).json()
    assert res["error_count"] == 3
    assert {e["row"] for e in res["errors"]} == {2, 3, 4}


def test_product_and_customer_import(client, admin):
    products = "sku,name,category,unit,cost_price,selling_price,tax_rate\nNEW-001,Test Granola 500g,Breakfast,pack,150,240,12\n"
    r = client.post("/api/imports/products?dry_run=false", headers=admin, files={"file": ("p.csv", products, "text/csv")})
    assert r.json()["created"] == 1
    with SessionLocal() as db:
        assert db.query(Product).filter_by(sku="NEW-001").one().category.name == "Breakfast"
    customers = "name,phone,city\nRita Sen,9811122233,Pune\nBad Phone,123,Pune\n"
    r = client.post("/api/imports/customers?dry_run=false", headers=admin, files={"file": ("c.csv", customers, "text/csv")})
    assert r.json()["error_count"] == 1 and not r.json()["committed"]


def test_import_template_download(client):
    r = client.get("/api/imports/templates/sales")
    assert r.status_code == 200 and r.text.startswith("invoice_no,date")


def test_forecast_endpoints(client, admin):
    r = client.get("/api/forecast?scope=total&horizon=14", headers=admin)
    assert r.status_code == 200, r.text
    fc = r.json()
    assert len(fc["forecast"]) == 14
    assert all(f["lower"] <= f["yhat"] <= f["upper"] for f in fc["forecast"])
    assert sum(1 for e in fc["evaluation"] if e.get("selected")) == 1
    r = client.get("/api/forecast?scope=product&target_id=14&horizon=30", headers=admin)
    assert r.status_code == 200 and "stock_plan" in r.json()
    assert client.get("/api/forecast?scope=product&target_id=99999", headers=admin).status_code == 404


def test_analytics_endpoints(client, admin):
    for path in ("sales", "products", "outlets", "customers"):
        r = client.get(f"/api/analytics/{path}?period=90d", headers=admin)
        assert r.status_code == 200, (path, r.text)
    abc = client.get("/api/analytics/products", headers=admin).json()
    assert abs(sum(v["share_pct"] for v in abc["summary"].values()) - 100) < 0.5


def test_crud_outlet_product_supplier_customer(client, admin):
    r = client.post("/api/outlets", headers=admin, json={"code": "tst-01", "name": "Test Outlet", "city": "Nagpur"})
    assert r.status_code == 201 and r.json()["code"] == "TST-01"
    assert client.post("/api/outlets", headers=admin, json={"code": "TST-01", "name": "Dup", "city": "Pune"}).status_code == 409
    r = client.post("/api/suppliers", headers=admin, json={"name": "Test Supplier", "lead_time_days": 2})
    assert r.status_code == 201
    r = client.post("/api/products", headers=admin, json={
        "sku": "tst-sku", "name": "Test Product", "category_id": 1, "supplier_id": r.json()["id"],
        "cost_price": 10, "selling_price": 15, "tax_rate": 5})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert client.delete(f"/api/products/{pid}", headers=admin).json()["deleted"]
    r = client.post("/api/customers", headers=admin, json={"name": "New Person", "phone": "9123456780"})
    assert r.status_code == 201
    assert client.post("/api/customers", headers=admin, json={"name": "Dup", "phone": "+919123456780"}).status_code == 409


def test_user_management(client, admin):
    r = client.post("/api/users", headers=admin, json={"email": "new.staff@eris.demo", "full_name": "New Staff",
                                                         "role": "staff", "outlet_id": 2, "password": "Password1"})
    assert r.status_code == 201
    r = client.post("/api/users", headers=admin, json={"email": "x@eris.demo", "full_name": "No Outlet",
                                                         "role": "manager", "password": "Password1"})
    assert r.status_code == 400


def test_assistant_answers_core_questions(client, admin):
    cases = {
        "How much did we sell yesterday?": "sales_summary",
        "Top 5 products this week": "top_products",
        "Which outlet performed best last month?": "outlet_ranking",
        "Forecast sales for next week": "forecast",
        "What should I reorder?": "reorder",
        "Which customers are at risk?": "customers",
        "When are our busiest hours?": "peak_hours",
        "Which products are bought together?": "basket_analysis",
        "How can I increase sales?": "advice",
        "Compare this month with last month": "compare_periods",
        "stock of eggs": "stock_status",
        "hello": "help",
    }
    for q, intent in cases.items():
        r = client.post("/api/assistant/chat", headers=admin, json={"message": q})
        assert r.status_code == 200, q
        body = r.json()
        assert body["intent"] == intent, (q, body["intent"])
        assert body["answer"]
    # follow-up keeps the previous intent but switches outlet
    client.post("/api/assistant/chat", headers=admin, json={"message": "Revenue at Bandra last month"})
    r = client.post("/api/assistant/chat", headers=admin, json={"message": "what about Pune?"}).json()
    assert r["intent"] == "sales_summary" and "Koregaon Park" in r["answer"]
    history = client.get("/api/assistant/history", headers=admin).json()
    assert len(history) >= 2


def test_assistant_uses_llm_when_rules_are_unsure(client, admin, monkeypatch):
    """With a local LLM available, low-confidence questions are routed through it (mocked here)."""
    from app.services.assistant import llm

    monkeypatch.setattr(llm, "status", lambda force=False: {"available": True, "model": "mock", "provider": "ollama", "error": None})
    monkeypatch.setattr(llm, "classify", lambda q, o, c: {"intent": "top_products", "period": "last 7 days", "outlets": ["Bandra"],
                                                          "category": None, "product": None, "top_n": 3, "horizon_days": None})
    monkeypatch.setattr(llm, "general_answer", lambda q, facts, org: "Mocked advice")
    r = client.post("/api/assistant/chat", headers=admin, json={"message": "gimme the stars of bandra lately"}).json()
    assert r["engine"] == "rules+llm" and r["intent"] == "top_products"
    assert "Bandra" in r["answer"] and "last 7 days" in r["answer"]
    r = client.post("/api/assistant/chat", headers=admin, json={"message": "tell me a joke"}).json()
    assert r["intent"] in ("general", "top_products")


def test_auto_refresh_shifts_stale_demo(seeded):
    from datetime import timedelta

    from sqlalchemy import func, select

    from app.models import Sale
    from app.seed.refresh import is_untouched_demo

    with SessionLocal() as db:
        # the test database has manual/imported sales by now, so real data must never be shifted
        assert not is_untouched_demo(db)
        assert db.scalar(select(func.max(Sale.sale_date))) >= date.today() - timedelta(days=1)


def test_login_lockout_after_repeated_failures(client):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"email": "locked@eris.demo", "password": "nope"}).status_code == 401
    r = client.post("/api/auth/login", json={"email": "locked@eris.demo", "password": "nope"})
    assert r.status_code == 429
