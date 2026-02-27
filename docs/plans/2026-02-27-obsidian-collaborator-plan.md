# Obsidian Collaborator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone Python daemon that watches the Obsidian Files vault for hashtag triggers in daily notes, calls the Claude API, and writes Zettelkasten notes back to the vault.

**Architecture:** A watchdog-based file watcher dispatches tag detections to specialized handlers. Each handler calls the Claude API with rich context (system prompt + rolling memory + vault excerpts) and writes a formatted Zettelkasten note. SHA-256 hashes deduplicate across vault saves and iCloud sync events.

**Tech Stack:** Python 3.11+, watchdog, anthropic, requests, PyYAML, pytest, subprocess (git, osascript)

**Source:** `Claude-Sessions/obsidian-agent/`
**Runtime state:** `~/.obsidian-agent/` (not in git)

---

## Task 1: Project Scaffold

**Files:**
- Create: `obsidian-agent/requirements.txt`
- Create: `obsidian-agent/config.json`
- Create: `obsidian-agent/obsidian_agent/__init__.py`
- Create: `obsidian-agent/obsidian_agent/handlers/__init__.py`
- Create: `obsidian-agent/tests/__init__.py`

**Step 1: Create directory structure**
```bash
mkdir -p obsidian-agent/obsidian_agent/handlers
mkdir -p obsidian-agent/tests/fixtures
mkdir -p obsidian-agent/launch_agent
touch obsidian-agent/obsidian_agent/__init__.py
touch obsidian-agent/obsidian_agent/handlers/__init__.py
touch obsidian-agent/tests/__init__.py
touch obsidian-agent/tests/fixtures/.gitkeep
```

**Step 2: Write `obsidian-agent/requirements.txt`**
```
anthropic>=0.40.0
watchdog>=4.0.0
requests>=2.31.0
PyYAML>=6.0
pytest>=8.0.0
```

**Step 3: Write `obsidian-agent/config.json` (template)**
```json
{
  "_comment": "Copy to ~/.obsidian-agent/config.json and fill in your values",
  "vault_path": "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Files",
  "daily_notes_folder": "Daily Notes",
  "output_folder": "Zettelkasten",
  "website_repo_local": "~/.obsidian-agent/repos/nostem.github.io",
  "website_repo_remote": "https://github.com/Nostem/nostem.github.io",
  "bookshelf_file": "data/books.json",
  "model": "claude-sonnet-4-6",
  "max_memory_lines": 100,
  "search_provider": "brave",
  "search_api_key_env": "BRAVE_API_KEY",
  "anthropic_api_key_env": "ANTHROPIC_API_KEY"
}
```

**Step 4: Commit**
```bash
git add obsidian-agent/
git commit -m "feat: scaffold obsidian-agent project structure"
```

---

## Task 2: Config Loader

**Files:**
- Create: `obsidian-agent/obsidian_agent/config.py`
- Create: `obsidian-agent/tests/test_config.py`

**Step 1: Write the failing test**
```python
# tests/test_config.py
import json, pytest
from obsidian_agent.config import load_config, ConfigError

def test_load_valid_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "vault_path": str(tmp_path), "daily_notes_folder": "Daily Notes",
        "output_folder": "Zettelkasten", "model": "claude-sonnet-4-6",
        "anthropic_api_key_env": "ANTHROPIC_API_KEY"
    }))
    assert load_config(str(cfg))["model"] == "claude-sonnet-4-6"

def test_missing_key_raises(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"vault_path": "/tmp"}))
    with pytest.raises(ConfigError, match="missing required key"):
        load_config(str(cfg))

def test_tilde_expanded(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "vault_path": "~/some/path", "daily_notes_folder": "Daily Notes",
        "output_folder": "Zettelkasten", "model": "claude-sonnet-4-6",
        "anthropic_api_key_env": "ANTHROPIC_API_KEY"
    }))
    assert not load_config(str(cfg))["vault_path"].startswith("~")
```

**Step 2: Run — expect FAIL (ImportError)**
```bash
cd obsidian-agent && python -m pytest tests/test_config.py -v
```

**Step 3: Implement `obsidian_agent/config.py`**
```python
import json, os
from pathlib import Path

REQUIRED = ["vault_path", "daily_notes_folder", "output_folder", "model", "anthropic_api_key_env"]

class ConfigError(Exception):
    pass

def load_config(path: str) -> dict:
    with open(path) as f:
        cfg = json.load(f)
    for k in REQUIRED:
        if k not in cfg:
            raise ConfigError(f"missing required key: {k}")
    for k in ["vault_path", "website_repo_local"]:
        if k in cfg:
            cfg[k] = str(Path(cfg[k]).expanduser())
    return cfg
```

**Step 4: Run — expect 3 PASS**
```bash
python -m pytest tests/test_config.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/config.py tests/test_config.py
git commit -m "feat: config loader with validation and path expansion"
```

---

## Task 3: State Manager (Deduplication)

**Files:**
- Create: `obsidian-agent/obsidian_agent/state.py`
- Create: `obsidian-agent/tests/test_state.py`

**Step 1: Write the failing tests**
```python
# tests/test_state.py
from obsidian_agent.state import StateManager

def test_new_item_not_processed(tmp_path):
    sm = StateManager(str(tmp_path / "state.json"))
    assert not sm.is_processed("2026-02-27", "research", "cold exposure")

def test_mark_and_check(tmp_path):
    sm = StateManager(str(tmp_path / "state.json"))
    sm.mark_processed("2026-02-27", "research", "cold exposure")
    assert sm.is_processed("2026-02-27", "research", "cold exposure")

def test_different_arg_not_processed(tmp_path):
    sm = StateManager(str(tmp_path / "state.json"))
    sm.mark_processed("2026-02-27", "research", "topic A")
    assert not sm.is_processed("2026-02-27", "research", "topic B")

def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "state.json")
    StateManager(path).mark_processed("2026-02-27", "research", "test")
    assert StateManager(path).is_processed("2026-02-27", "research", "test")
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_state.py -v
```

