# Multi-Source Web Scraping & Data Consolidation

## Project overview

This project builds a Python ETL pipeline that scrapes the public practice sites Books to Scrape and Quotes to Scrape, normalizes their different HTML structures into one CSV schema, validates records, removes equivalent duplicates, and writes a summary report and log.

The executable entry point is `python main.py`. It performs the sequence:

`Scrape -> Clean -> Validate -> Deduplicate -> Consolidate -> Write outputs`

## Python and environment

- Requires Python 3.10, 3.11, or 3.12.
- The current workspace uses Python 3.14.2 for local verification, but the code is compatible with Python 3.10+.
- Create a private environment from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Run

```powershell
python main.py
```

The run creates or overwrites:

- `output/final_dataset.csv`
- `output/summary_report.json`
- `logs/scraper.log`

## Dependencies

The pinned dependencies are in `requirements.txt`:

- requests 2.32.5
- beautifulsoup4 4.13.5
- lxml 6.0.2
- pytest 8.4.1

## Source inspection and data model

| Field | Books to Scrape | Quotes to Scrape |
|---|---|---|
| source | Books to Scrape | Quotes to Scrape |
| source_url | Book detail page URL | Page URL where the quote appeared |
| name_or_title | Book title | Quote text |
| category | Empty; listing page does not expose it | Empty |
| price | Number from `p.price_color` | Empty |
| rating | Integer from the `star-rating` class | Empty |
| author | Empty | Author name from `small.author` |
| tags | Empty | Tags from `a.tag`, joined with `;` |
| description | Empty; listing page does not expose it | Empty |
| scraped_at | UTC timestamp | UTC timestamp |

Missing source-specific values are represented by empty CSV cells rather than invented values. The source URL for books is the product detail URL; for quotes it is the page URL containing the quote.

## Scraping and pagination

Both scrapers use a shared `requests.Session` with a User-Agent header, a 15-second timeout, retries for HTTP 429/500/502/503/504, and a 0.5-second pause between requests.

- Books starts at `https://books.toscrape.com/` and follows each `li.next > a` link with `urljoin`.
- Quotes starts at `https://quotes.toscrape.com/` and follows each `li.next > a` link with `urljoin`.
- The pagination loop does not hard-code a page count. A failed page is logged and stops only that source, allowing the other source to continue.
- Individual malformed records are logged and skipped rather than crashing the run.

## Cleaning, validation, and duplicate detection

- `clean_text` collapses whitespace, tabs, newlines, and non-breaking spaces.
- `clean_price` extracts a non-negative decimal from currency text such as `£51.77`.
- `clean_rating` converts words such as `Three` and numeric values to integers from 1 through 5.
- `clean_tags` lowercases, removes duplicate tags, sorts them, and joins them with semicolons.
- `normalize_url` resolves relative URLs and rejects malformed or non-HTTP(S) URLs.
- `validate_record` returns a list of reason codes. Empty means valid. It checks source, non-empty name, URL, non-negative numeric price, and rating range.
- Duplicate detection uses a SHA-256 fingerprint of source-specific identity fields. Books use source and title; quotes use source, author, and the first 50 characters of quote text. Punctuation is removed, lowercased, and whitespace is collapsed. Duplicates are removed rather than retained with an extra column.

## Error handling

The shared HTTP helper handles transient request failures with retries. Page failures are logged at error level. Malformed records, invalid values, and failed validation are logged as warnings. The two source scrapers are isolated so a failure in one source does not prevent the other source from running.

## Tests

Run all unit tests without network access:

```powershell
python -m pytest -q
```

The tests cover whitespace cleanup, price and rating conversion, tag normalization, URL normalization, validation reasons, and case/spacing-insensitive duplicate detection.

## Output and reconciliation

The summary contains collected and cleaned counts per source, rejected reasons, duplicates removed, final rows, timestamps, and duration. The expected invariant is:

`collected - rejected - duplicates = final_record_count`

This is evaluated from the generated summary and final CSV rather than assumed from the source counts.

## Assumptions and limitations

- The public sites are finite, plain server-rendered HTML pages and are only accessed through their public URLs.
- Books category and description are not taken from the listing pages because they are not exposed there; they remain empty.
- The run uses a learning-oriented User-Agent and does not bypass access controls or CAPTCHA.
- The target sites may change their HTML, so selectors should be reviewed if a run returns unexpectedly few records.
- A temporary page failure can cause that source to stop after its last successful page; the other source still runs.

## AI usage summary

See `AI_USAGE.md` for the tools, prompts, review changes, limitations found, and final verification.
