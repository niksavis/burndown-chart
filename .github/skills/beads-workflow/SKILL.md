---
name: beads-workflow
description: 'Full multi-developer beads (bd) issue lifecycle: syncing before new work, searching for duplicates, creating beads with descriptions, publishing state changes immediately so teammates see claims and new tasks without waiting for the next code push. Use when starting new work, creating issues, claiming a bead, updating status to in_progress or blocked, closing completed work, or resolving a duplicate before implementing. Covers the complete lifecycle: fetch -> search -> create -> export -> claim -> export -> work -> close -> push.'
---

# Skill: Beads Workflow (Multi-Developer)

Enforces the team-safe beads lifecycle so that every developer always sees
current assignments, newly created issues, and in-progress claims without
waiting for the next code push.

## When to Use This Skill

- Starting a new session or a new work item
- Before creating any new issue
- After creating, claiming, closing, or blocking a bead
- When a teammate may be working on the same area
- When task status changes and delay would cause duplicate work

## Prerequisites

- `bd` v0.60.0+ installed and on `PATH`
- `bd context` shows `backend=dolt`
- Repo cloned; `bd bootstrap` and `bd backup fetch-git` run at least once

Verify:

```powershell
bd --version   # must be 0.60.0+
bd context     # must show backend=dolt
bd status      # must show 600+ issues
```

---

## Step 0: Sync Before Starting Any Work

**Always run before creating a new bead or starting on an existing one.**
Skipping this step creates duplicate work.

```powershell
git pull --rebase            # pulls code + triggers post-merge hook (auto-fetches beads)
bd ready --json              # shows open, unblocked, unclaimed work
```

If you did not do a `git pull`, fetch beads explicitly:

```powershell
bd backup fetch-git
bd ready --json
```

> The post-merge git hook calls `bd backup fetch-git` automatically on
> every `git pull`, so an explicit fetch is only needed when you want
> mid-session visibility without pulling code.

---

## Step 1: Search Before Creating

Check for existing or similar beads before creating a new one.

```powershell
bd search "keyword" --json          # full-text search
bd list --status open --json        # browse open issues
```

**Decision rules:**

| Finding | Action |
|---|---|
| Exact duplicate found | Do **not** create. Extend the existing bead with `bd note <id> "..."`. |
| Closely related found | Add a comment/note, or create a sub-task and link it: `--deps <parent-id>` |
| Nothing relevant found | Proceed to Step 2. |

---

## Step 2: Create the Bead

Create **before** writing code. Always include `--description`.

```powershell
bd create "Short imperative title" \
    --description="Context: why this is needed. Acceptance: what done looks like." \
    -t feature|bug|task|chore \
    -p 0|1|2|3|4 \
    --json
```

Priority guide: `0`=critical `1`=high `2`=medium (default) `3`=low `4`=backlog

**NEVER** use `bd edit` — it opens an interactive editor agents cannot use.

---

## Step 3: Export Immediately After Create

Publish the new bead so teammates see it before you start working.

```powershell
bd backup export-git
```

Run this right after every `bd create` call. Do not wait until the next push.

---

## Step 4: Claim and Export When Starting Work

```powershell
bd update <id> --claim --json      # sets status=in_progress, owner=you
bd backup export-git               # publish claim immediately
```

**Order is required**: claim first, export second. Teammates who run
`bd backup fetch-git` after this point will see the bead as taken.

---

## Step 5: Mark Blocked If Stuck

If a blocking dependency or impediment is discovered:

```powershell
bd update <id> --status blocked --json
bd note <id> "Blocked by: <reason or dep-id>"
bd backup export-git
```

Add the blocking bead as a dependency when possible:

```powershell
bd dep add <id> <blocking-id>
```

---

## Step 6: Close and Push When Done

```powershell
bd close <id> --reason "Brief summary of what was done" --json
```

**Do not export manually here.** The pre-push hook runs `bd backup export-git`
automatically before every code push. Close the bead, then commit and push:

```powershell
git add .
git commit -m "type(scope): description (burndown-chart-<id>)"
git push    # hook auto-exports beads snapshot
```

If the work is abandoned rather than completed:

```powershell
bd close <id> --reason "Abandoned: <why>" --json
bd backup export-git    # export now since no push is imminent
```

---

## Commit Message Format (Required)

```
type(scope): description (burndown-chart-<id>)
```

Types: `feat | fix | docs | style | refactor | perf | test | build | ci | chore`

Example: `feat(visualization): add burndown forecast line (burndown-chart-42)`

---

## Quick Reference: When to Export Manually

| Event | Export needed? | Why |
|---|---|---|
| `bd create` | **Yes** — immediately | Hook does not fire on create |
| `bd update --claim` | **Yes** — immediately | Prevents duplicate claims |
| `bd update --status blocked` | **Yes** — immediately | Team visibility |
| `bd close` + `git push` | No | Pre-push hook handles it |
| `bd close` without push | **Yes** | No push = no hook |
| `bd note` / comment | Optional | Low urgency |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `bd status` shows 0 issues after session start | Run `bd backup fetch-git` explicitly |
| Duplicate bead discovered after creating | Close the new one: `bd close <new-id> --reason "Duplicate of <old-id>"`, link with `bd duplicate <new-id> <old-id>` |
| Teammate claimed same bead | Whoever claimed second: `bd update <id> --status open --json` to unclaim, defer to first claimer |
| `bd backup export-git` fails | Check `git remote -v` — needs `origin` with write access |
| Pre-push hook skips beads export | Hook only fires on code pushes (not tag/delete/beads-backup-only pushes) — export manually if needed |
