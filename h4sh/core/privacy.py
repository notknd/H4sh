"""Privacy helpers for public-source, operator-authorized lookups."""
from __future__ import annotations


def mask_phone(value: str) -> str:
    """Keep enough digits for a session audit without retaining the whole number."""
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) <= 4:
        return "••••"
    return f"••••••{digits[-4:]}"
