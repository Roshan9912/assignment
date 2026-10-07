"""Books to Scrape pagination and source-specific extraction."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base_scraper import create_session, delay_between_requests, get_page

LOGGER = logging.getLogger(__name__)
SOURCE = "Books to Scrape"
START_URL = "https://books.toscrape.com/"


def _extract_book(article: Any, page_url: str) -> dict[str, Any]:
    title_link = article.select_one("h3 > a")
    title = title_link.get("title") if title_link else None
    href = title_link.get("href") if title_link else None
    price = article.select_one("p.price_color")
    rating = article.select_one("p.star-rating")
    rating_classes = " ".join(rating.get("class", [])) if rating else ""
    return {
        "source": SOURCE,
        "source_url": urljoin(page_url, href) if href else page_url,
        "name_or_title": title,
        "category": None,
        "price": price.get_text(" ", strip=True) if price else None,
        "rating": rating_classes,
        "author": None,
        "tags": None,
        "description": None,
        "scraped_at": None,
    }


def scrape_books(session: Any, start_url: str = START_URL) -> list[dict[str, Any]]:
    """Scrape every page through the site's next-page link."""
    records: list[dict[str, Any]] = []
    url = start_url
    page_number = 0
    while url:
        page_number += 1
        LOGGER.info("Scraping book page %d: %s", page_number, url)
        try:
            response = get_page(session, url)
            soup = BeautifulSoup(response.text, "lxml")
            articles = soup.select("article.product_pod")
            for article in articles:
                try:
                    records.append(_extract_book(article, response.url))
                except Exception as exc:
                    LOGGER.warning("Skipping malformed book record on %s: %s", response.url, exc)
            next_link = soup.select_one("li.next > a")
            url = urljoin(response.url, next_link["href"]) if next_link and next_link.get("href") else None
        except Exception as exc:
            LOGGER.error("Book page failed: %s: %s", url, exc)
            break
        if url:
            delay_between_requests()
    return records


def scrape_all_books() -> list[dict[str, Any]]:
    return scrape_books(create_session())
