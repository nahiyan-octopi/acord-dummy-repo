"""
Validation Service

Handles document validation workflow:
- Extracts data via ExtractionService
- Persists document/content records
- Validates extracted values against validation_rules
"""

from typing import Dict, Any
import json
import re
from datetime import datetime
from difflib import SequenceMatcher

from fastapi import UploadFile
from nltk.stem.porter import PorterStemmer

from app.config.database_config import db
from app.services.ai.openai_service import get_openai_service


class ValidationService:
    """Service for validating extracted document data."""

    TOKEN_OVERLAP_THRESHOLD = 0.6
    STEM_OVERLAP_THRESHOLD = 0.5
    FUZZY_THRESHOLD = 0.80
    FUZZY_SHORT_STRING_THRESHOLD = 0.70
    MIN_TOKEN_INTERSECTION = 1

    def __init__(self, extraction_service):
        self.extraction_service = extraction_service
        self.openai_service = get_openai_service()
        self.stemmer = PorterStemmer()

    async def validate_data(self, file: UploadFile) -> Dict[str, Any]:
        """
        Extract and validate certificate data against validation rules.

        Validation criteria:
        - Certificate documents only
        - Approval requires both certificate_type and product_name match
        """
        extraction_result = await self.extraction_service.extract_data(file)

        if not extraction_result.get("success"):
            return {
                "success": False,
                "error": extraction_result.get("error", "Extraction failed"),
                "file_path": extraction_result.get("file_path")
            }

        document_type = str(extraction_result.get("document_type") or "").strip()
        certificate_type = extraction_result.get("certificate_type")
        formatted_data = extraction_result.get("formatted_data", {}) or {}
        file_info = extraction_result.get("file_info", {}) or {}

        save_result = self._save_document_and_content(
            file_info=file_info,
            document_type=document_type,
            certificate_type=certificate_type,
            extraction_method=extraction_result.get("extraction_method", "unknown"),
            formatted_data=formatted_data,
            raw_payload=extraction_result
        )

        if not save_result.get("success"):
            return {
                "success": False,
                "error": save_result.get("error", "Failed to persist extracted data"),
                "file_path": extraction_result.get("file_path")
            }

        is_certificate = document_type.lower() == "certificate"

        if not is_certificate:
            return {
                "success": True,
                "message": "Validation completed",
                "file_path": extraction_result.get("file_path"),
                "data": {
                    "document_id": save_result.get("document_id"),
                    "document_content_id": save_result.get("document_content_id"),
                    "document_type": document_type or "Document",
                    "certificate_type": certificate_type,
                    "validation_status": "rejected",
                    "validation_message": f"There's no validation rule for \"{document_type or 'Document'}\".",
                    "extracted_product_names": [],
                    "matched_rule": None,
                    "rules_checked_count": 0
                }
            }

        normalized_certificate_type = self._normalize_text(certificate_type)
        if not normalized_certificate_type:
            return {
                "success": True,
                "message": "Validation completed",
                "file_path": extraction_result.get("file_path"),
                "data": {
                    "document_id": save_result.get("document_id"),
                    "document_content_id": save_result.get("document_content_id"),
                    "document_type": document_type,
                    "certificate_type": certificate_type,
                    "validation_status": "rejected",
                    "validation_message": "No certificate type was extracted from the document.",
                    "extracted_product_names": [],
                    "matched_rule": None,
                    "rules_checked_count": 0
                }
            }

        extracted_product_names = self._extract_product_names(formatted_data)
        normalized_products = [
            self._normalize_text(v)
            for v in extracted_product_names
            if self._normalize_text(v)
        ]
        normalized_products_set = set(normalized_products)

        rules = self._get_active_rules_by_certificate_type(certificate_type)
        expanded_rules: list[Dict[str, Any]] = []
        normalized_rule_products: list[str] = []

        for rule in rules:
            candidates = self._normalized_rule_product_candidates(rule.get("product_name"))
            if not candidates:
                continue
            expanded_rules.append({"rule": rule, "candidates": candidates})
            normalized_rule_products.extend(candidates)

        if not rules or not expanded_rules:
            return {
                "success": True,
                "message": "Validation completed",
                "file_path": extraction_result.get("file_path"),
                "data": {
                    "document_id": save_result.get("document_id"),
                    "document_content_id": save_result.get("document_content_id"),
                    "document_type": document_type,
                    "certificate_type": certificate_type,
                    "validation_status": "rejected",
                    "validation_message": f"No active validation rules found for certificate type '{certificate_type}'.",
                    "extracted_product_names": extracted_product_names,
                    "matched_rule": None,
                    "rules_checked_count": 0
                }
            }

        matched_rule = None
        matched_rule_product_name = None
        match_type = None
        match_score = None

        for expanded_rule in expanded_rules:
            rule = expanded_rule["rule"]
            for rule_product_normalized in expanded_rule["candidates"]:
                if rule_product_normalized in normalized_products_set:
                    matched_rule = rule
                    matched_rule_product_name = rule_product_normalized
                    match_type = "exact"
                    match_score = 1.0
                    break
            if matched_rule is not None:
                break

        if matched_rule is None:
            for expanded_rule in expanded_rules:
                rule = expanded_rule["rule"]
                for rule_product_normalized in expanded_rule["candidates"]:
                    for product_name in normalized_products:
                        if (
                            rule_product_normalized in product_name
                            or product_name in rule_product_normalized
                        ):
                            matched_rule = rule
                            matched_rule_product_name = rule_product_normalized
                            match_type = "contains"
                            match_score = 0.9
                            break
                    if matched_rule is not None:
                        break
                if matched_rule is not None:
                    break

        if matched_rule is None:
            best_score = 0.0
            best_rule = None
            best_rule_product_name = None

            for expanded_rule in expanded_rules:
                rule = expanded_rule["rule"]
                for rule_product_normalized in expanded_rule["candidates"]:
                    for product_name in normalized_products:
                        score = self._token_overlap_score(rule_product_normalized, product_name)
                        if score > best_score:
                            best_score = score
                            best_rule = rule
                            best_rule_product_name = rule_product_normalized

            if best_rule is not None and best_score >= self.TOKEN_OVERLAP_THRESHOLD:
                matched_rule = best_rule
                matched_rule_product_name = best_rule_product_name
                match_type = "token_overlap"
                match_score = round(best_score, 3)

        # Tier 4: Stem-based token overlap (morphological variants)
        if matched_rule is None:
            best_score = 0.0
            best_rule = None
            best_rule_product_name = None

            for expanded_rule in expanded_rules:
                rule = expanded_rule["rule"]
                for rule_product_normalized in expanded_rule["candidates"]:
                    for product_name in normalized_products:
                        score = self._stem_based_overlap_score(rule_product_normalized, product_name)
                        if score > best_score:
                            best_score = score
                            best_rule = rule
                            best_rule_product_name = rule_product_normalized

            if best_rule is not None and best_score >= self.STEM_OVERLAP_THRESHOLD:
                matched_rule = best_rule
                matched_rule_product_name = best_rule_product_name
                match_type = "stem_overlap"
                match_score = round(best_score, 3)

        # Tier 5: Fuzzy string matching (typos, truncation)
        if matched_rule is None:
            best_score = 0.0
            best_rule = None
            best_rule_product_name = None

            for expanded_rule in expanded_rules:
                rule = expanded_rule["rule"]
                for rule_product_normalized in expanded_rule["candidates"]:
                    for product_name in normalized_products:
                        score = self._fuzzy_similarity(rule_product_normalized, product_name)
                        if score > 0.0:
                            if score > best_score:
                                best_score = score
                                best_rule = rule
                                best_rule_product_name = rule_product_normalized

            if best_rule is not None:
                matched_rule = best_rule
                matched_rule_product_name = best_rule_product_name
                match_type = "fuzzy"
                match_score = round(best_score, 3)

        if matched_rule:
            validation_status = "approved"
            validation_message = (
                f"Certificate type '{certificate_type}' matched. "
                f"Product name '{matched_rule_product_name or matched_rule['product_name']}' matched an active validation rule."
            )
        else:
            validation_status = "rejected"
            validation_message = (
                f"Certificate type '{certificate_type}' matched, "
                f"but none of the extracted product names matched an active validation rule."
            )

        return {
            "success": True,
            "message": "Validation completed",
            "file_path": extraction_result.get("file_path"),
            "data": {
                "document_id": save_result.get("document_id"),
                "document_content_id": save_result.get("document_content_id"),
                "document_type": document_type,
                "certificate_type": certificate_type,
                "validation_status": validation_status,
                "validation_message": validation_message,
                "extracted_product_names": extracted_product_names,
                "normalized_extracted_product_names": normalized_products,
                "normalized_rule_product_names": normalized_rule_products,
                "matched_rule_product_name": matched_rule_product_name,
                "matched_rule": matched_rule,
                "match_type": match_type,
                "match_score": match_score,
                "rules_checked_count": len(rules)
            }
        }

    def _normalize_text(self, value: Any) -> str:
        """Normalize text for case-insensitive and whitespace-insensitive matching."""
        if value is None:
            return ""
        text = str(value).strip().lower()
        text = text.replace("&", " and ")
        text = text.replace("+", " and ")
        text = text.replace("/", " ")
        text = text.replace("_", " ")
        text = text.replace("-", " ")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return text.strip()

    def _normalized_rule_product_candidates(self, raw_rule_value: Any) -> list[str]:
        """Split a rule row product field into normalized product candidates."""
        if raw_rule_value is None:
            return []

        raw_text = str(raw_rule_value).strip()
        if not raw_text:
            return []

        split_parts = re.split(r"[,;\n|]+", raw_text)

        normalized_candidates: list[str] = []
        seen: set[str] = set()
        for part in split_parts:
            normalized = self._normalize_text(part)
            if normalized and normalized not in seen:
                seen.add(normalized)
                normalized_candidates.append(normalized)

        if normalized_candidates:
            return normalized_candidates

        normalized_full = self._normalize_text(raw_text)
        return [normalized_full] if normalized_full else []

    def _token_overlap_score(self, left: str, right: str) -> float:
        """Compute Jaccard-like token overlap score for fuzzy matching."""
        left_tokens = {tok for tok in left.split(" ") if tok}
        right_tokens = {tok for tok in right.split(" ") if tok}

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = left_tokens.intersection(right_tokens)
        if len(intersection) < self.MIN_TOKEN_INTERSECTION:
            return 0.0

        union = left_tokens.union(right_tokens)
        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _stem_tokens(self, text: str) -> set:
        """Convert normalized text to set of stemmed tokens."""
        tokens = text.split()
        return {self.stemmer.stem(tok) for tok in tokens if tok}

    def _stem_based_overlap_score(self, left: str, right: str) -> float:
        """Compute Jaccard similarity on stemmed tokens for morphological matching."""
        left_stems = self._stem_tokens(left)
        right_stems = self._stem_tokens(right)

        if not left_stems or not right_stems:
            return 0.0

        intersection = left_stems.intersection(right_stems)
        if not intersection:
            return 0.0

        union = left_stems.union(right_stems)
        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _fuzzy_similarity(self, str1: str, str2: str) -> float:
        """
        Compute fuzzy string similarity with dynamic threshold.
        Short strings (<=4 chars) use 0.70 threshold (lenient).
        Medium strings (5-10 chars) use 0.75 threshold.
        Long strings (>10 chars) use 0.80 threshold.
        Returns similarity score (0.0-1.0) if meets threshold, else 0.0.
        """
        ratio = SequenceMatcher(None, str1, str2).ratio()
        min_len = min(len(str1), len(str2))

        # Dynamic threshold based on string length
        if min_len <= 4:
            threshold = 0.70
        elif min_len <= 10:
            threshold = 0.75
        else:
            threshold = self.FUZZY_THRESHOLD

        return ratio if ratio >= threshold else 0.0

    def _extract_product_names_from_structure(self, payload: Any) -> list[str]:
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

            key_norm = self._normalize_text(parent_key)
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

    def _extract_product_names(self, formatted_data: Dict[str, Any]) -> list[str]:
        """
        Extract actual product names from the certificate's extracted data using AI.

        Sends the structured extracted data to GPT and asks it to identify
        the real product / item names—not section headers, dates, or labels.
        """
        try:
            data_text = json.dumps(formatted_data, indent=2, ensure_ascii=False)

            prompt = (
                "You are given the structured extracted data from a certificate document.\n"
                "Your task is to identify ALL actual product names or item names that the "
                "certificate covers or pertains to.\n\n"
                "RULES:\n"
                "1. Return ONLY real product names (e.g. \"Organic Sugar\", \"Cocoa Powder\", \"Wheat Flour\").\n"
                "2. Do NOT return section headers, field labels, dates, addresses, or generic words "
                "like \"Products\", \"product list\", \"production dates\".\n"
                "3. If you cannot find any actual product names, return an empty list.\n"
                "4. Return valid JSON: {\"product_names\": [\"Name1\", \"Name2\"]}\n\n"
                f"EXTRACTED DATA:\n{data_text}"
            )

            result = self.openai_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )

            if not result.get("success") or not result.get("content"):
                return self._extract_product_names_from_structure(formatted_data)

            parsed = json.loads(result["content"])
            names = parsed.get("product_names", [])

            seen: set[str] = set()
            unique: list[str] = []
            for name in names:
                cleaned = str(name).strip()
                if cleaned and cleaned.lower() not in seen:
                    seen.add(cleaned.lower())
                    unique.append(cleaned)

            if unique:
                return unique

            return self._extract_product_names_from_structure(formatted_data)
        except Exception as e:
            print(f"AI product-name extraction failed: {e}")
            return self._extract_product_names_from_structure(formatted_data)

    def _get_active_rules_by_certificate_type(self, certificate_type: Any) -> list[Dict[str, Any]]:
        """Fetch active validation rules for a specific certificate type."""
        query = """
        SELECT id, certificate_type, product_name, is_active
        FROM validation_rules
        WHERE LOWER(LTRIM(RTRIM(certificate_type))) = LOWER(LTRIM(RTRIM(?)))
          AND is_active = 1
        ORDER BY id DESC
        """
        rows = db.execute_query(query, (str(certificate_type).strip(),))
        return [
            {
                "id": int(row.get("id")),
                "certificate_type": row.get("certificate_type"),
                "product_name": row.get("product_name"),
                "is_active": bool(row.get("is_active"))
            }
            for row in rows
        ]

    def _save_document_and_content(
        self,
        file_info: Dict[str, Any],
        document_type: str,
        certificate_type: Any,
        extraction_method: str,
        formatted_data: Dict[str, Any],
        raw_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist extracted document metadata and content using existing DB schema."""
        try:
            document_schema = self._get_table_schema("documents")
            content_schema = self._get_table_schema("document_content")

            if not document_schema:
                return {"success": False, "error": "Table 'documents' not found or schema unavailable."}
            if not content_schema:
                return {"success": False, "error": "Table 'document_content' not found or schema unavailable."}

            document_base = {
                "filename": file_info.get("filename") or "unknown.pdf",
                "size_bytes": file_info.get("file_size"),
            }

            with db.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    prepared_document = self._prepare_insert_data(document_schema, document_base)
                    document_id = self._insert_row(cursor, "documents", document_schema, prepared_document)

                    if document_id is None:
                        raise Exception("Unable to persist document row: no document id returned")

                    content_base = {
                        "document_id": document_id,
                        "text_data": json.dumps(formatted_data, ensure_ascii=False),
                        "document_type": document_type,
                        "certificate_type": certificate_type,
                    }

                    prepared_content = self._prepare_insert_data(content_schema, content_base)
                    document_content_id = self._insert_row(cursor, "document_content", content_schema, prepared_content)

                    conn.commit()
                    return {
                        "success": True,
                        "document_id": document_id,
                        "document_content_id": document_content_id
                    }
                except Exception:
                    conn.rollback()
                    raise
        except Exception as e:
            return {
                "success": False,
                "error": f"Persistence failed: {str(e)}"
            }

    def _get_table_schema(self, table_name: str) -> list[Dict[str, Any]]:
        """Get table schema including identity metadata."""
        query = """
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME), c.COLUMN_NAME, 'IsIdentity') AS IS_IDENTITY
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
        """
        rows = db.execute_query(query, (table_name,))

        return [
            {
                "column_name": row.get("COLUMN_NAME"),
                "data_type": str(row.get("DATA_TYPE") or "").lower(),
                "is_nullable": str(row.get("IS_NULLABLE") or "YES").upper() == "YES",
                "has_default": row.get("COLUMN_DEFAULT") is not None,
                "is_identity": bool(row.get("IS_IDENTITY") == 1)
            }
            for row in rows
        ]

    def _prepare_insert_data(self, schema: list[Dict[str, Any]], base_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare insert payload based on actual table schema and required columns."""
        prepared: Dict[str, Any] = {}

        for col in schema:
            name = col["column_name"]
            dtype = col["data_type"]

            if col["is_identity"]:
                continue

            if name in base_data and base_data[name] is not None:
                prepared[name] = base_data[name]
                continue

            if col["is_nullable"] or col["has_default"]:
                continue

            if "date" in dtype or "time" in dtype:
                prepared[name] = datetime.utcnow()
            elif dtype in {"int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money", "smallmoney"}:
                prepared[name] = 0
            elif dtype == "bit":
                prepared[name] = 0
            else:
                prepared[name] = ""

        return prepared

    def _insert_row(
        self,
        cursor,
        table_name: str,
        schema: list[Dict[str, Any]],
        payload: Dict[str, Any]
    ) -> Any:
        """Insert row and return inserted id when table has id column."""
        available_columns = {col["column_name"] for col in schema if not col["is_identity"]}
        insert_columns = [key for key in payload.keys() if key in available_columns]

        if not insert_columns:
            raise Exception(f"No insertable columns found for table '{table_name}'")

        placeholders = ", ".join(["?"] * len(insert_columns))
        columns_sql = ", ".join(insert_columns)
        values = tuple(payload[col] for col in insert_columns)

        identity_column = next(
            (col["column_name"] for col in schema if col.get("is_identity")),
            None
        )

        return_column = identity_column
        if return_column is None:
            preferred_columns = ["id", "document_id", "doc_id", "documents_id"]
            schema_columns_lower = {
                col["column_name"].lower(): col["column_name"]
                for col in schema
            }
            for candidate in preferred_columns:
                if candidate in schema_columns_lower:
                    return_column = schema_columns_lower[candidate]
                    break

        if return_column:
            query = (
                f"INSERT INTO {table_name} ({columns_sql}) "
                f"OUTPUT INSERTED.[{return_column}] VALUES ({placeholders})"
            )
            cursor.execute(query, values)
            inserted = cursor.fetchone()
            if inserted:
                return inserted[0]

        query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        cursor.execute(query, values)
        return None
