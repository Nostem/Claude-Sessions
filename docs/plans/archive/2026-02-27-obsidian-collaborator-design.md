# Obsidian Collaborator — Design Document

**Date:** 2026-02-27
**Status:** Approved
**Project:** Claude-Sessions / obsidian-agent

---

## Overview

A standalone Python daemon that watches the personal **Obsidian Files** vault for
hashtag triggers in daily notes, calls the Claude API to execute tasks, and writes
results back as Zettelkasten notes. Operates independently of OpenClaw.

---

## Architecture

```
Obsidian Files/Daily Notes/  ←  user writes "- #research X"
    │
    ▼  watchdog (file change event, ~1–3 second latency)
obsidian-watcher.py
    ├─ dedup check  (SHA-256 hash → ~/.obsidian-agent/processed.json)
    ├─ reads Claude-Sessions/obsidian-agent/SYSTEM.md     (persona + rules)
    ├─ reads ~/.obsidian-agent/memory.md                  (rolling context)
    ├─ scans Zettelkasten/ for related notes              (vault link enrichment)
    │
    ├─ #research    → web search (Brave/Serper) + Claude synthesis
    ├─ #writingprompt → Claude brainstorm + outline
    ├─ #reflect     → Claude journal synthesis + vault cross-reference
    └─ #book        → OpenLibrary metadata + Amazon cover + Claude notes
                          → nostem.github.io bookshelf commit + push
    │
    ├─ writes note to Obsidian Files/Zettelkasten/
    ├─ appends summary to ~/.obsidian-agent/memory.md
    └─ fires macOS notification (osascript)
```

---

## File Locations

### Source (version-controlled in Claude-Sessions)

```
Claude-Sessions/obsidian-agent/
    obsidian-watcher.py         — main daemon
    SYSTEM.md                   — editable agent persona + Zettelkasten rules
    config.json                 — vault paths, model, API keys (template)
    requirements.txt            — watchdog, anthropic, requests
    launch_agent/
        ai.obsidian.agent.plist — LaunchAgent (auto-start on login)
```

### Runtime state (not in git)

```
~/.obsidian-agent/
    config.json                 — active config (copied/symlinked from source)
    memory.md                   — rolling context, auto-updated after each task
    processed.json              — SHA-256 dedup state
    repos/
        nostem.github.io/       — cloned website repo for #book pushes
```

---

## Tag Vocabulary

| Tag | Syntax example | Output |
|-----|---------------|--------|
| `#research` | `- #research effects of cold exposure` | Research note with web-sourced findings |
| `#writingprompt` | `- #writingprompt essay on solitude` | Outline note with angles, structure, opening ideas |
| `#reflect` | `- #reflect on why I keep avoiding deep work` | Journal synthesis cross-referencing related vault notes |
| `#book` | `- #book Deep Work by Cal Newport` | Book note + website bookshelf update |

All agent-created notes receive `#review` tag in YAML frontmatter.

---

## Tag Handlers

### `#research [topic]`

1. Call Brave Search API (or Serper) with the topic query
2. Pass search results + topic to Claude (Sonnet) for synthesis
3. Scan `Zettelkasten/` for related notes → extract `[[wikilinks]]`
4. Write note to `Zettelkasten/YYYY-MM-DD - [Topic].md`
5. YAML: `tags: [review, research]`, `created:`, `source: obsidian-agent`, `query:`, `related:`

**Note template:**
```markdown
---
tags: [review, research]
created: YYYY-MM-DD
source: obsidian-agent
type: research
query: "topic here"
related: "[[Related Note 1]], [[Related Note 2]]"
---

# Topic — Research Note

## Summary

## Key Findings

## Open Questions

## Sources

## Related
```

---

### `#writingprompt [subject]`

1. Pass subject to Claude (Sonnet) for brainstorm
2. Agent generates: core thesis, 3–5 angles, structural outline, opening ideas
3. Scan vault for related research/reflect notes → add wikilinks
4. Write note to `Zettelkasten/YYYY-MM-DD - [Subject] Outline.md`
5. YAML: `tags: [review, writing-prompt]`

**Note template:**
```markdown
---
tags: [review, writing-prompt]
created: YYYY-MM-DD
source: obsidian-agent
type: writing-prompt
subject: "subject here"
related: "[[Related Note 1]]"
---

# [Subject] — Writing Outline

## Core Thesis

## Angles to Explore

## Structure

## Opening Ideas

## Inspiration / Related
```

---

### `#reflect [topic]`

1. Scan vault for notes related to the reflection topic (last 30 days + all time)
2. Include related note excerpts as context in Claude call
3. Claude generates: synthesis, patterns, tensions, open questions
4. Write note to `Zettelkasten/YYYY-MM-DD - Reflection - [Topic].md`
5. YAML: `tags: [review, reflection]`

**Note template:**
```markdown
---
tags: [review, reflection]
created: YYYY-MM-DD
source: obsidian-agent
type: reflection
topic: "topic here"
related: "[[Related Note 1]]"
---

# Reflection — [Topic]

## What the vault says

## Synthesis

## Tensions / Questions

## What I might do differently

## Related
```

---

