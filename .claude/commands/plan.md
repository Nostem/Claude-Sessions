Force structured planning before implementing any complex change.

Before writing a single line of code or making any edits, produce a complete implementation plan:

1. **Restate the goal** — one sentence describing what needs to be achieved.

2. **Scope assessment** — classify the task:
   - Simple (1 file, <50 lines) → direct tool use
   - Medium (2–5 files) → sequential tools
   - Complex (3+ files, new features) → swarm_init + parallel agents

3. **File inventory** — list every file that will be created or modified, with a one-line description of what changes.

4. **Dependency order** — if changes must happen in sequence, number them. Mark parallel-safe steps explicitly.

5. **Risks / open questions** — any ambiguities, potential breakage, or decisions that need user input.

6. **Model routing** — which model tier is appropriate (Haiku / Sonnet / Opus) and why.

7. **Confirmation** — present the plan and ask: "Proceed with this plan, or adjust first?"

Do NOT begin implementation until the user confirms. If this is a simple task (single file, trivial change), skip the plan and proceed directly.
