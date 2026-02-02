"""
Community Commerce Service - Stock Swapping & Bulk Buying
Marketplace for retailers to exchange dead stock and aggregate purchasing
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from api.db.models import (
    CommunityListing, BulkBuyGroup, BulkBuyParticipant,
    Product, User, ListingType
)

class CommunityCommerceService:
    """Service for stock swapping and bulk buying"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== STOCK SWAPPING ====================
    
    def create_stock_listing(
        self,
        retailer_id: int,
        product_id: int,
        quantity: int,
        price_per_unit: Decimal,
        reason: str,
        location: str,
        expires_days: int = 30
    ) -> CommunityListing:
        """
        Create a stock swap listing
        
        Args:
            retailer_id: User ID of retailer
            product_id: Product to sell
            quantity: Units available
            price_per_unit: Selling price
            reason: 'dead_stock', 'overstock', 'seasonal'
            location: City/area for pickup
            expires_days: Listing expires in X days
        
        Returns:
            Created listing
        """
        listing = CommunityListing(
            listing_type=ListingType.STOCK_SWAP,
            retailer_id=retailer_id,
            product_id=product_id,
            quantity_available=quantity,
            price_per_unit=price_per_unit,
            reason=reason,
            location=location,
            expires_at=datetime.now() + timedelta(days=expires_days),
            status="active"
        )
        
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        
        return listing
    
    def get_available_listings(
        self,
        location: Optional[str] = None,
        reason: Optional[str] = None,
        product_category: Optional[str] = None,
        limit: int = 50
    ) -> List[CommunityListing]:
        """
        Get active stock swap listings
        
        Args:
            location: Filter by location
            reason: Filter by reason (dead_stock, overstock, seasonal)
            product_category: Filter by product category
            limit: Max listings to return
        
        Returns:
            List of active listings
        """
        query = self.db.query(CommunityListing).filter(
            and_(
                CommunityListing.listing_type == ListingType.STOCK_SWAP,
                CommunityListing.status == "active",
                CommunityListing.expires_at > datetime.now()
            )
        )
        
        if location:
            query = query.filter(CommunityListing.location.ilike(f"%{location}%"))
        
        if reason:
            query = query.filter(CommunityListing.reason == reason)
        
        if product_category:
            query = query.join(Product).filter(Product.category == product_category)
        
        return query.order_by(CommunityListing.created_at.desc()).limit(limit).all()
    
    def find_matching_listings(
        self,
        product_id: int,
        location: str,
        max_distance_km: int = 50
    ) -> List[CommunityListing]:
        """
        Find listings that match buyer's needs
        
        Args:
            product_id: Product buyer wants
            location: Buyer's location
            max_distance_km: Maximum distance for matches
        
        Returns:
            Matching listings sorted by relevance
        """
        # For MVP, simple location-based matching
        # In production, would use geospatial distance calculation
        
        return self.db.query(CommunityListing).filter(
            and_(
                CommunityListing.product_id == product_id,
                CommunityListing.location.ilike(f"%{location}%"),
                CommunityListing.status == "active",
                CommunityListing.expires_at > datetime.now()
            )
        ).order_by(CommunityListing.price_per_unit.asc()).all()
    
    def mark_listing_matched(self, listing_id: int, buyer_id: int) -> CommunityListing:
        """Mark listing as matched with a buyer"""
        listing = self.db.query(CommunityListing).filter(
            CommunityListing.id == listing_id
        ).first()
        
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        if listing.status != "active":
            raise ValueError(f"Listing is not active (status: {listing.status})")
        
        listing.status = "matched"
        self.db.commit()
        self.db.refresh(listing)
        
        return listing
    
    def get_dead_stock_opportunities(
        self,
        min_days_no_sale: int = 180
    ) -> List[Dict]:
        """
        Find dead stock that could be listed for swapping
        
        Args:
            min_days_no_sale: Minimum days since last sale
        
        Returns:
            List of products with dead stock info
        """
        products = self.db.query(Product).filter(
            and_(
                Product.is_dead_stock == True,
                Product.days_since_last_sale >= min_days_no_sale
            )
        ).limit(100).all()
        
        opportunities = []
        for product in products:
            # Check if already listed
            existing = self.db.query(CommunityListing).filter(
                and_(
                    CommunityListing.product_id == product.id,
                    CommunityListing.status == "active"
                )
            ).first()
            
            if not existing:
                opportunities.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "days_no_sale": product.days_since_last_sale,
                    "cost_price": float(product.cost_price) if product.cost_price else 0,
                    "suggested_price": float(product.cost_price * Decimal("0.7")) if product.cost_price else 0,
                    "hsn_code": product.hsn_code
                })
        
        return opportunities
    
    # ==================== BULK BUYING ====================
    
    def create_bulk_buy_group(
        self,
        coordinator_id: int,
        product_id: int,
        target_quantity: int,
        target_price: Decimal,
        deadline_days: int = 14
    ) -> BulkBuyGroup:
        """
        Create a bulk buying group
        
        Args:
            coordinator_id: User organizing the bulk buy
            product_id: Product to buy in bulk
            target_quantity: Minimum units needed
            target_price: Target price per unit
            deadline_days: Group closes in X days
        
        Returns:
            Created bulk buy group
        """
        group = BulkBuyGroup(
            product_id=product_id,
            target_quantity=target_quantity,
            current_quantity=0,
            target_price=target_price,
            coordinator_id=coordinator_id,
            status="forming",
            deadline=datetime.now() + timedelta(days=deadline_days)
        )
        
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        return group
    
    def join_bulk_buy_group(
        self,
        group_id: int,
        retailer_id: int,
        quantity: int
    ) -> BulkBuyParticipant:
        """
        Join a bulk buying group
        
        Args:
            group_id: Bulk buy group ID
            retailer_id: Retailer joining
            quantity: Units they want to buy
        
        Returns:
            Participant record
        """
        group = self.db.query(BulkBuyGroup).filter(
            BulkBuyGroup.id == group_id
        ).first()
        
        if not group:
            raise ValueError(f"Bulk buy group {group_id} not found")
        
        if group.status not in ["forming", "ready"]:
            raise ValueError(f"Group is not accepting participants (status: {group.status})")
        
        if group.deadline < datetime.now():
            raise ValueError("Group deadline has passed")
        
        # Check if already participating
        existing = self.db.query(BulkBuyParticipant).filter(
            and_(
                BulkBuyParticipant.group_id == group_id,
                BulkBuyParticipant.retailer_id == retailer_id
            )
        ).first()
        
        if existing:
            raise ValueError("Already participating in this group")
        
        # Create participant
        participant = BulkBuyParticipant(
            group_id=group_id,
            retailer_id=retailer_id,
            quantity=quantity
        )
        
        self.db.add(participant)
        
        # Update group quantity
        group.current_quantity += quantity
        
        # Check if target reached
        if group.current_quantity >= group.target_quantity:
            group.status = "ready"
        
        self.db.commit()
        self.db.refresh(participant)
        
        return participant
    
    def get_active_bulk_buy_groups(
        self,
        product_category: Optional[str] = None,
        limit: int = 50
    ) -> List[BulkBuyGroup]:
        """Get active bulk buying groups"""
        query = self.db.query(BulkBuyGroup).filter(
            and_(
                BulkBuyGroup.status.in_(["forming", "ready"]),
                BulkBuyGroup.deadline > datetime.now()
            )
        )
        
        if product_category:
            query = query.join(Product).filter(Product.category == product_category)
        
        return query.order_by(BulkBuyGroup.created_at.desc()).limit(limit).all()
    
    def get_bulk_buy_details(self, group_id: int) -> Dict:
        """Get detailed information about a bulk buy group"""
        group = self.db.query(BulkBuyGroup).filter(
            BulkBuyGroup.id == group_id
        ).first()
        
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        participants = self.db.query(BulkBuyParticipant).filter(
            BulkBuyParticipant.group_id == group_id
        ).all()
        
        product = self.db.query(Product).filter(Product.id == group.product_id).first()
        
        return {
            "group": {
                "id": group.id,
                "product_id": group.product_id,
                "product_name": product.name if product else "Unknown",
                "target_quantity": group.target_quantity,
                "current_quantity": group.current_quantity,
                "target_price": float(group.target_price),
                "status": group.status,
                "deadline": group.deadline.isoformat(),
                "progress_percentage": (group.current_quantity / group.target_quantity * 100) if group.target_quantity > 0 else 0
            },
            "participants": [
                {
                    "retailer_id": p.retailer_id,
                    "quantity": p.quantity,
                    "joined_at": p.joined_at.isoformat()
                }
                for p in participants
            ],
            "participant_count": len(participants),
            "quantity_remaining": group.target_quantity - group.current_quantity
        }
    
    def finalize_bulk_buy(self, group_id: int) -> BulkBuyGroup:
        """Mark bulk buy as ordered"""
        group = self.db.query(BulkBuyGroup).filter(
            BulkBuyGroup.id == group_id
        ).first()
        
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        if group.status != "ready":
            raise ValueError(f"Group is not ready to order (status: {group.status})")
        
        group.status = "ordered"
        self.db.commit()
        self.db.refresh(group)
        
        return group
    
    def get_marketplace_stats(self) -> Dict:
        """Get overall marketplace statistics"""
        active_listings = self.db.query(CommunityListing).filter(
            and_(
                CommunityListing.status == "active",
                CommunityListing.expires_at > datetime.now()
            )
        ).count()
        
        matched_listings = self.db.query(CommunityListing).filter(
            CommunityListing.status == "matched"
        ).count()
        
        active_groups = self.db.query(BulkBuyGroup).filter(
            BulkBuyGroup.status.in_(["forming", "ready"])
        ).count()
        
        ready_groups = self.db.query(BulkBuyGroup).filter(
            BulkBuyGroup.status == "ready"
        ).count()
        
        total_participants = self.db.query(BulkBuyParticipant).count()
        
        return {
            "stock_swapping": {
                "active_listings": active_listings,
                "matched_listings": matched_listings,
                "match_rate": (matched_listings / (active_listings + matched_listings) * 100) if (active_listings + matched_listings) > 0 else 0
            },
            "bulk_buying": {
                "active_groups": active_groups,
                "ready_to_order": ready_groups,
                "total_participants": total_participants,
                "avg_participants_per_group": (total_participants / active_groups) if active_groups > 0 else 0
            }
        }
