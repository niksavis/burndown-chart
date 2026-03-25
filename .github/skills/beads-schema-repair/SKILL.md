---
name: beads-schema-repair
description: >-
  Diagnose and repair beads (bd) Dolt schema mismatches that prevent issue
  restoration. Use when bd backup fetch-git returns 0 issues with "Unknown
  column" warnings, when bd migrate reports version match but issues still fail
  to restore, after fresh bd bootstrap on a machine with an older binary, or
  whenever bd status shows 0 issues after a fetch. Covers symptom recognition,
  column diffing, ALTER TABLE repair via dolt CLI, verification, and re-run
  of the restore. Platform: Windows (Git Bash primary; PowerShell required for data-pipeline inspection steps).
---

# Skill: Beads Dolt Schema Repair

Use this skill when `bd backup fetch-git` succeeds structurally but restores
0 issues, emitting repeated `Unknown column '<name>' in 'issues'` warnings.

---

## When to Use This Skill

- `bd backup fetch-git` output ends with `Issues: 0` and warnings like:
  ```
  Warning: failed to restore issues row: Error 1054 (HY000): Unknown column 'hook_bead' in 'issues'
  ```
- `bd migrate` reports "Version matches" but the backup still won't restore.
- After wiping `.beads\dolt` and running `bd bootstrap` + `bd migrate` on a machine
  whose binary predates some schema additions made on another machine.
- `bd status` shows 0 total issues after a fresh setup.

---

## Prerequisites

- `dolt.exe` on PATH (verify: `dolt version`)
- `bd dolt status` shows server running (or start it with `bd dolt start`)
- Know the Dolt port: check output of `bd dolt start` or `bd dolt status`
- All commands run from the **repo root** (`C:\Development\burndown-chart`) unless
  noted otherwise

> **Issue prefix**: Always read `.beads/config.yaml` (`issue-prefix` field) before
> referencing any bead IDs in commit messages or commands. For this repo it is
> `burndown-chart` (e.g. `burndown-chart-42`), never `bd-42`.
> ```bash
> grep "issue-prefix" .beads/config.yaml
> ```

---

## Step 1 — Confirm the Symptom

```bash
bd backup fetch-git 2>&1 | tail -10
```

Expected failure output:
```
Warning: failed to restore issues row: Error 1054 (HY000): Unknown column 'hook_bead' in 'issues'
...
  Issues: 0
  Labels: 813
  Events: 1373
```

If `Issues:` is non-zero, the schema is fine — this skill does not apply.

---

## Step 2 — Identify Missing Columns

### What columns does the backup expect?

```bash
git show origin/beads-backup:.beads/backup/issues.jsonl | \
  head -1 | jq 'keys[]'
```

### What columns does the live schema have?

Start the Dolt server if not running:

```bash
bd dolt start
```

Note the port from the output (e.g. `port 55311`). Then from `.beads\dolt`:

```bash
cd .beads/dolt
dolt sql -q "USE burndown_chart; SHOW COLUMNS FROM issues" 2>&1
```

> **Why from `.beads\dolt`?** When run from the data directory, `dolt sql` detects
> the running server and routes through it automatically — no credentials or
> TLS flags needed.

### Compute the diff

Compare the two column lists. Columns in the JSONL but absent from `SHOW COLUMNS`
are the ones to add. Common missing columns (bd 0.62.0 binary `1402021b`):

| Column | Type |
|---|---|
| `hook_bead` | `VARCHAR(255) NULL DEFAULT ''` |
| `rig` | `VARCHAR(255) NULL DEFAULT ''` |
| `agent_state` | `TEXT NULL DEFAULT ''` |
| `role_bead` | `VARCHAR(255) NULL DEFAULT ''` |
| `role_type` | `VARCHAR(32) NULL DEFAULT ''` |
| `last_activity` | `DATETIME NULL` |

---

## Step 3 — Apply ALTER TABLE

**Stay in `.beads\dolt`** (from Step 2). Build a single `ALTER TABLE` with all
missing columns. Example for the known 6-column gap:

