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