### `#book [Title] by [Author]` (or `#book Title Author`)

1. Query **OpenLibrary API** for metadata (ISBN, year, synopsis, subjects)
2. Construct **Amazon CDN cover URL** from ISBN:
   `https://images-na.ssl-images-amazon.com/images/P/{ISBN10}.01.LZZZZZZZ.jpg`
3. Write note to `Zettelkasten/[Title] - [Author].md`
4. Pull `~/.obsidian-agent/repos/nostem.github.io/`, find bookshelf data file,
   append entry, commit and push to `github.com/Nostem/nostem.github.io`
5. YAML: `tags: [review, book]`, `author:`, `published:`, `isbn:`, `cover:`, `status: to-read`

**Note template:**
```markdown
---
tags: [review, book]
created: YYYY-MM-DD
source: obsidian-agent
type: book
author: "Author Name"
published: YYYY
isbn: "ISBN10"
cover: "https://images-na.ssl-images-amazon.com/images/P/{ISBN10}.01.LZZZZZZZ.jpg"
status: to-read
---

# [Title] — [Author]

![Cover](https://images-na.ssl-images-amazon.com/images/P/{ISBN10}.01.LZZZZZZZ.jpg)

## Synopsis

## Key Concepts

## My Notes

*Space for your notes as you read.*

## Related
```

---

## Vault Link Enrichment

On every note creation:
1. Extract 3–5 key terms from the content
2. Search `Zettelkasten/` filenames and YAML frontmatter for matches
3. Populate `related:` frontmatter with `[[wikilinks]]` to matching notes
4. Include inline `[[wikilinks]]` in the body where contextually appropriate

---

## Memory System

`~/.obsidian-agent/memory.md` — append-only rolling log, included as context in every API call:

```
2026-02-27 | research | "cold exposure" → 5 findings, linked [[Hormesis]], [[Recovery]]
2026-02-27 | book | "Deep Work - Cal Newport" → added to bookshelf, to-read
2026-02-28 | reflect | "avoiding deep work" → linked 3 related notes
```

Memory keeps the agent coherent across sessions — it knows what you've explored, what topics you return to, what books you own.

---

## macOS Notifications

After every successful note creation:
```bash
osascript -e 'display notification "Note created: [Title]" with title "Obsidian Collaborator" subtitle "#[tag]"'
```

---

## Web Search (`#research`)

Provider options (pick one, configurable in config.json):
- **Brave Search API** — free tier (2,000 queries/month), privacy-focused
- **Serper API** — free tier (2,500 queries/month), Google results

The watcher calls the search API first, passes the top 5–8 results (titles, snippets, URLs) to Claude as context before synthesis.

---

## Config (`config.json` template)

```json
{
  "vault_path": "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Files",
  "daily_notes_folder": "Daily Notes",
  "output_folder": "Zettelkasten",
  "website_repo_local": "~/.obsidian-agent/repos/nostem.github.io",
  "website_repo_remote": "https://github.com/Nostem/nostem.github.io",
  "model": "claude-sonnet-4-6",
  "search_provider": "brave",
  "search_api_key_env": "BRAVE_API_KEY",
  "anthropic_api_key_env": "ANTHROPIC_API_KEY"
}
```

---

## LaunchAgent (`ai.obsidian.agent.plist`)

```xml
<key>WatchPaths</key>
<array>
    <string>~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Files/Daily Notes</string>
</array>
<key>ThrottleInterval</key>
<integer>10</integer>
```

- Fires on any file change in the daily notes folder
- 10-second debounce (avoids double-firing on iCloud sync writes)
- `RunAtLoad`: true (starts on login)
- Logs to `~/.obsidian-agent/logs/`

---

## Daily Note Syntax

Tags are detected on bullet lines:

```
- #research effects of cold exposure on metabolism
- #writingprompt essay on the virtue of slowness
- #reflect on why I keep starting new projects before finishing old ones
- #book Deep Work by Cal Newport
```

Detection rules:
- Line must start with `- ` (list item) or `* `
- Tag must be first token on the line (after `-`)
- Remainder of line is the argument/topic passed to the handler
- Case-insensitive (`#Research`, `#research` both work)

---

## Deduplication

Each detected tag+argument is hashed (SHA-256 of `date|tag|argument`).
Hash stored in `~/.obsidian-agent/processed.json`. Prevents re-processing if:
- Obsidian auto-saves mid-edit
- iCloud syncs multiple times
- The watcher restarts

---

## Out of Scope (v1)

- Obsidian Local REST API plugin bridge
- Excalidraw diagram generation
- Book status workflow (`to-read → reading → finished`)
- Weekly synthesis cron (add after vault has 2–3 weeks of content)
- Two-way tag updates (agent editing notes it didn't create)

---

## Success Criteria

- Write a tag in daily note → note appears in Zettelkasten within 15 seconds
- macOS notification confirms creation
- All notes have `#review` tag, correct YAML frontmatter, and at least one `[[wikilink]]`
- `#book` notes appear on nostem.github.io bookshelf within 60 seconds
- `#research` notes contain web-sourced content (not just training data)
- Memory.md grows coherently across sessions
- Zero duplicate notes (dedup working correctly)
