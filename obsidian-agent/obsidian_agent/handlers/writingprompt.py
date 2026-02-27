import os
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.vault import find_related_notes

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def handle_writingprompt(subject: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    zettel = os.path.join(config["vault_path"], config["output_folder"])
    related = find_related_notes(subject, zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a writing outline for: "{subject}"

## Related vault notes to link
{related_str or "(none yet)"}

## Required sections (exact H2 headings)
- ## Core Thesis
- ## Angles to Explore
- ## Structure
- ## Opening Ideas
- ## Inspiration / Related

Be substantive — actual angles and ideas, not placeholders.
Include [[wikilinks]] for concepts in the related notes list.
Start with: # {subject.title()} — Writing Outline"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    note_path = os.path.join(zettel, f"{date} - {subject.title()} Outline.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "writing-prompt"], created=date, type="writing-prompt",
        subject=subject, related=related_str
    ), body)
    send_notification("Obsidian Collaborator", "#writingprompt", f"Outline: {subject.title()}")
    return note_path
