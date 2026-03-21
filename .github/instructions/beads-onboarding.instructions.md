---
applyTo: '.beads/**,agents.md'
description: 'Enforce beads (bd) onboarding, update, and team sync procedures'
---

# Beads Onboarding and Team Sync

This repository uses [Beads (bd)](https://github.com/steveyegge/beads) for issue tracking.
Issues are stored in a local Dolt database and synced between developers via the
`beads-backup` git branch. No DoltHub account or external server is required.

---

## Prerequisites

Both binaries must be installed globally and available on `PATH` before using beads.

### 1. Dolt CLI

Dolt is the version-controlled database engine that beads uses internally.

**Windows:**
```powershell
winget install DoltHub.Dolt
# Or download the MSI from https://github.com/dolthub/dolt/releases/latest
```

**macOS:**
```bash
brew install dolt
```

**Linux:**
```bash
sudo bash -c 'curl -L https://github.com/dolthub/dolt/releases/latest/download/install.sh | bash'
```

Verify: `dolt version`

### 2. bd (Beads) CLI

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```

Verify: `bd --version` (minimum 0.60.0)

---

## Fresh Developer Setup (new clone)

Run these three commands from the repo root after cloning:

```powershell
bd bootstrap          # sets up local Dolt database from .beads/metadata.json
bd backup fetch-git   # restores all issues from the origin/beads-backup snapshot
bd status             # verify: should show 663+ issues
```

Then install the git hooks so beads integrates with git commits:

```powershell
bd hooks install
```

---

## Migrating from Old Beads (SQLite / worktree-based)

If a developer has the old pre-Dolt version of beads, follow these steps to migrate cleanly.

### Step 1: Identify old version

```powershell
bd --version
```

If the version is below 0.60.0, or if `.git/beads-worktrees/` exists, the old setup is present.

### Step 2: Remove old beads artefacts from the repo

Run these from the repository root (do NOT delete the `bd` binary):

```powershell
# Remove old git hooks installed by beads
Remove-Item .git\hooks\prepare-commit-msg -Force -ErrorAction SilentlyContinue
Remove-Item .git\hooks\post-checkout -Force -ErrorAction SilentlyContinue
Remove-Item .git\hooks\*.backup -Force -ErrorAction SilentlyContinue

# Remove old worktree
if (Test-Path .git\beads-worktrees) {
    Remove-Item .git\beads-worktrees -Recurse -Force
}

# Remove old beads git config entries
git config --unset merge.beads.driver 2>$null
git config --unset merge.beads.name 2>$null
git config --unset include.path 2>$null

# Remove old .beads directory
if (Test-Path .beads) {
    Remove-Item .beads -Recurse -Force
}
```

### Step 3: Install new bd

```powershell
# Windows
irm https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1 | iex
```

Verify the new version: `bd --version` (must be 0.60.0+)

### Step 4: Re-initialize and restore

```powershell
git pull --rebase           # get the current .beads/ config committed by the team
bd bootstrap                # set up fresh local Dolt database
bd backup fetch-git         # restore all issues from origin/beads-backup
bd hooks install            # reinstall git hooks for new version
bd status                   # verify issues loaded correctly
```

---

## Updating bd (existing installation)

```powershell
bd upgrade
bd --version   # confirm new version
```

If the upgrade adds new hook versions, reinstall hooks:

```powershell
bd hooks install
```

---

## Daily Sync Workflow

### Start of session

```powershell
git pull --rebase
bd backup fetch-git   # pull latest issue snapshot from team
```

### End of session

```powershell
bd backup export-git  # publish your issue changes to origin/beads-backup
git push              # push code changes to origin/main
```

The `beads-backup` branch on `origin` is the shared issue snapshot. It is separate
from `main` and only contains JSONL backup files — never code.

---

## Issue Prefix

All issues in this repository use the prefix `burndown-chart-` (e.g. `burndown-chart-42`).
This is set explicitly in `.beads/config.yaml` so it is consistent regardless of the
name of the local clone directory.

---

## Verify Your Setup is Correct

```powershell
bd context   # should show: database=burndown_chart, backend=dolt
bd status    # should show 663+ issues
bd ready     # shows unblocked work available
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `bd` command not found | Ensure `~/.beads/bin` (or the install location) is on `PATH`. Restart the terminal after install. |
| `dolt` not found | Install Dolt and ensure it is on `PATH`. |
| `bd status` shows 0 issues | Run `bd backup fetch-git` to restore from the team snapshot. |
| Wrong prefix (e.g. `my-repo-1` instead of `burndown-chart-1`) | Delete `.beads/dolt/` and re-run `bd bootstrap` then `bd backup fetch-git`. The prefix is locked in `.beads/config.yaml`. |
| Dolt server fails to start | Run `bd doctor` to diagnose and repair. |
| Hook conflicts after update | Run `bd hooks install` to refresh hooks. |
