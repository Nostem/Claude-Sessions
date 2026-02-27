# tests/test_handler_book.py
import json
from unittest.mock import patch
from obsidian_agent.handlers.book import handle_book

def cfg(tmp_path):
    repo = str(tmp_path / "repo")
    return {"vault_path": str(tmp_path/"vault"), "output_folder": "Zettelkasten",
            "model": "claude-sonnet-4-6", "anthropic_api_key_env": "ANTHROPIC_API_KEY",
            "website_repo_local": repo, "website_repo_remote": "https://github.com/Nostem/nostem.github.io",
            "bookshelf_file": "data/books.json"}

def test_creates_note(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    (tmp_path/"repo"/"data").mkdir(parents=True)
    (tmp_path/"repo"/"data"/"books.json").write_text("[]")
    meta = {"title":"Deep Work","author":"Cal Newport","isbn":"0804137390",
            "published":2016,"subjects":["Productivity"],"cover_url":"https://..."}
    with patch("obsidian_agent.handlers.book.lookup_book", return_value=meta),\
         patch("obsidian_agent.handlers.book.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.book.clone_or_pull_repo"),\
         patch("obsidian_agent.handlers.book.commit_and_push"),\
         patch("obsidian_agent.handlers.book.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY":"test"}):
        M.return_value.call.return_value = "# Deep Work\n\n## Synopsis\nAbout focus."
        handle_book("Deep Work by Cal Newport", cfg(tmp_path), memory_context="", date="2026-02-27")
    assert len(list((tmp_path/"vault"/"Zettelkasten").glob("*.md"))) == 1

def test_updates_bookshelf(tmp_path):
    (tmp_path/"vault"/"Zettelkasten").mkdir(parents=True)
    (tmp_path/"repo"/"data").mkdir(parents=True)
    books_file = tmp_path/"repo"/"data"/"books.json"
    books_file.write_text("[]")
    meta = {"title":"Deep Work","author":"Cal Newport","isbn":"0804137390",
            "published":2016,"subjects":[],"cover_url":"https://..."}
    with patch("obsidian_agent.handlers.book.lookup_book", return_value=meta),\
         patch("obsidian_agent.handlers.book.ClaudeClient") as M,\
         patch("obsidian_agent.handlers.book.clone_or_pull_repo"),\
         patch("obsidian_agent.handlers.book.commit_and_push"),\
         patch("obsidian_agent.handlers.book.send_notification"),\
         patch.dict("os.environ", {"ANTHROPIC_API_KEY":"test"}):
        M.return_value.call.return_value = "# Deep Work\n\n## Synopsis\nContent."
        handle_book("Deep Work by Cal Newport", cfg(tmp_path), memory_context="", date="2026-02-27")
    data = json.loads(books_file.read_text())
    assert len(data) == 1
    assert data[0]["title"] == "Deep Work"
