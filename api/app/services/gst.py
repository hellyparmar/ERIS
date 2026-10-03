"""GST helpers for DEMO invoices: state codes, GSTIN format/checksum, tax split.

ERIS generates a syntactically valid but synthetic GSTIN for the demo company. It is marked `is_demo`,
printed with a "DEMO - NOT FOR TAX FILING" watermark and never sent to the Invoice Registration Portal.
This is a calculation demonstration, not tax advice or a compliance tool.
"""
from __future__ import annotations

import random
import re

STATES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand",
    "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura", "17": "Meghalaya",
    "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh",
}
STATE_CODE_BY_NAME = {v.lower(): k for k, v in STATES.items()}
_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def gstin_checksum(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        v = _CHARS.index(ch) * (2 if i % 2 else 1)
        total += v // 36 + v % 36
    return _CHARS[(36 - total % 36) % 36]


def is_valid_gstin(gstin: str | None) -> bool:
    if not gstin or not GSTIN_RE.match(gstin):
        return False
    return gstin[:2] in STATES and gstin_checksum(gstin[:14]) == gstin[14]


def demo_gstin(state_code: str, seed: int) -> str:
    """Deterministic, checksum-valid but synthetic GSTIN (marked as demo everywhere it is shown)."""
    rng = random.Random(seed)
    # PAN-like part: 4th letter "C" = company, 5th = first letter of the business name ("U"rban Harvest).
    pan = "AA" + rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") + "CU" + f"{rng.randint(1000, 9999)}" + \
        rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
    first14 = f"{state_code}{pan}1Z"
    return first14 + gstin_checksum(first14)


def split_tax(tax_amount: float, intra_state: bool) -> tuple[float, float, float]:
    """Return (cgst, sgst, igst). Intra-state supply splits GST equally into CGST + SGST; inter-state is IGST."""
    if intra_state:
        half = round(tax_amount / 2, 2)
        return half, round(tax_amount - half, 2), 0.0
    return 0.0, 0.0, round(tax_amount, 2)
