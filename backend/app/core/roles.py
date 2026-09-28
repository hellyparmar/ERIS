"""Canonical role vocabulary for the single-organization ERIS application."""

from enum import Enum
from typing import Any


ADMIN = "admin"
MANAGER = "manager"
VIEWER = "viewer"
CANONICAL_ROLES = (ADMIN, MANAGER, VIEWER)

_ALIASES = {
    "admin": ADMIN,
    "super_admin": ADMIN,
    "superadmin": ADMIN,
    "administrator": ADMIN,
    "manager": MANAGER,
    "area_manager": MANAGER,
    "outlet_manager": MANAGER,
    "staff": MANAGER,
    "analyst": VIEWER,
    "viewer": VIEWER,
    "guest": VIEWER,
}


def normalize_role(value: Any) -> str:
    """Return one of admin/manager/viewer while accepting legacy role names."""
    if value is None:
        return VIEWER
    if isinstance(value, Enum):
        value = value.value
    elif not isinstance(value, str):
        enum_value = getattr(value, "value", None)
        role_name = getattr(value, "name", None)
        if isinstance(enum_value, str):
            value = enum_value
        elif isinstance(role_name, str):
            value = role_name
    key = str(value).strip().lower().replace(" ", "_")
    return _ALIASES.get(key, key)
