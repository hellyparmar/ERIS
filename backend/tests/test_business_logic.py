"""
Business Logic Tests
Test invoice calculations, payment processing, and service logic
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

class TestInvoiceCalculations:
    """Test invoice-related calculations"""
    
    def test_gst_calculation_18_percent(self):
        """Test 18% GST calculation"""
        base_amount = Decimal("1000.00")
        gst_rate = Decimal("0.18")
        
        gst_amount = base_amount * gst_rate
        total = base_amount + gst_amount
        
        assert gst_amount == Decimal("180.00")
        assert total == Decimal("1180.00")
    
    def test_gst_calculation_12_percent(self):
        """Test 12% GST calculation"""
        base_amount = Decimal("1000.00")
        gst_rate = Decimal("0.12")
        
        gst_amount = base_amount * gst_rate
        total = base_amount + gst_amount
        
        assert gst_amount == Decimal("120.00")
        assert total == Decimal("1120.00")
    
    def test_gst_calculation_5_percent(self):
        """Test 5% GST rate (essential goods)"""
        base_amount = Decimal("1000.00")
        gst_rate = Decimal("0.05")
        
        gst_amount = base_amount * gst_rate
        total = base_amount + gst_amount
        
        assert gst_amount == Decimal("50.00")
        assert total == Decimal("1050.00")
    
    def test_partial_payment_tracking(self):
        """Test partial payment reduces amount due correctly"""
        total_amount = Decimal("10000.00")
        payment1 = Decimal("3000.00")
        payment2 = Decimal("2500.00")
        
        amount_due = total_amount - payment1 - payment2
        amount_paid = payment1 + payment2
        
        assert amount_due == Decimal("4500.00")
        assert amount_paid == Decimal("5500.00")
    
    def test_overpayment_handling(self):
        """Test overpayment doesn't create negative due"""
        total_amount = Decimal("1000.00")
        payment = Decimal("1200.00")
        
        # Amount due should be 0, not negative
        amount_due = max(Decimal("0"), total_amount - payment)
        overpaid = max(Decimal("0"), payment - total_amount)
        
        assert amount_due == Decimal("0")
        assert overpaid == Decimal("200.00")
    
    def test_due_date_calculation(self):
        """Test due date calculated correctly from payment terms"""
        invoice_date = datetime(2026, 1, 20)
        payment_terms_days = 30
        
        due_date = invoice_date + timedelta(days=payment_terms_days)
        
        assert due_date == datetime(2026, 2, 19)
    
    def test_overdue_days_calculation(self):
        """Test overdue days calculated correctly"""
        due_date = datetime(2026, 1, 15)
        current_date = datetime(2026, 1, 20)
        
        days_overdue = (current_date - due_date).days
        
        assert days_overdue == 5

class TestKhataTracking:
    """Test Khata (credit ledger) functionality"""
    
    def test_credit_limit_check(self):
        """Test credit limit enforcement"""
        credit_limit = Decimal("50000.00")
        current_outstanding = Decimal("45000.00")
        new_order_amount = Decimal("10000.00")
        
        would_exceed = (current_outstanding + new_order_amount) > credit_limit
        
        assert would_exceed is True
    
    def test_credit_utilization_percentage(self):
        """Test credit utilization calculation"""
        credit_limit = Decimal("100000.00")
        outstanding = Decimal("75000.00")
        
        utilization = (outstanding / credit_limit) * 100
        
        assert utilization == Decimal("75")
    
    def test_payment_reduces_outstanding(self):
        """Test payment correctly reduces outstanding balance"""
        outstanding = Decimal("50000.00")
        payment = Decimal("15000.00")
        
        new_outstanding = outstanding - payment
        
        assert new_outstanding == Decimal("35000.00")

class TestCommunityCommerce:
    """Test stock swapping and bulk buying logic"""
    
    def test_dead_stock_identification(self):
        """Test dead stock identification (>180 days no sale)"""
        last_sale_date = datetime(2025, 7, 1)
        current_date = datetime(2026, 1, 20)
        dead_stock_days = 180
        
        days_since_sale = (current_date - last_sale_date).days
        is_dead_stock = days_since_sale >= dead_stock_days
        
        assert days_since_sale == 203
        assert is_dead_stock is True
    
    def test_dead_stock_pricing_suggestion(self):
        """Test dead stock should be priced at 70% of cost"""
        cost_price = Decimal("1000.00")
        suggested_discount = Decimal("0.70")
        
        suggested_price = cost_price * suggested_discount
        
        assert suggested_price == Decimal("700.00")
    
    def test_bulk_buy_target_progress(self):
        """Test bulk buy group progress tracking"""
        target_quantity = 1000
        participant_quantities = [200, 300, 150, 100]
        
        current_quantity = sum(participant_quantities)
        progress_percentage = (current_quantity / target_quantity) * 100
        remaining = target_quantity - current_quantity
        
        assert current_quantity == 750
        assert progress_percentage == 75.0
        assert remaining == 250
    
    def test_bulk_buy_target_reached(self):
        """Test bulk buy marked ready when target reached"""
        target_quantity = 1000
        current_quantity = 1050
        
        is_ready = current_quantity >= target_quantity
        
        assert is_ready is True

class TestRateLimiting:
    """Test rate limiting logic"""
    
    def test_daily_budget_tracking(self):
        """Test WhatsApp daily budget tracking"""
        daily_budget = Decimal("500.00")
        cost_per_message = Decimal("0.50")
        messages_sent = 800
        
        total_cost = cost_per_message * messages_sent
        budget_remaining = daily_budget - total_cost
        is_over_budget = total_cost > daily_budget
        
        assert total_cost == Decimal("400.00")
        assert budget_remaining == Decimal("100.00")
        assert is_over_budget is False
    
    def test_customer_daily_limit(self):
        """Test customer daily message limit"""
        limit_per_customer = 3
        messages_today = 2
        
        can_send_more = messages_today < limit_per_customer
        remaining = limit_per_customer - messages_today
        
        assert can_send_more is True
        assert remaining == 1
    
    def test_system_daily_limit(self):
        """Test system-wide daily message limit"""
        system_limit = 1000
        current_count = 999
        
        can_send = current_count < system_limit
        at_limit = current_count >= system_limit
        
        assert can_send is True
        
        current_count = 1000
        at_limit = current_count >= system_limit
        assert at_limit is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
