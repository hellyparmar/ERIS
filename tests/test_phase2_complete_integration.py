"""
Phase 2 Session 3: Database Integration Complete

Test suite for executing all Phase 2 API integration tests with database
"""

import pytest
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import database and app
from api.db.database import Base, get_db
from api.db.phase2_models import (
    Invoice, InvoiceLineItem, InvoicePayment,
    CustomerCredit, CreditTransaction, CreditReminder,
    GSTConfiguration
)
from main_phase2 import app


# ==================== Test Database Setup ====================

# Use SQLite for testing (in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ==================== Test Fixtures ====================

@pytest.fixture(scope="function")
def db():
    """Database fixture"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def gst_config(db):
    """Create sample GST configuration"""
    config = GSTConfiguration(
        business_id="BIZ001",
        gstin="27AAFCU5055K1Z0",
        business_name="Test Retail Business",
        financial_year="2024-04-01",
        intra_state_cgst=Decimal("9"),
        intra_state_sgst=Decimal("9"),
        inter_state_igst=Decimal("18")
    )
    db.add(config)
    db.commit()
    return config


@pytest.fixture(scope="function")
def credit_account(db):
    """Create sample credit account"""
    account = CustomerCredit(
        business_id="BIZ001",
        customer_id="CUST001",
        customer_name="Test Customer",
        credit_limit=Decimal("50000"),
        used_credit=Decimal("10000"),
        credit_score=75,
        credit_status="GOOD"
    )
    db.add(account)
    db.commit()
    return account


@pytest.fixture(scope="function")
def sample_invoice_data():
    """Sample invoice data"""
    return {
        "business_id": "BIZ001",
        "customer_id": "CUST001",
        "customer_name": "Test Customer",
        "line_items": [
            {
                "product_name": "Product A",
                "quantity": 2,
                "unit_price": "500.00",
                "tax_rate": "18"
            },
            {
                "product_name": "Product B",
                "quantity": 1,
                "unit_price": "1000.00",
                "tax_rate": "18"
            }
        ],
        "is_intra_state": True
    }


# ==================== Health Check Tests ====================

class TestHealthChecks:
    """Test application health endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "application" in response.json()
        assert response.json()["version"] == "2.0.0"
    
    def test_health_endpoint(self):
        """Test health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
    
    def test_api_v2_health(self):
        """Test Phase 2 API health check"""
        response = client.get("/api/v2/health")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0.0"
        assert "components" in data
    
    def test_api_v2_info(self):
        """Test Phase 2 API info endpoint"""
        response = client.get("/api/v2/info")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert "invoicing" in data["features"]
        assert "credit_management" in data["features"]
        assert "gst_compliance" in data["features"]
    
    def test_api_v2_test_connection(self):
        """Test database connection"""
        response = client.post("/api/v2/test/connection")
        assert response.status_code == 200
        assert response.json()["status"] in ["success", "failed"]


# ==================== Invoice API Tests ====================

class TestInvoiceAPI:
    """Test invoice management endpoints"""
    
    def test_create_invoice(self, sample_invoice_data):
        """Test invoice creation"""
        response = client.post("/api/v2/invoice/create", json=sample_invoice_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "invoice" in data
        assert "invoice_number" in data["invoice"]
    
    def test_create_invoice_invalid_data(self):
        """Test invoice creation with invalid data"""
        response = client.post("/api/v2/invoice/create", json={
            "business_id": "BIZ001",
            "line_items": []  # Missing customer_id and required fields
        })
        assert response.status_code in [400, 422]
    
    def test_list_invoices(self, sample_invoice_data, db):
        """Test invoice listing"""
        # Create an invoice first
        invoice = Invoice(
            business_id="BIZ001",
            customer_id="CUST001",
            customer_name="Test Customer",
            invoice_number="INV001",
            total_taxable=Decimal("2000"),
            total_tax=Decimal("360"),
            total_amount=Decimal("2360"),
            payment_status="PENDING"
        )
        db.add(invoice)
        db.commit()
        
        response = client.get("/api/v2/invoice/?business_id=BIZ001")
        assert response.status_code == 200
        assert "invoices" in response.json()
    
    def test_get_invoice_details(self, db):
        """Test getting invoice details"""
        # Create invoice
        invoice = Invoice(
            business_id="BIZ001",
            customer_id="CUST001",
            customer_name="Test Customer",
            invoice_number="INV001",
            total_taxable=Decimal("2000"),
            total_tax=Decimal("360"),
            total_amount=Decimal("2360")
        )
        db.add(invoice)
        db.commit()
        
        response = client.get(f"/api/v2/invoice/{invoice.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_update_invoice_payment(self, db):
        """Test updating invoice payment status"""
        invoice = Invoice(
            business_id="BIZ001",
            customer_id="CUST001",
            customer_name="Test Customer",
            invoice_number="INV001",
            total_amount=Decimal("2360"),
            payment_status="PENDING"
        )
        db.add(invoice)
        db.commit()
        
        response = client.put(
            f"/api/v2/invoice/{invoice.id}",
            json={"payment_status": "PAID"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


# ==================== Credit API Tests ====================

class TestCreditAPI:
    """Test credit management endpoints"""
    
    def test_create_credit_account(self):
        """Test credit account creation"""
        response = client.post("/api/v2/credit/accounts/create", json={
            "business_id": "BIZ001",
            "customer_id": "CUST001",
            "customer_name": "Test Customer",
            "credit_limit": 50000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["account"]["customer_id"] == "CUST001"
    
    def test_create_duplicate_account(self, credit_account):
        """Test duplicate account creation error"""
        response = client.post("/api/v2/credit/accounts/create", json={
            "business_id": "BIZ001",
            "customer_id": "CUST001",
            "customer_name": "Test Customer",
            "credit_limit": 50000
        })
        assert response.status_code == 400
    
    def test_get_credit_account(self, credit_account):
        """Test getting credit account"""
        response = client.get("/api/v2/credit/accounts/CUST001")
        assert response.status_code == 200
        data = response.json()
        assert data["account"]["customer_id"] == "CUST001"
    
    def test_get_credit_balance(self, credit_account):
        """Test getting credit balance"""
        response = client.get("/api/v2/credit/accounts/CUST001/balance")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert data["balance"]["customer_id"] == "CUST001"
    
    def test_record_transaction(self, credit_account):
        """Test recording credit transaction"""
        response = client.post("/api/v2/credit/transactions/record", json={
            "customer_id": "CUST001",
            "transaction_type": "CREDIT",
            "amount": "5000",
            "due_date": (date.today() + timedelta(days=30)).isoformat()
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_credit_score(self, credit_account):
        """Test getting credit score"""
        response = client.get("/api/v2/credit/score/CUST001")
        assert response.status_code == 200
        data = response.json()
        assert "credit_profile" in data
        assert 0 <= data["credit_profile"]["credit_score"] <= 100


# ==================== GST API Tests ====================

class TestGSTAPI:
    """Test GST compliance endpoints"""
    
    def test_setup_gst_configuration(self):
        """Test GST configuration setup"""
        response = client.post("/api/v2/gst/config/setup", json={
            "business_id": "BIZ001",
            "gstin": "27AAFCU5055K1Z0",
            "business_name": "Test Business",
            "financial_year": "2024-04-01",
            "intra_state_cgst": "9",
            "intra_state_sgst": "9",
            "inter_state_igst": "18"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_gst_configuration(self, gst_config):
        """Test getting GST configuration"""
        response = client.get("/api/v2/gst/config/BIZ001")
        assert response.status_code == 200
        data = response.json()
        assert data["configuration"]["gstin"] == "27AAFCU5055K1Z0"
    
    def test_calculate_intra_state_tax(self, gst_config):
        """Test intra-state tax calculation"""
        response = client.post("/api/v2/gst/calculate/intra-state", json={
            "business_id": "BIZ001",
            "amount": "1000"
        })
        assert response.status_code == 200
        data = response.json()
        assert "calculation" in data
        assert data["calculation"]["cgst_rate"] == 9.0
        assert data["calculation"]["sgst_rate"] == 9.0
    
    def test_calculate_inter_state_tax(self, gst_config):
        """Test inter-state tax calculation"""
        response = client.post("/api/v2/gst/calculate/inter-state", json={
            "business_id": "BIZ001",
            "amount": "1000"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["calculation"]["igst_rate"] == 18.0
    
    def test_get_standard_rates(self, gst_config):
        """Test getting standard tax rates"""
        response = client.get("/api/v2/gst/rates/standard/BIZ001")
        assert response.status_code == 200
        data = response.json()
        assert "rates" in data
    
    def test_get_tax_slabs(self):
        """Test getting tax slabs"""
        response = client.get("/api/v2/gst/tax-slabs/BIZ001")
        assert response.status_code == 200
        data = response.json()
        assert "tax_slabs" in data


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Test error handling"""
    
    def test_nonexistent_resource(self):
        """Test 404 for nonexistent resource"""
        response = client.get("/api/v2/invoice/99999")
        assert response.status_code == 404
    
    def test_invalid_endpoint(self):
        """Test 404 for invalid endpoint"""
        response = client.get("/api/v2/invalid/endpoint")
        assert response.status_code in [404, 405]
    
    def test_missing_required_field(self):
        """Test validation error for missing field"""
        response = client.post("/api/v2/credit/accounts/create", json={
            "business_id": "BIZ001"
            # Missing required fields
        })
        assert response.status_code in [400, 422]


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
