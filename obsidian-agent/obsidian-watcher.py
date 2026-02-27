#!/usr/bin/env python3
"""Obsidian Collaborator — one-shot processor called by the Shell Commands plugin on save.

Usage (configured in Shell Commands plugin):
    /path/to/venv/bin/python3 /path/to/obsidian-watcher.py "{{file_path:absolute}}"
"""
import os, re, sys, logging
from datetime import date as date_cls
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from obsidian_agent.config import load_config
from obsidian_agent.state import StateManager
from obsidian_agent.memory import Memory
from obsidian_agent.parser import parse_tags
from obsidian_agent.dispatcher import dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

CONFIG_PATH = os.path.expanduser("~/.obsidian-agent/config.json")
STATE_PATH  = os.path.expanduser("~/.obsidian-agent/processed.json")
MEMORY_PATH = os.path.expanduser("~/.obsidian-agent/memory.md")


def _annotate(filepath: str, tag: str, arg: str, note_path: str) -> None:
    note_name = Path(note_path).stem
    suffix = f" 'Agent Complete' [[{note_name}]]"
    try:
        text = Path(filepath).read_text(encoding="utf-8")
        pattern = re.compile(
            rf'^([*-]\s+#{re.escape(tag)}\s+{re.escape(arg)})\s*$',
            re.MULTILINE | re.IGNORECASE,
        )
        updated = pattern.sub(rf'\1{suffix}', text)
        if updated != text:
            Path(filepath).write_text(updated, encoding="utf-8")
            log.info(f"Annotated bullet with [[{note_name}]]")
    except Exception as e:
        log.error(f"Could not annotate bullet: {e}")


def _process(filepath: str, config: dict) -> None:
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Cannot read {filepath}: {e}")
        return

    state  = StateManager(STATE_PATH)
    memory = Memory(MEMORY_PATH, max_lines=config.get("max_memory_lines", 100))
    today  = date_cls.today().isoformat()

    for item in parse_tags(content):
        tag, arg = item["tag"], item["argument"]
        if state.is_processed(today, tag, arg):
            continue
        log.info(f"Processing #{tag}: {arg}")
        try:
            note_path = dispatch(tag, arg, config, memory.read_context(), today)
            state.mark_processed(today, tag, arg)
            memory.append(today, tag, arg, "note created")
            if note_path:
                _annotate(filepath, tag, arg, note_path)
        except Exception as e:
            log.error(f"Handler error #{tag} '{arg}': {e}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: obsidian-watcher.py <absolute_path_to_note>")
        print("This script is meant to be called by the Obsidian Shell Commands plugin on save.")
        sys.exit(1)

    filepath = sys.argv[1]

    if not filepath.endswith(".md"):
        log.debug(f"Skipping non-markdown file: {filepath}")
        sys.exit(0)

    if not os.path.exists(CONFIG_PATH):
        print(f"Config not found: {CONFIG_PATH}")
        print("Run setup.sh first.")
        sys.exit(1)

    config = load_config(CONFIG_PATH)

    # Only process files inside the configured daily notes folder
    daily_path = os.path.join(config["vault_path"], config["daily_notes_folder"])
    if not filepath.startswith(os.path.realpath(daily_path)):
        log.debug(f"Not a daily note, skipping: {filepath}")
        sys.exit(0)

    _process(filepath, config)


if __name__ == "__main__":
    main()