**Step 3: Implement `obsidian_agent/state.py`**
```python
import hashlib, json, os

class StateManager:
    def __init__(self, path: str):
        self.path = path
        self._set = self._load()

    def _load(self) -> set:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return set(json.load(f).get("processed", []))
        return set()

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump({"processed": list(self._set)}, f, indent=2)

    def _hash(self, date, tag, arg) -> str:
        return hashlib.sha256(f"{date}|{tag.lower()}|{arg.lower().strip()}".encode()).hexdigest()

    def is_processed(self, date, tag, arg) -> bool:
        return self._hash(date, tag, arg) in self._set

    def mark_processed(self, date, tag, arg):
        self._set.add(self._hash(date, tag, arg))
        self._save()
```

**Step 4: Run — expect 4 PASS**
```bash
python -m pytest tests/test_state.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/state.py tests/test_state.py
git commit -m "feat: SHA-256 dedup state manager"
```

---

## Task 4: Tag Parser

**Files:**
- Create: `obsidian-agent/obsidian_agent/parser.py`
- Create: `obsidian-agent/tests/test_parser.py`

**Step 1: Write the failing tests**
```python
# tests/test_parser.py
from obsidian_agent.parser import parse_tags

NOTE = """# Feb 27
- #research cold exposure on metabolism
- #book Deep Work by Cal Newport
- #writingprompt essay on slowness
- just a regular bullet
- #reflect on avoiding deep work
* #research asterisk format works
"""

def test_finds_all_supported_tags():
    tags = parse_tags(NOTE)
    assert len(tags) == 5  # 2 research + book + writingprompt + reflect

def test_argument_extracted():
    tags = parse_tags("- #research cold exposure")
    assert tags[0]["argument"] == "cold exposure"

def test_case_insensitive():
    tags = parse_tags("- #Research Cold Exposure\n- #BOOK Some Book")
    assert tags[0]["tag"] == "research"
    assert tags[1]["tag"] == "book"

def test_asterisk_bullet():
    tags = parse_tags("* #research topic here")
    assert tags[0]["tag"] == "research"

def test_skips_untagged_bullets():
    tags = parse_tags("- just a regular bullet")
    assert tags == []

def test_returns_hash():
    tags = parse_tags("- #research some topic")
    assert len(tags[0]["hash"]) == 64

def test_empty_note():
    assert parse_tags("") == []
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_parser.py -v
```

**Step 3: Implement `obsidian_agent/parser.py`**
```python
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
```

**Step 4: Run — expect all PASS**
```bash
python -m pytest tests/test_parser.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/parser.py tests/test_parser.py
git commit -m "feat: markdown tag parser for hashtag bullet lines"
```

---

## Task 5: Memory System

**Files:**
- Create: `obsidian-agent/obsidian_agent/memory.py`
- Create: `obsidian-agent/tests/test_memory.py`

**Step 1: Write the failing tests**
```python
# tests/test_memory.py
from obsidian_agent.memory import Memory

def test_empty_returns_empty_string(tmp_path):
    assert Memory(str(tmp_path / "memory.md")).read_context() == ""

def test_append_and_read(tmp_path):
    m = Memory(str(tmp_path / "memory.md"))
    m.append("2026-02-27", "research", "cold exposure", "5 findings, linked [[Hormesis]]")
    ctx = m.read_context()
    assert "cold exposure" in ctx
    assert "research" in ctx

def test_max_lines_respected(tmp_path):
    m = Memory(str(tmp_path / "memory.md"), max_lines=3)
    for i in range(10):
        m.append("2026-02-27", "research", f"topic {i}", "summary")
    lines = [l for l in m.read_context().split("\n") if l.strip()]
    assert len(lines) <= 3
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_memory.py -v
```

**Step 3: Implement `obsidian_agent/memory.py`**
```python
import os

class Memory:
    def __init__(self, path: str, max_lines: int = 100):
        self.path = path
        self.max_lines = max_lines

    def read_context(self) -> str:
        if not os.path.exists(self.path):
            return ""
        with open(self.path) as f:
            lines = f.readlines()
        recent = [l for l in lines if l.strip()][-self.max_lines:]
        return "".join(recent)

    def append(self, date: str, tag: str, argument: str, summary: str):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a") as f:
            f.write(f"{date} | {tag} | \"{argument}\" → {summary}\n")
```

**Step 4: Run — expect 3 PASS**
```bash
python -m pytest tests/test_memory.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/memory.py tests/test_memory.py
git commit -m "feat: rolling memory system"
```

---

## Task 6: Vault Link Enrichment

**Files:**
- Create: `obsidian-agent/obsidian_agent/vault.py`
- Create: `obsidian-agent/tests/test_vault.py`

**Step 1: Write the failing tests**
```python
# tests/test_vault.py
from obsidian_agent.vault import find_related_notes

def test_finds_by_filename(tmp_path):
    z = tmp_path / "Z"
    z.mkdir()
    (z / "Cold Exposure Research.md").write_text("# Cold Exposure\n...")
    assert "[[Cold Exposure Research]]" in find_related_notes("cold exposure", str(z))

def test_finds_by_content(tmp_path):
    z = tmp_path / "Z"
    z.mkdir()
    (z / "Sleep Science.md").write_text("# Sleep\nMetabolism and cold exposure cycles.")
    assert "[[Sleep Science]]" in find_related_notes("cold exposure metabolism", str(z))

def test_no_false_positives(tmp_path):
    z = tmp_path / "Z"
    z.mkdir()
    (z / "Pasta Recipes.md").write_text("# Pasta\nBoil water, add salt.")
    assert "[[Pasta Recipes]]" not in find_related_notes("cold exposure", str(z))

def test_empty_vault_returns_empty(tmp_path):
    z = tmp_path / "Z"
    z.mkdir()
    assert find_related_notes("any topic", str(z)) == []

def test_max_five_results(tmp_path):
    z = tmp_path / "Z"
    z.mkdir()
    for i in range(10):
        (z / f"Cold Note {i}.md").write_text("cold exposure test content")
    assert len(find_related_notes("cold exposure", str(z))) <= 5
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_vault.py -v
```

