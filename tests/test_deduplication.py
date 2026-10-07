from processing.deduplication import find_duplicates, make_fingerprint


def test_duplicate_detection_is_case_and_space_insensitive():
    base = {
        "source": "Books to Scrape",
        "name_or_title": "Example Book Title",
        "author": None,
    }
    records = [
        base,
        {**base, "name_or_title": "  Example Book Title  "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
    ]
    unique, duplicates = find_duplicates(records)
    assert len(unique) == 1
    assert len(duplicates) == 2
    assert make_fingerprint(records[0]) == make_fingerprint(records[1])
