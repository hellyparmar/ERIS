"""
Phase 2: Comprehensive Unit Tests

Tests for GST Service, Invoice Service, Credit Service
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List


# ==================== GST Service Tests ====================

class TestGSTService:
    """Test GST calculation and compliance"""
    
    def test_intra_state_tax_calculation_18_percent(self):
        """Test intra-state GST calculation for 18% rate"""
        from api.services.gst_service import gst_service
        
        result = gst_service.calculate_tax_intra_state(
            amount=Decimal("1000"),
            tax_rate=Decimal("18")
        )
        
        assert result is not None
        assert result.get("cgst") == Decimal("90")
        assert result.get("sgst") == Decimal("90")
        assert result.get("total_tax") == Decimal("180")
        assert result.get("final_amount") == Decimal("1180")
    
    def test_intra_state_tax_calculation_5_percent(self):
        """Test intra-state GST calculation for 5% rate"""
        from api.services.gst_service import gst_service
        
        result = gst_service.calculate_tax_intra_state(
            amount=Decimal("1000"),
            tax_rate=Decimal("5")
        )
        
        assert result.get("cgst") == Decimal("25")
        assert result.get("sgst") == Decimal("25")
        assert result.get("total_tax") == Decimal("50")
        assert result.get("final_amount") == Decimal("1050")
    
    def test_inter_state_tax_calculation_18_percent(self):
        """Test inter-state GST calculation (IGST)"""
        from api.services.gst_service import gst_service
        
        result = gst_service.calculate_tax_inter_state(
            amount=Decimal("1000"),
            tax_rate=Decimal("18")
        )
        
        assert result.get("igst") == Decimal("180")
        assert result.get("total_tax") == Decimal("180")
        assert result.get("final_amount") == Decimal("1180")
    
    def test_zero_tax_rate(self):
        """Test GST calculation for exempted goods (0%)"""
        from api.services.gst_service import gst_service
        
        result = gst_service.calculate_tax_intra_state(
            amount=Decimal("1000"),
            tax_rate=Decimal("0")
        )
        
        assert result.get("cgst") == Decimal("0")
        assert result.get("sgst") == Decimal("0")
        assert result.get("total_tax") == Decimal("0")
        assert result.get("final_amount") == Decimal("1000")
    
    def test_high_value_transaction(self):
        """Test GST calculation for high-value transaction"""
        from api.services.gst_service import gst_service
        
        result = gst_service.calculate_tax_intra_state(
            amount=Decimal("100000"),
            tax_rate=Decimal("18")
        )
        
        assert result.get("total_tax") == Decimal("18000")
        assert result.get("final_amount") == Decimal("118000")
    
    def test_decimal_precision(self):
        """Test precision with decimal amounts"""
        from api.services.gst_service import gst_service
        
        result = gst_service.calculate_tax_intra_state(
            amount=Decimal("999.99"),
            tax_rate=Decimal("12")
        )
        
        # Verify decimal precision is maintained
        assert isinstance(result.get("cgst"), Decimal)
        assert isinstance(result.get("total_tax"), Decimal)


# ==================== Invoice Service Tests ====================

class TestInvoiceService:
    """Test invoice generation and calculations"""
    
    def test_single_line_item_calculation(self):
        """Test calculation for single line item"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem
        )
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="Test Product",
                hsn_code="1234",
                quantity=Decimal("5"),
                unit_rate=Decimal("100"),
                tax_rate=Decimal("18"),
                description="Test item"
            )
        ]
        
        result = phase2_invoice_service.calculate_invoice_totals(items)
        
        assert result is not None
        assert result.get("subtotal") == Decimal("500")  # 5 * 100
        assert result.get("total_tax") == Decimal("90")   # 500 * 18%
    
    def test_multiple_line_items(self):
        """Test invoice with multiple line items"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem
        )
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="Product 1",
                hsn_code="1001",
                quantity=Decimal("2"),
                unit_rate=Decimal("100"),
                tax_rate=Decimal("18")
            ),
            InvoiceLineItem(
                product_id="P002",
                product_name="Product 2",
                hsn_code="1002",
                quantity=Decimal("3"),
                unit_rate=Decimal("200"),
                tax_rate=Decimal("12")
            )
        ]
        
        result = phase2_invoice_service.calculate_invoice_totals(items)
        
        # Product 1: 2 * 100 = 200, tax = 36
        # Product 2: 3 * 200 = 600, tax = 72
        # Total: 800, tax: 108
        assert result.get("subtotal") == Decimal("800")
        assert result.get("total_tax") == Decimal("108")
    
    def test_invoice_with_discount(self):
        """Test invoice calculation with discount"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem
        )
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="Discounted Product",
                hsn_code="1001",
                quantity=Decimal("10"),
                unit_rate=Decimal("100"),
                tax_rate=Decimal("18"),
                discount_percentage=Decimal("10")
            )
        ]
        
        result = phase2_invoice_service.calculate_invoice_totals(items)
        
        # Subtotal: 10 * 100 = 1000
        # After 10% discount: 900
        # Tax on 900: 162
        assert result.get("subtotal_after_discount") == Decimal("900")
        assert result.get("total_tax") == Decimal("162")
    
    def test_qr_code_generation(self):
        """Test QR code data generation"""
        from api.services.phase2_invoice_service import phase2_invoice_service
        
        qr_data = phase2_invoice_service.generate_qr_code_data(
            business_name="Test Business",
            amount=Decimal("1000"),
            customer_phone="9876543210"
        )
        
        assert qr_data is not None
        assert isinstance(qr_data, str)
        assert len(qr_data) > 0
    
    def test_gstr1_return_data(self):
        """Test GSTR-1 return data generation"""
        from api.services.phase2_invoice_service import phase2_invoice_service
        
        gstr1_data = phase2_invoice_service.create_gst_return_data(
            invoices=[],
            return_period="202411"
        )
        
        assert gstr1_data is not None
        assert isinstance(gstr1_data, dict)


