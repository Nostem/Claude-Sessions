# tests/test_parser.py
from obsidian_agent.parser import parse_tags

NOTE = """# Feb 27
- #research cold exposure on metabolism
- #book Deep Work by Cal Newport
- #writingprompt essay on slowness
- just a regular bullet
- #reflect on avoiding deep work
* #research asterisk format works
"""

def test_finds_all_supported_tags():
    tags = parse_tags(NOTE)
    assert len(tags) == 5  # 2 research + book + writingprompt + reflect

def test_argument_extracted():
    tags = parse_tags("- #research cold exposure")
    assert tags[0]["argument"] == "cold exposure"

def test_case_insensitive():
    tags = parse_tags("- #Research Cold Exposure\n- #BOOK Some Book")
    assert tags[0]["tag"] == "research"
    assert tags[1]["tag"] == "book"

def test_asterisk_bullet():
    tags = parse_tags("* #research topic here")
    assert tags[0]["tag"] == "research"

def test_skips_untagged_bullets():
    tags = parse_tags("- just a regular bullet")
    assert tags == []

def test_returns_hash():
    tags = parse_tags("- #research some topic")
    assert len(tags[0]["hash"]) == 64

def test_empty_note():
    assert parse_tags("") == []
