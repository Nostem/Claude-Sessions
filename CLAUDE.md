# Claude Sessions — Workspace Instructions

This repo tracks Claude Code sessions for the **OpenClaw** multi-agent system and **Polygun-trading** project.

---

## claude-flow (Ruflo) Integration

This workspace uses [claude-flow](https://github.com/ruvnet/claude-flow) (package: `ruflo@alpha`) for multi-agent orchestration, persistent memory, and intelligent task routing.

### MCP Tools Available (when ruflo MCP server is running)

| Tool | Purpose |
|------|---------|
| `swarm_init` | Initialize an agent swarm for a complex task |
| `agent_spawn` | Launch a specialized agent (coder, researcher, analyst…) |
| `task_orchestrate` | Coordinate multi-step workflows across agents |
| `memory_search` | Semantic vector search over past session patterns |
| `memory_store` | Persist patterns for future session reuse |
| `neural_train` | Trigger self-learning from recent patterns |
| `github_swarm` | Automate GitHub repo tasks with agent swarms |
| `swarm_status` | Check real-time coordination metrics |

### Starting the MCP Server

```bash
npm run mcp          # starts ruflo MCP server
# or
npx ruflo@alpha mcp start
```

---

## Core Workflow Principles

### 1. Concurrency-First Execution

**All independent operations MUST run in parallel in a single message.**

- Batch `TodoWrite` calls (5–10 items minimum for complex tasks)
- Spawn subagents concurrently via the Task tool
- Run parallel file reads, searches, and Bash commands in one response
- Never wait sequentially for operations that can run simultaneously

### 2. Task Complexity → Agent Strategy

| Complexity | Trigger | Approach |
|------------|---------|----------|
| Simple (1 file, <50 lines) | Single edit | Direct tool use |
| Medium (2–5 files) | Feature addition | Plan mode + sequential tools |
| Complex (3+ files, new features, API changes) | Multi-file refactor | `swarm_init` → spawn agents → orchestrate |
| Large (cross-repo, architecture) | System redesign | Hive-mind with queen coordination |

**Complexity triggers for agent swarms:**
- Changes spanning 3+ files
- New features with tests
- API changes with downstream effects
- Security modifications
- Cross-project coordination (OpenClaw ↔ Polygun)

### 3. Memory-Driven Sessions

Before starting any non-trivial task, search session memory:
```
memory_search: "relevant keywords from the task"
```

After completing a task, store the pattern:
```
memory_store: { pattern, outcome, tags }
```

This builds a knowledge base that accelerates future sessions — successful patterns get reused automatically.

### 4. Model Routing (Cost Optimization)

| Task Type | Model | Cost |
|-----------|-------|------|
| Simple transforms, boilerplate | Agent Booster (WASM) | Free |
| Structured edits, summaries | Haiku | ~$0.001 |
| Feature implementation, analysis | Sonnet | ~$0.003 |
| Architecture, complex reasoning | Opus | ~$0.015 |

Default to the cheapest model that can handle the task.

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

## Session Startup Checklist

When starting a new session in this repo:

1. Check `CHANGELOG.md` in the relevant project folder for prior session context
2. Run `memory_search` for the task domain to surface past patterns
3. Create a `TodoWrite` list before executing (5+ items for complex tasks)
4. Spawn swarm agents for multi-file or cross-project work
5. Store successful patterns to memory before ending session

---

## Agent Spawning Pattern (claude-flow)

For complex tasks, use this sequence in **one message**:

```
1. mcp__ruflo__swarm_init({ topology: "hierarchical", maxAgents: 5 })
2. [parallel] Spawn all needed agents via Task tool
3. [parallel] BatchTodoWrite with all subtasks
4. [parallel] Begin concurrent file operations
```

Never spawn agents sequentially when they can be initialized together.

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
npm run mcp           # Start ruflo MCP server
npm run flow:list     # List available agents
npm run flow:status   # Check swarm status
npx ruflo hive-mind spawn "objective"   # Launch agent swarm
npx ruflo memory search -q "keywords"  # Search session memory
```
