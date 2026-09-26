"""
Unit tests for Odoo & Zoho Integration endpoints and encryption
"""

import unittest
from fastapi import HTTPException
from app.routers.integrations import (
    test_odoo_connection as api_test_odoo, test_zoho_connection as api_test_zoho,
    OdooConfigRequest, ZohoConfigRequest
)
from app.api.utils.encryption import encrypt_data, decrypt_data
import asyncio


class TestIntegrations(unittest.TestCase):

    def test_encryption_roundtrip(self):
        """Ensure sensitive API keys are correctly encrypted and decrypted via Fernet"""
        raw_key = "secret_odoo_api_key_12345"
        encrypted = encrypt_data(raw_key)
        self.assertNotEqual(raw_key, encrypted)
        decrypted = decrypt_data(encrypted)
        self.assertEqual(raw_key, decrypted)

    def test_odoo_test_connection_mock_mode(self):
        """Odoo test connection in mock mode returns success without external network call"""
        req = OdooConfigRequest(
            url="https://mock-odoo.test",
            db_name="mock_db",
            username="admin@test.com",
            api_key="MOCK_KEY_FOR_TESTS",  # not a real credential
            mock_mode=True
        )
        res = api_test_odoo(req)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("uid"), 9999)

    def test_odoo_test_connection_real_failure(self):
        """Odoo test connection against invalid domain raises HTTP 502 with real connection error"""
        req = OdooConfigRequest(
            url="http://localhost:59999",
            db_name="invalid_db",
            username="invalid_user",
            api_key="INVALID_KEY_FOR_TESTS",  # intentionally invalid to trigger 502
            mock_mode=False
        )
        with self.assertRaises(HTTPException) as ctx:
            api_test_odoo(req)
        self.assertEqual(ctx.exception.status_code, 502)

    def test_zoho_test_connection_mock_mode(self):
        """Zoho test connection in mock mode returns connected"""
        req = ZohoConfigRequest(
            org_id="60001234567",
            mock_mode=True
        )
        res = asyncio.run(api_test_zoho(req))
        self.assertTrue(res.get("connected"))

    def test_zoho_test_connection_real_failure(self):
        """Zoho test connection with unauthenticated credentials raises HTTP 502 or 400 with real error"""
        req = ZohoConfigRequest(
            org_id="60009999999",
            client_id="1000.INVALID",
            client_secret="INVALID_SECRET_FOR_TESTS",  # intentionally invalid to trigger 502
            mock_mode=False
        )
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(api_test_zoho(req))
        self.assertEqual(ctx.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
