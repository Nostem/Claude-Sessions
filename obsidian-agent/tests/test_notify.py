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
