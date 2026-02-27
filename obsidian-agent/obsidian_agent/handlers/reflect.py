import os
from pathlib import Path
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.vault import find_related_notes, _keywords

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def get_vault_excerpts(topic: str, zettel_path: str, max_notes: int = 5, chars: int = 400) -> str:
    if not os.path.exists(zettel_path):
        return "(vault is empty)"
    kws = _keywords(topic)
    excerpts = []
    for f in Path(zettel_path).glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(k in (f.stem + " " + content).lower() for k in kws):
            excerpts.append(f"**[[{f.stem}]]**\n{content[:chars]}...")
        if len(excerpts) >= max_notes:
            break
    return "\n\n---\n\n".join(excerpts) if excerpts else "(no related notes found yet)"

def handle_reflect(topic: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    zettel = os.path.join(config["vault_path"], config["output_folder"])
    excerpts = get_vault_excerpts(topic, zettel)
    related = find_related_notes(topic, zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a reflection note on: "{topic}"

## Relevant vault excerpts
{excerpts}

## Required sections (exact H2 headings)
- ## What the vault says
- ## Synthesis
- ## Tensions / Questions
- ## What I might do differently
- ## Related

Be honest and nuanced. Use [[wikilinks]] to reference the excerpted notes.
Start with: # Reflection — {topic.title()}"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    note_path = os.path.join(zettel, f"{date} - Reflection - {topic.title()}.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "reflection"], created=date, type="reflection",
        topic=topic, related=related_str
    ), body)
    send_notification("Obsidian Collaborator", "#reflect", f"Reflection: {topic.title()}")
    return note_path
