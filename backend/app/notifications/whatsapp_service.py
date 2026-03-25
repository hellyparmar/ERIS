import logging
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_key = settings.MSG91_API_KEY
        self.sender_id = settings.MSG91_SENDER_ID
        self.base_url = "https://api.msg91.com/api/v5/whatsapp/whatsapp-outbound-message/"

    def is_configured(self) -> bool:
        """Check if MSG91 API key exists"""
        return bool(self.api_key)

    async def send_template_message(self, phone: str, template_id: str, variables: Dict[str, str]) -> bool:
        """Send via MSG91 API"""
        if not self.is_configured():
            logger.warning("WhatsApp not configured (missing MSG91_API_KEY), skipping")
            return False

        # Normalize phone (remove +, add country code if missing - assuming 91 for India if not specified)
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone

        payload = {
            "integrated_number": "91XXXXXXXXXX", # This should normally come from settings if multi-number
            "content_type": "template",
            "payload": {
                "to": clean_phone,
                "type": "template",
                "template": {
                    "name": template_id,
                    "language": {"code": "en"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": val} for val in variables.values()
                            ]
                        }
                    ]
                }
            }
        }

        headers = {
            "authkey": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"WhatsApp template message sent to {phone}")
                return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {phone}: {str(e)}")
            return False

# Singleton Instance
whatsapp_service = WhatsAppService()
