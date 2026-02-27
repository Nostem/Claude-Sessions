#!/usr/bin/env python3
"""Obsidian Collaborator — main daemon entry point."""
import os, re, sys, time, logging
from datetime import date as date_cls
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.insert(0, os.path.dirname(__file__))

from obsidian_agent.config import load_config
from obsidian_agent.state import StateManager
from obsidian_agent.memory import Memory
from obsidian_agent.parser import parse_tags
from obsidian_agent.dispatcher import dispatch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CONFIG_PATH = os.path.expanduser("~/.obsidian-agent/config.json")
STATE_PATH  = os.path.expanduser("~/.obsidian-agent/processed.json")
MEMORY_PATH = os.path.expanduser("~/.obsidian-agent/memory.md")

class DailyNoteHandler(FileSystemEventHandler):
    def __init__(self, config: dict):
        self.config = config
        self.state  = StateManager(STATE_PATH)
        self.memory = Memory(MEMORY_PATH, max_lines=config.get("max_memory_lines", 100))

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(event.src_path)

    def on_moved(self, event):
        # Obsidian on macOS uses atomic saves (write temp → rename), firing on_moved
        if not event.is_directory and event.dest_path.endswith(".md"):
            self._process(event.dest_path)

    def _annotate(self, filepath: str, tag: str, arg: str, note_path: str):
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

    def _process(self, filepath: str):
        try:
            content = Path(filepath).read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Cannot read {filepath}: {e}")
            return
        today = date_cls.today().isoformat()
        for item in parse_tags(content):
            tag, arg = item["tag"], item["argument"]
            if self.state.is_processed(today, tag, arg):
                continue
            log.info(f"Processing #{tag}: {arg}")
            try:
                note_path = dispatch(tag, arg, self.config, self.memory.read_context(), today)
                self.state.mark_processed(today, tag, arg)
                self.memory.append(today, tag, arg, "note created")
                if note_path:
                    self._annotate(filepath, tag, arg, note_path)
            except Exception as e:
                log.error(f"Handler error #{tag} '{arg}': {e}")

def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"Config not found: {CONFIG_PATH}")
        print("Copy obsidian-agent/config.json to ~/.obsidian-agent/config.json")
        sys.exit(1)
    config = load_config(CONFIG_PATH)
    watch_path = os.path.join(config["vault_path"], config["daily_notes_folder"])
    if not os.path.exists(watch_path):
        print(f"Daily notes folder not found: {watch_path}")
        sys.exit(1)
    log.info(f"Watching: {watch_path}")
    handler  = DailyNoteHandler(config)
    observer = Observer()
    observer.schedule(handler, watch_path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
