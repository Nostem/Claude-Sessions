# tests/test_search.py
from unittest.mock import patch, MagicMock
from obsidian_agent.search import search_brave, format_results

def test_returns_results():
    mock = MagicMock()
    mock.json.return_value = {"web": {"results": [
        {"title": "Study A", "description": "Finding A", "url": "https://a.com"},
    ]}}
    with patch("requests.get", return_value=mock):
        results = search_brave("cold exposure", api_key="test")
    assert results[0]["title"] == "Study A"
    assert results[0]["snippet"] == "Finding A"

def test_format_results_for_prompt():
    results = [{"title": "Study A", "snippet": "Finding A", "url": "https://a.com"}]
    formatted = format_results(results)
    assert "Study A" in formatted
    assert "Finding A" in formatted
    assert "https://a.com" in formatted

def test_handles_api_error():
    with patch("requests.get", side_effect=Exception("network error")):
        assert search_brave("query", "key") == []
