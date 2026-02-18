"""
Phase 2: Credit/Khata Management Service

Handles customer credit limits, payment tracking, credit scoring, and reminders
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """Credit transaction types"""
    DEBIT = "DEBIT"  # Sale (amount owed)
    CREDIT = "CREDIT"  # Payment (reduces amount owed)
    ADJUSTMENT = "ADJUSTMENT"  # Manual adjustment


class ReminderType(str, Enum):
    """Payment reminder types"""
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class CreditStatus(str, Enum):
    """Customer credit status"""
    EXCELLENT = "EXCELLENT"  # Score 85-100
    GOOD = "GOOD"  # Score 70-84
    FAIR = "FAIR"  # Score 50-69
    POOR = "POOR"  # Score 0-49


class Phase2CreditService:
    """
    Phase 2 Credit/Khata Management Service
    
    Features:
    - Customer credit limits
    - Credit score calculation
    - Payment tracking
    - Automated reminders
    - Credit analysis and reports
    """
    
    # Configuration
    DEFAULT_CREDIT_LIMIT = Decimal("10000")
    DEFAULT_CREDIT_SCORE = 75  # Starting score
    
    # Scoring parameters
    LATE_PAYMENT_PENALTY = 3
    MISSED_PAYMENT_PENALTY = 10
    ON_TIME_BONUS = 2
    RELATIONSHIP_BONUS_YEARLY = 5
    
    def __init__(self):
        self.logger = logger
    
    def initialize_credit_account(
        self,
        customer_id: str,
        credit_limit: Decimal = None
    ) -> Dict:
        """
        Initialize credit account for new customer
        
        Args:
            customer_id: Customer ID
            credit_limit: Credit limit (default if not provided)
            
        Returns:
            Dict: Credit account data
        """
        if credit_limit is None:
            credit_limit = self.DEFAULT_CREDIT_LIMIT
        
        return {
            "customer_id": customer_id,
            "credit_limit": float(credit_limit),
            "current_balance": 0.0,
            "credit_score": self.DEFAULT_CREDIT_SCORE,
            "credit_status": self.get_status_from_score(self.DEFAULT_CREDIT_SCORE),
            "total_transactions": 0,
            "on_time_payments": 0,
            "late_payments": 0,
            "missed_payments": 0,
            "last_payment_date": None,
            "last_transaction_date": None,
            "is_active": True,
            "is_blocked": False,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def record_transaction(
        self,
        customer_id: str,
        transaction_type: TransactionType,
        amount: Decimal,
        current_balance: Decimal,
        reference_id: Optional[str] = None,
        due_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Record a credit transaction
        
        Args:
            customer_id: Customer ID
            transaction_type: DEBIT, CREDIT, or ADJUSTMENT
            amount: Transaction amount
            current_balance: Balance before transaction
            reference_id: Invoice/Payment ID
            due_date: Due date (for DEBIT)
            description: Transaction description
            
        Returns:
            Dict: Transaction record
        """
        # Calculate new balance
        if transaction_type == TransactionType.DEBIT:
            new_balance = current_balance + amount
        elif transaction_type == TransactionType.CREDIT:
            new_balance = max(Decimal("0"), current_balance - amount)
        else:  # ADJUSTMENT
            new_balance = amount
        
        return {
            "customer_id": customer_id,
            "transaction_type": transaction_type.value,
            "amount": float(amount),
            "balance_before": float(current_balance),
            "balance_after": float(new_balance),
            "reference_id": reference_id,
            "due_date": due_date.isoformat() if due_date else None,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def record_payment(
        self,
        customer_id: str,
        payment_amount: Decimal,
        current_balance: Decimal,
        payment_date: date,
        is_on_time: bool,
        reference_number: Optional[str] = None
    ) -> Dict:
        """
        Record customer payment
        
        Args:
            customer_id: Customer ID
            payment_amount: Payment amount
            current_balance: Current balance before payment
            payment_date: Payment date
            is_on_time: Is payment on time?
            reference_number: Payment reference
            
        Returns:
            Dict: Payment record
        """
        # Record as CREDIT transaction
        transaction = self.record_transaction(
            customer_id,
            TransactionType.CREDIT,
            payment_amount,
            current_balance,
            reference_id=reference_number,
            description=f"Payment received: {reference_number}"
        )
        
        transaction["is_on_time"] = is_on_time
        transaction["payment_date"] = payment_date.isoformat()
        
        return transaction
    
    def calculate_credit_score(
        self,
        total_transactions: int,
        on_time_payments: int,
        late_payments: int,
        missed_payments: int,
        years_as_customer: float = 1.0,
        current_balance: Decimal = Decimal("0"),
        credit_limit: Decimal = Decimal("10000")
    ) -> int:
        """
        Calculate customer credit score (0-100)
        
        Args:
            total_transactions: Total transactions
            on_time_payments: On-time payments
            late_payments: Late payments
            missed_payments: Missed payments
            years_as_customer: Customer relationship duration
            current_balance: Current outstanding balance
            credit_limit: Credit limit
            
        Returns:
            int: Credit score (0-100)
        """
        score = 75  # Starting score
        
        # Transaction history (up to 20 points)
        if total_transactions > 0:
            on_time_ratio = on_time_payments / total_transactions
            score += int(on_time_ratio * 20)
        
        # Late/missed payments (penalties)
        score -= (late_payments * self.LATE_PAYMENT_PENALTY)
        score -= (missed_payments * self.MISSED_PAYMENT_PENALTY)
        
        # Relationship bonus (up to 10 points)
        years_bonus = min(10, int(years_as_customer * self.RELATIONSHIP_BONUS_YEARLY))
        score += years_bonus
        
        # Credit utilization (up to 10 points)
        if credit_limit > 0:
            utilization = current_balance / credit_limit
            if utilization < 0.5:  # Less than 50% utilized
                score += 10
            elif utilization < 0.7:  # 50-70% utilized
                score += 5
            # Over 70% utilization = no bonus
        
        # Clamp to 0-100
        return max(0, min(100, score))
    
    def get_status_from_score(self, score: int) -> str:
        """
        Get credit status from score
        
        Args:
            score: Credit score
            
        Returns:
            str: Status
        """
        if score >= 85:
            return CreditStatus.EXCELLENT.value
        elif score >= 70:
            return CreditStatus.GOOD.value
        elif score >= 50:
            return CreditStatus.FAIR.value
        else:
            return CreditStatus.POOR.value
    
    def can_extend_credit(
        self,
        credit_score: int,
        credit_status: str,
        requested_amount: Decimal,
        credit_limit: Decimal,
        current_balance: Decimal,
        is_blocked: bool = False
    ) -> Tuple[bool, str, Optional[Decimal]]:
        """
        Determine if credit can be extended
        
        Args:
            credit_score: Customer credit score
            credit_status: Customer credit status
            requested_amount: Requested credit amount
            credit_limit: Credit limit
            current_balance: Current balance
            is_blocked: Is customer blocked from credit?
            
        Returns:
            Tuple: (can_extend, reason, available_amount)
        """
        # Check if blocked
        if is_blocked:
            return (False, "Customer blocked from credit", Decimal("0"))
        
        # Check available balance
        available = credit_limit - current_balance
        
        if requested_amount > available:
            return (False, f"Exceeds credit limit. Available: {available}", available)
        
        # Check credit status
        if credit_status == CreditStatus.POOR.value:
            new_limit = credit_limit * Decimal("0.5")
            if requested_amount > new_limit:
                return (False, "Poor credit status. Limited credit available", new_limit)
        
        return (True, "Credit approved", available)
    
    def get_payment_reminder_message(
        self,
        customer_name: str,
        outstanding_amount: Decimal,
        due_date: date,
        reminder_type: str = "SMS"
    ) -> str:
        """
        Generate payment reminder message
        
        Args:
            customer_name: Customer name
            outstanding_amount: Outstanding amount
            due_date: Payment due date
            reminder_type: SMS, EMAIL, WHATSAPP
            
        Returns:
            str: Reminder message
        """
        days_until_due = (due_date - date.today()).days
        
        if reminder_type == "SMS":
            if days_until_due > 0:
                return f"Hi {customer_name}, Your payment of ₹{outstanding_amount} is due on {due_date}. Please clear at your earliest."
            else:
                days_overdue = abs(days_until_due)
                return f"Hi {customer_name}, Your payment of ₹{outstanding_amount} is {days_overdue} days overdue. Please pay immediately."
        
        elif reminder_type == "EMAIL":
            if days_until_due > 0:
                subject = "Payment Reminder"
                body = f"Dear {customer_name},\n\nThis is a reminder that your payment of ₹{outstanding_amount} is due on {due_date}.\n\nPlease arrange the payment at your earliest convenience.\n\nThank you!"
            else:
                days_overdue = abs(days_until_due)
                subject = "Urgent: Overdue Payment"
                body = f"Dear {customer_name},\n\nYour payment of ₹{outstanding_amount} is now {days_overdue} days overdue.\n\nPlease remit payment immediately to avoid suspension of credit.\n\nThank you!"
            
            return f"Subject: {subject}\n\n{body}"
        
        elif reminder_type == "WHATSAPP":
            if days_until_due > 0:
                return f"Payment due: ₹{outstanding_amount}\nDue date: {due_date}\nPlease pay on time. Thank you!"
            else:
                days_overdue = abs(days_until_due)
                return f"⚠️ Overdue Payment Alert ⚠️\nAmount: ₹{outstanding_amount}\nDays Overdue: {days_overdue}\nPlease pay immediately!"
        
        return ""
    
    def generate_aging_report(
        self,
        customers: List[Dict]
    ) -> Dict:
        """
        Generate aging report for all customers
        
        Args:
            customers: List of customer credit data
            
        Returns:
            Dict: Aging report
        """
        current_date = date.today()
        aging_buckets = {
            "current": Decimal("0"),  # 0-30 days
            "30_60": Decimal("0"),  # 31-60 days
            "60_90": Decimal("0"),  # 61-90 days
            "90_plus": Decimal("0")  # 90+ days
        }
        
        for customer in customers:
            balance = Decimal(str(customer.get("current_balance", 0)))
            last_transaction = customer.get("last_transaction_date")
            
            if last_transaction:
                days_old = (current_date - datetime.fromisoformat(last_transaction).date()).days
                
                if days_old <= 30:
                    aging_buckets["current"] += balance
                elif days_old <= 60:
                    aging_buckets["30_60"] += balance
                elif days_old <= 90:
                    aging_buckets["60_90"] += balance
                else:
                    aging_buckets["90_plus"] += balance
        
        total = sum(aging_buckets.values())
        
        return {
            "total_outstanding": float(total),
            "current_0_30_days": float(aging_buckets["current"]),
            "overdue_31_60_days": float(aging_buckets["30_60"]),
            "overdue_61_90_days": float(aging_buckets["60_90"]),
            "overdue_90_plus_days": float(aging_buckets["90_plus"]),
            "percentage_current": float((aging_buckets["current"] / total * 100) if total > 0 else 0),
            "percentage_overdue": float(((total - aging_buckets["current"]) / total * 100) if total > 0 else 0)
        }
    
    def get_credit_analysis(self, customer_credit: Dict) -> Dict:
        """
        Get detailed credit analysis for a customer
        
        Args:
            customer_credit: Customer credit data
            
        Returns:
            Dict: Credit analysis
        """
        score = customer_credit.get("credit_score", 75)
        status = self.get_status_from_score(score)
        
        available = Decimal(str(customer_credit.get("credit_limit", 0))) - Decimal(str(customer_credit.get("current_balance", 0)))
        
        return {
            "customer_id": customer_credit.get("customer_id"),
            "credit_limit": customer_credit.get("credit_limit"),
            "current_balance": customer_credit.get("current_balance"),
            "available_credit": float(available),
            "credit_score": score,
            "credit_status": status,
            "utilization_percentage": float((Decimal(str(customer_credit.get("current_balance", 0))) / Decimal(str(customer_credit.get("credit_limit", 1)))) * 100),
            "payment_history": {
                "total_transactions": customer_credit.get("total_transactions", 0),
                "on_time_payments": customer_credit.get("on_time_payments", 0),
                "late_payments": customer_credit.get("late_payments", 0),
                "missed_payments": customer_credit.get("missed_payments", 0),
                "on_time_percentage": float((customer_credit.get("on_time_payments", 0) / max(1, customer_credit.get("total_transactions", 1))) * 100)
            },
            "recommendation": self._get_recommendation(score, available)
        }
    
    def _get_recommendation(self, score: int, available: Decimal) -> str:
        """Get credit recommendation"""
        if score >= 85:
            return "Excellent customer. Approve credit requests."
        elif score >= 70:
            return "Good customer. Approve up to available limit."
        elif score >= 50:
            return "Fair customer. Approve with monitoring."
        else:
            return "Poor customer. Consider credit freeze or manual review."


# Initialize global service
phase2_credit_service = Phase2CreditService()
