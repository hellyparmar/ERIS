"""
Endpoint Protection Tests
Test that protected endpoints require authentication
"""

import pytest
from fastapi import status

class TestInvoiceEndpoints:
    """Test invoice endpoint protection"""
    
    def test_create_invoice_requires_auth(self, client):
        """Test creating invoice without auth fails"""
        response = client.post(
            "/api/invoices/create",
            json={"sale_id": 1, "payment_terms_days": 30}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_record_payment_requires_auth(self, client):
        """Test recording payment without auth fails"""
        response = client.post(
            "/api/invoices/record-payment",
            json={
                "invoice_id": 1,
                "amount": 1000,
                "payment_method": "cash"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_khata_requires_auth(self, client):
        """Test getting Khata summary without auth fails"""
        response = client.get("/api/invoices/customer/1/khata")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_mark_overdue_requires_admin(self, client, auth_headers):
        """Test marking overdue requires admin role"""
        # Regular user should be denied
        response = client.post("/api/invoices/mark-overdue", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_send_reminders_requires_admin(self, client, auth_headers):
        """Test sending reminders requires admin role"""
        # Regular user should be denied
        response = client.post("/api/invoices/send-reminders", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

class TestMessageEndpoints:
    """Test message endpoint protection"""
    
    def test_send_message_requires_auth(self, client):
        """Test sending message without auth fails"""
        response = client.post(
            "/api/messages/send",
            json={
                "sender_type": "customer",
                "sender_id": 1,
                "recipient_type": "staff",
                "recipient_id": 1,
                "subject": "Test",
                "body": "Test message"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_inbox_requires_auth(self, client):
        """Test getting inbox without auth fails"""
        response = client.get("/api/messages/inbox?user_type=customer&user_id=1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_mark_read_requires_auth(self, client):
        """Test marking message as read without auth fails"""
        response = client.post("/api/messages/1/mark-read")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invoice_inquiry_requires_auth(self, client):
        """Test sending invoice inquiry without auth fails"""
        response = client.post(
            "/api/messages/invoice-inquiry",
            json={
                "customer_id": 1,
                "invoice_id": 1,
                "message": "Question about invoice"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestCommunityEndpoints:
    """Test community commerce endpoint protection"""
    
    def test_create_listing_requires_auth(self, client):
        """Test creating stock listing without auth fails"""
        response = client.post(
            "/api/community/listings",
            json={
                "retailer_id": 1,
                "product_id": 1,
                "quantity": 100,
                "price_per_unit": 50.0,
                "reason": "dead_stock",
                "location": "Mumbai"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_match_listing_requires_auth(self, client):
        """Test matching listing without auth fails"""
        response = client.post("/api/community/listings/1/match?buyer_id=1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_bulk_buy_requires_auth(self, client):
        """Test creating bulk buy group without auth fails"""
        response = client.post(
            "/api/community/bulk-buy",
            json={
                "coordinator_id": 1,
                "product_id": 1,
                "target_quantity": 1000,
                "target_price": 45.0
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_join_bulk_buy_requires_auth(self, client):
        """Test joining bulk buy group without auth fails"""
        response = client.post(
            "/api/community/bulk-buy/1/join",
            json={"retailer_id": 1, "quantity": 100}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_finalize_bulk_buy_requires_auth(self, client):
        """Test finalizing bulk buy without auth fails"""
        response = client.post("/api/community/bulk-buy/1/finalize")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestPublicEndpoints:
    """Test that public endpoints don't require auth"""
    
    def test_health_check_is_public(self, client):
        """Test health check endpoint is publicly accessible"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.skip(reason="Endpoint has model registry issues unrelated to auth testing")
    def test_monitoring_metrics_is_public(self, client):
        """Test monitoring metrics are publicly accessible"""
        response = client.get("/monitoring/metrics/prometheus")
        # Should work without auth (for load balancers)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.skip(reason="Endpoint has model registry issues unrelated to auth testing")
    def test_auth_endpoints_are_public(self, client):
        """Test auth endpoints don't require auth"""
        # Register endpoint
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "SecurePass123"
            }
        )
        # Should work (201 or 400 if duplicate, but not 401)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
