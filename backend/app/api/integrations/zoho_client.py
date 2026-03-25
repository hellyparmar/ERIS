"""
Zoho Books REST API Client
Handles all API calls to Zoho Books
"""

import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.api.integrations.zoho_auth import ZohoAuthService, ZOHO_API_BASE_URL


class ZohoAPIError(Exception):
    """Custom exception for Zoho API errors"""
    pass


class ZohoRateLimitError(ZohoAPIError):
    """Raised when rate limit is exceeded"""
    pass


class ZohoClient:
    """Zoho Books API Client"""
    
    def __init__(self, auth_service: ZohoAuthService, organization_id: str):
        self.auth_service = auth_service
        self.organization_id = organization_id
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = ZOHO_API_BASE_URL

    async def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with valid token"""
        token = await self.auth_service.get_valid_token(self.organization_id)
        
        if not token:
            raise ZohoAPIError("Not authenticated with Zoho Books")
        
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make API request to Zoho Books
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/items')
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            API response data
        """
        headers = await self._get_headers()
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                raise ZohoRateLimitError("Rate limit exceeded. Please try again later.")
            
            # Handle errors
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                raise ZohoAPIError(f"Zoho API error: {error_message}")
            
            # Parse response
            data = response.json()
            
            # Zoho wraps responses in different keys
            if data.get("code") == 0:  # Success
                return data
            else:
                raise ZohoAPIError(data.get("message", "Unknown error"))
                
        except httpx.HTTPError as e:
            raise ZohoAPIError(f"HTTP error: {str(e)}")

    # ========== Items (Products) API ==========
    
    async def get_items(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all items (products) from Zoho Books
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page (max 200)
            
        Returns:
            dict with items list and pagination info
        """
        params = {
            "page": page,
            "per_page": min(per_page, 200)
        }
        
        response = await self._make_request("GET", "/items", params=params)
        
        return {
            "items": response.get("items", []),
            "page_context": response.get("page_context", {}),
            "total": response.get("page_context", {}).get("total", 0)
        }

    async def get_item_by_id(self, item_id: str) -> Dict[str, Any]:
        """Get single item by ID"""
        response = await self._make_request("GET", f"/items/{item_id}")
        return response.get("item", {})

    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new item in Zoho Books
        
        Args:
            item_data: Item data (name, rate, description, etc.)
            
        Returns:
            Created item data
        """
        response = await self._make_request("POST", "/items", json_data=item_data)
        return response.get("item", {})

    async def update_item(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing item"""
        response = await self._make_request("PUT", f"/items/{item_id}", json_data=item_data)
        return response.get("item", {})

    async def delete_item(self, item_id: str) -> bool:
        """Delete item"""
        await self._make_request("DELETE", f"/items/{item_id}")
        return True

    # ========== Contacts (Customers) API ==========
    
    async def get_contacts(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all contacts (customers) from Zoho Books
        
        Args:
            page: Page number
            per_page: Contacts per page (max 200)
            
        Returns:
            dict with contacts list
        """
        params = {
            "page": page,
            "per_page": min(per_page, 200)
        }
        
        response = await self._make_request("GET", "/contacts", params=params)
        
        return {
            "contacts": response.get("contacts", []),
            "page_context": response.get("page_context", {}),
            "total": response.get("page_context", {}).get("total", 0)
        }

    async def get_contact_by_id(self, contact_id: str) -> Dict[str, Any]:
        """Get single contact by ID"""
        response = await self._make_request("GET", f"/contacts/{contact_id}")
        return response.get("contact", {})

    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact"""
        response = await self._make_request("POST", "/contacts", json_data=contact_data)
        return response.get("contact", {})

    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact"""
        response = await self._make_request("PUT", f"/contacts/{contact_id}", json_data=contact_data)
        return response.get("contact", {})

    # ========== Invoices API ==========
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create invoice in Zoho Books
        
        Args:
            invoice_data: Invoice data with line items
            
        Returns:
            Created invoice data
        """
        response = await self._make_request("POST", "/invoices", json_data=invoice_data)
        return response.get("invoice", {})

    async def get_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Get invoice by ID"""
        response = await self._make_request("GET", f"/invoices/{invoice_id}")
        return response.get("invoice", {})

    async def update_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing invoice"""
        response = await self._make_request("PUT", f"/invoices/{invoice_id}", json_data=invoice_data)
        return response.get("invoice", {})

    async def get_invoices(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get all invoices"""
        params = {
            "page": page,
            "per_page": min(per_page, 200)
        }
        
        response = await self._make_request("GET", "/invoices", params=params)
        
        return {
            "invoices": response.get("invoices", []),
            "page_context": response.get("page_context", {}),
            "total": response.get("page_context", {}).get("total", 0)
        }

    # ========== Organizations API ==========
    
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get list of organizations in Zoho Books account
        
        Returns:
            List of organization data
        """
        response = await self._make_request("GET", "/organizations")
        return response.get("organizations", [])

    async def get_organization_details(self, organization_id: str) -> Dict[str, Any]:
        """Get details of specific organization"""
        # Note: This uses the organization_id from Zoho, not R-DIOS
        response = await self._make_request("GET", f"/organizations/{organization_id}")
        return response.get("organization", {})

    # ========== Utility Methods ==========
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Zoho Books
        
        Returns:
            Connection status and user info
        """
        try:
            orgs = await self.get_organizations()
            
            return {
                "connected": True,
                "organizations": orgs,
                "organization_count": len(orgs)
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
