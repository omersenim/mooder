"""Keyword extraction, suggestion, and management."""

import re
from typing import Any

from .data import ALL_KEYWORDS, DEFAULT_KEYWORDS

# ──────────────────────────────────────────────────────────────────────
# Extraction
# ──────────────────────────────────────────────────────────────────────

# Word boundary regex for matching keywords in text
# Handles: "great", "great!", "great...", "awesome sauce", "worst day"
_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in ALL_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Multi-word phrases that should be recognized as single keywords
PHRASE_KEYWORDS = {
    "awesome sauce": "awesome",
    "worst day of my life": "worst",
    "i hate my life": "miserable",
    "best day ever": "amazing",
    "pretty good": "good",
    "not bad": "okay",
    "could be better": "meh",
    "burned out": "burned out",
    "burn out": "burned out",
}

def extract_keywords(text: str) -> list[str]:
    """
    Extract known keywords from free text.
    Returns lowercase matched keywords (deduplicated, preserving order of first appearance).
    """
    if not text:
        return []

    found = []
    seen = set()

    # 1. Check multi-word phrases first
    text_lower = text.lower()
    for phrase, canonical in PHRASE_KEYWORDS.items():
        if phrase in text_lower and canonical not in seen:
            found.append(canonical)
            seen.add(canonical)

    # 2. Check single-word keywords via regex
    for match in _KEYWORD_PATTERN.finditer(text_lower):
        kw = match.group(1)
        if kw not in seen:
            found.append(kw)
            seen.add(kw)

    return found


def suggest_keywords_for_entry(entry: dict[str, Any]) -> list[str]:
    """
    Given an entry dict, return suggested keywords based on notes + reflection.
    """
    parts = []
    if entry.get("notes"):
        parts.append(entry["notes"])
    if entry.get("reflection", {}).get("answer"):
        parts.append(entry["reflection"]["answer"])
    combined = " ".join(parts)
    return extract_keywords(combined)


# ──────────────────────────────────────────────────────────────────────
# Management
# ──────────────────────────────────────────────────────────────────────

def get_all_keywords() -> dict[str, list[str]]:
    """Return the full keyword dictionary by category."""
    return {k: v[:] for k, v in DEFAULT_KEYWORDS.items()}


def get_keyword_category(keyword: str) -> str | None:
    """Return 'positive' | 'neutral' | 'negative' for a keyword, or None."""
    kl = keyword.lower()
    for cat, kws in DEFAULT_KEYWORDS.items():
        if kl in kws:
            return cat
    return None


def add_custom_keyword(keyword: str, category: str = "neutral") -> bool:
    """
    Add a user-defined keyword to the global set.
    Category must be one of: positive, neutral, negative.
    Returns True if added, False if invalid category or already exists.
    """
    cat = category.lower()
    if cat not in DEFAULT_KEYWORDS:
        return False
    kl = keyword.strip().lower()
    if not kl or kl in ALL_KEYWORDS:
        return False
    DEFAULT_KEYWORDS[cat].append(kl)
    ALL_KEYWORDS.add(kl)
    # Rebuild regex pattern
    global _KEYWORD_PATTERN
    _KEYWORD_PATTERN = re.compile(
        r"\b(" + "|".join(re.escape(kw) for kw in ALL_KEYWORDS) + r")\b",
        re.IGNORECASE,
    )
    return True


def remove_keyword(keyword: str) -> bool:
    """Remove a keyword from all categories and the global set."""
    kl = keyword.strip().lower()
    if kl not in ALL_KEYWORDS:
        return False
    for cat in DEFAULT_KEYWORDS:
        if kl in DEFAULT_KEYWORDS[cat]:
            DEFAULT_KEYWORDS[cat].remove(kl)
            break
    ALL_KEYWORDS.discard(kl)
    global _KEYWORD_PATTERN
    _KEYWORD_PATTERN = re.compile(
        r"\b(" + "|".join(re.escape(kw) for kw in ALL_KEYWORDS) + r")\b",
        re.IGNORECASE,
    )
    return True