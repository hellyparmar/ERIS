import os
import requests
import logging
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """MSG91 based WhatsApp notification service"""

    def __init__(self):
        self.auth_key = settings.MSG91_API_KEY
        self.sender_id = settings.MSG91_SENDER_ID
        self.base_url = "https://api.msg91.com/api/v5/whatsapp/whatsapp-outbound-send"
        self.enabled = settings.ENABLE_WHATSAPP and bool(self.auth_key)

    def send_template_message(
        self, 
        phone: str, 
        template_name: str, 
        variables: List[str]
    ) -> Dict[str, Any]:
        """Send a WhatsApp template message via MSG91"""
        if not self.enabled:
            logger.info("WhatsApp service skipped (disabled or no API key).")
            return {"success": False, "error": "WhatsApp service not active", "skipped": True}

        # MSG91 payload format (V5 API)
        # Note: Exact payload depends on template mapping
        payload = {
            "integrated_number": self.sender_id,
            "content_type": "template",
            "payload": {
                "to": phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en", "policy": "deterministic"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": v} for v in variables]
                        }
                    ]
                }
            }
        }

        headers = {
            "authkey": self.auth_key,
            "content-type": "application/json"
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                logger.info(f"WhatsApp message sent to {phone}")
                return {"success": True}
            else:
                logger.error(f"WhatsApp failed: {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {e}")
            return {"success": False, "error": str(e)}

# Singleton Instance
whatsapp_service = WhatsAppService()
