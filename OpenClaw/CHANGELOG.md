# OpenClaw Optimization — Session Changelog

Tracking all changes made to the OpenClaw multi-agent setup across Claude Code sessions.

**Repo:** `~/.openclaw`
**Fleet:** 12 agents (main/Opus, kimi, grok41, gemini3, trinity, kb-agent, infra-agent, minimax, glm, astro, poly, codex)

---

## Session 2 — 2026-02-25

### Obsidian Daily Note Pipeline (seq 2 of initiative queue)

**Problem:** Phase 5 of the Obsidian integration project (Daily Note → Agent Task dispatch) was fully designed in `PROJECT.md` but not yet built.

#### Built: `~/.openclaw/scripts/daily-note-scanner.py`
- Deterministic Python scanner (no LLM, free to run)
- Reads daily notes from `KoemKlaw/ops/Daily/` (e.g. `February 21st, 2026.md`)
- Detects inline hashtag bullets: `- #Research some question` / `- #KoemKlaw ingest x`
- Writes structured Inbox items to `KoemKlaw/ops/Inbox/` with YAML frontmatter
- Deduplicates via SHA-256 hash → `~/.openclaw/state/scanner-processed.json`
- Flags: `--date YYYY-MM-DD`, `--all` (backfill), `--dry-run`, `--json`

**Tag routing table:**

| Tag | Agent |
|-----|-------|
| `#Research` | minimax-agent |
| `#Code` | codex-agent |
| `#Kb` | kb-agent |
| `#Idea` | main |
| `#KoemKlaw` | main |
| `#Task` | main |
| `#Write` | main (TBD) |

#### Built: `~/Library/LaunchAgents/ai.openclaw.daily-note-scanner.plist`
- WatchPaths on `KoemKlaw/ops/Daily/` — fires on file save
- StartInterval: 1800s (30-min fallback for iCloud sync delays)
- ThrottleInterval: 30s debounce
- Logs to `~/.openclaw/logs/daily-note-scanner-{stdout,stderr}.log`

#### Built: `obsidian-inbox-distiller` cron job (`cron/jobs.json`)
- Schedule: `*/30 * * * *` (every 30 min)
- Agent: main (haiku35 model — ~$0.001/task)
- Reads `ops/Inbox/` for `status: inbox` items
- Distills each into a proper TaskNote in `ops/Tasks/` with title, acceptance criteria, priority
- Updates inbox item to `status: processed`
- Posts Discord summary: `📋 New task(s) dispatched: [title] → [agent]`

#### Built: `KoemKlaw/ops/Tag Routing.md`
- Routing reference document in the vault with pipeline diagram
- Full tag vocabulary, pipeline architecture, deduplication notes, how to add new tags

#### Backfill
- Ran `daily-note-scanner.py --all` → 6 Inbox items extracted from 9 historical daily notes:
  - `#Research` → minimax: tanning/cancer, glyphosate, grocery ingredients, Vadim Zealand
  - `#KoemKlaw` → main: ingest remaining Bashar transcripts
  - `#idea` → main: automated Bashar newsletter

#### Updated
- `workspace/projects/obsidian-integration/PROJECT.md` — checked off Phase 5.1, 5.2, 5.3 items
- `workspace-main/state/initiative_queue.json` — seq 1 & 2 marked done, seq 3 (astro-client-intake) now active

---

## Session 1 — 2026-02-20 to 2026-02-24

### Initial Setup & Fleet Audit

**Context:** Full familiarization of the 12-agent OpenClaw setup + comprehensive improvements pass.

---

### 1. Session Instructions — `~/.openclaw/CLAUDE.md`
**Created** — Session-scoped instructions for Claude Code covering:
- Workflow orchestration, plan mode, subagent strategy
- Self-improvement loop, verification, elegance standards
- Autonomous bug fixing, task management, core principles

---

### 2. Agent Lessons System — All 10 workspaces

**Created `tasks/lessons.md`** in all 10 agent workspaces:
- Standard format: `YYYY-MM-DD — Short description / What happened / Root cause / Rule`
- Each seeded with agent-specific starter lessons from observed issues
- Workspaces: main, kimi, grok41, gemini3, glm, minimax, poly, kb-agent, trinity, infra

**Updated `AGENTS.md`** in all 10 workspaces:
- Added Step 7 to Every Session checklist: `Read tasks/lessons.md — rules you've written for yourself (create if missing)`
- Added `## 📚 Lessons & Self-Improvement` section with when/how to write lessons

---

### 3. Missing Scripts — kb-agent & poly-agent

