import os

test_code = """
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_active_user, get_db, get_db_sync_dependency
from unittest.mock import MagicMock

client = TestClient(app)

class TestRouterDataIsolation(unittest.TestCase):
    def setUp(self):
        self.outlet_1_id = 10
        self.outlet_2_id = 20
        
        self.manager_a = Mock()
        self.manager_a.id = 1
        self.manager_a.role = UserRoleEnum.outlet_manager
        self.manager_a.outlet_id = self.outlet_1_id
        acc_a = Mock(spec=UserOutletAccess)
        acc_a.outlet_id = self.outlet_1_id
        self.manager_a.outlet_access = [acc_a]

        self.manager_b = Mock()
        self.manager_b.id = 2
        self.manager_b.role = UserRoleEnum.outlet_manager
        self.manager_b.outlet_id = self.outlet_2_id
        acc_b = Mock(spec=UserOutletAccess)
        acc_b.outlet_id = self.outlet_2_id
        self.manager_b.outlet_access = [acc_b]
        
    def _override_user(self, user_mock):
        app.dependency_overrides[get_current_active_user] = lambda: user_mock
        app.dependency_overrides[get_db] = lambda: AsyncMock()
        try:
            app.dependency_overrides[get_db_sync_dependency] = lambda: MagicMock()
        except:
            pass

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_sales_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/sales/?outlet_id={self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)
        
        res = client.get(f"/api/v1/sales/?outlet_id={self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)

    def test_forecasting_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/forecasting/sales-forecast?outlet_id={self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)
        
        res = client.get(f"/api/v1/forecasting/sales-forecast?outlet_id={self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)

    def test_causal_analysis_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/causal/holiday-impact?outlet_id={self.outlet_2_id}&year=2023")
        self.assertEqual(res.status_code, 403)
        
        res = client.get(f"/api/v1/causal/holiday-impact?outlet_id={self.outlet_1_id}&year=2023")
        self.assertNotEqual(res.status_code, 403)

    def test_employees_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/employees/?store_id={self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)
        
        res = client.get(f"/api/v1/employees/?store_id={self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)

    def test_outlets_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/outlets/{self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)
        
        res = client.get(f"/api/v1/outlets/{self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)
"""

with open('backend/tests/unit/test_data_isolation.py', 'r') as f:
    content = f.read()

if 'TestRouterDataIsolation' not in content:
    content = content.replace('if __name__ == "__main__":', test_code + '\nif __name__ == "__main__":')
    with open('backend/tests/unit/test_data_isolation.py', 'w') as f:
        f.write(content)
