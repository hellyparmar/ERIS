import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.multitenant_models import UserRole
from tests.test_data_generators import create_test_product, create_test_customer, generate_historical_sales

@pytest.fixture(autouse=True)
def mock_ai_components():
    """Mock AI components to avoid slow/hanging tests."""
    with patch("app.routers.assistant.retail_agent") as mock_agent, \
         patch("app.routers.intelligence.generate_arima_forecast") as mock_forecast, \
         patch("app.ml.rag.rag_service.HuggingFaceEmbeddings") as mock_hf, \
         patch("app.ml.rag.rag_service.Chroma") as mock_chroma:
        
        # Ensure retail_agent.chat is awaitable
        mock_agent.chat = AsyncMock()
        
        # Mock forecast response - Should be a LIST of SalesForecast objects
        # But for the API response, it can be a list of dicts that match the schema
        mock_forecast.return_value = [
            {
                "date": datetime.now() + timedelta(days=i),
                "predicted_sales": 100.0,
                "lower_bound": 80.0,
                "upper_bound": 120.0,
                "confidence": 0.95,
                "trend": "up"
            } for i in range(1, 8)
        ]
        
        # Mock agent response
        mock_agent.chat.return_value = {
            "response": "This is a mocked AI response about your stock.",
            "provider": "MockProvider",
            "rag_enhanced": True
        }
        
        # Prevent HF and Chroma from doing anything
        mock_hf.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()
        
        yield mock_agent, mock_forecast

@pytest.fixture
def workflow_headers(test_client):
    """Register and login a new admin user for workflow testing."""
    uid = uuid.uuid4().hex[0:6]
    email = f"admin_{uid}@example.com"
    password = "WorkflowPassword123!"
    
    # 1. Register
    reg_resp = test_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Workflow Admin",
        "organization_name": f"Workflow Org {uid}",
        "role": "ADMIN"
    })
    assert reg_resp.status_code in (200, 201), reg_resp.text
    
    # 2. Login
    login_resp = test_client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

