# tests/test_watcher.py
import importlib.util, sys, os
from pathlib import Path
from unittest.mock import MagicMock, patch

# obsidian-watcher.py has a hyphen so we must load it via importlib
_WATCHER_PATH = os.path.join(os.path.dirname(__file__), "..", "obsidian-watcher.py")
_spec = importlib.util.spec_from_file_location("obsidian_watcher", _WATCHER_PATH)
obsidian_watcher = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(obsidian_watcher)
DailyNoteHandler = obsidian_watcher.DailyNoteHandler


def _make_handler(tmp_path):
    config = {
        "vault_path": str(tmp_path / "vault"),
        "output_folder": "Zettelkasten",
        "model": "claude-sonnet-4-6",
        "anthropic_api_key_env": "ANTHROPIC_API_KEY",
        "max_memory_lines": 100,
    }
    handler = DailyNoteHandler.__new__(DailyNoteHandler)
    handler.config = config
    handler.state = MagicMock()
    handler.state.is_processed.return_value = False
    handler.memory = MagicMock()
    handler.memory.read_context.return_value = ""
    return handler


def test_on_moved_processes_dest_path(tmp_path):
    handler = _make_handler(tmp_path)
    note = tmp_path / "daily.md"
    note.write_text("- #research cold exposure\n")
    event = MagicMock()
    event.is_directory = False
    event.dest_path = str(note)
    with patch.object(handler, "_process") as mock_process:
        handler.on_moved(event)
        mock_process.assert_called_once_with(str(note))


def test_on_moved_ignores_non_md(tmp_path):
    handler = _make_handler(tmp_path)
    event = MagicMock()
    event.is_directory = False
    event.dest_path = str(tmp_path / "file.tmp")
    with patch.object(handler, "_process") as mock_process:
        handler.on_moved(event)
        mock_process.assert_not_called()


def test_annotate_appends_wikilink(tmp_path):
    handler = _make_handler(tmp_path)
    note = tmp_path / "daily.md"
    note.write_text("- #research cold exposure\n")
    note_path = str(tmp_path / "Zettelkasten" / "2026-02-27 - Cold Exposure.md")
    handler._annotate(str(note), "research", "cold exposure", note_path)
    result = note.read_text()
    assert "'Agent Complete'" in result
    assert "[[2026-02-27 - Cold Exposure]]" in result


def test_annotate_idempotent(tmp_path):
    # Calling annotate twice should not double-append the suffix
    handler = _make_handler(tmp_path)
    note = tmp_path / "daily.md"
    note.write_text("- #research cold exposure\n")
    note_path = str(tmp_path / "2026-02-27 - Cold Exposure.md")
    handler._annotate(str(note), "research", "cold exposure", note_path)
    first = note.read_text()
    # Second call: annotated line no longer matches bare pattern → file unchanged
    handler._annotate(str(note), "research", "cold exposure", note_path)
    assert note.read_text() == first
