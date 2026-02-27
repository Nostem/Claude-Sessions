import os
from pathlib import Path
from typing import Any, Dict, List
import yaml

def build_frontmatter(tags: List[str], created: str, **extra) -> Dict:
    fm = {"tags": tags, "created": created, "source": "obsidian-agent"}
    fm.update({k: v for k, v in extra.items() if v is not None and v != ""})
    return fm

def write_note(path: str, frontmatter: Dict[str, Any], body: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\n{yaml_str}---\n\n{body}\n")