**Step 3: Implement `obsidian_agent/vault.py`**
```python
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
```

**Step 4: Run — expect all PASS**
```bash
python -m pytest tests/test_vault.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/vault.py tests/test_vault.py
git commit -m "feat: vault link enrichment via keyword matching"
```

---

## Task 7: Note Writer

**Files:**
- Create: `obsidian-agent/obsidian_agent/note_writer.py`
- Create: `obsidian-agent/tests/test_note_writer.py`

**Step 1: Write the failing tests**
```python
# tests/test_note_writer.py
from obsidian_agent.note_writer import write_note, build_frontmatter
from pathlib import Path

def test_creates_file(tmp_path):
    write_note(str(tmp_path / "Note.md"), {"tags": ["review"]}, "# Title\nBody.")
    assert (tmp_path / "Note.md").exists()

def test_yaml_frontmatter_present(tmp_path):
    write_note(str(tmp_path / "Note.md"), {"tags": ["review", "research"], "created": "2026-02-27"}, "# Title")
    content = (tmp_path / "Note.md").read_text()
    assert content.startswith("---\n")
    assert "review" in content
    assert "# Title" in content

def test_creates_parent_dirs(tmp_path):
    path = str(tmp_path / "deep" / "nested" / "note.md")
    write_note(path, {"tags": ["review"]}, "# Note")
    assert Path(path).exists()

def test_build_frontmatter_merges_extra():
    fm = build_frontmatter(tags=["review"], created="2026-02-27", query="cold exposure")
    assert fm["query"] == "cold exposure"
    assert fm["source"] == "obsidian-agent"
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_note_writer.py -v
```

**Step 3: Implement `obsidian_agent/note_writer.py`**
```python
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
```

**Step 4: Run — expect all PASS**
```bash
python -m pytest tests/test_note_writer.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/note_writer.py tests/test_note_writer.py
git commit -m "feat: note writer with YAML frontmatter"
```

---

## Task 8: macOS Notification

**Files:**
- Create: `obsidian-agent/obsidian_agent/notify.py`
- Create: `obsidian-agent/tests/test_notify.py`

**Step 1: Write the failing tests**
```python
# tests/test_notify.py
from unittest.mock import patch
from obsidian_agent.notify import send_notification

def test_calls_osascript():
    with patch("subprocess.run") as mock:
        send_notification("Obsidian Collaborator", "#research", "Note created: Cold Exposure")
        args = mock.call_args[0][0]
        assert args[0] == "osascript"
        assert "Obsidian Collaborator" in " ".join(args)

def test_does_not_raise_on_failure():
    with patch("subprocess.run", side_effect=Exception("not on macOS")):
        send_notification("Title", "subtitle", "message")  # must not raise
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_notify.py -v
```

**Step 3: Implement `obsidian_agent/notify.py`**
```python
import subprocess

def send_notification(title: str, subtitle: str, message: str):
    script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass  # Best-effort; works on macOS only
```

**Step 4: Run — expect 2 PASS**
```bash
python -m pytest tests/test_notify.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/notify.py tests/test_notify.py
git commit -m "feat: macOS notification wrapper"
```

---

## Task 9: SYSTEM.md + Claude API Client

**Files:**
- Create: `obsidian-agent/SYSTEM.md`
- Create: `obsidian-agent/obsidian_agent/claude_client.py`
- Create: `obsidian-agent/tests/test_claude_client.py`

**Step 1: Write `obsidian-agent/SYSTEM.md`**
```markdown
# Obsidian Collaborator — System Prompt

You are an Obsidian vault collaborator. Your job is to create high-quality
Zettelkasten notes in response to hashtag requests from the user's daily notes.
Write clearly, concisely, and with genuine intellectual substance.

## Zettelkasten Conventions
- Atomic notes: one idea per note
- Use [[wikilinks]] to reference related concepts inline
- Headers: H2 (##) for sections, H3 (###) for subsections
- Be substantive — real findings, not filler

## Output Rules
- Return ONLY the note body (no YAML frontmatter — added by the system)
- Start with a single H1: `# [Title]`
- Use the exact section structure given in each prompt
- Keep notes under 800 words unless depth demands more
- Add [[wikilinks]] wherever concepts might connect to other notes

## Memory Context
When you see session memory entries above the prompt, use them to:
- Avoid repeating topics already covered
- Reference prior notes with [[wikilinks]]
- Build on existing vault patterns
```

**Step 2: Write the failing tests**
```python
# tests/test_claude_client.py
from unittest.mock import patch, MagicMock
from obsidian_agent.claude_client import ClaudeClient

def test_returns_text(tmp_path):
    sys_md = tmp_path / "SYSTEM.md"
    sys_md.write_text("You are helpful.")
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="# Note\n\nContent.")]
    with patch("anthropic.Anthropic") as MockA:
        MockA.return_value.messages.create.return_value = mock_resp
        client = ClaudeClient("test-key", str(sys_md), "claude-sonnet-4-6")
        assert client.call("Write a note", "") == "# Note\n\nContent."

def test_memory_included_in_prompt(tmp_path):
    sys_md = tmp_path / "SYSTEM.md"
    sys_md.write_text("You are helpful.")
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="Result")]
    with patch("anthropic.Anthropic") as MockA:
        instance = MockA.return_value
        instance.messages.create.return_value = mock_resp
        client = ClaudeClient("test-key", str(sys_md), "claude-sonnet-4-6")
        client.call("Write a note", "2026-02-27 | research | prior topic → created note")
        prompt_sent = instance.messages.create.call_args[1]["messages"][0]["content"]
        assert "prior topic" in prompt_sent
```

**Step 3: Run — expect FAIL**
```bash
python -m pytest tests/test_claude_client.py -v
```

**Step 4: Implement `obsidian_agent/claude_client.py`**
```python
import anthropic

