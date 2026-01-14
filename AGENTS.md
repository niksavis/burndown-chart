# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Starting a New Session

**Simple approach** - Let the agent discover work:
```bash
What beads tasks are ready to work on?
```

**Better approach** - Use the handoff prompt from the previous session:
```bash
Continue work on bd-123: [issue title]. [Brief context]
```

The agent from the previous session should have provided this prompt in their final message.

**Quick discovery commands:**
```bash
bd ready                          # See available tasks
bd list --status in_progress      # See what's currently being worked on
bd show bd-123                    # View specific issue details
```

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

**WARNING**: DO NOT use `bd edit` - it opens an interactive editor which AI agents cannot use.

Use `bd update` with flags instead:
```bash
bd update <id> --description "new description"
bd update <id> --title "new title"  
bd update <id> --notes "additional notes"
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide next session prompt to user:
   ```
   **Next Session Prompt:**
   "Continue work on bd-X: [issue title]. [What was done, what's next]"
   ```

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
- ALWAYS provide a specific prompt for the next session

