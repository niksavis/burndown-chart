# Beads - Issue Tracking for burndown-chart

This repository uses [Beads (bd)](https://github.com/steveyegge/beads) for issue tracking.
Issues live in a local Dolt database at `.beads/dolt/` and are synced between developers
via the `beads-backup` git branch (no DoltHub or external server required).

---

## New Developer Setup

### 1. Install bd globally

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1 | iex
```

Verify: `bd --version`

### 2. Clone the repository and restore the issue database

```powershell
git clone https://github.com/niksavis/burndown-chart.git
cd burndown-chart
bd bootstrap          # sets up the local Dolt database
bd backup fetch-git   # pulls the latest JSONL snapshot from origin/beads-backup and restores it
bd status             # confirm issues are loaded
```

That is all. Your local beads database is now in sync with the team.

---

## Daily Workflow

### Start of session

```powershell
git pull --rebase
bd backup fetch-git   # pull latest issue snapshot from the team
```

### End of session

```powershell
git pull --rebase
bd backup export-git  # publish your issue changes to origin/beads-backup
git push              # push code changes to origin/main
```

### Check what is ready to work on

```powershell
bd ready --json
```

---

## Common Commands

```powershell
# Create a new issue (always include --description)
bd create "Title" --description="Context explaining why this matters" -t feature -p 2 --json

# Show issue details
bd show burndown-chart-42 --json

# Claim and start an issue
bd update burndown-chart-42 --claim --json

# Close a completed issue
bd close burndown-chart-42 --reason "Implemented in commit abc123" --json

# List open issues
bd list

# View dependency graph
bd graph
```

---

## Sync Architecture

Team sync works via git (no DoltHub / no server):

```
Developer A                    GitHub origin                Developer B
-----------                    -------------                -----------
bd backup export-git  ──────►  beads-backup branch  ◄──── bd backup fetch-git
git push              ──────►  main branch           ◄──── git pull --rebase
```

- `bd backup export-git` exports a JSONL snapshot of all issues and pushes it to `origin/beads-backup`.
- `bd backup fetch-git` fetches that snapshot and restores it into the local Dolt database.
- The primary database is always local Dolt — git carries the portable JSONL snapshot.
- Conflict handling: last writer wins (acceptable for a small team working sequentially).

---

## Issue Prefixes

Issues in this repo are prefixed `burndown-chart-` (e.g. `burndown-chart-42`).

---

## Rules for AI Agents

- Always use `--json` flag for programmatic use.
- Always include `--description` when creating issues.
- Never use `bd edit` (opens interactive editor that agents cannot use).
- Check `bd ready` before starting new work.
- Publish at end of every session with `bd backup export-git`.

