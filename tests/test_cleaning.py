from processing.cleaning import clean_price, clean_rating, clean_text, clean_tags, normalize_url


def test_clean_text_collapses_whitespace():
    assert clean_text("  Hello\xa0World\n") == "Hello World"


def test_clean_price_and_rating():
    assert clean_price("£51.77") == 51.77
    assert clean_rating("Three") == 3
    assert clean_rating("star-rating Three") == 3


def test_clean_tags_are_normalized():
    assert clean_tags([" Fiction ", "fiction", "Science"]) == "fiction;science"


def test_normalize_url():
    assert normalize_url("/author/Example", "https://quotes.toscrape.com/") == "https://quotes.toscrape.com/author/Example"
