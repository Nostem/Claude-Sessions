import os
from pathlib import Path
from typing import List

_STOP = {"a","an","the","and","or","in","on","at","to","for","of","with","by","is","it","be","as"}

def _keywords(text: str) -> List[str]:
    return [w for w in text.lower().split() if len(w) > 3 and w not in _STOP]

def find_related_notes(query: str, zettel_path: str, max_results: int = 5) -> List[str]:
    if not os.path.exists(zettel_path):
        return []
    kws = _keywords(query)
    if not kws:
        return []
    scored = []
    for f in Path(zettel_path).glob("*.md"):
        try:
            text = (f.stem + " " + f.read_text(encoding="utf-8")[:500]).lower()
        except Exception:
            continue
        score = sum(1 for k in kws if k in text)
        if score > 0:
            scored.append((score, f.stem))
    scored.sort(reverse=True)
    return [f"[[{s}]]" for _, s in scored[:max_results]]
