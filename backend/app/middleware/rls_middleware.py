from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.tenant_context import TenantContextManager
import logging

logger = logging.getLogger(__name__)

class RLSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Extracts tenant context from the authenticated user/JWT token
        and attaches it to request.state.tenant_context.
        """
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # This will populate request.state.tenant_context
                await TenantContextManager.extract_from_request(request)
            except Exception as e:
                # We log but do not block here, so public endpoints can still work.
                # Endpoints needing tenant context will enforce it via dependencies.
                logger.debug(f"Could not extract tenant context in middleware: {e}")
                
        return await call_next(request)
