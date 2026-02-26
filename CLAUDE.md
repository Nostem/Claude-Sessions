# Claude Sessions — Workspace Instructions

This repo tracks Claude Code sessions for the **OpenClaw** multi-agent system and **Polygun-trading** project.

This workspace uses two complementary systems:
- **superpowers** — process discipline, workflow gates, TDD, debugging methodology
- **claude-flow (ruflo)** — multi-agent orchestration, persistent memory, model routing

---

## Workflow: How the Two Systems Work Together

```
User request
    │
    ▼
[superpowers] brainstorming        ← design gate (BEFORE any code)
    │  clarify → propose → approve
    ▼
[superpowers] writing-plans        ← creates docs/plans/YYYY-MM-DD-<feature>.md
    │
    ├─── Simple/medium task ──────► [superpowers] executing-plans
    │                                   batch execution + human checkpoints
    │
    └─── Complex/multi-file ──────► [claude-flow] swarm_init + agent_spawn
                                        ↓
                                    [superpowers] subagent-driven-development
                                        fresh agent per task + two-stage review
    │
    ▼
[superpowers] test-driven-development   ← mandatory per task (RED→GREEN→REFACTOR)
    │
    ▼
[superpowers] verification-before-completion  ← run tests, read output, THEN claim done
    │
    ▼
[superpowers] finishing-a-development-branch
```

---

## superpowers Skills (14 available)

Skills auto-load in remote sessions via the SessionStart hook. On local machines,
install once with:
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

### Mandatory Gates (always invoke these)

| Skill | When | What It Enforces |
|-------|------|-----------------|
| `brainstorming` | Before ANY feature/change | Design approval before code; produces design doc |
| `test-driven-development` | Before ANY implementation | RED→GREEN→REFACTOR; no production code without a failing test first |
| `systematic-debugging` | On ANY bug/failure | Root cause investigation before fixes |
| `verification-before-completion` | Before claiming done | Run tests fresh, read full output, only then claim |

### Execution Skills

| Skill | When |
|-------|------|
| `writing-plans` | After approved design → creates `docs/plans/YYYY-MM-DD-<name>.md` |
| `executing-plans` | Batch execution with human checkpoints |
| `subagent-driven-development` | Independent tasks in current session; spec + quality review per task |
| `dispatching-parallel-agents` | 2+ independent failures or tasks with no shared state |
| `using-git-worktrees` | Feature work needing branch isolation |

### Quality Skills

| Skill | When |
|-------|------|
| `requesting-code-review` | After tasks complete, before merging |
| `receiving-code-review` | When feedback arrives; evaluate technically, not emotionally |
| `finishing-a-development-branch` | Implementation done, tests pass, ready to integrate |
| `writing-skills` | Capturing a new reusable workflow pattern |

---

## claude-flow (ruflo) Integration

### MCP Tools (when `npm run mcp` is running locally)

| Tool | Purpose |
|------|---------|
| `swarm_init` | Initialize a hierarchical agent swarm |
| `agent_spawn` | Launch a specialized agent (coder, researcher, analyst…) |
| `task_orchestrate` | Coordinate multi-step workflows across agents |
| `memory_search` | Semantic vector search over past session patterns |
| `memory_store` | Persist patterns for future session reuse |
| `neural_train` | Trigger self-learning from recent patterns |
| `github_swarm` | Automate GitHub repo tasks with agent swarms |
| `swarm_status` | Check real-time coordination metrics |

### Task Complexity → Agent Strategy

| Complexity | Trigger | Approach |
|------------|---------|----------|
| Simple (1 file, <50 lines) | Single edit | Direct tool use |
| Medium (2–5 files) | Feature addition | superpowers brainstorm → plan → execute |
| Complex (3+ files, new features) | Multi-file refactor | `swarm_init` → `agent_spawn` → subagent-driven-development |
| Large (cross-repo, architecture) | System redesign | Hive-mind with queen coordination |

### Model Routing (Cost Optimization)

| Task Type | Model | Cost |
|-----------|-------|------|
| Simple transforms, boilerplate | Agent Booster (WASM) | Free |
| Structured edits, summaries | Haiku | ~$0.001 |
| Feature implementation, analysis | Sonnet | ~$0.003 |
| Architecture, complex reasoning | Opus | ~$0.015 |

### Memory-Driven Sessions

Before any non-trivial task:
```
memory_search: "relevant keywords"
```

After completing a task:
```
memory_store: { pattern, outcome, tags }
```

### Starting the MCP Server
```bash
npm run mcp    # from the Claude-Sessions repo root
```

---

## Session Startup Checklist

1. Check `CHANGELOG.md` in the relevant project folder for prior context
2. Run `memory_search` for the task domain to surface past patterns
3. **Always invoke `brainstorming` before implementing anything**
4. Create a `TodoWrite` list (5+ items for complex tasks)
5. Store successful patterns to memory before ending the session

---

## Projects

### OpenClaw (`./OpenClaw/`)

Multi-agent orchestration system with 12-agent fleet.

- **Config:** `~/.openclaw/`
- **Vault:** `KoemKlaw` (Obsidian, iCloud-synced)
- **Fleet:** main/Opus, kimi, grok41, gemini3, trinity, kb-agent, infra-agent, minimax, glm, astro, poly, codex
- **Sessions log:** `./OpenClaw/CHANGELOG.md`

**Key pipelines:**
- Daily Note Scanner → Inbox → Agent dispatch
- Obsidian vault ingestion (Bashar transcripts)
- Cron-based distiller (every 30 min)

### Polygun-trading (`./Polygun-trading/`)

Algorithmic trading strategy workspace.

- **Strategy doc:** `./Polygun-trading/Polygun-Strategy.html`

---

## Behavioral Constraints

- Do what has been asked; nothing more, nothing less
- Never create files unless necessary; prefer editing existing files
- Always read files before editing
- Never commit `.env` files or API keys
- Never push to `master` or `main` without explicit instruction
- Session changelogs go in the relevant project's `CHANGELOG.md`

---

## Quick Commands

```bash
npm run mcp              # Start ruflo MCP server (local)
npm run flow:list        # List available agents
npm run flow:status      # Check swarm status
npx ruflo hive-mind spawn "objective"    # Launch agent swarm
npx ruflo memory search -q "keywords"   # Search session memory
```
