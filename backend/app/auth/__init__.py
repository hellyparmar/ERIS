"""
backend/app/auth/__init__.py
Makes `app.auth` a proper package and re-exports all public auth symbols.
"""

from .auth import (   # noqa: F401
    validate_password,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    oauth2_scheme,
    get_current_user,
    require_role,
    require_admin,
    require_manager,
)