class ClaudeClient:
    def __init__(self, api_key: str, system_md_path: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        with open(system_md_path) as f:
            self.system = f.read()

    def call(self, prompt: str, memory_context: str) -> str:
        full = prompt
        if memory_context.strip():
            full = f"## Recent session memory\n\n{memory_context}\n\n---\n\n{prompt}"
        resp = self.client.messages.create(
            model=self.model, max_tokens=2048,
            system=self.system,
            messages=[{"role": "user", "content": full}]
        )
        return resp.content[0].text
```

**Step 5: Run — expect 2 PASS**
```bash
python -m pytest tests/test_claude_client.py -v
```

**Step 6: Commit**
```bash
git add obsidian_agent/claude_client.py tests/test_claude_client.py SYSTEM.md
git commit -m "feat: Claude API client with system prompt and memory context"
```

---

## Task 10: Web Search Client

**Files:**
- Create: `obsidian-agent/obsidian_agent/search.py`
- Create: `obsidian-agent/tests/test_search.py`

**Step 1: Write the failing tests**
```python
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
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_search.py -v
```

**Step 3: Implement `obsidian_agent/search.py`**
```python
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
```

**Step 4: Run — expect 3 PASS**
```bash
python -m pytest tests/test_search.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/search.py tests/test_search.py
git commit -m "feat: Brave Search API client"
```

---

## Task 11: #research Handler

**Files:**
- Create: `obsidian-agent/obsidian_agent/handlers/research.py`
- Create: `obsidian-agent/tests/test_handler_research.py`

**Step 1: Write the failing tests**
```python
# tests/test_handler_research.py
from unittest.mock import patch
from obsidian_agent.handlers.research import handle_research
import yaml

def cfg(tmp_path):
    return {"vault_path": str(tmp_path/"vault"), "output_folder": "Zettelkasten",
            "model": "claude-sonnet-4-6", "anthropic_api_key_env": "ANTHROPIC_API_KEY",
            "search_provider": "brave", "search_api_key_env": "BRAVE_API_KEY"}

def test_creates_note(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    with patch("obsidian_agent.handlers.research.search_brave", return_value=[]),\
         patch("obsidian_agent.handlers.research.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.research.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY":"test","BRAVE_API_KEY":"test"}):
        M.return_value.call.return_value = "# Cold Exposure\n\n## Summary\nFindings."
        handle_research("cold exposure", cfg(tmp_path), memory_context="", date="2026-02-27")
    notes = list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))
    assert len(notes) == 1

def test_note_has_review_tag(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    with patch("obsidian_agent.handlers.research.search_brave", return_value=[]),\
         patch("obsidian_agent.handlers.research.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.research.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY":"test","BRAVE_API_KEY":"test"}):
        M.return_value.call.return_value = "# Note\n\n## Summary\nContent."
        handle_research("cold exposure", cfg(tmp_path), memory_context="", date="2026-02-27")
    content = list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))[0].read_text()
    assert "review" in content
    assert "research" in content
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_handler_research.py -v
```

**Step 3: Implement `obsidian_agent/handlers/research.py`**
```python
import os
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.search import search_brave, format_results
from obsidian_agent.vault import find_related_notes

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def handle_research(topic: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    search_key = os.environ.get(config.get("search_api_key_env", "BRAVE_API_KEY"), "")
    zettel = os.path.join(config["vault_path"], config["output_folder"])

    results = search_brave(topic, api_key=search_key) if search_key else []
    search_ctx = format_results(results)
    related = find_related_notes(topic, zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a research note for: "{topic}"

## Web Search Results
{search_ctx}

## Related vault notes
{related_str or "(none yet)"}

## Required sections (exact H2 headings)
- ## Summary
- ## Key Findings
- ## Open Questions
- ## Sources
- ## Related

Include [[wikilinks]] for concepts in the related notes list.
Start with: # {topic.title()} — Research Note"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    note_path = os.path.join(zettel, f"{date} - {topic.title()}.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "research"], created=date, type="research",
        query=topic, related=related_str
    ), body)
    send_notification("Obsidian Collaborator", "#research", f"Note: {topic.title()}")
    return note_path
```

**Step 4: Run — expect 2 PASS**
```bash
python -m pytest tests/test_handler_research.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/handlers/research.py tests/test_handler_research.py
git commit -m "feat: #research handler with web search and vault enrichment"
```

---

## Task 12: #writingprompt Handler

**Files:**
- Create: `obsidian-agent/obsidian_agent/handlers/writingprompt.py`
- Create: `obsidian-agent/tests/test_handler_writingprompt.py`

**Step 1: Write the failing tests**
```python
# tests/test_handler_writingprompt.py
from unittest.mock import patch
from obsidian_agent.handlers.writingprompt import handle_writingprompt

def cfg(tmp_path):
    return {"vault_path": str(tmp_path/"vault"), "output_folder": "Zettelkasten",
            "model": "claude-sonnet-4-6", "anthropic_api_key_env": "ANTHROPIC_API_KEY"}

def test_creates_note(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    with patch("obsidian_agent.handlers.writingprompt.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.writingprompt.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}):
        M.return_value.call.return_value = "# Essay Outline\n\n## Core Thesis\nContent."
        handle_writingprompt("essay on solitude", cfg(tmp_path), memory_context="", date="2026-02-27")
    assert len(list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))) == 1

def test_note_has_writing_prompt_tag(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    with patch("obsidian_agent.handlers.writingprompt.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.writingprompt.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}):
        M.return_value.call.return_value = "# Outline\n\n## Core Thesis\nContent."
        handle_writingprompt("essay on solitude", cfg(tmp_path), memory_context="", date="2026-02-27")
    content = list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))[0].read_text()
    assert "writing-prompt" in content
    assert "review" in content
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_handler_writingprompt.py -v
```

**Step 3: Implement `obsidian_agent/handlers/writingprompt.py`**
```python
import os
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.vault import find_related_notes

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def handle_writingprompt(subject: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    zettel = os.path.join(config["vault_path"], config["output_folder"])
    related = find_related_notes(subject, zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a writing outline for: "{subject}"

## Related vault notes to link
{related_str or "(none yet)"}

## Required sections (exact H2 headings)
- ## Core Thesis
- ## Angles to Explore
- ## Structure
- ## Opening Ideas
- ## Inspiration / Related

Be substantive — actual angles and ideas, not placeholders.
Include [[wikilinks]] for concepts in the related notes list.
Start with: # {subject.title()} — Writing Outline"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    note_path = os.path.join(zettel, f"{date} - {subject.title()} Outline.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "writing-prompt"], created=date, type="writing-prompt",
        subject=subject, related=related_str
    ), body)
    send_notification("Obsidian Collaborator", "#writingprompt", f"Outline: {subject.title()}")
    return note_path
