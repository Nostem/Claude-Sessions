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