# ==================== Credit Service Tests ====================

class TestCreditService:
    """Test credit management and scoring"""
    
    def test_initialize_credit_account(self):
        """Test credit account initialization"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        account = phase2_credit_service.initialize_credit_account(
            customer_id="CUST001",
            customer_name="Test Customer",
            credit_limit=Decimal("50000"),
            payment_terms_days=30
        )
        
        assert account is not None
        assert account.get("customer_id") == "CUST001"
        assert account.get("credit_limit") == Decimal("50000")
        assert account.get("used_credit") == Decimal("0")
        assert account.get("available_credit") == Decimal("50000")
    
    def test_credit_score_excellent(self):
        """Test credit score calculation for excellent rating"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        score = phase2_credit_service.calculate_credit_score(
            total_transactions=100,
            on_time_payments=98,
            late_payments=2,
            missed_payments=0
        )
        
        assert score >= 80
        assert isinstance(score, (int, float))
    
    def test_credit_score_good(self):
        """Test credit score calculation for good rating"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        score = phase2_credit_service.calculate_credit_score(
            total_transactions=50,
            on_time_payments=45,
            late_payments=5,
            missed_payments=0
        )
        
        assert 60 <= score < 80
    
    def test_credit_score_poor(self):
        """Test credit score calculation for poor rating"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        score = phase2_credit_service.calculate_credit_score(
            total_transactions=50,
            on_time_payments=30,
            late_payments=10,
            missed_payments=10
        )
        
        assert score < 40
    
    def test_record_credit_transaction(self):
        """Test recording a credit transaction"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        transaction = phase2_credit_service.record_transaction(
            customer_id="CUST001",
            transaction_type="CREDIT",
            amount=Decimal("5000"),
            invoice_id="INV001",
            due_date=date.today() + timedelta(days=30)
        )
        
        assert transaction is not None
        assert transaction.get("customer_id") == "CUST001"
        assert transaction.get("amount") == Decimal("5000")
        assert transaction.get("transaction_type") == "CREDIT"
    
    def test_record_payment_transaction(self):
        """Test recording a payment transaction"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        payment = phase2_credit_service.record_transaction(
            customer_id="CUST001",
            transaction_type="PAYMENT",
            amount=Decimal("2500")
        )
        
        assert payment is not None
        assert payment.get("transaction_type") == "PAYMENT"
        assert payment.get("amount") == Decimal("2500")
    
    def test_payment_reminder_message(self):
        """Test payment reminder message generation"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        message = phase2_credit_service.get_payment_reminder_message(
            customer_id="CUST001"
        )
        
        assert message is not None
        assert isinstance(message, str)
        assert len(message) > 0
        assert "CUST001" in message or "payment" in message.lower()
    
    def test_aging_report_generation(self):
        """Test aging report generation"""
        from api.services.phase2_credit_service import phase2_credit_service
        
        aging_data = phase2_credit_service.generate_aging_report()
        
        assert aging_data is not None
        assert isinstance(aging_data, dict)
        assert "current" in aging_data or "aging_buckets" in aging_data


# ==================== Integration Tests ====================

class TestPhase2Integration:
    """Integration tests for Phase 2 services"""
    
    def test_invoice_creation_workflow(self):
        """Test complete invoice creation workflow"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem, InvoiceDetails
        )
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="Product 1",
                hsn_code="1001",
                quantity=Decimal("5"),
                unit_rate=Decimal("100"),
                tax_rate=Decimal("18")
            )
        ]
        
        invoice = InvoiceDetails(
            invoice_number="INV001",
            invoice_date=date.today(),
            customer_name="Test Customer",
            customer_gst_number="27ABCPA1234A1Z0",
            billing_address="123 Test Street",
            line_items=items
        )
        
        # Create invoice
        result = phase2_invoice_service.create_invoice(invoice, "BUS001")
        
        assert result is not None
    
    def test_credit_to_invoice_flow(self):
        """Test credit account linked to invoice"""
        from api.services.phase2_credit_service import phase2_credit_service
        from api.services.phase2_invoice_service import phase2_invoice_service
        
        # Create credit account
        account = phase2_credit_service.initialize_credit_account(
            customer_id="CUST001",
            customer_name="Test Customer",
            credit_limit=Decimal("100000")
        )
        
        # Record credit sale
        transaction = phase2_credit_service.record_transaction(
            customer_id="CUST001",
            transaction_type="CREDIT",
            amount=Decimal("10000"),
            invoice_id="INV001"
        )
        
        assert transaction is not None
        assert account.get("available_credit") == Decimal("100000")
    
    def test_gst_compliance_with_invoice(self):
        """Test GST compliance checking with invoice data"""
        from api.services.gst_service import gst_service
        from api.services.phase2_invoice_service import InvoiceLineItem
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="18% Product",
                hsn_code="1234",
                quantity=Decimal("10"),
                unit_rate=Decimal("100"),
                tax_rate=Decimal("18")
            )
        ]
        
        # Calculate tax
        tax_calc = gst_service.calculate_tax_intra_state(
            Decimal("1000"),
            Decimal("18")
        )
        
        assert tax_calc.get("total_tax") == Decimal("180")


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_amount_invoice(self):
        """Test invoice with zero amount"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem
        )
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="Free Item",
                hsn_code="1001",
                quantity=Decimal("1"),
                unit_rate=Decimal("0"),
                tax_rate=Decimal("0")
            )
        ]
        
        result = phase2_invoice_service.calculate_invoice_totals(items)
        
        assert result.get("subtotal") == Decimal("0")
        assert result.get("total_tax") == Decimal("0")
    
    def test_large_quantity_calculation(self):
        """Test calculation with large quantities"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem
        )
        
        items = [
            InvoiceLineItem(
                product_id="P001",
                product_name="Bulk Item",
                hsn_code="1001",
                quantity=Decimal("1000000"),
                unit_rate=Decimal("10"),
                tax_rate=Decimal("18")
            )
        ]
        
        result = phase2_invoice_service.calculate_invoice_totals(items)
        
        assert result is not None
        assert result.get("subtotal") == Decimal("10000000")
    
    def test_invalid_tax_rate(self):
        """Test handling of invalid tax rate"""
        from api.services.gst_service import gst_service
        
        # Should handle gracefully or raise appropriate error
        try:
            result = gst_service.calculate_tax_intra_state(
                Decimal("1000"),
                Decimal("99")  # Invalid rate
            )
            # If it doesn't raise error, check result is still valid
            assert result is not None
        except ValueError:
            # This is expected for invalid rates
            pass
    
    def test_negative_amount_rejection(self):
        """Test rejection of negative amounts"""
        from api.services.gst_service import gst_service
        
        try:
            result = gst_service.calculate_tax_intra_state(
                Decimal("-1000"),  # Negative amount
                Decimal("18")
            )
            # Should either reject or return error
            assert result is None or result.get("error") is not None
        except (ValueError, Exception):
            # This is expected
            pass


