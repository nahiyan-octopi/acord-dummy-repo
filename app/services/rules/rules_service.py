"""
Rules Service

Business logic for creating validation rules in SQL Server.
"""
from typing import Dict, Any

from app.config.database_config import db


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

        placeholders = ",".join(["?"] * len(normalized_ids))
        find_query = f"""
        SELECT id, certificate_type, product_name, is_active
        FROM validation_rules
        WHERE id IN ({placeholders})
        """

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

                delete_query = f"DELETE FROM validation_rules WHERE id IN ({placeholders})"
                cursor.execute(delete_query, tuple(normalized_ids))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        deleted_by_id = {
            int(rule["id"]): {
                "id": int(rule["id"]),
                "certificate_type": rule["certificate_type"],
                "product_name": rule["product_name"],
                "is_active": bool(rule["is_active"]),
            }
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

        duplicate_check_query = """
        SELECT TOP 1 id
        FROM validation_rules
        WHERE LOWER(certificate_type) = LOWER(?)
          AND LOWER(product_name) = LOWER(?)
        """

        insert_query = """
        INSERT INTO validation_rules (certificate_type, product_name, is_active)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
        """

        created_rules: list[Dict[str, Any]] = []

        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for rule in normalized_rules:
                    cursor.execute(
                        duplicate_check_query,
                        (rule["certificate_type"], rule["product_name"]),
                    )
                    existing = cursor.fetchone()
                    if existing:
                        raise ValueError(
                            "A rule with the same certificate_type and product_name already exists"
                        )

                    cursor.execute(
                        insert_query,
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
                        {
                            "id": int(inserted[0]),
                            "certificate_type": rule["certificate_type"],
                            "product_name": rule["product_name"],
                            "is_active": bool(rule["is_active"]),
                        }
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

        placeholders = ",".join(["?"] * len(normalized_rules))
        find_query = f"""
        SELECT id
        FROM validation_rules
        WHERE id IN ({placeholders})
        """

        duplicate_query = """
        SELECT TOP 1 id
        FROM validation_rules
        WHERE LOWER(certificate_type) = LOWER(?)
          AND LOWER(product_name) = LOWER(?)
          AND id <> ?
        """

        update_query = """
        UPDATE validation_rules
        SET certificate_type = ?,
            product_name = ?,
            is_active = ?
        WHERE id = ?
        """

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
                        duplicate_query,
                        (rule["certificate_type"], rule["product_name"], rule["id"])
                    )
                    existing = cursor.fetchone()
                    if existing:
                        raise ValueError(
                            "A rule with the same certificate_type and product_name already exists"
                        )

                    cursor.execute(
                        update_query,
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
                        {
                            "id": int(rule["id"]),
                            "certificate_type": rule["certificate_type"],
                            "product_name": rule["product_name"],
                            "is_active": bool(rule["is_active"]),
                        }
                    )

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return updated_rules

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """Return a single validation rule by id."""
        query = """
        SELECT TOP 1 id, certificate_type, product_name, is_active
        FROM validation_rules
        WHERE id = ?
        """
        rows = db.execute_query(query, (rule_id,))
        if not rows:
            raise LookupError("Rule not found")

        row = rows[0]
        return {
            "id": int(row["id"]),
            "certificate_type": row["certificate_type"],
            "product_name": row["product_name"],
            "is_active": bool(row["is_active"])
        }

    def list_rules(self) -> list[Dict[str, Any]]:
        """Return all validation rules ordered by latest first."""
        query = """
        SELECT id, certificate_type, product_name, is_active
        FROM validation_rules
        ORDER BY id DESC
        """
        rows = db.execute_query(query)
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
        normalized_certificate_type = certificate_type.strip()
        normalized_product_name = product_name.strip()

        if not normalized_certificate_type:
            raise ValueError("certificate_type is required")

        if not normalized_product_name:
            raise ValueError("product_name is required")

        duplicate_query = """
        SELECT TOP 1 id
        FROM validation_rules
        WHERE LOWER(certificate_type) = LOWER(?)
          AND LOWER(product_name) = LOWER(?)
        """
        duplicate_rows = db.execute_query(
            duplicate_query,
            (normalized_certificate_type, normalized_product_name)
        )

        if duplicate_rows:
            raise ValueError("A rule with the same certificate_type and product_name already exists")

        insert_query = """
        INSERT INTO validation_rules (certificate_type, product_name, is_active)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
        """

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                insert_query,
                (
                    normalized_certificate_type,
                    normalized_product_name,
                    1 if is_active else 0
                )
            )
            inserted_row = cursor.fetchone()
            conn.commit()

        if not inserted_row:
            raise Exception("Failed to create rule")

        return {
            "id": int(inserted_row[0]),
            "certificate_type": normalized_certificate_type,
            "product_name": normalized_product_name,
            "is_active": bool(is_active)
        }

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
        normalized_certificate_type = certificate_type.strip()
        normalized_product_name = product_name.strip()

        if not normalized_certificate_type:
            raise ValueError("certificate_type is required")

        if not normalized_product_name:
            raise ValueError("product_name is required")

        exists_query = """
        SELECT TOP 1 id
        FROM validation_rules
        WHERE id = ?
        """
        existing_rule = db.execute_query(exists_query, (rule_id,))
        if not existing_rule:
            raise LookupError("Rule not found")

        duplicate_query = """
        SELECT TOP 1 id
        FROM validation_rules
        WHERE LOWER(certificate_type) = LOWER(?)
          AND LOWER(product_name) = LOWER(?)
          AND id <> ?
        """
        duplicate_rows = db.execute_query(
            duplicate_query,
            (normalized_certificate_type, normalized_product_name, rule_id)
        )
        if duplicate_rows:
            raise ValueError("A rule with the same certificate_type and product_name already exists")

        update_query = """
        UPDATE validation_rules
        SET certificate_type = ?,
            product_name = ?,
            is_active = ?
        WHERE id = ?
        """
        affected_rows = db.execute_non_query(
            update_query,
            (
                normalized_certificate_type,
                normalized_product_name,
                1 if is_active else 0,
                rule_id
            )
        )

        if affected_rows == 0:
            raise LookupError("Rule not found")

        return {
            "id": int(rule_id),
            "certificate_type": normalized_certificate_type,
            "product_name": normalized_product_name,
            "is_active": bool(is_active)
        }

    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Delete an existing validation rule by id.

        Args:
            rule_id: Rule id to delete

        Returns:
            Deleted rule summary
        """
        find_query = """
        SELECT TOP 1 id, certificate_type, product_name, is_active
        FROM validation_rules
        WHERE id = ?
        """
        existing = db.execute_query(find_query, (rule_id,))
        if not existing:
            raise LookupError("Rule not found")

        rule = existing[0]

        delete_query = """
        DELETE FROM validation_rules
        WHERE id = ?
        """
        affected_rows = db.execute_non_query(delete_query, (rule_id,))
        if affected_rows == 0:
            raise LookupError("Rule not found")

        return {
            "id": int(rule["id"]),
            "certificate_type": rule["certificate_type"],
            "product_name": rule["product_name"],
            "is_active": bool(rule["is_active"])
        }
