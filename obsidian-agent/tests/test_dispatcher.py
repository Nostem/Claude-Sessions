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
