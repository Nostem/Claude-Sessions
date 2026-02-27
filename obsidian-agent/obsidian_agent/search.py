import requests
from typing import List, Dict

def search_brave(query: str, api_key: str, count: int = 8) -> List[Dict]:
    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": query, "count": count},
            timeout=10
        )
        r.raise_for_status()
        return [
            {"title": x.get("title",""), "snippet": x.get("description",""), "url": x.get("url","")}
            for x in r.json().get("web", {}).get("results", [])
        ]
    except Exception:
        return []

def format_results(results: List[Dict]) -> str:
    if not results:
        return "(No search results available)"
    lines = []
    for i, r in enumerate(results, 1):
        lines += [f"{i}. **{r['title']}**", f"   {r['snippet']}", f"   Source: {r['url']}"]
    return "\n".join(lines)
