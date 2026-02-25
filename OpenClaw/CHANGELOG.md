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
