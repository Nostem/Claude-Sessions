# tests/test_website.py
import json
from unittest.mock import patch, MagicMock
from obsidian_agent.website import clone_or_pull_repo, update_bookshelf, commit_and_push

def test_adds_book_entry(tmp_path):
    f = tmp_path / "books.json"
    f.write_text(json.dumps([{"title": "Existing", "author": "A"}]))
    update_bookshelf(str(f), {"title": "Deep Work", "author": "Cal Newport", "isbn": "x", "cover": "", "status": "to-read", "added": "2026-02-27"})
    data = json.loads(f.read_text())
    assert len(data) == 2
    assert data[-1]["title"] == "Deep Work"

def test_prevents_duplicate(tmp_path):
    f = tmp_path / "books.json"
    f.write_text(json.dumps([{"title": "Deep Work", "author": "Cal Newport"}]))
    update_bookshelf(str(f), {"title": "Deep Work", "author": "Cal Newport", "isbn": "", "cover": "", "status": "to-read", "added": "2026-02-27"})
    assert len(json.loads(f.read_text())) == 1

def test_commit_and_push_runs_git(tmp_path):
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0)
        commit_and_push(str(tmp_path), "Add Deep Work")
    calls = [str(c) for c in mock.call_args_list]
    assert any("commit" in c for c in calls)
    assert any("push" in c for c in calls)
