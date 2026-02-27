# tests/test_handler_research.py
from unittest.mock import patch
from obsidian_agent.handlers.research import handle_research

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
