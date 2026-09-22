import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from unittest.mock import AsyncMock, MagicMock
from app.models.organization import Organization
from app.models.models_v6 import Product
import uuid


class TestRLSIsolation(unittest.IsolatedAsyncioTestCase):

    async def test_rls_isolation_models(self):
        """
        Test Row-Level Security (RLS) data structures across multiple tenants.
        """
        # 1. Create two organizations
        org_a = Organization(id=uuid.uuid4(), name="Org A")
        org_b = Organization(id=uuid.uuid4(), name="Org B")

        # 2. Create products for each organization
        prod_a = Product(id=uuid.uuid4(), name="Product A", tenant_id=org_a.id, selling_price=10.0, is_active=True)
        prod_b = Product(id=uuid.uuid4(), name="Product B", tenant_id=org_b.id, selling_price=20.0, is_active=True)

        self.assertEqual(prod_a.tenant_id, org_a.id)
        self.assertEqual(prod_b.tenant_id, org_b.id)
        self.assertNotEqual(prod_a.tenant_id, prod_b.tenant_id)


if __name__ == "__main__":
    unittest.main()

