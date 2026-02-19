"""Normalization and validation helpers for rules service payloads."""

from typing import Any, Dict


def normalize_rule_ids(rule_ids: list[int]) -> list[int]:
    """Validate and normalize bulk delete ids."""
    if not rule_ids:
        raise ValueError("At least one rule id is required")

    normalized_ids: list[int] = []
    seen_ids: set[int] = set()
    for rule_id in rule_ids:
        normalized_id = int(rule_id)
        if normalized_id <= 0:
            raise ValueError("All rule ids must be positive integers")
        if normalized_id in seen_ids:
            raise ValueError(f"Duplicate rule id in request: {normalized_id}")
        seen_ids.add(normalized_id)
        normalized_ids.append(normalized_id)

    return normalized_ids


def normalize_bulk_create_rules(rules: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Validate and normalize bulk create payload."""
    if not rules:
        raise ValueError("At least one rule is required")

    normalized_rules: list[Dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for rule in rules:
        certificate_type = str(rule.get("certificate_type", "")).strip()
        product_name = str(rule.get("product_name", "")).strip()
        is_active = bool(rule.get("is_active", True))

        if not certificate_type:
            raise ValueError("certificate_type is required for all rules")
        if not product_name:
            raise ValueError("product_name is required for all rules")

        pair_key = (certificate_type.lower(), product_name.lower())
        if pair_key in seen_pairs:
            raise ValueError(
                f"Duplicate rule in request: certificate_type='{certificate_type}', product_name='{product_name}'"
            )
        seen_pairs.add(pair_key)

        normalized_rules.append(
            {
                "certificate_type": certificate_type,
                "product_name": product_name,
                "is_active": is_active,
            }
        )

    return normalized_rules


def normalize_bulk_update_rules(rules: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Validate and normalize bulk update payload."""
    if not rules:
        raise ValueError("At least one rule is required")

    normalized_rules: list[Dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_pairs: set[tuple[str, str]] = set()

    for rule in rules:
        rule_id = int(rule.get("id", 0))
        certificate_type = str(rule.get("certificate_type", "")).strip()
        product_name = str(rule.get("product_name", "")).strip()
        is_active = bool(rule.get("is_active", True))

        if rule_id <= 0:
            raise ValueError("All rule ids must be positive integers")
        if rule_id in seen_ids:
            raise ValueError(f"Duplicate rule id in request: {rule_id}")
        seen_ids.add(rule_id)

        if not certificate_type:
            raise ValueError("certificate_type is required for all rules")
        if not product_name:
            raise ValueError("product_name is required for all rules")

        pair_key = (certificate_type.lower(), product_name.lower())
        if pair_key in seen_pairs:
            raise ValueError(
                f"Duplicate rule in request: certificate_type='{certificate_type}', product_name='{product_name}'"
            )
        seen_pairs.add(pair_key)

        normalized_rules.append(
            {
                "id": rule_id,
                "certificate_type": certificate_type,
                "product_name": product_name,
                "is_active": is_active,
            }
        )

    return normalized_rules


def normalize_rule_fields(certificate_type: str, product_name: str, is_active: bool = True) -> Dict[str, Any]:
    """Validate and normalize single-rule create/update fields."""
    normalized_certificate_type = certificate_type.strip()
    normalized_product_name = product_name.strip()

    if not normalized_certificate_type:
        raise ValueError("certificate_type is required")

    if not normalized_product_name:
        raise ValueError("product_name is required")

    return {
        "certificate_type": normalized_certificate_type,
        "product_name": normalized_product_name,
        "is_active": bool(is_active),
    }


def build_rule_response(rule_id: int, certificate_type: str, product_name: str, is_active: bool) -> Dict[str, Any]:
    """Build a consistent rule payload for API responses."""
    return {
        "id": int(rule_id),
        "certificate_type": certificate_type,
        "product_name": product_name,
        "is_active": bool(is_active),
    }