**Problem:** `HEARTBEAT.md` in both agents referenced scripts that didn't exist → ENOENT on every heartbeat.

**Fixed:**
- Created `workspace-kb-agent/scripts/check_usage.py`
- Created `workspace-poly-agent/scripts/check_usage.py`
- Copied `health_check.sh` from infra-agent to both workspaces

---

### 4. poly-agent MEMORY.md Rebuild

**Problem:** MEMORY.md was accidentally overwritten with a raw copy-trading monitor update (trader list) instead of curated memory.

**Rebuilt with:**
- User profile, agent mission (daily 5AM + weekly Sunday reports)
- Polygun context: Telegram-based Polymarket copy-trading service
- Monitored wallet: `0xd19bff5dd8e408c55f8ef21facfb0d82632c8054`
- Tracked traders: anoin123 and Sharky
- Performance targets, strategy notes

---

### 5. Bashar Cron Pipeline Fixes

**Two root-cause bugs fixed:**

**Bug A — "Action send requires a target" (Kimi drops target param)**

Fixed `SUMMARY_SKILL.md` in both `workspace/skills/bashar-watcher/` and `workspace-kimi-agent/skills/bashar-watcher/`:
```
# Before (ambiguous):
Send Discord post to target=channel:1470814714664718641 via message action=send channel=discord

# After (explicit with warning):
3. **Send Discord post** — call the message tool with EXACTLY this target:
   message action=send target=channel:1470814714664718641
   ⚠️ target=channel:1470814714664718641 is REQUIRED — omitting it causes a "requires a target" error.
   Do NOT use channel=discord — the target param already specifies the Discord channel.
```

**Bug B — LLM timeout on large transcripts**

`cron/jobs.json`: `bashar-backfill` and `bashar-new-check` `timeoutSeconds` bumped 600 → 900s  
(successful runs were hitting ~550s, leaving almost no headroom)

---

### 6. Initiative Queue Rebuild — `workspace-main/state/initiative_queue.json`

**Problem:** Malformed JSON (missing `{` on duplicate entry, no `id` fields) → `json.load()` crashed.

**Rebuilt:** 18 clean items with `seq`, `id`, `title`, `priority`, `status`, `owner`, `depends_on`:

| Seq | Item | Priority |
|-----|------|----------|
| 1 | Cron preflight validator | critical |
| 2 | Daily Note hashtag dispatch pipeline | high |
| 3 | Astro client intake workflow | high |
| 4 | Proactive daily transit reports | high |
| 5 | KB entity extraction backfill | high |
| 6 | KB-Obsidian auto-export | medium |
| 7 | Cost visibility dashboard | medium |
| … | …13 more items… | … |

---

### 7. Cron Validator — `workspace-infra-agent/scripts/validate_cron_jobs.py`

**Built** comprehensive validator for all cron jobs. Checks:
- Unknown `agentId` references
- Missing `channel:` prefix on `delivery.to` fields
- `timeoutSeconds` sanity (warn if >600, error if >3600)
- Invalid model alias references
- Empty `agentTurn.message` fields
- Basic cron expression format
- Consecutive error counts

Flags: `--json`, `--enabled-only`, `--job <name>`  
Exit code: 0 = clean, 1 = errors found  
**Found 5 real bugs on first run.**

---

### 8. Config Validator — `~/.openclaw/validate_config.py`

**Built** validator for `openclaw.json`. Checks:
- Valid JSON syntax
- Required top-level keys: `agents`, `models`, `gateway`, `skills`
- Agent required fields, duplicate agent IDs
- Missing workspace paths
- Gateway port present
- Provider baseUrls
- Discord token

Flags: `--json`, path argument

---

### 9. Gemini3 Heartbeat Noise Fix

**Problem:** gemini3-agent generating dozens of near-identical "calm sky" spiritual reflection entries per heartbeat cycle, burning tokens and polluting memory.

**Fixed:** `workspace-gemini3-agent/HEARTBEAT.md` Check 2 (Spiritual Awareness):
```
# Added gate:
First: Check memory/YYYY-MM-DD.md — if it already has a reflection entry from today, skip this check entirely.
```
→ One reflection per day max.

---

### 10. Infra Heartbeat — Preflight Validators

**Updated** `workspace-infra-agent/HEARTBEAT.md`:
- Added Check 0 (runs before all other checks):
  ```
  python3 scripts/validate_cron_jobs.py --json
  python3 /Users/fredm/.openclaw/validate_config.py
  ```

---

### 11. Ghost Jobs Archived

