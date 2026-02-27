Perform a full end-of-session wrap-up.

Execute these steps in order:

1. **Summarize the session** — list everything accomplished, files changed, and decisions made.

2. **Check for uncommitted work** — run `git status`. If there are uncommitted changes, ask the user whether to commit them before closing.

3. **Update CHANGELOG** — append a dated entry to the CHANGELOG.md in the relevant project folder (OpenClaw or Polygun-trading, whichever was active). Format:
   ```
   ## YYYY-MM-DD
   - <brief summary of changes>
   ```

4. **Store memory patterns** — identify the most reusable pattern from this session (approach, solution, workflow) and call:
   ```
   memory_store: {
     pattern: "<description>",
     outcome: "success",
     tags: ["<tag1>", "<tag2>"]
   }
   ```

5. **Clean up** — delete `.claude/context-snapshot.md` if it exists and is now stale.

6. **Final report** — print a one-paragraph summary of the session for the user.
