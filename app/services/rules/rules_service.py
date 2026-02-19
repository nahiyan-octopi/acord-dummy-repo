"""
Rules Service

Business logic for creating validation rules in SQL Server.
"""
from typing import Dict, Any

from app.config.database_config import db
from app.services.rules.rules_normalization import (
    build_rule_response,
    normalize_bulk_create_rules,
    normalize_bulk_update_rules,
    normalize_rule_fields,
    normalize_rule_ids,
)
from app.services.rules.rules_queries import (
    BULK_DUPLICATE_CHECK_QUERY,
    BULK_INSERT_QUERY,
    BULK_UPDATE_DUPLICATE_QUERY,
    BULK_UPDATE_QUERY,
    GET_RULE_QUERY,
    LIST_RULES_QUERY,
    SINGLE_DELETE_QUERY,
    SINGLE_DUPLICATE_QUERY,
    SINGLE_EXISTS_QUERY,
    SINGLE_FIND_FOR_DELETE_QUERY,
    SINGLE_INSERT_QUERY,
    SINGLE_UPDATE_DUPLICATE_QUERY,
    SINGLE_UPDATE_QUERY,
    build_delete_rules_by_ids_query,
    build_find_rule_ids_query,
    build_find_rules_by_ids_query,
)


class RulesService:
    """Service for validation rules operations."""

    def delete_rules_bulk(self, rule_ids: list[int]) -> list[Dict[str, Any]]:
        """
        Delete multiple validation rules in a single transaction.

        Args:
            rule_ids: List of rule IDs to delete

        Returns:
            List of deleted rules
        """
        normalized_ids = normalize_rule_ids(rule_ids)

        placeholders = ",".join(["?"] * len(normalized_ids))
        find_query = build_find_rules_by_ids_query(placeholders)

        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(find_query, tuple(normalized_ids))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                found_rules = [dict(zip(columns, row)) for row in rows]

                found_ids = {int(rule["id"]) for rule in found_rules}
                missing_ids = [rule_id for rule_id in normalized_ids if rule_id not in found_ids]
                if missing_ids:
                    raise LookupError(f"Rule not found for id(s): {missing_ids}")

                delete_query = build_delete_rules_by_ids_query(placeholders)
                cursor.execute(delete_query, tuple(normalized_ids))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        deleted_by_id = {
            int(rule["id"]): build_rule_response(
                rule_id=int(rule["id"]),
                certificate_type=rule["certificate_type"],
                product_name=rule["product_name"],
                is_active=bool(rule["is_active"]),
            )
            for rule in found_rules
        }
        return [deleted_by_id[rule_id] for rule_id in normalized_ids]

    def create_rules_bulk(self, rules: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Create multiple validation rules in a single transaction.

        Args:
            rules: List of rules with certificate_type, product_name, is_active

        Returns:
            List of created rules with IDs
        """
        normalized_rules = normalize_bulk_create_rules(rules)

        created_rules: list[Dict[str, Any]] = []

        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for rule in normalized_rules:
                    cursor.execute(
                        BULK_DUPLICATE_CHECK_QUERY,
                        (rule["certificate_type"], rule["product_name"]),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        raise ValueError(
                            "A rule with the same certificate_type and product_name already exists"
                        )

                    cursor.execute(
                        BULK_INSERT_QUERY,
                        (
                            rule["certificate_type"],
                            rule["product_name"],
                            1 if rule["is_active"] else 0,
                        ),
                    )
                    inserted = cursor.fetchone()
                    if not inserted:
                        raise Exception("Failed to create one of the rules")

                    created_rules.append(
                        build_rule_response(
                            rule_id=int(inserted[0]),
                            certificate_type=rule["certificate_type"],
                            product_name=rule["product_name"],
                            is_active=bool(rule["is_active"]),
                        )
                    )

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return created_rules

    def update_rules_bulk(self, rules: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Update multiple validation rules in a single transaction.

        Args:
            rules: List of rules with id, certificate_type, product_name, is_active

        Returns:
            List of updated rules with IDs
        """
        normalized_rules = normalize_bulk_update_rules(rules)

        placeholders = ",".join(["?"] * len(normalized_rules))
        find_query = build_find_rule_ids_query(placeholders)

        updated_rules: list[Dict[str, Any]] = []

        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(find_query, tuple(rule["id"] for rule in normalized_rules))
                rows = cursor.fetchall()
                found_ids = {int(row[0]) for row in rows}
                missing_ids = [rule["id"] for rule in normalized_rules if rule["id"] not in found_ids]
                if missing_ids:
                    raise LookupError(f"Rule not found for id(s): {missing_ids}")

                for rule in normalized_rules:
                    cursor.execute(
                        BULK_UPDATE_DUPLICATE_QUERY,
                        (rule["certificate_type"], rule["product_name"], rule["id"])
                    )
                    existing = cursor.fetchone()
                    if existing:
                        raise ValueError(
                            "A rule with the same certificate_type and product_name already exists"
                        )

                    cursor.execute(
                        BULK_UPDATE_QUERY,
                        (
                            rule["certificate_type"],
                            rule["product_name"],
                            1 if rule["is_active"] else 0,
                            rule["id"],
                        )
                    )
                    if cursor.rowcount == 0:
                        raise LookupError("Rule not found")

                    updated_rules.append(
                        build_rule_response(
                            rule_id=int(rule["id"]),
                            certificate_type=rule["certificate_type"],
                            product_name=rule["product_name"],
                            is_active=bool(rule["is_active"]),
                        )
                    )

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return updated_rules

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """Return a single validation rule by id."""
        rows = db.execute_query(GET_RULE_QUERY, (rule_id,))
        if not rows:
            raise LookupError("Rule not found")

        row = rows[0]
        return build_rule_response(
            rule_id=int(row["id"]),
            certificate_type=row["certificate_type"],
            product_name=row["product_name"],
            is_active=bool(row["is_active"]),
        )

    def list_rules(self) -> list[Dict[str, Any]]:
        """Return all validation rules ordered by latest first."""
        rows = db.execute_query(LIST_RULES_QUERY)
        for row in rows:
            row["id"] = int(row["id"])
            row["is_active"] = bool(row["is_active"])
        return rows

    def create_rule(self, certificate_type: str, product_name: str, is_active: bool = True) -> Dict[str, Any]:
        """
        Create a new validation rule in validation_rules table.

        Args:
            certificate_type: Rule certificate type
            product_name: Rule product name
            is_active: Rule active status

        Returns:
            Created rule payload
        """
        normalized_rule = normalize_rule_fields(certificate_type, product_name, is_active)

        duplicate_rows = db.execute_query(
            SINGLE_DUPLICATE_QUERY,
            (normalized_rule["certificate_type"], normalized_rule["product_name"])
        )

        if duplicate_rows:
            raise ValueError("A rule with the same certificate_type and product_name already exists")

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                SINGLE_INSERT_QUERY,
                (
                    normalized_rule["certificate_type"],
                    normalized_rule["product_name"],
                    1 if normalized_rule["is_active"] else 0
                )
            )
            inserted_row = cursor.fetchone()
            conn.commit()

        if not inserted_row:
            raise Exception("Failed to create rule")

        return build_rule_response(
            rule_id=int(inserted_row[0]),
            certificate_type=normalized_rule["certificate_type"],
            product_name=normalized_rule["product_name"],
            is_active=bool(normalized_rule["is_active"]),
        )

    def update_rule(self, rule_id: int, certificate_type: str, product_name: str, is_active: bool) -> Dict[str, Any]:
        """
        Update an existing validation rule.

        Args:
            rule_id: Existing rule id
            certificate_type: Rule certificate type
            product_name: Rule product name
            is_active: Rule active status

        Returns:
            Updated rule payload
        """
        normalized_rule = normalize_rule_fields(certificate_type, product_name, is_active)

        existing_rule = db.execute_query(SINGLE_EXISTS_QUERY, (rule_id,))
        if not existing_rule:
            raise LookupError("Rule not found")

        duplicate_rows = db.execute_query(
            SINGLE_UPDATE_DUPLICATE_QUERY,
            (normalized_rule["certificate_type"], normalized_rule["product_name"], rule_id)
        )
        if duplicate_rows:
            raise ValueError("A rule with the same certificate_type and product_name already exists")

        affected_rows = db.execute_non_query(
            SINGLE_UPDATE_QUERY,
            (
                normalized_rule["certificate_type"],
                normalized_rule["product_name"],
                1 if normalized_rule["is_active"] else 0,
                rule_id
            )
        )

        if affected_rows == 0:
            raise LookupError("Rule not found")

        return build_rule_response(
            rule_id=int(rule_id),
            certificate_type=normalized_rule["certificate_type"],
            product_name=normalized_rule["product_name"],
            is_active=bool(normalized_rule["is_active"]),
        )

    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Delete an existing validation rule by id.

        Args:
            rule_id: Rule id to delete

        Returns:
            Deleted rule summary
        """
        existing = db.execute_query(SINGLE_FIND_FOR_DELETE_QUERY, (rule_id,))
        if not existing:
            raise LookupError("Rule not found")

        rule = existing[0]

        affected_rows = db.execute_non_query(SINGLE_DELETE_QUERY, (rule_id,))
        if affected_rows == 0:
            raise LookupError("Rule not found")

        return build_rule_response(
            rule_id=int(rule["id"]),
            certificate_type=rule["certificate_type"],
            product_name=rule["product_name"],
            is_active=bool(rule["is_active"]),
        )
