"""Pure transformation helpers for standardized records."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()
    return text or None


def strip_quotes(value: Any) -> str | None:
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    return cleaned.strip("\u2018\u2019\u201c\u201d\"")


def clean_price(value: Any) -> float | None:
    if value is None or value == "":
        return None
    match = re.search(r"[-+]?\d*\.?\d+", str(value).replace(",", ""))
    if match is None:
        return None
    price = float(match.group())
    return price if price >= 0 else None


def clean_rating(value: Any) -> int | None:
    if value is None:
        return None
    text = clean_text(value)
    if not text:
        return None
    lowered = text.lower()
    if lowered.isdigit():
        number = int(lowered)
        return number if 1 <= number <= 5 else None
    for word in lowered.split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(values: Any) -> str | None:
    if not values:
        return None
    if isinstance(values, str):
        tags = [values]
    else:
        tags = list(values)
    cleaned = sorted({clean_text(tag).lower() for tag in tags if clean_text(tag)})
    return ";".join(cleaned) or None


def normalize_url(value: Any, base_url: str | None = None) -> str | None:
    if value is None:
        return None
    text = clean_text(value)
    if not text:
        return None
    if base_url:
        text = urljoin(base_url, text)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return text


def clean_record(raw: dict[str, Any], source: str, source_url: str) -> dict[str, Any]:
    """Convert one source-specific raw dictionary to the common schema."""
    name = clean_text(raw.get("name_or_title"))
    category = clean_text(raw.get("category"))
    author = clean_text(raw.get("author"))
    tags = clean_tags(raw.get("tags"))
    return {
        "source": source,
        "source_url": normalize_url(source_url) or source_url,
        "name_or_title": name,
        "category": category,
        "price": clean_price(raw.get("price")),
        "rating": clean_rating(raw.get("rating")),
        "author": author,
        "tags": tags,
        "description": clean_text(raw.get("description")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }
