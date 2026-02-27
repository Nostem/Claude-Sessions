import os
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.search import search_brave, format_results
from obsidian_agent.vault import find_related_notes

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def handle_research(topic: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    search_key = os.environ.get(config.get("search_api_key_env", "BRAVE_API_KEY"), "")
    zettel = os.path.join(config["vault_path"], config["output_folder"])

    results = search_brave(topic, api_key=search_key) if search_key else []
    search_ctx = format_results(results)
    related = find_related_notes(topic, zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a research note for: "{topic}"

## Web Search Results
{search_ctx}

## Related vault notes
{related_str or "(none yet)"}

## Required sections (exact H2 headings)
- ## Summary
- ## Key Findings
- ## Open Questions
- ## Sources
- ## Related

Include [[wikilinks]] for concepts in the related notes list.
Start with: # {topic.title()} — Research Note"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    note_path = os.path.join(zettel, f"{date} - {topic.title()}.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "research"], created=date, type="research",
        query=topic, related=related_str
    ), body)
    send_notification("Obsidian Collaborator", "#research", f"Note: {topic.title()}")
    return note_path
