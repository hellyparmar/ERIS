import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock

from app.models.notification import Notification, NotificationTypeEnum
from app.models.users import User, Role, UserOutletAccess
from app.models.outlet import Outlet
from app.models.inventory import Inventory
from app.models.models_v6 import Product


class TestNotificationModel(unittest.TestCase):

    def test_notification_model_fields(self):
        """Test notification model instance attributes"""
        notif = Notification(
            id=1,
            user_id=10,
            outlet_id=2,
            type=NotificationTypeEnum.low_stock,
            title="Test Title",
            message="Test message details",
            is_read=False,
            link="/inventory",
            created_at=datetime.now()
        )
        self.assertEqual(notif.id, 1)
        self.assertEqual(notif.user_id, 10)
        self.assertEqual(notif.outlet_id, 2)
        self.assertEqual(notif.type, NotificationTypeEnum.low_stock)
        self.assertEqual(notif.title, "Test Title")
        self.assertEqual(notif.message, "Test message details")
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.link, "/inventory")


if __name__ == "__main__":
    unittest.main()