```bash
dolt sql -q "USE burndown_chart; ALTER TABLE issues ADD COLUMN hook_bead VARCHAR(255) NULL DEFAULT '', ADD COLUMN rig VARCHAR(255) NULL DEFAULT '', ADD COLUMN agent_state TEXT NULL DEFAULT '', ADD COLUMN role_bead VARCHAR(255) NULL DEFAULT '', ADD COLUMN role_type VARCHAR(32) NULL DEFAULT '', ADD COLUMN last_activity DATETIME NULL" 2>&1
```

No output = success. An error message means a column already exists (safe to remove
that column from the statement) or a type mismatch (check JSONL sample values).

> **PowerShell gotchas — NEVER do these:**
>
> - `dolt sql ... < file.sql` — PowerShell treats `<` as a reserved token; use `-q` inline.
> - `Write-Output "" | dolt ... sql -q ...` — piping stdin for password breaks credential
>   parsing: `Failed to parse credentials: The handle is invalid.`
> - `dolt --host ... --port ... --user root sql -q ...` — prompts interactively for password
>   and TLS; use the data-dir approach instead.

### Inferring column types from the JSONL

Sample a few rows to validate types before altering:

```bash
git show origin/beads-backup:.beads/backup/issues.jsonl | \
  head -5 | jq '{hook_bead, rig, agent_state, role_bead, role_type, last_activity}'
```

- Numeric 0/1 values → `TINYINT(1)` (boolean)
- Numeric large values → `BIGINT`
- Short strings / empty → `VARCHAR(255)`
- Long text / JSON → `TEXT`
- ISO-8601 datetime strings or `null` → `DATETIME NULL`

---

## Step 4 — Verify Schema

Still from `.beads\dolt`:

```bash
dolt sql -q "USE burndown_chart; SHOW COLUMNS FROM issues" 2>&1 | \
  grep -E "hook_bead|rig|agent_state|role_bead|role_type|last_activity"
```

All 6 (or however many you added) should appear with their types.

---

## Step 5 — Restore Issues

Return to repo root and re-run the fetch:

```bash
cd "$(git rev-parse --show-toplevel)"
bd backup fetch-git 2>&1 | tail -10
```

Expected success output:
```
Fetched backup snapshot from git branch beads-backup and restored local database
  Remote: origin
  Issues: 671
  Comments: 0
  Dependencies: 91
  Labels: 813
  Events: 1373
  Config: 11
```

---

## Step 6 — Final Verification

```bash
bd status
bd ready
```

`bd status` should show total issues matching the backup manifest count (check
`git show origin/beads-backup:.beads/backup/manifest.json`).
`bd ready` should list unblocked open work.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Issues: 0` after ALTER TABLE | Not all missing columns were added | Re-diff JSONL vs `SHOW COLUMNS`, add remaining |
| `dolt: error: unknown option 'host'` | Global flags must precede subcommand | Use `dolt --host ... sql` not `dolt sql --host ...` |
| `TLS requested but server does not support TLS` | Connecting via host/port triggers TLS | Run from `.beads\dolt` dir instead |
| `Failed to parse credentials: The handle is invalid` | Piped stdin breaks credential read | Use `-q` inline, never pipe stdin to dolt |
| `The '<' operator is reserved` | PowerShell stdin redirect blocked | Use `-q "SQL"` inline, never `< file.sql` |
| `ALTER TABLE` reports column already exists | Column was added by a previous partial run | Remove that column from the ALTER statement |
| `bd bootstrap` says "database already exists" after wipe | Dolt server cached state | Run `bd dolt stop`, wipe `.beads\dolt`, then `bd bootstrap` |
| `bd migrate` says "Version matches" but issues still 0 | Binary predates some migrations | This skill applies: check column diff manually |

---

## Nuclear Option: Full Wipe and Re-Bootstrap

If the schema is corrupted beyond targeted ALTER TABLE repair:

```bash
# Return to repo root first
cd "$(git rev-parse --show-toplevel)"
bd dolt stop
rm -rf .beads/dolt
bd bootstrap     # answer Y at prompt
```

Then return to Step 2 of this skill to identify and add missing columns before
running `bd backup fetch-git`.
