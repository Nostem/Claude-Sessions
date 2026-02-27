import hashlib, re
from typing import List, Dict

SUPPORTED_TAGS = {"research", "book", "writingprompt", "reflect"}
_PATTERN = re.compile(r'^[*-]\s+#(\w+)\s+(.*)', re.MULTILINE)

def parse_tags(content: str) -> List[Dict]:
    results = []
    for m in _PATTERN.finditer(content):
        tag = m.group(1).lower()
        arg = m.group(2).strip()
        if tag in SUPPORTED_TAGS and arg:
            h = hashlib.sha256(f"{tag}|{arg.lower()}".encode()).hexdigest()
            results.append({"tag": tag, "argument": arg, "hash": h})
    return results
