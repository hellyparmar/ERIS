"""
Phase 2: Invoice API Integration Tests

Tests for API endpoints with database layer
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any

# Will be imported from main app when integrated
# from main import app


class TestInvoiceAPIIntegration:
    """Test invoice API endpoints with database"""
    
    @pytest.fixture
    def test_client(self):
        """Provide test client"""
        # Will be implemented when app is integrated
        pass
    
    @pytest.fixture
    def sample_invoice_data(self) -> Dict[str, Any]:
        """Sample invoice data for testing"""
        return {
            "business_id": "BUS001",
            "customer_name": "Test Customer",
            "customer_id": "CUST001",
            "customer_email": "customer@test.com",
            "customer_phone": "9876543210",
            "customer_gst_number": "27ABCPA1234A1Z0",
            "billing_address": "123 Test Street, Test City",
            "line_items": [
                {
                    "product_id": "P001",
                    "product_name": "Product 1",
                    "hsn_code": "1234",
                    "quantity": 5,
                    "unit_rate": 100,
                    "tax_rate": 18,
                    "description": "Test product"
                },
                {
                    "product_id": "P002",
                    "product_name": "Product 2",
                    "hsn_code": "5678",
                    "quantity": 3,
                    "unit_rate": 200,
                    "tax_rate": 12,
                    "discount_percentage": 5
                }
            ],
            "payment_terms": "30 days",
            "notes": "Test invoice"
        }
    
    def test_create_invoice_success(self, test_client, sample_invoice_data):
        """Test successful invoice creation"""
        response = test_client.post(
            "/api/v2/invoices/create",
            json=sample_invoice_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "invoice_id" in data
        assert "invoice_number" in data["invoice"]
    
    def test_create_invoice_missing_line_items(self, test_client, sample_invoice_data):
        """Test invoice creation fails without line items"""
        invalid_data = sample_invoice_data.copy()
        invalid_data["line_items"] = []
        
        response = test_client.post(
            "/api/v2/invoices/create",
            json=invalid_data
        )
        
        assert response.status_code == 400
        assert "line item" in response.json()["detail"].lower()
    
    def test_get_invoice_details(self, test_client, sample_invoice_data):
        """Test retrieving invoice details"""
        # Create invoice first
        create_response = test_client.post(
            "/api/v2/invoices/create",
            json=sample_invoice_data
        )
        invoice_id = create_response.json()["invoice_id"]
        
        # Get invoice
        response = test_client.get(f"/api/v2/invoices/{invoice_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["invoice"]["id"] == invoice_id
    
    def test_list_invoices_with_filter(self, test_client, sample_invoice_data):
        """Test listing invoices with filters"""
        # Create multiple invoices
        for i in range(3):
            test_client.post("/api/v2/invoices/create", json=sample_invoice_data)
        
        # List invoices
        response = test_client.get(
            "/api/v2/invoices",
            params={"business_id": "BUS001", "limit": 20}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total"] >= 3
    
    def test_download_invoice_pdf(self, test_client, sample_invoice_data):
        """Test PDF download"""
        # Create invoice
        create_response = test_client.post(
            "/api/v2/invoices/create",
            json=sample_invoice_data
        )
        invoice_id = create_response.json()["invoice_id"]
        
        # Download PDF
        response = test_client.get(f"/api/v2/invoices/{invoice_id}/pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_update_invoice_payment_status(self, test_client, sample_invoice_data):
        """Test updating invoice payment status"""
        # Create invoice
        create_response = test_client.post(
            "/api/v2/invoices/create",
            json=sample_invoice_data
        )
        invoice_id = create_response.json()["invoice_id"]
        
        # Update payment status
        response = test_client.put(
            f"/api/v2/invoices/{invoice_id}",
            json={"payment_status": "PAID"}
        )
        
        assert response.status_code == 200
        assert response.json()["invoice"]["payment_status"] == "PAID"
    
    def test_cancel_invoice(self, test_client, sample_invoice_data):
        """Test invoice cancellation"""
        # Create invoice
        create_response = test_client.post(
            "/api/v2/invoices/create",
            json=sample_invoice_data
        )
        invoice_id = create_response.json()["invoice_id"]
        
        # Cancel invoice
        response = test_client.delete(f"/api/v2/invoices/{invoice_id}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_batch_invoice_generation(self, test_client):
        """Test batch invoice creation"""
        batch_data = {
            "business_id": "BUS001",
            "invoices": [
                {
                    "customer_name": f"Customer {i}",
                    "line_items": [
                        {
                            "product_name": "Item",
                            "quantity": 1,
                            "unit_rate": 100,
                            "tax_rate": 18
                        }
                    ]
                }
                for i in range(5)
            ]
        }
        
        response = test_client.post(
            "/api/v2/invoices/batch-generate",
            json=batch_data
        )
        
        assert response.status_code == 200
        assert response.json()["generated"] == 5
    
    def test_invoice_calculations_accuracy(self, test_client):
        """Test that calculations are accurate"""
        invoice_data = {
            "business_id": "BUS001",
            "customer_name": "Calc Test",
            "line_items": [
                {
                    "product_name": "Item 1",
                    "quantity": 10,
                    "unit_rate": 100,
                    "tax_rate": 18
                }
            ]
        }
        
        response = test_client.post(
            "/api/v2/invoices/create",
            json=invoice_data
        )
        
        invoice = response.json()["invoice"]
        # Subtotal: 10 * 100 = 1000
        # Tax (18%): 1000 * 0.18 = 180
        # Total: 1180
        
        assert invoice["total_taxable"] == 1000
        assert invoice["total_tax"] == 180
        assert invoice["total_amount"] == 1180


class TestCreditAPIIntegration:
    """Test credit API endpoints with database"""
    
    def test_create_credit_account(self, test_client):
        """Test credit account creation"""
        response = test_client.post(
            "/api/v2/credit/accounts/create",
            json={
                "business_id": "BUS001",
                "customer_id": "CUST001",
                "customer_name": "Test Customer",
                "credit_limit": 50000,
                "payment_terms_days": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["account"]["credit_limit"] == 50000
        assert data["account"]["available_credit"] == 50000
    
    def test_record_credit_transaction(self, test_client):
        """Test recording credit transaction"""
        # Create account first
        test_client.post(
            "/api/v2/credit/accounts/create",
            json={
                "business_id": "BUS001",
                "customer_id": "CUST001",
                "customer_name": "Test",
                "credit_limit": 50000
            }
        )
        
        # Record transaction
        response = test_client.post(
            "/api/v2/credit/transactions/record",
            json={
                "customer_id": "CUST001",
                "transaction_type": "CREDIT",
                "amount": 5000,
                "invoice_id": "INV001"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["transaction"]["amount"] == 5000
    
    def test_credit_score_calculation(self, test_client):
        """Test credit score calculation"""
        # Create account
        test_client.post(
            "/api/v2/credit/accounts/create",
            json={
                "business_id": "BUS001",
                "customer_id": "CUST001",
                "customer_name": "Test",
                "credit_limit": 50000
            }
        )
        
        # Get credit score
        response = test_client.get(
            "/api/v2/credit/score/CUST001"
        )
        
        assert response.status_code == 200
        score = response.json()["credit_profile"]["credit_score"]
        assert 0 <= score <= 100
    
    def test_payment_reminder_sending(self, test_client):
        """Test payment reminder"""
        response = test_client.post(
            "/api/v2/credit/reminders/send",
            params={
                "customer_id": "CUST001",
                "channels": ["SMS", "EMAIL"]
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestGSTAPIIntegration:
    """Test GST API endpoints with database"""
    
    def test_get_tax_rates(self, test_client):
        """Test getting tax rates"""
        response = test_client.get("/api/v2/gst/rates")
        
        assert response.status_code == 200
        rates = response.json()["tax_rates"]
        assert "0" in rates
        assert "5" in rates
        assert "18" in rates
    
    def test_tax_calculation(self, test_client):
        """Test GST tax calculation"""
        response = test_client.post(
            "/api/v2/gst/calculate/tax",
            json={
                "business_id": "1",
                "amount": 1000,
                "tax_rate": 18
            }
        )
        
        assert response.status_code in [200, 201]
        if response.status_code == 200:
            calc = response.json()["calculation"]
            assert "tax_amount" in calc
            assert "total_amount" in calc
        
        assert response.status_code == 200
        calc = response.json()["calculation"]
        assert calc["igst"] == 180
        assert calc["total_tax"] == 180
    
    def test_gstr1_return_generation(self, test_client):
        """Test GSTR-1 return generation"""
        response = test_client.get(
            "/api/v2/gst/return/gstr1",
            params={
                "business_id": "BUS001",
                "month": 11,
                "year": 2024
            }
        )
        
        assert response.status_code == 200
        assert response.json()["return"]["return_type"] == "GSTR-1"


class TestErrorHandling:
    """Test error handling in API"""
    
    def test_invalid_request_format(self, test_client):
        """Test handling of invalid request format"""
        response = test_client.post(
            "/api/v2/invoices/create",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
    
    def test_not_found_error(self, test_client):
        """Test 404 not found error"""
        response = test_client.get("/api/v2/invoices/nonexistent")
        
        assert response.status_code == 404
    
    def test_duplicate_invoice_number(self, test_client):
        """Test handling of duplicate invoice numbers"""
        data = {
            "business_id": "BUS001",
            "customer_name": "Customer",
            "line_items": [
                {
                    "product_name": "Item",
                    "quantity": 1,
                    "unit_rate": 100,
                    "tax_rate": 18
                }
            ]
        }
        
        # Create first invoice
        test_client.post("/api/v2/invoices/create", json=data)
        
        # Try to create duplicate - should handle gracefully
        response = test_client.post("/api/v2/invoices/create", json=data)
        
        # Should either succeed with new number or fail gracefully
        assert response.status_code in [200, 400, 409]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