**Removed 3 ghost cron jobs** referencing non-existent agents:
- `session-hygiene-nudge` → was `ollama-agent`
- `polymarket-daily-report` → was `polymarket-agent`
- `polymarket-weekly-report` → was `polymarket-agent`

**Created** `cron/jobs_archived.json` with metadata: `_archivedAt`, `_archivedReason`.

**Fixed** `ops-weekly-slo-report`: `agentId` changed from `ollama-agent` → `infra-agent`.

---

### 12. Cron Delivery Field Fixes

**Fixed 4 jobs** with bare channel IDs (missing `channel:` prefix in `delivery.to`):
- `agent-workspace-lint-6h`
- `memory-weekly-compaction`
- `Daily workflow surprise improvement`
- One additional session-hygiene job

---

### 13. TOOLS.md Update — `workspace-main/TOOLS.md`

Appended Config Safety section with:
- Before-change: run `validate_config.py`
- After-change: run `validate_config.py` again
- Usage instructions for both validators

---

## Summary Stats

| Metric | Count |
|--------|-------|
| Files created | 25+ |
| Files modified | 15+ |
| Agents touched | 10/12 |
| Cron bugs fixed | 7 (5 in validator pass + agentId + delivery fields) |
| Ghost jobs archived | 3 |
| Lessons seeded | 10 (one per workspace) |
| Inbox items backfilled | 6 |

---

## Next Up (Active Initiative Queue)

| Seq | Item | Status |
|-----|------|--------|
| ✓ 1 | Cron preflight validator | done |
| ✓ 2 | Daily Note → Task pipeline | done |
| ▶ 3 | Astro client chart intake workflow | active |
| ○ 4 | Proactive daily transit reports | pending |
| ○ 5 | KB entity extraction backfill | pending |
| ○ 6 | KB-Obsidian auto-export | pending |
| ○ 7 | Cost visibility dashboard | pending |


---

## Session 2 (continued) — 2026-02-25

### Astro Client Chart Reading Workflow (seq 3 of initiative queue)

**Option chosen:** Public-facing (anyone in Discord can request a reading)

#### Built: `skills/client-intake/SKILL.md`
Complete workflow playbook for the intake pipeline:
- Step 1: How to post the standing intake card (modal component JSON)
- Step 2: How to handle modal submissions (save_request.py call)
- Step 3: Full reading processing flow (chart scripts → interpretation → Discord delivery)
- State file schema, privacy rules, error handling table, channel config notes

#### Built: `skills/client-intake/scripts/save_request.py`
State manager for the reading queue. Supports:
- `--name/--date/--time/--city/--notes` — save new reading request (assigns `rdg-YYYYMMDD-{hash}` ID)
- `--list` — show all readings and statuses
- `--next` — JSON output of next pending reading (for cron)
- `--mark-processing / --mark-done / --mark-failed` — lifecycle state transitions
- `--set-card-id` — save intake card message ID after posting
- `--set-chart` — attach PNG path to a reading record

#### Built: `skills/client-intake/scripts/process_reading.py`
Deterministic pre-processor called by the astro-reading-processor cron:
- Claims next pending reading (marks processing)
- Runs `chart.py natal` → natal text data
- Runs `chart.py image` → PNG chart file (~/.openclaw/media/outbound/)
- Runs `chart.py transits-to-natal` → current sky overlay
- Outputs structured JSON context for Astro-Grok to write the interpretation
- Includes delivery instructions and mark-done command in the output

#### Discord intake modal (5 fields)
```
Title: Chart Reading Request
Button: "Request a Reading 🔮" (primary style)
Fields:
  1. Your Name (short, required)
  2. Birth Date — YYYY-MM-DD (short, required)
  3. Birth Time — HH:MM or 'unknown' (short, required)
  4. Birth City & Country (short, required)
  5. Questions / Focus Areas (paragraph, optional)
```

#### Cron jobs added
- `astro-reading-processor` — every 15 min, grok41-fast — picks up next pending reading, generates chart, delivers to Discord
- `astro-intake-card-refresh` — every Monday 9 AM — checks if card message ID is null and re-posts the intake card if needed

#### Other files
- `state/pending-readings.json` — initialized with `{card_message_id: null, readings: []}`
- `tasks/lessons.md` — created for astro-agent (was missed in Session 1)
- `AGENTS.md` — added Client Chart Reading Intake section + Step 7 (read lessons.md)

#### Next step for Nostem (manual)
Post the intake card for the first time:
1. Tell astro-agent: "Post the reading intake card to Discord"
2. It will use the modal block in SKILL.md Step 1
3. Or wait for Monday's `astro-intake-card-refresh` cron to auto-post it

