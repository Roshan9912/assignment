"""Run the complete scraping, cleaning, validation, deduplication, and export pipeline."""

from __future__ import annotations

import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from processing.cleaning import clean_record
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.books_scraper import scrape_all_books
from scrapers.quotes_scraper import scrape_all_quotes

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
LOG_DIR = ROOT / "logs"
FIELDNAMES = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "scraped_at",
]


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("assignment")


def clean_raw_records(raw_records: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for raw in raw_records:
        try:
            cleaned.append(clean_record(raw, source, raw.get("source_url", "")))
        except Exception as exc:
            LOGGER.warning("Failed to clean a %s record: %s", source, exc)
    return cleaned


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def write_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def run_pipeline() -> dict[str, Any]:
    start_time = datetime.now(timezone.utc)
    raw_by_source: dict[str, list[dict[str, Any]]] = {
        "Books to Scrape": [],
        "Quotes to Scrape": [],
    }
    cleaned_by_source: dict[str, list[dict[str, Any]]] = {
        "Books to Scrape": [],
        "Quotes to Scrape": [],
    }
    rejected_by_reason: Counter[str] = Counter()
    valid_records: list[dict[str, Any]] = []

    try:
        raw_by_source["Books to Scrape"] = scrape_all_books()
    except Exception as exc:
        LOGGER.error("Books source failed entirely: %s", exc)
    try:
        raw_by_source["Quotes to Scrape"] = scrape_all_quotes()
    except Exception as exc:
        LOGGER.error("Quotes source failed entirely: %s", exc)

    for source, raw_records in raw_by_source.items():
        cleaned_by_source[source] = clean_raw_records(raw_records, source)
        for record in cleaned_by_source[source]:
            problems = validate_record(record)
            if problems:
                rejected_by_reason.update(problems)
                LOGGER.warning(
                    "Rejected %s record: %s; reasons=%s",
                    source,
                    record.get("name_or_title"),
                    problems,
                )
            else:
                valid_records.append(record)

    unique_records, duplicates = find_duplicates(valid_records)
    final_records = sorted(unique_records, key=lambda record: (record["source"], record["name_or_title"] or ""))

    write_csv(final_records, OUTPUT_DIR / "final_dataset.csv")
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    summary = {
        "start_time": start_time.isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 3),
        "collected_per_source": {
            source: len(raw_by_source[source]) for source in raw_by_source
        },
        "cleaned_per_source": {
            source: len(cleaned_by_source[source]) for source in cleaned_by_source
        },
        "rejected_count": sum(rejected_by_reason.values()),
        "rejected_by_reason": dict(sorted(rejected_by_reason.items())),
        "duplicates_detected": len(duplicates),
        "duplicates_removed": len(duplicates),
        "final_record_count": len(final_records),
        "sources": sorted(raw_by_source),
    }
    write_summary(summary, OUTPUT_DIR / "summary_report.json")
    LOGGER.info("Pipeline completed: %d final records from %d sources", len(final_records), len(raw_by_source))
    return summary


LOGGER = configure_logging()


if __name__ == "__main__":
    started = time.perf_counter()
    result = run_pipeline()
    LOGGER.info("Run duration: %.3f seconds", time.perf_counter() - started)
    print(json.dumps(result, indent=2, ensure_ascii=False))
