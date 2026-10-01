"""Canonical role vocabulary for the single-organization ERIS application."""

from enum import Enum
from typing import Any


ADMIN = "admin"
MANAGER = "manager"
VIEWER = "viewer"
CANONICAL_ROLES = (ADMIN, MANAGER, VIEWER)


def normalize_role(value: Any) -> str:
    """Return one of admin/manager/viewer, defaulting unknown values to viewer."""
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
    key = str(value).strip().lower()
    return key if key in CANONICAL_ROLES else VIEWER


def user_role(user: Any) -> str:
    """Return the canonical role for a user-like object."""
    role = getattr(user, "role", None)
    if role is not None:
        name = getattr(role, "name", None)
        if name is not None:
            return normalize_role(name)
        return normalize_role(role)
    return normalize_role(None)