---

### GitHub Tracking
Added `CHANGELOG.md` and `README.md` to `Nostem/Claude-Sessions/OpenClaw/` for session tracking.
Changelog updated after each seq completion going forward.


---

## Session 2 (continued) — 2026-02-25

### Proactive Daily Transit Reports (seq 4 of initiative queue)

**Goal:** Ongoing astrology content that builds Discord audience and funnels readers to the chart intake card.

#### Built: `skills/transit-reports/SKILL.md`
Format guide and style rules for transit posts:
- Daily format: Moon sign lead, 3-5 bullets, grounded interpretation, CTA
- Weekly format: biggest transit of the week, Moon journey, lunations, "best days for..." section, CTA
- Discord rules: no tables, bullets with •, planet glyphs, under 2000 chars
- CTA templates (varied week to week)
- Consistency log instruction (note key themes in memory to avoid repetition)
- ⚠️ Python binary warning: must use `/usr/bin/python3`, not `python3`

#### Cron jobs added
- `astro-daily-transits` — 7 AM EST daily (grok41-fast, 180s timeout)
  - Runs `chart.py transits`, writes Discord post, logs theme to memory
- `astro-weekly-preview` — 7 AM EST every Monday (grok41-fast, 240s timeout)
  - Week-ahead preview covering major transits, Moon journey, lunations, best-day windows

#### Bug fixed: Python binary in process_reading.py
`process_reading.py` was using `sys.executable` (Homebrew Python 3.13, no kerykeion).
Fixed: hardcoded to `/usr/bin/python3` (system Python, has kerykeion).

#### TOOLS.md updated
Added critical note: always use `/usr/bin/python3` for astrology scripts with correct/incorrect examples.

---

### Path Bug Fix (client-intake scripts)
Discovered and fixed during first live reading submission (Alfredo Montan):
- `save_request.py` and `process_reading.py` used `parents[2]` → resolved to `workspace/skills/` instead of workspace root
- Fixed to `parents[3]`
- State data migrated from `skills/state/` to correct `state/` path
- Card message ID (`1476285049220370618`) and reading saved correctly
- Lesson added to `tasks/lessons.md`

---

## Session 3 — 2026-02-25

### Bashar Transcript Reformat (seq 5 — done)
**Script**: `workspace/scripts/reformat_bashar.py`
**State**: `state/bashar-reformat-progress.json`

**What was built:**
- `reformat_bashar.py` — deterministic reformatter for 1,197 Bashar transcript KB entries
  - Merges consecutive `**BASHAR:**` lines into clean unlabeled paragraphs
  - Converts `**QUESTIONER:**` lines to `**Q:**` prefix
  - Strips `[Music]`, `[Applause]`, `[Laughter]` sound cues
  - Cleans titles: `"(2014 01 25) Bashar   Cosmic Awakening.en fixed"` → `"Cosmic Awakening — Bashar (January 25, 2014)"`
  - Updates `title` column in `kb.db`
  - Progress tracking via `state/bashar-reformat-progress.json`
  - Flags: `--limit`, `--dry-run`, `--entry-id`, `--list-pending`, `--list-pending-topics`, `--set-topics`, `--stats`

**Results:**
- 1,178 entries successfully reformatted
- 19 entries skipped (different format — YouTube summaries, already clean)
- All 1,197 entries marked `format_done`

### Bashar Topic Re-Analyzer Cron (Phase 2)
**Cron job**: `bashar-topic-reanalyzer`
**Schedule**: 3am + 3pm daily (2×/day)
**Agent**: kimi-agent / minimax model
**Batch size**: 30 entries per run (~20 days to full completion)

Replaces generic topic tags (`money, relationships, health`) with per-entry specific topics analyzed from actual transcript content.

**Script flags for Phase 2:**
- `--list-pending-topics --limit N` → JSON list of entries + transcript excerpts for LLM analysis
- `--set-topics ENTRY_ID --topics '["t1","t2"]'` → writes analyzed topics to YAML + DB

### Initiative Queue Updated
- New seq 5: `bashar-transcript-reformat` (done)
- Old seq 5→6: `kb-entity-backfill-cron` (still active)
- Items renumbered 6–19 accordingly

### Files Changed
| File | Change |
|------|--------|
| `workspace/scripts/reformat_bashar.py` | Created — 420 lines |
| `state/bashar-reformat-progress.json` | Created — tracks 1,197 entries |
| `cron/jobs.json` | Added `bashar-topic-reanalyzer` job |
| `workspace-main/state/initiative_queue.json` | Inserted seq 5, renumbered 6–19 |