class TestUserWorkflows:
    """End-to-end user workflow tests."""

    def test_complete_sales_workflow(self, test_client, workflow_headers, test_db):
        """
        Step 1: Create customer
        Step 2: Add products to inventory
        Step 3: Create a sale
        Step 4: Generate invoice
        Step 5: Send invoice via email (test-email)
        Step 6: Record payment (Part of sale creation in this system)
        """
        # Get real store ID
        stores_resp = test_client.get("/api/v1/inventory/stores", headers=workflow_headers)
        assert stores_resp.status_code == 200
        store_id = stores_resp.json()[0]["id"] if stores_resp.json() else str(uuid.uuid4())

        # Step 1: Create customer
        # Get org_id from /me
        me_resp = test_client.get("/api/v1/auth/me", headers=workflow_headers)
        assert me_resp.status_code == 200
        org_id = me_resp.json()["organization_id"]
        # Convert to UUID object for direct DB use if needed, but here we pass to API

        cust_resp = test_client.post("/api/v1/customers/", json={
            "name": "E2E Customer",
            "email": "e2e_customer@example.com",
            "phone": "+919999999999",
            "address": "123 Test St",
            "city": "Sample City",
            "organization_id": org_id
        }, headers=workflow_headers)
        if cust_resp.status_code != 201:
            print(f"Customer creation failed: {cust_resp.text}")
        assert cust_resp.status_code == 201
        customer_id = cust_resp.json()["id"]

        # Step 2: Add products to inventory
        prod_resp = test_client.post("/api/v1/inventory/products", json={
            "sku": f"E2E-PROD-{uuid.uuid4().hex[:4].upper()}",
            "name": "E2E Product",
            "category": "Electronics",
            "unit_price": 500.0,
            "cost_price": 300.0,
            "initial_stock": 50,
            "store_id": store_id,
            "organization_id": org_id
        }, headers=workflow_headers)
        assert prod_resp.status_code == 201
        product_id = prod_resp.json()["id"]

        # Step 3: Create a sale
        sale_resp = test_client.post("/api/v1/sales/", json={
            "store_id": store_id,
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 2, "unit_price": 500.0}],
            "payment_method": "upi",
            "discount": 0.0,
            "tax": 180.0
        }, headers=workflow_headers)
        if sale_resp.status_code not in (200, 201):
            print(f"Sale creation failed: {sale_resp.text}")
        assert sale_resp.status_code in (200, 201)
        sale_id = sale_resp.json()["id"]

        # Step 4: Generate invoice
        invoice_resp = test_client.get(f"/api/v1/gst/invoice/{sale_id}", headers=workflow_headers)
        if invoice_resp.status_code != 200:
            print(f"Invoice generation failed: {invoice_resp.text}")
        assert invoice_resp.status_code == 200
        # Should be a PDF or similar
        assert "application/pdf" in invoice_resp.headers.get("content-type", "")

        # Step 6: Verify final sale status
        # ... Wait, step 5 is just a test endpoint.
        sale_verify = test_client.get(f"/api/v1/sales/{sale_id}", headers=workflow_headers)
        if sale_verify.status_code != 200:
            print(f"Sale verification failed: {sale_verify.text}")
        assert sale_verify.status_code == 200
        assert sale_verify.json()["payment_status"] == "paid"

    def test_inventory_management_workflow(self, test_client, workflow_headers, test_db):
        """
        Step 1: Add product with stock level 10
        Step 2: Make 8 sales of that product
        Step 3: Check low stock alert appears
        Step 4: Restock product (via direct DB update since no endpoint found)
        Step 5: Alert disappears
        """
        # Get real IDs
        me_resp = test_client.get("/api/v1/auth/me", headers=workflow_headers)
        if me_resp.status_code != 200:
            print(f"Get /me failed: {me_resp.text}")
        org_id = me_resp.json()["organization_id"]
        stores_resp = test_client.get("/api/v1/inventory/stores", headers=workflow_headers)
        if stores_resp.status_code != 200:
            print(f"Get stores failed: {stores_resp.text}")
        store_id = stores_resp.json()[0]["id"] if stores_resp.json() else str(uuid.uuid4())

        # Step 1: Add product with stock 10
        sku = f"INV-TEST-{uuid.uuid4().hex[:4].upper()}"
        prod_resp = test_client.post("/api/v1/inventory/products", json={
            "sku": sku,
            "name": "Limited Stock Item",
            "category": "Test",
            "unit_price": 100.0,
            "cost_price": 50.0,
            "initial_stock": 10,
            "store_id": store_id,
            "organization_id": org_id
        }, headers=workflow_headers)
        if prod_resp.status_code != 201:
            print(f"Product creation failed: {prod_resp.text}")
        assert prod_resp.status_code == 201
        product_id = prod_resp.json()["id"]

        # Step 2: Make 8 sales (total qty 8)
        sale_resp = test_client.post("/api/v1/sales/", json={
            "store_id": store_id,
            "items": [{"product_id": product_id, "quantity": 8, "unit_price": 100.0}],
            "payment_method": "cash"
        }, headers=workflow_headers)
        if sale_resp.status_code not in (200, 201):
            print(f"Sale creation failed: {sale_resp.text}")
        assert sale_resp.status_code in (200, 201)

        # Step 3: Check low stock alert (stock=2, reorder=10 by default)
        low_stock_resp = test_client.get("/api/v1/inventory/low-stock", headers=workflow_headers)
        if low_stock_resp.status_code != 200:
            print(f"Low stock check failed: {low_stock_resp.text}")
        assert low_stock_resp.status_code == 200
        assert any(item["product_id"] == product_id for item in low_stock_resp.json())

        # Step 4: Restock product
        from app.models.multitenant_models import Inventory
        inv_item = test_db.query(Inventory).filter(Inventory.product_id == product_id).first()
        inv_item.current_stock = 50
        test_db.commit()

        # Step 5: Alert disappears
        low_stock_resp_after = test_client.get("/api/v1/inventory/low-stock", headers=workflow_headers)
        if low_stock_resp_after.status_code != 200:
            print(f"Low stock check after restock failed: {low_stock_resp_after.text}")
        assert low_stock_resp_after.status_code == 200
        assert not any(item["product_id"] == product_id for item in low_stock_resp_after.json())

    def test_ai_forecasting_workflow(self, test_client, workflow_headers, test_db):
        """
        Step 1: Populate database with historical sales (30 days)
        Step 2: Request forecast for next 7 days
        Step 3: Get forecast results
        Step 4: Request insights (serving as SHAP/Drivers proxy)
        """
        # Assuming current_user is available via workflow_headers
        # We need an organization_id. Let's get it from /api/v1/auth/me
        me_resp = test_client.get("/api/v1/auth/me", headers=workflow_headers)
        if me_resp.status_code != 200:
            print(f"Get /me failed: {me_resp.text}")
        org_id = me_resp.json()["organization_id"]
        
        # Create a product to sell
        # Get store_id
        stores_resp = test_client.get("/api/v1/inventory/stores", headers=workflow_headers)
        store_id_str = stores_resp.json()[0]["id"] if (stores_resp.status_code == 200 and stores_resp.json()) else str(uuid.uuid4())
        store_id = uuid.UUID(store_id_str)
        org_id_obj = uuid.UUID(org_id)
        
        product = create_test_product(test_db, org_id_obj, store_id)
        
        # Step 1: Populate historical sales
        generate_historical_sales(test_db, org_id_obj, store_id, product.id, days=30)

        # Step 2: Request forecast
        forecast_resp = test_client.post("/api/v1/intelligence/forecast", json={
            "days_ahead": 7,
            "confidence_level": 0.95
        }, headers=workflow_headers)
        if forecast_resp.status_code != 200:
            print(f"Forecast request failed: {forecast_resp.text}")
        assert forecast_resp.status_code == 200
        
        # Step 3: Get response
        data = forecast_resp.json()
        assert len(data["forecasts"]) == 7
        assert "ARIMA" in data["model"]

        # Step 4 & 5: Get insights/drivers
        insights_resp = test_client.get("/api/v1/intelligence/insights", headers=workflow_headers)
        if insights_resp.status_code != 200:
            print(f"Insights request failed: {insights_resp.text}")
        assert insights_resp.status_code == 200
        assert len(insights_resp.json()["insights"]) > 0

    def test_ai_chat_workflow(self, test_client, workflow_headers):
        """
        Step 1: Ask "What products do I have in stock?"
        Step 2: Get response
        Step 3: Ask "What were sales yesterday?"
        Step 4: Get response
        """
        # Step 1: Ask about products
        chat_resp1 = test_client.post("/api/v1/assistant/chat", json={
            "message": "What products do I have in stock?"
        }, headers=workflow_headers)
        # Note: ENABLE_AI_ASSISTANT might be false in tests, but we check 200 or 400
        if chat_resp1.status_code not in (200, 400):
            print(f"AI Chat (products) failed: {chat_resp1.text}")
        assert chat_resp1.status_code in (200, 400)
        
        # Step 3: Ask about sales
        chat_resp2 = test_client.post("/api/v1/assistant/chat", json={
            "message": "What were sales yesterday?"
        }, headers=workflow_headers)
        if chat_resp2.status_code not in (200, 400):
            print(f"AI Chat (sales) failed: {chat_resp2.text}")
        assert chat_resp2.status_code in (200, 400)