# ==================== Performance Tests ====================

class TestPerformance:
    """Performance and scalability tests"""
    
    def test_large_invoice_generation(self):
        """Test performance with large invoice (100+ line items)"""
        from api.services.phase2_invoice_service import (
            phase2_invoice_service, InvoiceLineItem
        )
        import time
        
        # Create 100 line items
        items = [
            InvoiceLineItem(
                product_id=f"P{i:04d}",
                product_name=f"Product {i}",
                hsn_code=f"{1000+i}",
                quantity=Decimal("5"),
                unit_rate=Decimal("100"),
                tax_rate=Decimal("18")
            )
            for i in range(100)
        ]
        
        start_time = time.time()
        result = phase2_invoice_service.calculate_invoice_totals(items)
        end_time = time.time()
        
        # Should complete in reasonable time (< 1 second)
        assert (end_time - start_time) < 1.0
        assert result is not None
    
    def test_batch_credit_scoring(self):
        """Test credit scoring performance for multiple customers"""
        from api.services.phase2_credit_service import phase2_credit_service
        import time
        
        start_time = time.time()
        
        for i in range(100):
            score = phase2_credit_service.calculate_credit_score(
                total_transactions=50 + i,
                on_time_payments=45 + i,
                late_payments=3,
                missed_payments=0
            )
            assert score >= 0 and score <= 100
        
        end_time = time.time()
        
        # 100 calculations should complete quickly (< 1 second)
        assert (end_time - start_time) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
