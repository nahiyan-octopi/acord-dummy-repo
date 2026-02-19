"""SQL builders and constants for rules service."""


def build_find_rules_by_ids_query(placeholders: str) -> str:
    return f"""
    SELECT id, certificate_type, product_name, is_active
    FROM validation_rules
    WHERE id IN ({placeholders})
    """


def build_delete_rules_by_ids_query(placeholders: str) -> str:
    return f"DELETE FROM validation_rules WHERE id IN ({placeholders})"


def build_find_rule_ids_query(placeholders: str) -> str:
    return f"""
    SELECT id
    FROM validation_rules
    WHERE id IN ({placeholders})
    """


BULK_DUPLICATE_CHECK_QUERY = """
SELECT TOP 1 id
FROM validation_rules
WHERE LOWER(certificate_type) = LOWER(?)
  AND LOWER(product_name) = LOWER(?)
"""


BULK_INSERT_QUERY = """
INSERT INTO validation_rules (certificate_type, product_name, is_active)
OUTPUT INSERTED.id
VALUES (?, ?, ?)
"""


BULK_UPDATE_DUPLICATE_QUERY = """
SELECT TOP 1 id
FROM validation_rules
WHERE LOWER(certificate_type) = LOWER(?)
  AND LOWER(product_name) = LOWER(?)
  AND id <> ?
"""


BULK_UPDATE_QUERY = """
UPDATE validation_rules
SET certificate_type = ?,
    product_name = ?,
    is_active = ?
WHERE id = ?
"""


GET_RULE_QUERY = """
SELECT TOP 1 id, certificate_type, product_name, is_active
FROM validation_rules
WHERE id = ?
"""


LIST_RULES_QUERY = """
SELECT id, certificate_type, product_name, is_active
FROM validation_rules
ORDER BY id DESC
"""


SINGLE_DUPLICATE_QUERY = """
SELECT TOP 1 id
FROM validation_rules
WHERE LOWER(certificate_type) = LOWER(?)
  AND LOWER(product_name) = LOWER(?)
"""


SINGLE_INSERT_QUERY = """
INSERT INTO validation_rules (certificate_type, product_name, is_active)
OUTPUT INSERTED.id
VALUES (?, ?, ?)
"""


SINGLE_EXISTS_QUERY = """
SELECT TOP 1 id
FROM validation_rules
WHERE id = ?
"""


SINGLE_UPDATE_DUPLICATE_QUERY = """
SELECT TOP 1 id
FROM validation_rules
WHERE LOWER(certificate_type) = LOWER(?)
  AND LOWER(product_name) = LOWER(?)
  AND id <> ?
"""


SINGLE_UPDATE_QUERY = """
UPDATE validation_rules
SET certificate_type = ?,
    product_name = ?,
    is_active = ?
WHERE id = ?
"""


SINGLE_FIND_FOR_DELETE_QUERY = """
SELECT TOP 1 id, certificate_type, product_name, is_active
FROM validation_rules
WHERE id = ?
"""


SINGLE_DELETE_QUERY = """
DELETE FROM validation_rules
WHERE id = ?
"""
