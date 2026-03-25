import os
import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MSG91WhatsAppClient:
    """
    Client for MSG91 WhatsApp API.
    Ref: https://docs.msg91.com/p/tf9G97vpt/MSG91-API-Reference
    """

    def __init__(self, auth_key: Optional[str] = None, sender: Optional[str] = None):
        self.auth_key = auth_key or os.getenv("MSG91_API_KEY")
        self.sender = sender or os.getenv("MSG91_SENDER_ID")
        self.base_url = "https://api.msg91.com/api/v5/whatsapp/whatsapp-outbound-message/bulk/"

        if not self.auth_key:
            logger.warning("MSG91_API_KEY not found in environment.")

    def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        variables: List[str],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Send a template-based WhatsApp message.
        'to' should be in E.164 format (e.g., 919876543210)
        """
        if not self.auth_key:
            return {"status": "error", "message": "API key missing"}

        payload = {
            "integrated_number": self.sender,
            "content_type": "template",
            "payload": {
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "policy": "deterministic",
                        "code": language
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": v} for v in variables
                            ]
                        }
                    ]
                }
            }
        }

        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send MSG91 WhatsApp message: {e}")
            return {"status": "error", "message": str(e)}
