import hashlib, re
from typing import List, Dict

SUPPORTED_TAGS = {"research", "book", "writingprompt", "reflect"}
_PATTERN = re.compile(r'^[*-]\s+#(\w+)\s+(.*)', re.MULTILINE)
_ANNOTATION = re.compile(r"\s+'Agent Complete'\s+\[\[.*?\]\]\s*$", re.IGNORECASE)

def parse_tags(content: str) -> List[Dict]:
    results = []
    for m in _PATTERN.finditer(content):
        tag = m.group(1).lower()
        arg = _ANNOTATION.sub("", m.group(2)).strip()
        if tag in SUPPORTED_TAGS and arg:
            h = hashlib.sha256(f"{tag}|{arg.lower()}".encode()).hexdigest()
            results.append({"tag": tag, "argument": arg, "hash": h})
    return results
