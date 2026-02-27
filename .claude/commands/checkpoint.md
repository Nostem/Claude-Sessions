Snapshot the current task state mid-session.

1. Summarize what has been completed so far in this session (bullet points, concise)
2. List what is still in-progress or pending
3. Note any blockers, open questions, or decisions deferred
4. Check git status and list any uncommitted files
5. Write this snapshot to `.claude/context-snapshot.md` in the format:

```markdown
# Checkpoint — <timestamp>

## Completed
- ...

## In Progress
- ...

## Pending / Blocked
- ...

## Uncommitted Files
- ...

## Notes
- ...
```

6. Confirm the snapshot was written and print the summary to the user.
