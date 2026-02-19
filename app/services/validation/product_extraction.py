"""Helpers for extracting product names from structured payloads."""

from typing import Any

from app.services.validation.text_matching import normalize_text


def extract_product_names_from_structure(payload: Any) -> list[str]:
    """Deterministically walk extracted payload and collect likely product names."""
    candidates: list[str] = []
    product_key_hints = {
        "product",
        "products",
        "product_name",
        "item",
        "items",
        "commodity",
        "commodities",
        "sku",
    }

    def walk(value: Any, parent_key: str = ""):
        if isinstance(value, dict):
            for key, inner in value.items():
                walk(inner, key)
            return

        if isinstance(value, list):
            for inner in value:
                walk(inner, parent_key)
            return

        if not isinstance(value, str):
            return

        cleaned = value.strip()
        if not cleaned:
            return

        key_norm = normalize_text(parent_key)
        if any(hint in key_norm for hint in product_key_hints):
            candidates.append(cleaned)

    walk(payload)

    seen: set[str] = set()
    unique: list[str] = []
    for value in candidates:
        lowered = value.lower().strip()
        if lowered not in seen:
            seen.add(lowered)
            unique.append(value)

    return unique
