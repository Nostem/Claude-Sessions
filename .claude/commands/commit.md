Create a well-formatted git commit for the current staged/unstaged changes.

1. Run `git status` and `git diff` to understand exactly what has changed.

2. Run `git log --oneline -5` to match the existing commit style of this repo.

3. Draft a commit message following Conventional Commits format:
   ```
   <type>(<scope>): <short description>

   <optional body — explain WHY, not WHAT>
   ```
   Valid types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`

   Rules:
   - Subject line: max 72 characters, imperative mood ("add" not "added")
   - Never commit `.env` files, API keys, or secrets
   - Never commit to `master` or `main` without explicit user instruction

4. Stage the appropriate files (be specific — avoid `git add .` unless all changes are intentional).

5. Show the user the full commit message and staged files, then ask for confirmation before committing.

6. After confirmation, commit with the message.

7. Ask if the user wants to push the branch.
