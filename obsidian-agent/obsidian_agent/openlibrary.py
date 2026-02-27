from typing import Optional, Tuple
import requests

def parse_title_author(arg: str) -> Tuple[str, str]:
    if " by " in arg.lower():
        i = arg.lower().index(" by ")
        return arg[:i].strip(), arg[i+4:].strip()
    parts = arg.rsplit(" ", 2)
    return (parts[0], f"{parts[1]} {parts[2]}") if len(parts) >= 3 else (arg, "")

def amazon_cover_url(isbn10: str) -> str:
    return f"https://images-na.ssl-images-amazon.com/images/P/{isbn10}.01.LZZZZZZZ.jpg"

def lookup_book(title: str, author: str) -> Optional[dict]:
    try:
        r = requests.get("https://openlibrary.org/search.json",
            params={"q": f"{title} {author}", "limit": 1,
                    "fields": "title,author_name,first_publish_year,isbn,subject"},
            timeout=10)
        r.raise_for_status()
        docs = r.json().get("docs", [])
        if not docs:
            return None
        doc = docs[0]
        isbns = doc.get("isbn", [])
        isbn10 = next((i for i in isbns if len(i) == 10), isbns[0] if isbns else "")
        return {
            "title": doc.get("title", title),
            "author": (doc.get("author_name") or [author])[0],
            "published": doc.get("first_publish_year"),
            "isbn": isbn10,
            "subjects": doc.get("subject", [])[:5],
            "cover_url": amazon_cover_url(isbn10) if isbn10 else "",
        }
    except Exception:
        return None
