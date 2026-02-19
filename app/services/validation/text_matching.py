"""Reusable text matching helpers for validation workflows."""

from typing import Any
import re
from difflib import SequenceMatcher


def normalize_text(value: Any) -> str:
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


def normalized_rule_product_candidates(raw_rule_value: Any) -> list[str]:
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
        normalized = normalize_text(part)
        if normalized and normalized not in seen:
            seen.add(normalized)
            normalized_candidates.append(normalized)

    if normalized_candidates:
        return normalized_candidates

    normalized_full = normalize_text(raw_text)
    return [normalized_full] if normalized_full else []


def token_overlap_score(left: str, right: str, min_token_intersection: int) -> float:
    """Compute Jaccard-like token overlap score for fuzzy matching."""
    left_tokens = {tok for tok in left.split(" ") if tok}
    right_tokens = {tok for tok in right.split(" ") if tok}

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = left_tokens.intersection(right_tokens)
    if len(intersection) < min_token_intersection:
        return 0.0

    union = left_tokens.union(right_tokens)
    if not union:
        return 0.0

    return len(intersection) / len(union)


def stem_tokens(text: str, stemmer) -> set[str]:
    """Convert normalized text to set of stemmed tokens."""
    tokens = text.split()
    return {stemmer.stem(tok) for tok in tokens if tok}


def stem_based_overlap_score(left: str, right: str, stemmer) -> float:
    """Compute Jaccard similarity on stemmed tokens for morphological matching."""
    left_stems = stem_tokens(left, stemmer)
    right_stems = stem_tokens(right, stemmer)

    if not left_stems or not right_stems:
        return 0.0

    intersection = left_stems.intersection(right_stems)
    if not intersection:
        return 0.0

    union = left_stems.union(right_stems)
    if not union:
        return 0.0

    return len(intersection) / len(union)


def fuzzy_similarity(str1: str, str2: str, fuzzy_threshold: float) -> float:
    """
    Compute fuzzy string similarity with dynamic threshold.
    Short strings (<=4 chars) use 0.70 threshold (lenient).
    Medium strings (5-10 chars) use 0.75 threshold.
    Long strings (>10 chars) use configured threshold.
    Returns similarity score (0.0-1.0) if meets threshold, else 0.0.
    """
    ratio = SequenceMatcher(None, str1, str2).ratio()
    min_len = min(len(str1), len(str2))

    if min_len <= 4:
        threshold = 0.70
    elif min_len <= 10:
        threshold = 0.75
    else:
        threshold = fuzzy_threshold

    return ratio if ratio >= threshold else 0.0
