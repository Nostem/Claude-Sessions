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
