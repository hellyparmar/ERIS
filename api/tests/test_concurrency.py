"""Simultaneous requests: no overselling, no lost stock updates, no number clashes (SQLite and PostgreSQL)."""
from concurrent.futures import ThreadPoolExecutor

from app.db import SessionLocal
from app.models import InventoryItem


def _stock(outlet_id: int, product_id: int) -> float:
    with SessionLocal() as db:
        return db.query(InventoryItem).filter_by(outlet_id=outlet_id, product_id=product_id).one().quantity


def test_simultaneous_sales_of_the_last_units(client, admin):
    product, outlet = 30, 2
    client.post("/api/inventory/adjust", headers=admin, json={"outlet_id": outlet, "product_id": product, "mode": "set", "quantity": 3})

    def sell(_):
        body = {"outlet_id": outlet, "items": [{"product_id": product, "quantity": 1}]}
        return client.post("/api/sales", headers=admin, json=body).status_code

    with ThreadPoolExecutor(8) as pool:
        codes = sorted(pool.map(sell, range(8)))
    assert codes.count(201) == 3 and codes.count(400) == 5, codes
    assert _stock(outlet, product) == 0


def test_simultaneous_numbering(client, admin):
    product, outlet = 30, 2
    client.post("/api/inventory/adjust", headers=admin, json={"outlet_id": outlet, "product_id": product, "mode": "set", "quantity": 50})

    def sell(_):
        r = client.post("/api/sales", headers=admin, json={"outlet_id": outlet, "items": [{"product_id": product, "quantity": 1}]})
        return r.status_code, r.json().get("id")

    def order(_):
        return client.post("/api/purchase-orders", headers=admin, json={"supplier_id": 1, "outlet_id": outlet,
                                                                       "items": [{"product_id": product, "quantity": 2}]}).status_code

    with ThreadPoolExecutor(12) as pool:
        sales = list(pool.map(sell, range(12)))
        pos = list(pool.map(order, range(12)))
    assert all(code == 201 for code, _ in sales) and all(code == 201 for code in pos), (sales, pos)
    assert _stock(outlet, product) == 38

    def invoice(sale_id):
        return client.post("/api/invoices", headers=admin, json={"sale_id": sale_id}).status_code

    ids = [sid for _, sid in sales]
    with ThreadPoolExecutor(12) as pool:
        codes = list(pool.map(invoice, ids + [ids[0]] * 3))
    assert codes.count(201) == 12 and codes.count(200) == 3, codes
    numbers = {i["number"] for i in client.get("/api/invoices?page_size=200", headers=admin).json()["items"]}
    assert len(numbers) >= 12


def test_forecasts_are_saved_while_sales_are_written(client, admin):
    """A forecast (a GET) saves its run even when other requests write at the same moment."""
    product, outlet = 30, 2
    client.post("/api/inventory/adjust", headers=admin, json={"outlet_id": outlet, "product_id": product, "mode": "set", "quantity": 50})

    def sell(_):
        body = {"outlet_id": outlet, "items": [{"product_id": product, "quantity": 1}]}
        return client.post("/api/sales", headers=admin, json=body).status_code

    def forecast(horizon):
        r = client.get(f"/api/forecast?scope=outlet&target_id={outlet}&horizon={horizon}&model=seasonal_naive", headers=admin)
        return r.status_code, r.json().get("run_id")

    with ThreadPoolExecutor(8) as pool:
        sales = pool.map(sell, range(8))
        runs = pool.map(forecast, range(7, 15))
        sales, runs = list(sales), list(runs)
    assert all(code == 201 for code in sales), sales
    assert all(code == 200 and run_id for code, run_id in runs), runs
