from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.tenant_context import TenantContextManager
import logging

logger = logging.getLogger(__name__)

class RLSMiddleware(BaseHTTPMiddleware):
    """
    Tenant context middleware.

    Extracts the tenant/outlet context from the Bearer JWT and attaches it
    to ``request.state.tenant_context`` so downstream dependencies can use it
    without re-decoding the token.

    This middleware does NOT enforce PostgreSQL row-level security at the
    database session level.  DB-level isolation (SET LOCAL app.tenant_id) is
    the responsibility of the ``get_db`` dependency / query executor.
    """
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                await TenantContextManager.extract_from_request(request)
            except Exception as e:
                # Log but do not block — public/unauthenticated endpoints must
                # still work.  Authenticated endpoints enforce context via deps.
                logger.debug(f"Could not extract tenant context in middleware: {e}")

        return await call_next(request)
