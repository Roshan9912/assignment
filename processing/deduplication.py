"""Stable fingerprints for detecting equivalent records."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def make_fingerprint(record: dict[str, Any]) -> str:
    """Create a normalized hash for a source-specific identity key."""
    source = record.get("source", "")
    if source == "Books to Scrape":
        identity = f'{source} {record.get("name_or_title", "")}'
    else:
        identity = (
            f'{source} {record.get("author", "")} '
            f'{record.get("name_or_title", "")[:50]}'
        )
    normalized = re.sub(r"[^\w\s]", "", identity.lower())
    normalized = " ".join(normalized.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicates(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return unique records and duplicate records in source order."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for record in records:
        fingerprint = make_fingerprint(record)
        if fingerprint in seen:
            duplicates.append(record)
        else:
            seen.add(fingerprint)
            unique.append(record)
    return unique, duplicates