```

**Step 4: Run — expect 2 PASS**
```bash
python -m pytest tests/test_handler_writingprompt.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/handlers/writingprompt.py tests/test_handler_writingprompt.py
git commit -m "feat: #writingprompt handler"
```

---

## Task 13: #reflect Handler

**Files:**
- Create: `obsidian-agent/obsidian_agent/handlers/reflect.py`
- Create: `obsidian-agent/tests/test_handler_reflect.py`

**Step 1: Write the failing tests**
```python
# tests/test_handler_reflect.py
from unittest.mock import patch
from obsidian_agent.handlers.reflect import handle_reflect, get_vault_excerpts

def cfg(tmp_path):
    return {"vault_path": str(tmp_path/"vault"), "output_folder": "Zettelkasten",
            "model": "claude-sonnet-4-6", "anthropic_api_key_env": "ANTHROPIC_API_KEY"}

def test_creates_reflection_note(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    with patch("obsidian_agent.handlers.reflect.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.reflect.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}):
        M.return_value.call.return_value = "# Reflection\n\n## What the vault says\nContent."
        handle_reflect("avoiding deep work", cfg(tmp_path), memory_context="", date="2026-02-27")
    notes = list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))
    assert len(notes) == 1
    assert "Reflection" in notes[0].name

def test_get_excerpts_reads_related_notes(tmp_path):
    z = tmp_path / "Z"
    z.mkdir()
    (z / "Deep Work Research.md").write_text("# Deep Work\nConcentration and flow state...")
    excerpts = get_vault_excerpts("deep work", str(z))
    assert "Deep Work" in excerpts
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_handler_reflect.py -v
```

**Step 3: Implement `obsidian_agent/handlers/reflect.py`**
```python
import os
from pathlib import Path
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.vault import find_related_notes, _keywords

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def get_vault_excerpts(topic: str, zettel_path: str, max_notes: int = 5, chars: int = 400) -> str:
    if not os.path.exists(zettel_path):
        return "(vault is empty)"
    kws = _keywords(topic)
    excerpts = []
    for f in Path(zettel_path).glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(k in (f.stem + " " + content).lower() for k in kws):
            excerpts.append(f"**[[{f.stem}]]**\n{content[:chars]}...")
        if len(excerpts) >= max_notes:
            break
    return "\n\n---\n\n".join(excerpts) if excerpts else "(no related notes found yet)"

def handle_reflect(topic: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    zettel = os.path.join(config["vault_path"], config["output_folder"])
    excerpts = get_vault_excerpts(topic, zettel)
    related = find_related_notes(topic, zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a reflection note on: "{topic}"

## Relevant vault excerpts
{excerpts}

## Required sections (exact H2 headings)
- ## What the vault says
- ## Synthesis
- ## Tensions / Questions
- ## What I might do differently
- ## Related

Be honest and nuanced. Use [[wikilinks]] to reference the excerpted notes.
Start with: # Reflection — {topic.title()}"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    note_path = os.path.join(zettel, f"{date} - Reflection - {topic.title()}.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "reflection"], created=date, type="reflection",
        topic=topic, related=related_str
    ), body)
    send_notification("Obsidian Collaborator", "#reflect", f"Reflection: {topic.title()}")
    return note_path
```

**Step 4: Run — expect 2 PASS**
```bash
python -m pytest tests/test_handler_reflect.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/handlers/reflect.py tests/test_handler_reflect.py
git commit -m "feat: #reflect handler with vault excerpt cross-referencing"
```

---

## Task 14: OpenLibrary Client

**Files:**
- Create: `obsidian-agent/obsidian_agent/openlibrary.py`
- Create: `obsidian-agent/tests/test_openlibrary.py`

**Step 1: Write the failing tests**
```python
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
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_openlibrary.py -v
```

**Step 3: Implement `obsidian_agent/openlibrary.py`**
```python
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
```

**Step 4: Run — expect all PASS**
```bash
python -m pytest tests/test_openlibrary.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/openlibrary.py tests/test_openlibrary.py
git commit -m "feat: OpenLibrary API client with Amazon cover URL builder"
```

---

## Task 15: Website Updater

**Files:**
- Create: `obsidian-agent/obsidian_agent/website.py`
- Create: `obsidian-agent/tests/test_website.py`

**Step 1: Write the failing tests**
```python
# tests/test_website.py
import json
from unittest.mock import patch, MagicMock
from obsidian_agent.website import clone_or_pull_repo, update_bookshelf, commit_and_push

def test_adds_book_entry(tmp_path):
    f = tmp_path / "books.json"
    f.write_text(json.dumps([{"title": "Existing", "author": "A"}]))
    update_bookshelf(str(f), {"title": "Deep Work", "author": "Cal Newport", "isbn": "x", "cover": "", "status": "to-read", "added": "2026-02-27"})
    data = json.loads(f.read_text())
    assert len(data) == 2
    assert data[-1]["title"] == "Deep Work"

def test_prevents_duplicate(tmp_path):
    f = tmp_path / "books.json"
    f.write_text(json.dumps([{"title": "Deep Work", "author": "Cal Newport"}]))
    update_bookshelf(str(f), {"title": "Deep Work", "author": "Cal Newport", "isbn": "", "cover": "", "status": "to-read", "added": "2026-02-27"})
    assert len(json.loads(f.read_text())) == 1

