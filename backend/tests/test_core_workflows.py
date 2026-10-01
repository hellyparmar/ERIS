"""Regression tests for the portfolio-critical write workflows."""

from decimal import Decimal

from app.models.customers import Customer
from app.models.inventory import Inventory
from app.models.commerce import Product, ProductCategory, Sale, StockMovement
from app.models.outlet import Outlet


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _catalog(db):
    outlet = Outlet(organization_id=1, name="Workflow Outlet", city="Pune", is_active=True)
    category = ProductCategory(id=101, organization_id=1, name="Workflow Food", default_gst_rate=Decimal("5"))
    product = Product(
        id=101,
        organization_id=1,
        category_id=101,
        sku="TEST-WORKFLOW-101",
        name="Workflow Product",
        cost_price=Decimal("40"),
        selling_price=Decimal("100"),
        reorder_level=5,
        reorder_quantity=10,
    )
    customer = Customer(organization_id=1, first_name="Test", last_name="Buyer", phone="7000000101")
    db.add_all([outlet, category, product, customer])
    db.commit()
    db.refresh(outlet)
    db.refresh(customer)
    inventory = Inventory(
        organization_id=1, outlet_id=outlet.id, product_id=product.id, current_stock=20, reserved_stock=0
    )
    db.add(inventory)
    db.commit()
    return outlet, product, customer, inventory


def test_manual_sale_updates_inventory_and_customer(client, admin_token, db):
    outlet, product, customer, inventory = _catalog(db)
    response = client.post(
        "/api/v1/sales/",
        headers=_headers(admin_token),
        json={
            "outlet_id": outlet.id,
            "customer_id": customer.id,
            "discount": 10,
            "tax_amount": 9.5,
            "payment_method": "upi",
            "items": [{"product_id": product.id, "quantity": 2}],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["total_amount"] == "199.50"
    db.expire_all()
    assert db.get(Inventory, inventory.id).current_stock == 18
    saved_customer = db.get(Customer, customer.id)
    assert saved_customer.total_transactions == 1
    assert saved_customer.total_purchases == Decimal("199.50")
    movement = db.query(StockMovement).one()
    assert (movement.quantity, movement.stock_before, movement.stock_after) == (-2, 20, 18)


def test_csv_sales_import_persists_valid_rows(client, admin_token, db):
    outlet, product, _, inventory = _catalog(db)
    csv_text = (
        "sale_date,outlet_id,product_id,quantity,unit_price,payment_method,channel\n"
        f"2026-01-15,{outlet.id},{product.id},3,100,cash,offline\n"
    )
    response = client.post(
        "/api/v1/data/upload/sales",
        headers=_headers(admin_token),
        files={"file": ("sales.csv", csv_text, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"rows_processed": 1, "validation_errors": [], "status": "success"}
    db.expire_all()
    assert db.get(Inventory, inventory.id).current_stock == 17
    assert db.query(Sale).count() == 1
    assert db.query(StockMovement).one().notes == "CSV sales import"


def test_product_creation_and_adjustment_history(client, admin_token, db):
    outlet = Outlet(organization_id=1, name="New Product Outlet", city="Pune", is_active=True)
    db.add(outlet)
    db.commit()
    db.refresh(outlet)

    created = client.post(
        "/api/v1/inventory/create",
        headers=_headers(admin_token),
        json={
            "name": "New Portfolio Product",
            "category": "New Category",
            "sku": "TEST-NEW-PRODUCT",
            "unit_price": 125,
            "cost_price": 70,
            "current_stock": 12,
            "reorder_point": 4,
            "outlet_id": outlet.id,
        },
    )
    assert created.status_code == 201, created.text
    inventory_id = created.json()["inventory_id"]

    adjusted = client.put(
        f"/api/v1/inventory/{inventory_id}",
        headers=_headers(admin_token),
        json={"quantity": 18, "reason": "Received Shipment", "notes": "Test delivery"},
    )
    assert adjusted.status_code == 200, adjusted.text

    history = client.get(f"/api/v1/inventory/{inventory_id}/movement", headers=_headers(admin_token))
    assert history.status_code == 200, history.text
    assert [(row["type"], row["stock_after"]) for row in history.json()] == [
        ("adjustment", 18),
        ("purchase", 12),
    ]


def test_invoice_and_supplier_creation_are_persistent(client, admin_token, db):
    outlet, product, customer, _ = _catalog(db)
    invoice_response = client.post(
        "/api/v1/gst/invoices",
        headers=_headers(admin_token),
        json={
            "outlet_id": outlet.id,
            "customer_id": customer.id,
            "discount": 10,
            "items": [
                {"product_id": product.id, "description": product.name, "quantity": 2, "unit_price": 100, "gst_rate": 5}
            ],
        },
    )
    assert invoice_response.status_code == 201, invoice_response.text
    assert invoice_response.json()["total"] == 199.5

    supplier_response = client.post(
        "/api/v1/suppliers/",
        headers=_headers(admin_token),
        json={"name": "Test Supplier", "city": "Pune", "payment_terms_days": 30},
    )
    assert supplier_response.status_code == 201, supplier_response.text
    assert supplier_response.json()["data"]["name"] == "Test Supplier"


def test_viewer_cannot_mutate_inventory(client, seed_users, db):
    """The canonical viewer role is read-only for inventory writes."""
    from app.core.security import create_access_token

    outlet, _, _, inventory = _catalog(db)
    viewer = seed_users[2]
    token = create_access_token({"sub": viewer.username, "role": "viewer"})

    response = client.put(
        f"/api/v1/inventory/{inventory.id}",
        headers=_headers(token),
        json={"quantity": 999},
    )
    assert response.status_code == 403
    db.expire_all()
    assert db.get(Inventory, inventory.id).current_stock == 20


def test_inventory_alert_generation_and_acknowledgement(client, admin_token, db):
    """Low-stock alerts are persisted, listed with UUIDs, and acknowledgeable."""
    _, _, _, inventory = _catalog(db)
    inventory.current_stock = 2
    db.commit()

    generated = client.post("/api/v1/alerts/generate-inventory-alerts", headers=_headers(admin_token))
    assert generated.status_code == 200, generated.text
    assert generated.json()["alerts_created"] == 1

    listing = client.get("/api/v1/alerts/list?unread_only=true", headers=_headers(admin_token))
    assert listing.status_code == 200, listing.text
    item = listing.json()["items"][0]
    assert item["alert_type"] == "low_stock"
    assert item["current_stock"] == 2

    acknowledged = client.patch(f"/api/v1/alerts/{item['id']}/acknowledge", headers=_headers(admin_token))
    assert acknowledged.status_code == 200, acknowledged.text

    unread = client.get("/api/v1/alerts/list?unread_only=true", headers=_headers(admin_token))
    assert unread.json()["items"] == []
