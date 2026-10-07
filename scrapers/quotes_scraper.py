"""Quotes to Scrape pagination and source-specific extraction."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base_scraper import create_session, delay_between_requests, get_page

LOGGER = logging.getLogger(__name__)
SOURCE = "Quotes to Scrape"
START_URL = "https://quotes.toscrape.com/"


def _extract_quote(quote: Any, page_url: str) -> dict[str, Any]:
    text = quote.select_one("span.text")
    author = quote.select_one("small.author")
    tags = [tag.get_text(" ", strip=True) for tag in quote.select("a.tag")]
    return {
        "source": SOURCE,
        "source_url": page_url,
        "name_or_title": text.get_text(" ", strip=True) if text else None,
        "category": None,
        "price": None,
        "rating": None,
        "author": author.get_text(" ", strip=True) if author else None,
        "tags": tags,
        "description": None,
        "scraped_at": None,
    }


def scrape_quotes(session: Any, start_url: str = START_URL) -> list[dict[str, Any]]:
    """Scrape every page through the site's next-page link."""
    records: list[dict[str, Any]] = []
    url = start_url
    page_number = 0
    while url:
        page_number += 1
        LOGGER.info("Scraping quote page %d: %s", page_number, url)
        try:
            response = get_page(session, url)
            soup = BeautifulSoup(response.text, "lxml")
            for quote in soup.select("div.quote"):
                try:
                    records.append(_extract_quote(quote, response.url))
                except Exception as exc:
                    LOGGER.warning("Skipping malformed quote record on %s: %s", response.url, exc)
            next_link = soup.select_one("li.next > a")
            url = urljoin(response.url, next_link["href"]) if next_link and next_link.get("href") else None
        except Exception as exc:
            LOGGER.error("Quote page failed: %s: %s", url, exc)
            break
        if url:
            delay_between_requests()
    return records


def scrape_all_quotes() -> list[dict[str, Any]]:
    return scrape_quotes(create_session())