def test_commit_and_push_runs_git(tmp_path):
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0)
        commit_and_push(str(tmp_path), "Add Deep Work")
    calls = [str(c) for c in mock.call_args_list]
    assert any("commit" in c for c in calls)
    assert any("push" in c for c in calls)
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_website.py -v
```

**Step 3: Implement `obsidian_agent/website.py`**
```python
import json, os, subprocess

def clone_or_pull_repo(url: str, local: str):
    if os.path.exists(os.path.join(local, ".git")):
        subprocess.run(["git", "-C", local, "pull", "--rebase"], check=True)
    else:
        os.makedirs(os.path.dirname(local), exist_ok=True)
        subprocess.run(["git", "clone", url, local], check=True)

def update_bookshelf(path: str, new_book: dict):
    books = json.loads(open(path).read()) if os.path.exists(path) else []
    existing = {b.get("title","").lower() for b in books}
    if new_book.get("title","").lower() in existing:
        return
    books.append(new_book)
    with open(path, "w") as f:
        json.dump(books, f, indent=2)

def commit_and_push(repo: str, message: str):
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-m", message], check=True)
    subprocess.run(["git", "-C", repo, "push"], check=True)
```

**Step 4: Run — expect 3 PASS**
```bash
python -m pytest tests/test_website.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/website.py tests/test_website.py
git commit -m "feat: website bookshelf updater with git integration"
```

---

## Task 16: #book Handler

**Files:**
- Create: `obsidian-agent/obsidian_agent/handlers/book.py`
- Create: `obsidian-agent/tests/test_handler_book.py`

**Step 1: Write the failing tests**
```python
# tests/test_handler_book.py
import json
from unittest.mock import patch
from obsidian_agent.handlers.book import handle_book

def cfg(tmp_path):
    repo = str(tmp_path / "repo")
    return {"vault_path": str(tmp_path/"vault"), "output_folder": "Zettelkasten",
            "model": "claude-sonnet-4-6", "anthropic_api_key_env": "ANTHROPIC_API_KEY",
            "website_repo_local": repo, "website_repo_remote": "https://github.com/Nostem/nostem.github.io",
            "bookshelf_file": "data/books.json"}

def test_creates_note(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    (tmp_path/"repo"/"data").mkdir(parents=True)
    (tmp_path/"repo"/"data"/"books.json").write_text("[]")
    meta = {"title":"Deep Work","author":"Cal Newport","isbn":"0804137390",
            "published":2016,"subjects":["Productivity"],"cover_url":"https://..."}
    with patch("obsidian_agent.handlers.book.lookup_book", return_value=meta),\
         patch("obsidian_agent.handlers.book.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.book.clone_or_pull_repo"),\
         patch("obsidian_agent.handlers.book.commit_and_push"),\
         patch("obsidian_agent.handlers.book.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY":"test"}):
        M.return_value.call.return_value = "# Deep Work\n\n## Synopsis\nAbout focus."
        handle_book("Deep Work by Cal Newport", cfg(tmp_path), memory_context="", date="2026-02-27")
    assert len(list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))) == 1

