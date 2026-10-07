from processing.validation import validate_record


def test_valid_record_has_no_problems():
    record = {
        "source": "Books to Scrape",
        "name_or_title": "Example Book",
        "source_url": "https://books.toscrape.com/catalog/1.html",
        "price": 12.5,
        "rating": 4,
    }
    assert validate_record(record) == []


def test_invalid_values_are_reported():
    record = {
        "source": "Unknown",
        "name_or_title": "",
        "source_url": "not-a-url",
        "price": -1,
        "rating": 6,
    }
    assert set(validate_record(record)) == {
        "unknown_source", "missing_name", "invalid_url", "invalid_price", "invalid_rating"
    }
