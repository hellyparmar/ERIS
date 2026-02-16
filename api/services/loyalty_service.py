"""
Enterprise Retail Intelligence System v3.0
Loyalty Service - Loyalty points management and tier system
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from api.models.customer import Customer
from api.models.loyalty_transaction import LoyaltyTransaction


class LoyaltyService:
    """Service for loyalty points management"""
    
    # Tier thresholds
    TIER_THRESHOLDS = {
        'Bronze': 0,
        'Silver': 1000,
        'Gold': 5000,
        'Platinum': 10000
    }
    
    # Points earning rate (1 point per ₹10 spent)
    POINTS_PER_RUPEE = 0.1
    
    # Points expiry (1 year)
    EXPIRY_DAYS = 365
    
    @staticmethod
    def earn_points(
        db: Session,
        customer_id: int,
        sale_id: Optional[int],
        amount: float,
        notes: Optional[str] = None
    ) -> Dict:
        """Award loyalty points for a purchase"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Calculate points
        points = int(amount * LoyaltyService.POINTS_PER_RUPEE)
        
        if points <= 0:
            return {
                'success': False,
                'message': 'Amount too small to earn points'
            }
        
        # Update customer points
        customer.loyalty_points += points
        
        # Create transaction record
        transaction = LoyaltyTransaction(
            customer_id=customer_id,
            sale_id=sale_id,
            transaction_type='earn',
            points=points,
            balance_after=customer.loyalty_points,
            notes=notes or f'Earned from purchase of ₹{amount:.2f}',
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        
        # Update tier
        old_tier = customer.loyalty_tier
        new_tier = LoyaltyService._calculate_tier(customer.loyalty_points)
        customer.loyalty_tier = new_tier
        
        db.commit()
        
        return {
            'success': True,
            'points_earned': points,
            'total_points': customer.loyalty_points,
            'tier': new_tier,
            'tier_upgraded': new_tier != old_tier
        }
    
    @staticmethod
    def redeem_points(
        db: Session,
        customer_id: int,
        points: int,
        notes: Optional[str] = None
    ) -> Dict:
        """Redeem loyalty points"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        if customer.loyalty_points < points:
            return {
                'success': False,
                'message': f'Insufficient points. Available: {customer.loyalty_points}, Requested: {points}'
            }
        
        # Deduct points
        customer.loyalty_points -= points
        
        # Create transaction record
        transaction = LoyaltyTransaction(
            customer_id=customer_id,
            sale_id=None,
            transaction_type='redeem',
            points=-points,  # Negative for redemption
            balance_after=customer.loyalty_points,
            notes=notes or f'Redeemed {points} points',
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        
        # Update tier (might downgrade)
        customer.loyalty_tier = LoyaltyService._calculate_tier(customer.loyalty_points)
        
        db.commit()
        
        # Calculate discount value (1 point = ₹0.10)
        discount_value = points * 0.10
        
        return {
            'success': True,
            'points_redeemed': points,
            'discount_value': discount_value,
            'remaining_points': customer.loyalty_points,
            'tier': customer.loyalty_tier
        }
    
    @staticmethod
    def _calculate_tier(points: int) -> str:
        """Calculate loyalty tier based on points"""
        if points >= LoyaltyService.TIER_THRESHOLDS['Platinum']:
            return 'Platinum'
        elif points >= LoyaltyService.TIER_THRESHOLDS['Gold']:
            return 'Gold'
        elif points >= LoyaltyService.TIER_THRESHOLDS['Silver']:
            return 'Silver'
        else:
            return 'Bronze'
    
    @staticmethod
    def get_loyalty_balance(db: Session, customer_id: int) -> Dict:
        """Get customer's loyalty points balance and tier info"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        current_tier = customer.loyalty_tier
        current_points = customer.loyalty_points
        
        # Calculate next tier
        tier_order = ['Bronze', 'Silver', 'Gold', 'Platinum']
        current_tier_index = tier_order.index(current_tier)
        
        if current_tier_index < len(tier_order) - 1:
            next_tier = tier_order[current_tier_index + 1]
            next_tier_threshold = LoyaltyService.TIER_THRESHOLDS[next_tier]
            points_to_next_tier = next_tier_threshold - current_points
        else:
            next_tier = None
            next_tier_threshold = None
            points_to_next_tier = 0
        
        return {
            'customer_id': customer_id,
            'points': current_points,
            'tier': current_tier,
            'next_tier': next_tier,
            'points_to_next_tier': points_to_next_tier,
            'tier_thresholds': LoyaltyService.TIER_THRESHOLDS
        }
    
    @staticmethod
    def get_transaction_history(
        db: Session,
        customer_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get loyalty transaction history for a customer"""
        transactions = db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.customer_id == customer_id
        ).order_by(desc(LoyaltyTransaction.created_at)).limit(limit).all()
        
        return [t.to_dict() for t in transactions]
    
    @staticmethod
    def expire_old_points(db: Session) -> Dict:
        """Expire points older than EXPIRY_DAYS"""
        expiry_date = datetime.utcnow() - timedelta(days=LoyaltyService.EXPIRY_DAYS)
        
        # Find old earn transactions
        old_transactions = db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.transaction_type == 'earn',
            LoyaltyTransaction.created_at < expiry_date
        ).all()
        
        expired_count = 0
        total_expired_points = 0
        
        for transaction in old_transactions:
            customer = db.query(Customer).filter(Customer.id == transaction.customer_id).first()
            
            if customer and customer.loyalty_points >= transaction.points:
                # Deduct expired points
                customer.loyalty_points -= transaction.points
                
                # Create expiry transaction
                expiry_transaction = LoyaltyTransaction(
                    customer_id=customer.id,
                    sale_id=None,
                    transaction_type='expire',
                    points=-transaction.points,
                    balance_after=customer.loyalty_points,
                    notes=f'Expired points from {transaction.created_at.date()}',
                    created_at=datetime.utcnow()
                )
                
                db.add(expiry_transaction)
                
                # Update tier
                customer.loyalty_tier = LoyaltyService._calculate_tier(customer.loyalty_points)
                
                expired_count += 1
                total_expired_points += transaction.points
        
        db.commit()
        
        return {
            'expired_transactions': expired_count,
            'total_expired_points': total_expired_points
        }
    
    @staticmethod
    def get_tier_benefits() -> Dict:
        """Get tier benefits information"""
        return {
            'Bronze': {
                'points_required': 0,
                'benefits': ['1 point per ₹10 spent', 'Birthday bonus: 50 points']
            },
            'Silver': {
                'points_required': 1000,
                'benefits': ['1.2 points per ₹10 spent', 'Birthday bonus: 100 points', '5% discount on select items']
            },
            'Gold': {
                'points_required': 5000,
                'benefits': ['1.5 points per ₹10 spent', 'Birthday bonus: 200 points', '10% discount on select items', 'Early access to sales']
            },
            'Platinum': {
                'points_required': 10000,
                'benefits': ['2 points per ₹10 spent', 'Birthday bonus: 500 points', '15% discount on select items', 'Early access to sales', 'Free delivery']
            }
        }
