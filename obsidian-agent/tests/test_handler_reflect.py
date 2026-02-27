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
