# tests/test_memory.py
from obsidian_agent.memory import Memory

def test_empty_returns_empty_string(tmp_path):
    assert Memory(str(tmp_path / "memory.md")).read_context() == ""

def test_append_and_read(tmp_path):
    m = Memory(str(tmp_path / "memory.md"))
    m.append("2026-02-27", "research", "cold exposure", "5 findings, linked [[Hormesis]]")
    ctx = m.read_context()
    assert "cold exposure" in ctx
    assert "research" in ctx

def test_max_lines_respected(tmp_path):
    m = Memory(str(tmp_path / "memory.md"), max_lines=3)
    for i in range(10):
        m.append("2026-02-27", "research", f"topic {i}", "summary")
    lines = [l for l in m.read_context().split("\n") if l.strip()]
    assert len(lines) <= 3
