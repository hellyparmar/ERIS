import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
from app.models.base import Base
from app.models.models_v6 import SaleItem, Sale, Product
from app.models.loyalty import LoyaltyAccount, LoyaltyPoints, LoyaltyBonus
from app.models.odoo_config import OdooConfig
from app.models.payment_status import PaymentStatus
from app.models.community import CommunityListing


class TestCanonicalModels(unittest.TestCase):
    """Unit tests for newly consolidated and canonical models"""

    def test_sale_item_model(self):
        """Test SaleItem model definition and attributes"""
        self.assertTrue(hasattr(Base.metadata.tables, "get"))
        self.assertIn("sale_items", Base.metadata.tables)
        item = SaleItem(
            sale_id=1,
            product_id=10,
            quantity=5,
            unit_price=120.50,
            discount_percent=5.0,
            line_total=572.38
        )
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.unit_price, 120.50)
        self.assertEqual(item.line_total, 572.38)

    def test_loyalty_models(self):
        """Test LoyaltyAccount, LoyaltyPoints, LoyaltyBonus definitions"""
        self.assertIn("loyalty_accounts", Base.metadata.tables)
        self.assertIn("loyalty_points", Base.metadata.tables)
        self.assertIn("loyalty_bonuses", Base.metadata.tables)

        account = LoyaltyAccount(
            customer_id=101,
            points_balance=350,
            tier="gold",
            lifetime_points=1200
        )
        self.assertEqual(account.points_balance, 350)
        self.assertEqual(account.tier, "gold")

        points_entry = LoyaltyPoints(
            account_id=1,
            points=50,
            transaction_type="earned",
            reference_id="INV-2026-001"
        )
        self.assertEqual(points_entry.points, 50)
        self.assertEqual(points_entry.transaction_type, "earned")

        bonus = LoyaltyBonus(
            account_id=1,
            bonus_points=100,
            reason="Festival Welcome Bonus",
            is_claimed=False
        )
        self.assertEqual(bonus.bonus_points, 100)
        self.assertFalse(bonus.is_claimed)

    def test_odoo_config_model(self):
        """Test OdooConfig model definition"""
        self.assertIn("odoo_configs", Base.metadata.tables)
        config = OdooConfig(
            organization_id=1,
            url="https://erp.retailcompany.com",
            database_name="retail_prod_db",
            username="admin@retailcompany.com",
            api_key="sec_token_999",
            sync_products=True,
            sync_customers=True,
            sync_invoices=True
        )
        self.assertEqual(config.url, "https://erp.retailcompany.com")
        self.assertEqual(config.database_name, "retail_prod_db")
        self.assertTrue(config.sync_products)

    def test_payment_status_enum(self):
        """Test PaymentStatus enum values"""
        self.assertEqual(PaymentStatus.PENDING, "pending")
        self.assertEqual(PaymentStatus.COMPLETED, "completed")
        self.assertEqual(PaymentStatus.FAILED, "failed")
        self.assertEqual(PaymentStatus.REFUNDED, "refunded")
        self.assertEqual(PaymentStatus.CANCELLED, "cancelled")
        self.assertEqual(PaymentStatus.PARTIALLY_PAID, "partially_paid")

    def test_community_listing_model(self):
        """Test CommunityListing model definition"""
        self.assertIn("community_listings", Base.metadata.tables)
        listing = CommunityListing(
            organization_id=1,
            title="Local Artisan Bakery Pop-Up",
            description="Fresh sourdough and pastries available daily",
            category="marketplace",
            contact_name="Alice Baker",
            contact_info="alice@bakery.local",
            price=25.00,
            is_active=True
        )
        self.assertEqual(listing.title, "Local Artisan Bakery Pop-Up")
        self.assertEqual(listing.category, "marketplace")
        self.assertTrue(listing.is_active)


if __name__ == "__main__":
    unittest.main()
