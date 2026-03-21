# Agent Instructions - Compatibility Shim

## Purpose

This file is a lightweight compatibility bootstrap for external agents (for example, Claude Code or Codex CLI) that may not automatically load `.github/copilot-instructions.md`.

## Source of Truth

- Canonical always-on policy: `.github/copilot-instructions.md`.
- Repository-specific coding/workflow rules: `repo_rules.md`.
- Architecture standards: `docs/architecture/readme.md` and language guideline files.

Do not duplicate policy text here. Keep this file concise and operational.

## Loading Strategy

- VS Code Copilot agents: rely on `.github/copilot-instructions.md` and conditional instructions under `.github/instructions/`.
- External agents: load this file first, then load `.github/copilot-instructions.md` for canonical policy.

## Orchestration Bootstrap (External Agents)

For non-trivial implementation tasks, external agents should follow the orchestration policy in `.github/copilot-instructions.md`:

0. **CONTEXT7 (always)**: Before any code generation, library/API question, setup, or configuration task — call `resolve-library-id` then `query-docs`. Do not answer from memory. Route to `context7-expert` for version migration or upgrade-impact analysis.
1. Route to specialized subagents first.
2. Run read-only discovery in parallel only when independent.
3. Run edits/tests/validation in sequence.
4. End with quality gate checks.

If specialized patterns are discovered during implementation, run the self-evolving loop:

- Use `.github/agents/custom-agent-foundry.agent.md` to add/update subagents.
- Use `.github/instructions/agent-skills.instructions.md` + `.github/skills/make-skill-template/SKILL.md` to add/update skills.
- Update `.github/copilot_customization.md` and `.github/copilot_capability_map.md`.

## External Agent Quick Start

```powershell
bd daemon status
bd backup fetch-git
bd ready --json
git pull --rebase
```

## Beads Commands

```powershell
bd ready --json
bd show <id> --json
bd update <id> --status in_progress
bd create "Title" --description="Context" -p 0-4 -t bug|feature|task --json
bd close <id> --reason "Done" --json
```

Rules:

- Always include `--description` when creating beads.
- Never use `bd edit`.
- Team sync uses git (no DoltHub). Publish: `bd backup export-git`. Restore fresh clone: `bd backup fetch-git`.

## Dependency Onboarding Rule

For any new Python package, perform onboarding explicitly:

```powershell
# Runtime dependency
# 1) Edit requirements.in
pip-compile requirements.in
pip install -r requirements.txt

# Development dependency
# 1) Edit requirements-dev.in
pip-compile requirements-dev.in
pip install -r requirements-dev.txt
```

Never edit compiled requirement files directly.

## Non-Interactive Command Rule

Use `-Force` for file operations to avoid interactive hangs:

```powershell
Copy-Item -Force source dest
Move-Item -Force source dest
Remove-Item -Force file
Remove-Item -Recurse -Force dir
```

## Session End (External Agents)

Do not finish until both main and beads snapshot are pushed:

```powershell
git pull --rebase
bd backup export-git
git push
git status
```

<!-- BEGIN BEADS INTEGRATION v:1 profile:full hash:d4f96305 -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Dolt-powered version control with native sync
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs via Dolt:

- Each write auto-commits to Dolt history
- Use `bd dolt push`/`bd dolt pull` for remote sync
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd backup export-git
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->
