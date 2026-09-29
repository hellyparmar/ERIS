"""Deterministic, clearly synthetic GSTIN values for portfolio/demo data."""

import random
import re


_BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")


def _checksum(body: str) -> str:
    """Return the Luhn mod-N check character for a 14-character GSTIN body."""
    factor = 2
    total = 0
    for character in reversed(body):
        code_point = _BASE36.index(character)
        addend = factor * code_point
        factor = 1 if factor == 2 else 2
        total += (addend // 36) + (addend % 36)
    return _BASE36[(36 - (total % 36)) % 36]


def generate_synthetic_gstin(state_code: str, seed: int) -> str:
    """Generate a reproducible GSTIN-shaped identifier that is explicitly demo-only.

    The PAN-shaped segment starts with ``DEMOX`` so seed data cannot be mistaken for
    a taxpayer identifier supplied by a real business.
    """
    if not re.fullmatch(r"[0-9]{2}", state_code):
        raise ValueError("state_code must contain exactly two digits")
    state_number = int(state_code)
    if not 1 <= state_number <= 38:
        raise ValueError("state_code must be between 01 and 38")

    rng = random.Random(f"eris-demo-gstin:{state_code}:{seed}")
    pan = f"DEMOX{rng.randrange(10_000):04d}D"
    body = f"{state_code}{pan}1Z"
    return body + _checksum(body)


def is_valid_gstin(value: str) -> bool:
    """Validate GSTIN shape and checksum (not government registration status)."""
    normalized = value.strip().upper()
    return bool(_GSTIN_PATTERN.fullmatch(normalized)) and _checksum(normalized[:14]) == normalized[14]
