# tests/test_openlibrary.py
from unittest.mock import patch, MagicMock
from obsidian_agent.openlibrary import lookup_book, parse_title_author, amazon_cover_url

def test_parse_with_by():
    t, a = parse_title_author("Deep Work by Cal Newport")
    assert t == "Deep Work" and a == "Cal Newport"

def test_parse_without_by():
    t, a = parse_title_author("Deep Work Cal Newport")
    assert "Deep Work" in t or "Cal Newport" in a

def test_amazon_cover_url():
    url = amazon_cover_url("0804137390")
    assert "0804137390" in url and url.startswith("https://")

def test_lookup_returns_metadata():
    mock = MagicMock()
    mock.json.return_value = {"docs": [{"title": "Deep Work",
        "author_name": ["Cal Newport"], "first_publish_year": 2016,
        "isbn": ["0804137390"], "subject": ["Productivity"]}]}
    with patch("requests.get", return_value=mock):
        r = lookup_book("Deep Work", "Cal Newport")
    assert r["title"] == "Deep Work"
    assert r["isbn"] == "0804137390"
    assert r["published"] == 2016

def test_lookup_returns_none_if_not_found():
    mock = MagicMock()
    mock.json.return_value = {"docs": []}
    with patch("requests.get", return_value=mock):
        assert lookup_book("Nonexistent XYZ", "Nobody") is None