def test_updates_bookshelf(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    (tmp_path/"repo"/"data").mkdir(parents=True)
    books_file = tmp_path/"repo"/"data"/"books.json"
    books_file.write_text("[]")
    meta = {"title":"Deep Work","author":"Cal Newport","isbn":"0804137390",
            "published":2016,"subjects":[],"cover_url":"https://..."}
    with patch("obsidian_agent.handlers.book.lookup_book", return_value=meta),\
         patch("obsidian_agent.handlers.book.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.book.clone_or_pull_repo"),\
         patch("obsidian_agent.handlers.book.commit_and_push"),\
         patch("obsidian_agent.handlers.book.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY":"test"}):
        M.return_value.call.return_value = "# Deep Work\n\n## Synopsis\nContent."
        handle_book("Deep Work by Cal Newport", cfg(tmp_path), memory_context="", date="2026-02-27")
    data = json.loads(books_file.read_text())
    assert len(data) == 1
    assert data[0]["title"] == "Deep Work"
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_handler_book.py -v
```

**Step 3: Implement `obsidian_agent/handlers/book.py`**
```python
import os
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.openlibrary import lookup_book, parse_title_author
from obsidian_agent.website import clone_or_pull_repo, update_bookshelf, commit_and_push
from obsidian_agent.vault import find_related_notes

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def handle_book(argument: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    title, author = parse_title_author(argument)
    meta = lookup_book(title, author) or {"title": title, "author": author, "isbn": "",
                                           "published": None, "subjects": [], "cover_url": ""}
    zettel = os.path.join(config["vault_path"], config["output_folder"])
    related = find_related_notes(f"{meta['title']} {meta['author']}", zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a book note for: "{meta['title']}" by {meta['author']}
Published: {meta.get('published','unknown')}
Subjects: {', '.join(meta.get('subjects', [])) or 'unknown'}
Related vault notes: {related_str or '(none yet)'}

## Required sections (exact H2 headings)
- ## Synopsis
- ## Key Concepts
- ## My Notes
- ## Related

Keep "My Notes" as: *Space for your notes as you read.*
Include [[wikilinks]] for concepts in the related notes list.
Start with: # {meta['title']} — {meta['author']}"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    if meta.get("cover_url"):
        body = f"![Cover]({meta['cover_url']})\n\n{body}"

    note_path = os.path.join(zettel, f"{meta['title']} - {meta['author']}.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "book"], created=date, type="book",
        author=meta["author"], published=meta.get("published"),
        isbn=meta.get("isbn",""), cover=meta.get("cover_url",""),
        status="to-read", related=related_str
    ), body)

    repo = config.get("website_repo_local","")
    remote = config.get("website_repo_remote","")
    if repo and remote:
        clone_or_pull_repo(remote, repo)
        update_bookshelf(os.path.join(repo, config.get("bookshelf_file","data/books.json")),
            {"title":meta["title"],"author":meta["author"],"isbn":meta.get("isbn",""),
             "cover":meta.get("cover_url",""),"status":"to-read","added":date})
        commit_and_push(repo, f"Add book: {meta['title']} by {meta['author']}")

    send_notification("Obsidian Collaborator", "#book", f"Added: {meta['title']}")
    return note_path
```

**Step 4: Run — expect 2 PASS**
```bash
python -m pytest tests/test_handler_book.py -v
```

**Step 5: Commit**
```bash
git add obsidian_agent/handlers/book.py tests/test_handler_book.py
git commit -m "feat: #book handler with OpenLibrary, Amazon covers, and website sync"
```

---

## Task 17: Dispatcher + Main Watcher

**Files:**
- Create: `obsidian-agent/obsidian_agent/dispatcher.py`
- Create: `obsidian-agent/obsidian-watcher.py`
- Create: `obsidian-agent/tests/test_dispatcher.py`

**Step 1: Write the failing tests**
```python
# tests/test_dispatcher.py
from unittest.mock import patch
from obsidian_agent.dispatcher import dispatch

def cfg():
    return {"vault_path": "/tmp/vault", "output_folder": "Zettelkasten",
            "model": "claude-sonnet-4-6", "anthropic_api_key_env": "ANTHROPIC_API_KEY"}

def test_routes_research():
    with patch("obsidian_agent.dispatcher.handle_research") as m,\
         patch("obsidian_agent.dispatcher.handle_book"),\
         patch("obsidian_agent.dispatcher.handle_writingprompt"),\
         patch("obsidian_agent.dispatcher.handle_reflect"):
        dispatch("research", "cold exposure", cfg(), "", "2026-02-27")
        m.assert_called_once_with("cold exposure", cfg(), memory_context="", date="2026-02-27")

def test_routes_book():
    with patch("obsidian_agent.dispatcher.handle_book") as m,\
         patch("obsidian_agent.dispatcher.handle_research"),\
         patch("obsidian_agent.dispatcher.handle_writingprompt"),\
         patch("obsidian_agent.dispatcher.handle_reflect"):
        dispatch("book", "Deep Work by Cal Newport", cfg(), "", "2026-02-27")
        m.assert_called_once()

def test_unknown_tag_is_ignored():
    with patch("obsidian_agent.dispatcher.handle_research") as m:
        dispatch("unknowntag", "arg", cfg(), "", "2026-02-27")
        m.assert_not_called()
```

**Step 2: Run — expect FAIL**
```bash
python -m pytest tests/test_dispatcher.py -v
```

**Step 3: Implement `obsidian_agent/dispatcher.py`**
```python
from obsidian_agent.handlers.research import handle_research
from obsidian_agent.handlers.writingprompt import handle_writingprompt
from obsidian_agent.handlers.reflect import handle_reflect
from obsidian_agent.handlers.book import handle_book

_HANDLERS = {
    "research": handle_research,
    "writingprompt": handle_writingprompt,
    "reflect": handle_reflect,
    "book": handle_book,
}

def dispatch(tag: str, argument: str, config: dict, memory_context: str, date: str):
    handler = _HANDLERS.get(tag.lower())
    if handler:
        handler(argument, config, memory_context=memory_context, date=date)
```

**Step 4: Implement `obsidian-agent/obsidian-watcher.py`**
```python
#!/usr/bin/env python3
"""Obsidian Collaborator — main daemon entry point."""
import os, sys, time, logging
from datetime import date as date_cls
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.insert(0, os.path.dirname(__file__))

from obsidian_agent.config import load_config
from obsidian_agent.state import StateManager
from obsidian_agent.memory import Memory
from obsidian_agent.parser import parse_tags
from obsidian_agent.dispatcher import dispatch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CONFIG_PATH = os.path.expanduser("~/.obsidian-agent/config.json")
STATE_PATH  = os.path.expanduser("~/.obsidian-agent/processed.json")
MEMORY_PATH = os.path.expanduser("~/.obsidian-agent/memory.md")

class DailyNoteHandler(FileSystemEventHandler):
    def __init__(self, config: dict):
        self.config = config
        self.state  = StateManager(STATE_PATH)
        self.memory = Memory(MEMORY_PATH, max_lines=config.get("max_memory_lines", 100))

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(event.src_path)

    def _process(self, filepath: str):
        try:
            content = Path(filepath).read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Cannot read {filepath}: {e}")
            return
        today = date_cls.today().isoformat()
        for item in parse_tags(content):
            tag, arg = item["tag"], item["argument"]
            if self.state.is_processed(today, tag, arg):
                continue
            log.info(f"Processing #{tag}: {arg}")
            try:
                dispatch(tag, arg, self.config, self.memory.read_context(), today)
                self.state.mark_processed(today, tag, arg)
                self.memory.append(today, tag, arg, "note created")
            except Exception as e:
                log.error(f"Handler error #{tag} '{arg}': {e}")

def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"Config not found: {CONFIG_PATH}")
        print("Copy obsidian-agent/config.json to ~/.obsidian-agent/config.json")
        sys.exit(1)
    config = load_config(CONFIG_PATH)
    watch_path = os.path.join(config["vault_path"], config["daily_notes_folder"])
    if not os.path.exists(watch_path):
        print(f"Daily notes folder not found: {watch_path}")
        sys.exit(1)
    log.info(f"Watching: {watch_path}")
    handler  = DailyNoteHandler(config)
    observer = Observer()
    observer.schedule(handler, watch_path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
```

**Step 5: Run tests — expect 3 PASS**
```bash
python -m pytest tests/test_dispatcher.py -v
```

**Step 6: Commit**
```bash
git add obsidian_agent/dispatcher.py obsidian-watcher.py tests/test_dispatcher.py
git commit -m "feat: dispatcher and main watcher daemon"
```

---

## Task 18: LaunchAgent + Setup Script

**Files:**
- Create: `obsidian-agent/launch_agent/ai.obsidian.agent.plist`
- Create: `obsidian-agent/setup.sh`

**Step 1: Write `launch_agent/ai.obsidian.agent.plist`**

Note: `PLACEHOLDER_*` values are replaced by `setup.sh` using `sed`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.obsidian.agent</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>PLACEHOLDER_SCRIPT_PATH</string>
    </array>

    <key>WatchPaths</key>
    <array>
        <string>PLACEHOLDER_DAILY_NOTES_PATH</string>
    </array>

    <key>ThrottleInterval</key>
    <integer>10</integer>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>PLACEHOLDER_LOG_PATH/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>PLACEHOLDER_LOG_PATH/stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>PLACEHOLDER_ANTHROPIC_KEY</string>
        <key>BRAVE_API_KEY</key>
        <string>PLACEHOLDER_BRAVE_KEY</string>
    </dict>
</dict>
</plist>
```

**Step 2: Write `setup.sh`**

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME="$HOME/.obsidian-agent"
LOGS="$RUNTIME/logs"
PLIST_SRC="$SCRIPT_DIR/launch_agent/ai.obsidian.agent.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/ai.obsidian.agent.plist"

echo "=== Obsidian Collaborator Setup ==="

mkdir -p "$RUNTIME/repos" "$LOGS"

# Copy config template if not present
if [ ! -f "$RUNTIME/config.json" ]; then
    cp "$SCRIPT_DIR/config.json" "$RUNTIME/config.json"
    echo ""
    echo "Config copied to $RUNTIME/config.json"
    echo "Edit it now — set vault_path, daily_notes_folder, output_folder."
    echo "Press Enter when ready..."
    read
fi

# Read vault + daily notes path from config
VAULT=$(python3 -c "import json,os; c=json.load(open('$RUNTIME/config.json')); print(os.path.expanduser(c['vault_path']))")
DAILY=$(python3 -c "import json; c=json.load(open('$RUNTIME/config.json')); print(c.get('daily_notes_folder','Daily Notes'))")
DAILY_PATH="$VAULT/$DAILY"

echo ""
read -rsp "ANTHROPIC_API_KEY: " ANTHROPIC_KEY; echo
read -rsp "BRAVE_API_KEY (Enter to skip): " BRAVE_KEY; echo

# Install Python dependencies
pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet

# Write plist with real values
sed \
    -e "s|PLACEHOLDER_SCRIPT_PATH|$SCRIPT_DIR/obsidian-watcher.py|g" \
    -e "s|PLACEHOLDER_DAILY_NOTES_PATH|$DAILY_PATH|g" \
    -e "s|PLACEHOLDER_LOG_PATH|$LOGS|g" \
    -e "s|PLACEHOLDER_ANTHROPIC_KEY|$ANTHROPIC_KEY|g" \
    -e "s|PLACEHOLDER_BRAVE_KEY|$BRAVE_KEY|g" \
    "$PLIST_SRC" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo ""
echo "Done! Obsidian Collaborator is running."
echo "Write '- #research some topic' in today's daily note to test."
echo "Logs: $LOGS/"
```

**Step 3: Commit**
```bash
chmod +x obsidian-agent/setup.sh
git add obsidian-agent/launch_agent/ obsidian-agent/setup.sh
git commit -m "feat: LaunchAgent plist and setup script"
```

---

## Task 19: Full Test Suite + Smoke Test

**Step 1: Run the full test suite**
```bash
cd obsidian-agent && python -m pytest tests/ -v
```
Expected: **all tests PASS**

**Step 2: Manual smoke test (on the target macOS machine)**

```bash
# Terminal 1 — run watcher manually
cd /path/to/Claude-Sessions/obsidian-agent
ANTHROPIC_API_KEY=sk-... BRAVE_API_KEY=... python3 obsidian-watcher.py
```

```bash
# Terminal 2 — append a test tag to today's daily note
echo "- #research effects of cold exposure on metabolism" >> \
  ~/Library/Mobile\ Documents/iCloud\~md\~obsidian/Documents/Obsidian\ Files/Daily\ Notes/$(date +"%B %-d, %Y").md
```

Expected within 15 seconds:
- Log: `Processing #research: effects of cold exposure on metabolism`
- File created: `Zettelkasten/2026-02-27 - Effects Of Cold Exposure On Metabolism.md`
- macOS notification appears

**Step 3: Verify note structure**
```bash
head -20 "Zettelkasten/2026-02-27 - Effects Of Cold Exposure On Metabolism.md"
```
Expected:
- Starts with `---` (YAML frontmatter)
- Contains `tags:` with `review` and `research`
- Contains `source: obsidian-agent`
- Has a `# ... Research Note` H1 heading

**Step 4: Final commit and push**
```bash
git add .
git commit -m "test: full test suite passing, smoke test verified"
git push -u origin claude/integrate-claude-flow-KCxXT
```

---

## File Map Summary

```
obsidian-agent/
├── obsidian-watcher.py            ← main entry point
├── SYSTEM.md                      ← editable agent persona
├── config.json                    ← config template
├── requirements.txt
├── setup.sh                       ← install + LaunchAgent setup
├── launch_agent/
│   └── ai.obsidian.agent.plist   ← macOS LaunchAgent
├── obsidian_agent/
│   ├── config.py                 ← config loader
│   ├── state.py                  ← SHA-256 dedup
│   ├── memory.py                 ← rolling memory
│   ├── parser.py                 ← tag parser
│   ├── vault.py                  ← link enrichment
│   ├── note_writer.py            ← YAML + markdown writer
│   ├── notify.py                 ← macOS notifications
│   ├── claude_client.py          ← Anthropic API wrapper
│   ├── search.py                 ← Brave Search client
│   ├── openlibrary.py            ← OpenLibrary + Amazon covers
│   ├── website.py                ← git bookshelf updater
│   ├── dispatcher.py             ← tag → handler routing
│   └── handlers/
│       ├── research.py
│       ├── writingprompt.py
│       ├── reflect.py
│       └── book.py
└── tests/
    ├── test_config.py
    ├── test_state.py
    ├── test_memory.py
    ├── test_parser.py
    ├── test_vault.py
    ├── test_note_writer.py
    ├── test_notify.py
    ├── test_claude_client.py
    ├── test_search.py
    ├── test_openlibrary.py
    ├── test_website.py
    ├── test_dispatcher.py
    ├── test_handler_research.py
    ├── test_handler_writingprompt.py
    ├── test_handler_reflect.py
    └── test_handler_book.py
```
