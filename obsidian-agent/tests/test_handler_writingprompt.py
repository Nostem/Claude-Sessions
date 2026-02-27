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
