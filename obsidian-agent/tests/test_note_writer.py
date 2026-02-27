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
