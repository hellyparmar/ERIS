"""Compatibility alias for the canonical, fail-fast settings object.

New code should import from :mod:`app.core.config`. This module remains while
legacy modules are migrated away from ``app.config``.
"""

from app.core.config import Settings, settings

__all__ = ["Settings", "settings"]
