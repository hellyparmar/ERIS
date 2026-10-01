import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
from app.models.base import Base
from app.models.commerce import SaleItem


class TestCanonicalModels(unittest.TestCase):
    """Unit tests for newly consolidated and canonical models"""

    def test_sale_item_model(self):
        """Test SaleItem model definition and attributes"""
        self.assertTrue(hasattr(Base.metadata.tables, "get"))
        self.assertIn("sale_items", Base.metadata.tables)
        item = SaleItem(
            sale_id=1, product_id=10, quantity=5, unit_price=120.50, discount_percent=5.0, line_total=572.38
        )
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.unit_price, 120.50)
        self.assertEqual(item.line_total, 572.38)


if __name__ == "__main__":
    unittest.main()
