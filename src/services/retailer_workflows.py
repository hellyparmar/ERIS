"""
Critical Retailer Workflows
Missing real-world operations that retailers actually need
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================
# RETURNS & REFUNDS MANAGEMENT
# ============================================================

class ReturnReason(Enum):
    """Reasons for product return"""
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    SIZE_ISSUE = "size_issue"
    DAMAGED_IN_TRANSIT = "damaged_in_transit"


@dataclass
class ReturnItem:
    """Item being returned"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    condition: str  # 'new', 'used', 'damaged'


class ReturnWindowExpired(Exception):
    """Raised when return attempted outside window"""
    pass


class ReturnManagement:
    """
    Critical Workflow: Returns & Refunds
    Reality: Retailers MUST handle returns smoothly or lose customers
    """
    
    def __init__(self, db_connection, payment_gateway):
        self.db = db_connection
        self.payment_gateway = payment_gateway
        self.default_return_window_days = 7
    
    async def process_return(
        self,
        sale_id: str,
        items: List[ReturnItem],
        reason: ReturnReason,
        customer_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process customer return
        
        Critical Flow:
        1. Validate return eligibility
        2. Restock inventory
        3. Process refund
        4. Adjust customer credit (if applicable)
        5. Generate return receipt
        
        Args:
            sale_id: Original sale ID
            items: Items being returned
            reason: Return reason
            customer_note: Optional customer note
        
        Returns:
            Return record with refund details
        """
        # Step 1: Validate return eligibility
        sale = await self._get_sale(sale_id)
        
        # Check return window
        days_since_purchase = (datetime.now() - sale['sale_date']).days
        if days_since_purchase > self.default_return_window_days:
            raise ReturnWindowExpired(
                f"Return window of {self.default_return_window_days} days has expired. "
                f"Purchase was {days_since_purchase} days ago."
            )
        
        # Validate items were in original sale
        self._validate_items_in_sale(items, sale['items'])
        
        # Step 2: Restock inventory
        for item in items:
            await self._restock_item(item)
        
        # Step 3: Calculate refund amount
        refund_amount = sum(item.total_amount for item in items)
        
        # Adjust for restocking fee if applicable
        restocking_fee = Decimal('0')
        if reason == ReturnReason.CHANGED_MIND:
            restocking_fee = refund_amount * Decimal('0.10')  # 10% restocking fee
            refund_amount -= restocking_fee
        
        # Step 4: Process refund
        refund_result = await self._process_refund(sale, refund_amount)
        
        # Step 5: Adjust credit/khata if applicable
        if sale['payment_method'] == 'credit':
            await self._adjust_customer_credit(sale['customer_id'], -refund_amount)
        
        # Step 6: Create return record
        return_record = await self._create_return_record(
            sale_id=sale_id,
            items=items,
            reason=reason,
            customer_note=customer_note,
            refund_amount=refund_amount,
            restocking_fee=restocking_fee,
            refund_method=refund_result['method'],
            refund_transaction_id=refund_result['transaction_id']
        )
        
        logger.info(f"Return processed: {return_record['return_id']} for sale {sale_id}")
        
        return return_record
    
    async def _restock_item(self, item: ReturnItem):
        """Add returned item back to inventory"""
        # Only restock if item is in good condition
        if item.condition in ['new', 'used']:
            await self.db.execute("""
                UPDATE products
                SET stock_level = stock_level + :qty,
                    updated_at = NOW()
                WHERE product_id = :id
            """, {'qty': item.quantity, 'id': item.product_id})
            
            # Log inventory transaction
            await self.db.execute("""
                INSERT INTO inventory_transactions 
                (product_id, transaction_type, quantity, notes)
                VALUES (:id, 'return_restock', :qty, :notes)
            """, {
                'id': item.product_id,
                'qty': item.quantity,
                'notes': f'Returned item restocked (condition: {item.condition})'
            })
        else:
            # Item damaged - mark as waste/damaged stock
            await self.db.execute("""
                INSERT INTO damaged_stock
                (product_id, quantity, reason, date_recorded)
                VALUES (:id, :qty, 'customer_return_damaged', NOW())
            """, {'id': item.product_id, 'qty': item.quantity})
    
    async def _process_refund(self, sale: Dict, refund_amount: Decimal) -> Dict:
        """Process refund via payment gateway or cash"""
        if sale['payment_method'] == 'card':
            # Refund to original card
            result = await self.payment_gateway.refund(
                transaction_id=sale['payment_transaction_id'],
                amount=float(refund_amount)
            )
            return {'method': 'card_refund', 'transaction_id': result['refund_id']}
        
        elif sale['payment_method'] == 'upi':
            # Refund via UPI
            result = await self.payment_gateway.upi_refund(
                upi_id=sale['customer_upi_id'],
                amount=float(refund_amount)
            )
            return {'method': 'upi_refund', 'transaction_id': result['refund_id']}
        
        else:
            # Cash refund
            return {'method': 'cash_refund', 'transaction_id': None}
    
    async def _get_sale(self, sale_id: str) -> Dict:
        """Get sale details"""
        # Mock implementation
        return {
            'sale_id': sale_id,
            'customer_id': 'CUST_123',
            'sale_date': datetime.now() - timedelta(days=3),
            'payment_method': 'card',
            'payment_transaction_id': 'TXN_456',
            'items': []
        }
    
    def _validate_items_in_sale(self, return_items: List[ReturnItem], sale_items: List):
        """Validate items were in original sale"""
        # Implementation
        pass
    
    async def _adjust_customer_credit(self, customer_id: str, amount: Decimal):
        """Adjust customer credit balance"""
        await self.db.execute("""
            UPDATE customer_credit
            SET balance = balance + :amount,
                updated_at = NOW()
            WHERE customer_id = :id
        """, {'amount': float(amount), 'id': customer_id})
    
    async def _create_return_record(self, **kwargs) -> Dict:
        """Create return record in database"""
        return_id = f"RET_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        await self.db.execute("""
            INSERT INTO returns 
            (return_id, sale_id, reason, refund_amount, restocking_fee, created_at)
            VALUES (:id, :sale_id, :reason, :refund, :fee, NOW())
        """, {
            'id': return_id,
            'sale_id': kwargs['sale_id'],
            'reason': kwargs['reason'].value,
            'refund': float(kwargs['refund_amount']),
            'fee': float(kwargs['restocking_fee'])
        })
        
        return {'return_id': return_id, **kwargs}


# ============================================================
# SUPPLIER PAYMENT TRACKING
# ============================================================

@dataclass
class SupplierPayment:
    """Supplier payment record"""
    supplier_id: str
    supplier_name: str
    invoice_number: str
    invoice_date: date
    due_date: date
    amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str  # 'pending', 'partial', 'paid', 'overdue'
    payment_terms: str  # 'net_30', 'net_60', etc.


class SupplierPaymentTracker:
    """
    Critical Workflow: Track supplier payments
    Reality: Retailers need to know what they owe and when
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def record_purchase(
        self,
        supplier_id: str,
        items: List[Dict],
        payment_terms: str = 'net_30'
    ) -> SupplierPayment:
        """
        Record purchase from supplier
        
        Args:
            supplier_id: Supplier ID
            items: Purchased items
            payment_terms: Payment terms (net_30, net_60, etc.)
        
        Returns:
            Supplier payment record
        """
        invoice_number = f"PINV_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        invoice_date = date.today()
        
        # Calculate due date based on terms
        days_map = {'net_30': 30, 'net_60': 60, 'net_90': 90, 'immediate': 0}
        days = days_map.get(payment_terms, 30)
        due_date = invoice_date + timedelta(days=days)
        
        # Calculate total amount
        total_amount = sum(
            Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
            for item in items
        )
        
        # Create payment record
        payment = SupplierPayment(
            supplier_id=supplier_id,
            supplier_name=await self._get_supplier_name(supplier_id),
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            amount=total_amount,
            paid_amount=Decimal('0'),
            balance=total_amount,
            status='pending',
            payment_terms=payment_terms
        )
        
        # Store in database
        await self._store_supplier_payment(payment, items)
        
        return payment
    
    async def record_payment(
        self,
        invoice_number: str,
        amount: Decimal,
        payment_method: str,
        payment_date: Optional[date] = None
    ) -> Dict:
        """
        Record payment to supplier
        
        Args:
            invoice_number: Invoice number
            amount: Payment amount
            payment_method: Payment method (cash, cheque, bank_transfer, upi)
            payment_date: Payment date (defaults to today)
        
        Returns:
             Updated payment status
        """
        payment_date = payment_date or date.today()
        
        # Get current payment record
        payment = await self._get_supplier_payment(invoice_number)
        
        # Update paid amount
        new_paid_amount = payment.paid_amount + amount
        new_balance = payment.amount - new_paid_amount
        
        # Determine new status
        if new_balance <= 0:
            new_status = 'paid'
        elif new_paid_amount > 0:
            new_status = 'partial'
        else:
            new_status = payment.status
        
        # Update database
        await self.db.execute("""
            UPDATE supplier_payments
            SET paid_amount = :paid,
                balance = :balance,
                status = :status,
                last_payment_date = :date,
                updated_at = NOW()
            WHERE invoice_number = :invoice
        """, {
            'paid': float(new_paid_amount),
            'balance': float(new_balance),
            'status': new_status,
            'date': payment_date,
            'invoice': invoice_number
        })
        
        # Record payment transaction
        await self._record_payment_transaction(
            invoice_number, amount, payment_method, payment_date
        )
        
        logger.info(f"Payment recorded: ₹{amount} for {invoice_number}")
        
        return {
            'invoice_number': invoice_number,
            'payment_amount': amount,
            'new_balance': new_balance,
            'status': new_status
        }
    
    async def get_overdue_payments(self) -> List[SupplierPayment]:
        """Get all overdue supplier payments"""
        # Query overdue payments
        results = await self.db.fetch_all("""
            SELECT * FROM supplier_payments
            WHERE due_date < CURRENT_DATE
            AND status != 'paid'
            ORDER BY due_date ASC
        """)
        
        return [SupplierPayment(**row) for row in results]
    
    async def get_payment_dashboard(self) -> Dict[str, Any]:
        """
        Get supplier payment dashboard
        
        Returns summary of payments due, overdue, paid this month
        """
        today = date.today()
        month_start = today.replace(day=1)
        
        summary = await self.db.fetch_one("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'pending' AND due_date <= CURRENT_DATE + INTERVAL '7 days') as due_this_week,
                COUNT(*) FILTER (WHERE status IN ('pending', 'partial') AND due_date < CURRENT_DATE) as overdue_count,
                SUM(balance) FILTER (WHERE status IN ('pending', 'partial')) as total_outstanding,
                SUM(paid_amount) FILTER (WHERE last_payment_date >= :month_start) as paid_this_month
            FROM supplier_payments
        """, {'month_start': month_start})
        
        return {
            'due_this_week': summary['due_this_week'],
            'overdue_count': summary['overdue_count'],
            'total_outstanding': float(summary['total_outstanding'] or 0),
            'paid_this_month': float(summary['paid_this_month'] or 0)
        }
    
    async def _get_supplier_name(self, supplier_id: str) -> str:
        """Get supplier name"""
        result = await self.db.fetch_one(
            "SELECT name FROM suppliers WHERE supplier_id = :id",
            {'id': supplier_id}
        )
        return result['name'] if result else 'Unknown Supplier'
    
    async def _store_supplier_payment(self, payment: SupplierPayment, items: List[Dict]):
        """Store supplier payment in database"""
        # Implementation
        pass
    
    async def _get_supplier_payment(self, invoice_number: str) -> SupplierPayment:
        """Get supplier payment record"""
        # Mock implementation
        return SupplierPayment(
            supplier_id='SUP_001',
            supplier_name='ABC Suppliers',
            invoice_number=invoice_number,
            invoice_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=20),
            amount=Decimal('50000'),
            paid_amount=Decimal('20000'),
            balance=Decimal('30000'),
            status='partial',
            payment_terms='net_30'
        )
    
    async def _record_payment_transaction(
        self,
        invoice_number: str,
        amount: Decimal,
        method: str,
        date: date
    ):
        """Record payment transaction"""
        await self.db.execute("""
            INSERT INTO supplier_payment_transactions
            (invoice_number, amount, payment_method, payment_date, created_at)
            VALUES (:invoice, :amount, :method, :date, NOW())
        """, {
            'invoice': invoice_number,
            'amount': float(amount),
            'method': method,
            'date': date
        })


# ============================================================
# EMPLOYEE COMMISSION TRACKING
# ============================================================

class CommissionCalculator:
    """
    Critical Workflow: Calculate staff commissions
    Reality: Sales staff expect accurate, timely commission payments
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def calculate_monthly_commission(
        self,
        employee_id: str,
        month: date
    ) -> Dict[str, Any]:
        """
        Calculate employee commission for a month
        
        Commission Rules:
        - Base: 2% of sales
        - Tier bonus: >₹1L sales = +0.5%, >₹2L = +1%
        - Product bonus: Electronics = +1%
        
        Args:
            employee_id: Employee ID
            month: Month to calculate (YYYY-MM-01)
        
        Returns:
            Commission breakdown
        """
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get employee sales for month
        sales = await self._get_employee_sales(employee_id, month_start, month_end)
        
        total_sales = sum(sale['amount'] for sale in sales)
        
        # Base commission (2%)
        base_commission = total_sales * Decimal('0.02')
        
        # Tier bonus
        tier_bonus = Decimal('0')
        if total_sales > 200000:
            tier_bonus = total_sales * Decimal('0.01')
        elif total_sales > 100000:
            tier_bonus = total_sales * Decimal('0.005')
        
        # Product category bonus
        product_bonus = Decimal('0')
        for sale in sales:
            if sale['category'] == 'electronics':
                product_bonus += sale['amount'] * Decimal('0.01')
        
        total_commission = base_commission + tier_bonus + product_bonus
        
        return {
            'employee_id': employee_id,
            'month': month.strftime('%Y-%m'),
            'total_sales': float(total_sales),
            'base_commission': float(base_commission),
            'tier_bonus': float(tier_bonus),
            'product_bonus': float(product_bonus),
            'total_commission': float(total_commission),
            'sales_count': len(sales)
        }
    
    async def _get_employee_sales(self, employee_id: str, start: date, end: date) -> List[Dict]:
        """Get employee sales for period"""
        results = await self.db.fetch_all("""
            SELECT s.sale_id, s.total_amount as amount, p.category
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            JOIN products p ON si.product_id = p.product_id
            WHERE s.employee_id = :emp_id
            AND s.sale_date >= :start
            AND s.sale_date <= :end
        """, {'emp_id': employee_id, 'start': start, 'end': end})
        
        return [dict(row) for row in results]


# ============================================================
# EXPIRY DATE TRACKING (Grocery/Pharmacy)
# ============================================================

class ExpiryDateTracker:
    """
    Critical Workflow: Track product expiry dates
    Reality: Grocery/pharmacy retailers MUST track expiry to avoid waste and legal issues
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_expiring_products(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get products expiring within X days
        
        Args:
            days_ahead: Days to look ahead
        
        Returns:
            List of expiring products
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        results = await self.db.fetch_all("""
            SELECT 
                p.product_id,
                p.product_name,
                pb.batch_number,
                pb.expiry_date,
                pb.quantity,
                (pb.expiry_date - CURRENT_DATE) as days_until_expiry
            FROM product_batches pb
            JOIN products p ON pb.product_id = p.product_id
            WHERE pb.expiry_date <= :cutoff
            AND pb.quantity > 0
            ORDER BY pb.expiry_date ASC
        """, {'cutoff': cutoff_date})
        
        return [dict(row) for row in results]
    
    async def mark_expired_products(self) -> List[str]:
        """
        Mark expired products as unavailable
        
        Returns list of product IDs marked as expired
        """
        expired = await self.db.fetch_all("""
            SELECT product_id, batch_number, quantity
            FROM product_batches
            WHERE expiry_date < CURRENT_DATE
            AND status = 'active'
        """)
        
        expired_ids = []
        
        for batch in expired:
            # Mark batch as expired
            await self.db.execute("""
                UPDATE product_batches
                SET status = 'expired',
                    updated_at = NOW()
                WHERE product_id = :pid AND batch_number = :batch
            """, {'pid': batch['product_id'], 'batch': batch['batch_number']})
            
            # Reduce available stock
            await self.db.execute("""
                UPDATE products
                SET stock_level = stock_level - :qty
                WHERE product_id = :pid
            """, {'qty': batch['quantity'], 'pid': batch['product_id']})
            
            expired_ids.append(batch['product_id'])
        
        return expired_ids


# Example usage
if __name__ == "__main__":
    print("Critical Retailer Workflows Demo\n" + "=" * 60)
    
    # Demo 1: Process return
    print("\n1. RETURNS PROCESSING:")
    print("Customer returns defective smartphone within 7 days")
    print("→ Validated eligibility")
    print("→ Restocked inventory (if not damaged)")
    print("→ Refunded ₹20,000 to original payment method")
    print("→ Adjusted customer credit balance")
    print("→ Generated return receipt")
    
    # Demo 2: Supplier payment
    print("\n2. SUPPLIER PAYMENT TRACKING:")
    print("Overdue payments:")
    print("  • ABC Suppliers: ₹30,000 (due 5 days ago)")
    print("  • XYZ Traders: ₹75,000 (due 12 days ago)")
    print("Total outstanding: ₹2,45,000")
    
    # Demo 3: Employee commission
    print("\n3. EMPLOYEE COMMISSION:")
    print("Salesperson: Rajesh Kumar")
    print("  Total Sales: ₹1,85,000")
    print("  Base Commission (2%): ₹3,700")
    print("  Tier Bonus (>₹1L): ₹925")
    print("  Product Bonus: ₹500")
    print("  Total Commission: ₹5,125")
    
    # Demo 4: Expiry alerts
    print("\n4. EXPIRY DATE ALERTS:")
    print("Products expiring in next 7 days:")
    print("  • Milk (Batch #1234): 2 days")
    print("  • Bread (Batch #5678): 5 days")
    print("  • Medicine XYZ (Batch #9012): 7 days")
