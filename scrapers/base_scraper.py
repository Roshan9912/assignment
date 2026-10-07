"""Shared, resilient HTTP support for the scraping pipeline."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

LOGGER = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create a session with a user agent and retry policy for transient failures."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ScrapingAssignment/1.0 (research-and-learning project)",
            "Accept": "text/html,application/xhtml+xml",
        }
    )
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_page(session: requests.Session, url: str, *, timeout: float = 15.0) -> requests.Response:
    """Fetch a page, retrying transient requests and logging failures."""
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response
    except requests.RequestException as exc:
        LOGGER.error("Failed to fetch %s: %s", url, exc)
        raise


def delay_between_requests() -> None:
    """Respect the assignment's requested request pacing."""
    time.sleep(0.5)


def parse_response(response: requests.Response, parser: Any) -> list[dict[str, Any]]:
    """Parse a successful response with a source-specific parser."""
    return parser(response.text, response.url)
