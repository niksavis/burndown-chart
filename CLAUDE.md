# burndown-chart — agent guide

**Not a generated file.** basicly projects `.claude/CLAUDE.md`, `AGENTS.md` and
`.github/copilot-instructions.md`; this path is not one of its targets, so it survives
`basicly install` untouched. Claude Code loads this file **and** `.claude/CLAUDE.md`, so
keep this one short and specific to the current state of the work — the standing rules
live in fragments, not here.

**To change a standing rule, edit the fragment, not the projection.** Repo-specific rules
are 13 fragments under `.basicly-local/fragments/user/`, which install never overwrites.
Run `basicly build` after editing; `basicly check` reports drift. Editing a generated file
directly is lost on the next build.

## Where the work is tracked

`basicly tracker` over the append-only ledger in `.basicly/ledger/`. `bd` (beads) is
**retired** — the whole 702-record history was imported on 2026-09-11 and `.beads/` is
now an archive.

Record ids changed in that import. The ledger's id grammar allows a hyphen only as the
prefix/suffix separator, so the `burndown-chart` prefix was unrepresentable and every id
was refused verbatim. The prefix is now `burndownchart`: a `burndown-chart-2rm1` trailer
in git history is `burndownchart-2rm1` in the ledger. **That one hyphen is the whole
mapping.**

    basicly tracker ready        # what is unblocked, ranked
    basicly tracker stats        # 702 records: 691 closed, 3 in_progress, 8 open
    basicly tracker show <id>

Commits are gated: `type(scope): lowercase description (burndownchart-xxxx)`, and the id
must exist in the ledger. The `conventional-commits` skill has the full rules.

## Read these first

| Document | What it is |
| --- | --- |
| **`docs/improvement_backlog.md`** | **The audit evidence.** 77 items in 5 waves from four specialist audits (2026-09-10), with a measured baseline and a per-package change-safety map. The items are now ledger records (`burndownchart-impNNN`); this document keeps the reasoning and the evidence the ledger has no field for. |
| `docs/basicly_migration.md` | The migration record. Phases 0-1 and 3 are executed; Phase 2 (retiring the stale instruction files) and Phase 4 (deduping CI) are not. |
| `docs/architecture/` | Architecture standards and per-language guidelines. |
| `docs/metrics_index.md` | What each metric means and how it is calculated. |

## Current state

Test baseline, unchanged across the basicly install and verified either side of it:

    1922 passed, 5 skipped, 3 xfailed, 0 errors   (identical serial and -n auto)

The 3 `xfail(strict=True)` tests are genuine product bugs, tagged `IMP-005`. Strict means
fixing one turns CI red until you remove the marker — that is intended.

**Where to continue**, in the order recommended to the maintainer:

1. **Wave 1** — verified wrong numbers reaching users. The maintainer has approved fixing
   these *and* documenting each in the changelog, because several change values users
   already read (correcting the budget health polarity turns a currently-green dashboard
   red — correctly).
2. **Wave 2** — first-run configuration blockers. The setup checklist a novice needs is
   already fully written in `ui/config_status_panel.py` and simply never mounted.

## Where the risk is

Ranked by the maintainer, and confirmed by the audits:

1. **Calculations** (`data/`) are the most sensitive thing here — wrong numbers that look
   plausible are worse than a crash, because nobody investigates them. The audit found the
   same quantity implemented 2-4 times with copies that disagree, and absent data
   laundered into confident output. The `calculation-integrity` fragment is the rule set.
2. **Visualization** (`visualization/`) — a correct number presented misleadingly does the
   same damage. See the `chart-presentation` fragment.
3. **First-run UX** — novice users get stuck configuring the app. Wave 2.

`docs/improvement_backlog.md` carries a per-package safe/caution/danger rating. Consult it
before refactoring: `updater/` is at 0% coverage, `callbacks/` at 21%, and
`data/budget_calculator_consumption.py` and `_comparison.py` have **no test importing them
at all**.
