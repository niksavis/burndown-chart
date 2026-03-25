---
description: Set up beads (bd) issue tracking on a developer machine for this repository
---

# Beads Developer Setup

You are setting up the beads (bd) issue tracking tool for the burndown-chart repository on a new developer machine. Follow these steps in order.

## Step 1: Verify or install bd

Check if bd is installed:

```bash
bd --version
```

If not installed, guide the developer through installing it globally:

- **Windows:** `irm https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1 | iex`
- **macOS/Linux:** `curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash`

Verify the minimum version is 0.60.0 or newer.

## Step 2: Bootstrap the local database

Run `bd bootstrap` from the repository root. This sets up the local Dolt database without overwriting anything if already initialized.

```bash
bd bootstrap
```

If bootstrap reports the database is already initialized, that is fine — continue.

## Step 3: Fetch the team's latest issue snapshot

Pull the current issue snapshot from the `beads-backup` branch on origin:

```bash
bd backup fetch-git
```

Expected output: something like "Restored NNN issues from backup snapshot".

## Step 4: Verify the setup

```bash
bd status
bd ready --json
```

- `bd status` should show total issues (currently 663+) with a mix of open and closed.
- `bd ready --json` lists unblocked work ready to claim.

## Step 5: Confirm git hooks are installed

```bash
bd hooks install
```

This ensures beads git hooks (in `.beads/hooks/`) are symlinked into `.git/hooks/`.

## Step 6: Explain the daily sync workflow

Tell the developer the two commands they need to remember:

**Start of session (get latest issues from team):**
```bash
bd backup fetch-git
```

**End of session (publish your issue changes to team):**
```bash
bd backup export-git
```

These commands sync via the `beads-backup` branch on `origin` — no DoltHub account or external server is needed.

## Reference: .beads/README.md

The full onboarding guide and common commands live in `.beads/README.md`.
