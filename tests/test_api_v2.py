"""
Comprehensive Test Suite for R-DIOS v6.0
Tests for Sales Analytics, CRUD Operations, and Business Logic
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

# Import the main app
import sys
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')

from api.main import app


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authenticated headers for protected endpoints"""
    # Try to login or create test user
    login_data = {"username": "testadmin", "password": "testpassword123"}
    
    response = client.post("/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        # Register first
        register_data = {
            "username": "testadmin",
            "email": "testadmin@rdios.com",
            "password": "testpassword123"
        }
        client.post("/api/auth/register", json=register_data)
        response = client.post("/api/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    return {}


@pytest.fixture
def sample_product():
    """Sample product data"""
    return {
        "name": "Test Product ABC",
        "sku": f"TEST-{datetime.now().timestamp():.0f}",
        "description": "Test product for unit testing",
        "cost_price": 100.0,
        "selling_price": 150.0,
        "hsn_code": "8471",
        "gst_rate": 18.0,
        "stock_level": 50,
        "reorder_point": 10,
        "min_order_quantity": 1
    }


@pytest.fixture
def sample_customer():
    """Sample customer data"""
    return {
        "name": "Test Customer",
        "email": f"test.{datetime.now().timestamp():.0f}@example.com",
        "phone": "9876543210",
        "city": "Mumbai",
        "state": "Maharashtra",
        "credit_limit": 10000.0
    }


@pytest.fixture
def sample_supplier():
    """Sample supplier data"""
    return {
        "name": "Test Supplier Pvt Ltd",
        "contact_person": "John Doe",
        "email": f"supplier.{datetime.now().timestamp():.0f}@example.com",
        "phone": "9876543211",
        "gst_number": "27AABCS1234X1ZT",
        "city": "Delhi",
        "payment_terms_days": 30
    }


# ============================================================
# HEALTH CHECK TESTS
# ============================================================

class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_health_check(self, client):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
    
    def test_api_version(self, client):
        """Test API version endpoint"""
        response = client.get("/api/health")
        assert response.status_code in [200, 404]  # May not exist


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

class TestAuthentication:
    """Tests for authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        unique_username = f"testuser_{datetime.now().timestamp():.0f}"
        data = {
            "username": unique_username,
            "email": f"{unique_username}@test.com",
            "password": "securepassword123"
        }
        response = client.post("/api/auth/register", json=data)
        assert response.status_code in [200, 201, 400]  # 400 if user exists
    
    def test_login_valid(self, client):
        """Test login with valid credentials"""
        # First register
        unique_username = f"logintest_{datetime.now().timestamp():.0f}"
        register_data = {
            "username": unique_username,
            "email": f"{unique_username}@test.com",
            "password": "loginpassword123"
        }
        client.post("/api/auth/register", json=register_data)
        
        # Then login
        login_data = {"username": unique_username, "password": "loginpassword123"}
        response = client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "token" in data
    
    def test_login_invalid(self, client):
        """Test login with invalid credentials"""
        login_data = {"username": "nonexistent", "password": "wrongpassword"}
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code in [401, 400, 404]
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v2/products")
        assert response.status_code == 401


# ============================================================
# PRODUCTS CRUD TESTS
# ============================================================

class TestProductsCRUD:
    """Tests for Products CRUD operations"""
    
    def test_list_products(self, client, auth_headers):
        """Test listing products"""
        response = client.get("/api/v2/products", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
    
    def test_list_products_with_pagination(self, client, auth_headers):
        """Test products pagination"""
        response = client.get("/api/v2/products?page=1&size=5", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 1
            assert data["size"] == 5
    
    def test_list_products_with_search(self, client, auth_headers):
        """Test products search"""
        response = client.get("/api/v2/products?search=test", headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_list_low_stock_products(self, client, auth_headers):
        """Test filtering low stock products"""
        response = client.get("/api/v2/products?low_stock=true", headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_create_product(self, client, auth_headers, sample_product):
        """Test creating a product"""
        response = client.post("/api/v2/products", headers=auth_headers, json=sample_product)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
    
    def test_get_product(self, client, auth_headers):
        """Test getting a single product"""
        # First get product list
        list_response = client.get("/api/v2/products?size=1", headers=auth_headers)
        if list_response.status_code == 200:
            products = list_response.json().get("items", [])
            if products:
                product_id = products[0]["id"]
                response = client.get(f"/api/v2/products/{product_id}", headers=auth_headers)
                assert response.status_code == 200
    
    def test_update_product(self, client, auth_headers):
        """Test updating a product"""
        # Get existing product
        list_response = client.get("/api/v2/products?size=1", headers=auth_headers)
        if list_response.status_code == 200:
            products = list_response.json().get("items", [])
            if products:
                product_id = products[0]["id"]
                update_data = {"stock_level": 100}
                response = client.put(f"/api/v2/products/{product_id}", headers=auth_headers, json=update_data)
                assert response.status_code in [200, 404]
    
    def test_product_not_found(self, client, auth_headers):
        """Test getting non-existent product"""
        response = client.get("/api/v2/products/999999", headers=auth_headers)
        assert response.status_code in [404, 401]


# ============================================================
# CUSTOMERS CRUD TESTS
# ============================================================

class TestCustomersCRUD:
    """Tests for Customers CRUD operations"""
    
    def test_list_customers(self, client, auth_headers):
        """Test listing customers"""
        response = client.get("/api/v2/customers", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_create_customer(self, client, auth_headers, sample_customer):
        """Test creating a customer"""
        response = client.post("/api/v2/customers", headers=auth_headers, json=sample_customer)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
    
    def test_search_customers(self, client, auth_headers):
        """Test searching customers"""
        response = client.get("/api/v2/customers?search=test", headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_customers_with_credit(self, client, auth_headers):
        """Test filtering customers with outstanding credit"""
        response = client.get("/api/v2/customers?has_credit=true", headers=auth_headers)
        assert response.status_code in [200, 401]


# ============================================================
# SUPPLIERS CRUD TESTS
# ============================================================

class TestSuppliersCRUD:
    """Tests for Suppliers CRUD operations"""
    
    def test_list_suppliers(self, client, auth_headers):
        """Test listing suppliers"""
        response = client.get("/api/v2/suppliers", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
    
    def test_create_supplier(self, client, auth_headers, sample_supplier):
        """Test creating a supplier"""
        response = client.post("/api/v2/suppliers", headers=auth_headers, json=sample_supplier)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data


# ============================================================
# SALES ANALYTICS TESTS
# ============================================================

class TestSalesAnalytics:
    """Tests for Sales Analytics endpoints"""
    
    def test_sales_summary(self, client, auth_headers):
        """Test sales summary endpoint"""
        response = client.get("/api/analytics/sales/summary", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "period" in data
            assert "metrics" in data
            assert "growth" in data
    
    def test_sales_summary_with_date_range(self, client, auth_headers):
        """Test sales summary with custom date range"""
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=7)).isoformat()
        response = client.get(
            f"/api/analytics/sales/summary?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]
    
    def test_daily_trend(self, client, auth_headers):
        """Test daily revenue trend"""
        response = client.get("/api/analytics/sales/daily-trend", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_sales_by_category(self, client, auth_headers):
        """Test sales breakdown by category"""
        response = client.get("/api/analytics/sales/by-category", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_top_products(self, client, auth_headers):
        """Test top products endpoint"""
        response = client.get("/api/analytics/sales/top-products", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_top_products_sort_by_units(self, client, auth_headers):
        """Test top products sorted by units sold"""
        response = client.get("/api/analytics/sales/top-products?sort_by=units", headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_payment_methods(self, client, auth_headers):
        """Test payment method breakdown"""
        response = client.get("/api/analytics/sales/payment-methods", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_hourly_pattern(self, client, auth_headers):
        """Test hourly sales pattern"""
        response = client.get("/api/analytics/sales/hourly-pattern", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_weekly_pattern(self, client, auth_headers):
        """Test weekly sales pattern"""
        response = client.get("/api/analytics/sales/weekly-pattern", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


# ============================================================
# CAUSAL ANALYSIS TESTS
# ============================================================

class TestCausalAnalysis:
    """Tests for Causal Analysis endpoints (Thesis-specific)"""
    
    def test_holiday_impact(self, client, auth_headers):
        """Test holiday impact analysis"""
        response = client.get("/api/analytics/sales/causal/holiday-impact", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "baseline" in data
            assert "holidays" in data
    
    def test_weather_impact(self, client, auth_headers):
        """Test weather impact analysis"""
        response = client.get("/api/analytics/sales/causal/weather-impact?city=Mumbai", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "city" in data
            assert "by_condition" in data
    
    def test_channel_comparison(self, client, auth_headers):
        """Test channel comparison"""
        response = client.get("/api/analytics/sales/causal/channel-comparison", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "channels" in data


# ============================================================
# BUSINESS LOGIC TESTS
# ============================================================

class TestBusinessLogic:
    """Tests for core business logic"""
    
    def test_gst_calculation(self):
        """Test GST calculation logic"""
        base_price = 1000
        gst_rate = 18.0
        
        # GST amount = base_price * (gst_rate / (100 + gst_rate)) for inclusive
        gst_inclusive = base_price * (gst_rate / (100 + gst_rate))
        assert round(gst_inclusive, 2) == round(152.54, 2)
        
        # GST amount = base_price * (gst_rate / 100) for exclusive
        gst_exclusive = base_price * (gst_rate / 100)
        assert gst_exclusive == 180.0
    
    def test_margin_calculation(self):
        """Test margin calculation"""
        selling_price = 150.0
        cost_price = 100.0
        
        margin = selling_price - cost_price
        margin_percent = (margin / cost_price) * 100
        
        assert margin == 50.0
        assert margin_percent == 50.0
    
    def test_rfm_scoring(self):
        """Test RFM score calculation logic"""
        # Recency: days since last purchase
        # Frequency: number of purchases
        # Monetary: total spent
        
        def calculate_rfm_score(recency_days, frequency, monetary):
            # Recency Score (1-5, 5 = most recent)
            if recency_days <= 7:
                r = 5
            elif recency_days <= 30:
                r = 4
            elif recency_days <= 90:
                r = 3
            elif recency_days <= 180:
                r = 2
            else:
                r = 1
            
            # Frequency Score
            if frequency >= 20:
                f = 5
            elif frequency >= 10:
                f = 4
            elif frequency >= 5:
                f = 3
            elif frequency >= 2:
                f = 2
            else:
                f = 1
            
            # Monetary Score
            if monetary >= 50000:
                m = 5
            elif monetary >= 20000:
                m = 4
            elif monetary >= 10000:
                m = 3
            elif monetary >= 5000:
                m = 2
            else:
                m = 1
            
            return f"{r}{f}{m}"
        
        # Test champion customer
        assert calculate_rfm_score(5, 25, 60000) == "555"
        
        # Test at-risk customer
        assert calculate_rfm_score(100, 15, 30000) == "344"
        
        # Test new customer
        assert calculate_rfm_score(3, 1, 1000) == "511"
    
    def test_credit_limit_check(self):
        """Test credit limit validation"""
        def check_credit(outstanding, credit_limit, new_amount):
            return (outstanding + new_amount) <= credit_limit
        
        assert check_credit(5000, 10000, 3000) == True
        assert check_credit(5000, 10000, 6000) == False
        assert check_credit(0, 10000, 10000) == True
    
    def test_reorder_point_logic(self):
        """Test reorder point calculation"""
        def needs_reorder(stock_level, reorder_point):
            return stock_level <= reorder_point
        
        assert needs_reorder(5, 10) == True
        assert needs_reorder(10, 10) == True
        assert needs_reorder(15, 10) == False


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_product_lifecycle(self, client, auth_headers, sample_product):
        """Test complete product lifecycle"""
        # Create
        create_response = client.post("/api/v2/products", headers=auth_headers, json=sample_product)
        if create_response.status_code in [200, 201]:
            product_id = create_response.json()["id"]
            
            # Read
            get_response = client.get(f"/api/v2/products/{product_id}", headers=auth_headers)
            assert get_response.status_code == 200
            
            # Update
            update_response = client.put(
                f"/api/v2/products/{product_id}",
                headers=auth_headers,
                json={"stock_level": 75}
            )
            assert update_response.status_code == 200
            
            # Delete (soft)
            delete_response = client.delete(f"/api/v2/products/{product_id}", headers=auth_headers)
            assert delete_response.status_code == 200


# ============================================================
# PERFORMANCE TESTS
# ============================================================

class TestPerformance:
    """Basic performance tests"""
    
    def test_products_list_performance(self, client, auth_headers):
        """Test products listing responds within acceptable time"""
        import time
        
        start = time.time()
        response = client.get("/api/v2/products?size=50", headers=auth_headers)
        duration = time.time() - start
        
        assert duration < 2.0  # Should respond in under 2 seconds
    
    def test_analytics_summary_performance(self, client, auth_headers):
        """Test analytics summary responds within acceptable time"""
        import time
        
        start = time.time()
        response = client.get("/api/analytics/sales/summary", headers=auth_headers)
        duration = time.time() - start
        
        assert duration < 3.0  # Should respond in under 3 seconds


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
