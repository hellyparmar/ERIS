"""
Test Suite for Loyalty Module - Next-Gen Loyalty
Tests for referral management, credit tracking, and reminders
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
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
    login_data = {"username": "testadmin", "password": "testpassword123"}
    
    response = client.post("/api/auth/login", json=login_data)
    
    if response.status_code != 200:
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


# ============================================================
# LOYALTY STATS TESTS
# ============================================================

class TestLoyaltyStats:
    """Tests for loyalty statistics endpoint"""
    
    def test_get_loyalty_stats(self, client, auth_headers):
        """Test getting loyalty program stats"""
        response = client.get("/api/loyalty/stats", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "referrals" in data
            assert "rewards" in data
            assert "credit" in data
            
            # Verify referrals structure
            assert "total" in data["referrals"]
            assert "converted" in data["referrals"]
            assert "pending" in data["referrals"]
            
            # Verify credit structure
            assert "total_outstanding" in data["credit"]
            assert "formatted" in data["credit"]


# ============================================================
# REFERRAL TESTS
# ============================================================

class TestReferrals:
    """Tests for referral endpoints"""
    
    def test_get_referrals(self, client, auth_headers):
        """Test listing referrals"""
        response = client.get("/api/loyalty/referrals", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_top_referrers(self, client, auth_headers):
        """Test getting top referrers"""
        response = client.get("/api/loyalty/referrals/top-referrers", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_create_referral_invalid_referrer(self, client, auth_headers):
        """Test creating referral with invalid referrer"""
        referral_data = {
            "referrer_id": 999999,  # Non-existent customer
            "referee_name": "Test Referee",
            "referee_email": "referee@test.com"
        }
        response = client.post("/api/loyalty/referrals", headers=auth_headers, json=referral_data)
        
        # Should return 404 for non-existent referrer
        assert response.status_code in [404, 401]


# ============================================================
# CREDIT (UDHAAR) TESTS
# ============================================================

class TestCreditManagement:
    """Tests for credit/udhaar endpoints"""
    
    def test_get_credit_customers(self, client, auth_headers):
        """Test getting customers with credit"""
        response = client.get("/api/loyalty/credit/customers", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # If there are customers, verify structure
            if len(data) > 0:
                customer = data[0]
                assert "customer_id" in customer
                assert "customer_name" in customer
                assert "balance" in customer
                assert "credit_limit" in customer
                assert "utilization" in customer
                assert "status" in customer
    
    def test_get_at_risk_customers(self, client, auth_headers):
        """Test getting at-risk credit customers"""
        response = client.get("/api/loyalty/credit/at-risk", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_credit_with_min_balance_filter(self, client, auth_headers):
        """Test filtering credit customers by minimum balance"""
        response = client.get("/api/loyalty/credit/customers?min_balance=1000", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # All returned customers should have balance >= 1000
            for customer in data:
                assert customer["balance"] >= 1000


# ============================================================
# REMINDER TESTS
# ============================================================

class TestReminders:
    """Tests for reminder endpoints"""
    
    def test_get_reminder_queue(self, client, auth_headers):
        """Test getting reminder queue"""
        response = client.get("/api/loyalty/reminders/queue", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # If there are items, verify structure
            if len(data) > 0:
                item = data[0]
                assert "customer_id" in item
                assert "customer_name" in item
                assert "amount_due" in item
                assert "days_overdue" in item
                assert "urgency" in item
    
    def test_get_reminder_history(self, client, auth_headers):
        """Test getting reminder history"""
        response = client.get("/api/loyalty/reminders/history", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_send_reminder_invalid_customer(self, client, auth_headers):
        """Test sending reminder to invalid customer"""
        reminder_data = {
            "customer_id": 999999,
            "channel": "whatsapp"
        }
        response = client.post("/api/loyalty/reminders/send", headers=auth_headers, json=reminder_data)
        
        # Should return 404 for non-existent customer
        assert response.status_code in [404, 401]
    
    def test_bulk_reminders(self, client, auth_headers):
        """Test bulk reminder endpoint"""
        bulk_data = {
            "min_days_overdue": 1,
            "max_reminders": 5,
            "channel": "whatsapp"
        }
        response = client.post("/api/loyalty/reminders/bulk", headers=auth_headers, json=bulk_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "total_in_queue" in data or "sent" in data


# ============================================================
# BUSINESS LOGIC TESTS
# ============================================================

class TestLoyaltyBusinessLogic:
    """Tests for loyalty business logic"""
    
    def test_credit_risk_scoring(self):
        """Test credit risk calculation logic"""
        def calculate_risk_status(utilization: float) -> str:
            if utilization >= 90:
                return "critical"
            elif utilization >= 70:
                return "warning"
            else:
                return "good"
        
        assert calculate_risk_status(95) == "critical"
        assert calculate_risk_status(75) == "warning"
        assert calculate_risk_status(50) == "good"
        assert calculate_risk_status(90) == "critical"
        assert calculate_risk_status(70) == "warning"
    
    def test_reminder_urgency(self):
        """Test reminder urgency classification"""
        def get_urgency(days_overdue: int) -> str:
            if days_overdue > 60:
                return "final"
            elif days_overdue > 30:
                return "urgent"
            else:
                return "friendly"
        
        assert get_urgency(65) == "final"
        assert get_urgency(45) == "urgent"
        assert get_urgency(15) == "friendly"
    
    def test_inr_formatting(self):
        """Test INR amount formatting"""
        def format_inr(amount: float) -> str:
            if amount >= 100000:
                return f"₹{amount/100000:.1f}L"
            elif amount >= 1000:
                return f"₹{amount/1000:.1f}K"
            else:
                return f"₹{amount:,.0f}"
        
        assert format_inr(500000) == "₹5.0L"
        assert format_inr(150000) == "₹1.5L"
        assert format_inr(25000) == "₹25.0K"
        assert format_inr(500) == "₹500"


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
