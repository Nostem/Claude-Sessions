import os
from obsidian_agent.claude_client import ClaudeClient
from obsidian_agent.note_writer import write_note, build_frontmatter
from obsidian_agent.notify import send_notification
from obsidian_agent.openlibrary import lookup_book, parse_title_author
from obsidian_agent.website import clone_or_pull_repo, update_bookshelf, commit_and_push
from obsidian_agent.vault import find_related_notes

_SYSTEM_MD = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../SYSTEM.md"))

def handle_book(argument: str, config: dict, memory_context: str, date: str):
    api_key = os.environ.get(config.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
    title, author = parse_title_author(argument)
    meta = lookup_book(title, author) or {"title": title, "author": author, "isbn": "",
                                           "published": None, "subjects": [], "cover_url": ""}
    zettel = os.path.join(config["vault_path"], config["output_folder"])
    related = find_related_notes(f"{meta['title']} {meta['author']}", zettel)
    related_str = ", ".join(related)

    prompt = f"""Create a book note for: "{meta['title']}" by {meta['author']}
Published: {meta.get('published','unknown')}
Subjects: {', '.join(meta.get('subjects', [])) or 'unknown'}
Related vault notes: {related_str or '(none yet)'}

## Required sections (exact H2 headings)
- ## Synopsis
- ## Key Concepts
- ## My Notes
- ## Related

Keep "My Notes" as: *Space for your notes as you read.*
Include [[wikilinks]] for concepts in the related notes list.
Start with: # {meta['title']} — {meta['author']}"""

    body = ClaudeClient(api_key, _SYSTEM_MD, config["model"]).call(prompt, memory_context)
    if meta.get("cover_url"):
        body = f"![Cover]({meta['cover_url']})\n\n{body}"

    note_path = os.path.join(zettel, f"{meta['title']} - {meta['author']}.md")
    write_note(note_path, build_frontmatter(
        tags=["review", "book"], created=date, type="book",
        author=meta["author"], published=meta.get("published"),
        isbn=meta.get("isbn",""), cover=meta.get("cover_url",""),
        status="to-read", related=related_str
    ), body)

    repo = config.get("website_repo_local","")
    remote = config.get("website_repo_remote","")
    if repo and remote:
        clone_or_pull_repo(remote, repo)
        update_bookshelf(os.path.join(repo, config.get("bookshelf_file","data/books.json")),
            {"title":meta["title"],"author":meta["author"],"isbn":meta.get("isbn",""),
             "cover":meta.get("cover_url",""),"status":"to-read","added":date})
        commit_and_push(repo, f"Add book: {meta['title']} by {meta['author']}")

    send_notification("Obsidian Collaborator", "#book", f"Added: {meta['title']}")
    return note_path
