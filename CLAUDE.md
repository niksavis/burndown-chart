# burndown-chart — agent guide

> **Interim file.** `basicly install` generates this path from catalog fragments and
> will overwrite it **silently, with no backup**. Back it up out-of-repo first, and
> port anything durable into `.basicly-local/fragments/user/` beforehand — that overlay
> is never touched by install. See `docs/basicly_migration.md` §3.1.

## What this is

An agile delivery dashboard: burndown/burnup charts, velocity and completion
forecasting, DORA metrics, flow metrics, bug analytics — from Jira or imported tabular
data. Python 3.14+, Dash 4 + Plotly 6 on Waitress, pandas 3 / numpy 2 / scipy, SQLite,
Pydantic. Entry point `app.py`. Current release v2.15.3.

Layers, dependencies pointing downward only: `callbacks/` routes events → `data/` holds
business logic and calculations → `visualization/` builds figures → `ui/` renders.
`data/` imports none of the other three.

## Read these first

| Document | What it is |
| --- | --- |
| **`docs/improvement_backlog.md`** | **The work queue.** 77 items in 5 waves, from four specialist audits (2026-09-10), with a measured baseline and a change-safety map per package. Start here. |
| **`docs/basicly_migration.md`** | Plan for replacing this repo's hand-authored Copilot config with a `basicly`-projected one, and migrating the tracker. Not yet executed. |
| `docs/architecture/` | Architecture standards and per-language guidelines. |
| `docs/metrics_index.md` | What each metric means and how it is calculated. |

## Current state (2026-09-10)

**Wave 0 of the backlog is complete.** Before it, no automated gate ran the test suite —
CI stopped at pyright, `release.py` gated on lint only, and `tests/integration/` was
executed by nothing. It now runs everywhere and is deterministic:

    1922 passed, 5 skipped, 3 xfailed, 0 errors   (identical serial and -n auto)

The 3 `xfail(strict=True)` tests are genuine product bugs, tagged `IMP-005`. Strict
means fixing one turns CI red until you remove the marker — that is intended.

**Where to continue**, in the order recommended to the maintainer:

1. **Install basicly v0.12.0** — `docs/basicly_migration.md` is ready to execute. Do
   Phase 0b (the out-of-repo backups) first.
2. **Wave 1** — verified wrong numbers reaching users. The maintainer has approved
   fixing these *and* documenting each in the changelog, because several change values
   users already read (correcting the budget health polarity turns a currently-green
   dashboard red — correctly).
3. **Wave 2** — first-run configuration blockers. Note the setup checklist a novice
   needs is already fully written in `ui/config_status_panel.py` and simply never
   mounted.

## Where the risk is

Ranked by the maintainer, and confirmed by the audits:

1. **Calculations** (`data/`) are the most sensitive thing here — wrong numbers that
   look plausible are worse than a crash, because nobody investigates them. The audit
   found the same quantity implemented 2–4 times with copies that disagree, and absent
   data laundered into confident output. Read
   `.basicly-local/fragments/user/boundaries/calculation-integrity.fragment.yaml`
   before touching this layer.
2. **Visualization** (`visualization/`) — a correct number presented misleadingly does
   the same damage. See
   `.basicly-local/fragments/user/design/chart-presentation.fragment.yaml`.
3. **First-run UX** — novice users get stuck configuring the app. Wave 2.

`docs/improvement_backlog.md` carries a per-package safe/caution/danger rating. Consult
it before refactoring: `updater/` is at 0% coverage, `callbacks/` at 21%, and
`data/budget_calculator_consumption.py` and `_comparison.py` have **no test importing
them at all**.

## Working here

- **Set up an environment first** — there is no committed `.venv`, and the git hooks now
  refuse to run without one:

      python -m venv .venv
      .venv/bin/pip install -r requirements.txt -r requirements-dev.txt

- `python validate.py` runs ruff, djlint, pyright, markdownlint and pytest in one pass.
  Run it before pushing. `python install_hooks.py` installs the git hooks.
- Trunk-based: `main` is the only long-lived branch, integrate by rebasing locally, no
  remote PRs.
- Never weaken or skip a gate to make it pass. Fix the gate.

## Stale guidance — do not follow

`agents.md`, `repo_rules.md` and `.github/copilot-instructions.md` still document a
**`bd` (beads) workflow that is retired**: `bd ready`, `bd create`, `bd close`,
`bd backup export-git`, and a commit convention requiring a `(burndown-chart-XXXX)`
trailer. The tracker has been inert since 2026-05-05 and `bd` is not necessarily
installed. Do not file work with `bd`.

Until the migration runs, record new work in `docs/improvement_backlog.md` using the
existing `IMP-###` numbering. Afterwards it moves to `basicly tracker`, and the whole
702-record beads history imports in one command (`docs/basicly_migration.md` §3.3).

Those three files also predate the current stack in places — `.github/copilot-instructions.md`
still says "Python 3.13, Platform: Windows" while the repo targets `py314` and is
developed on WSL/Linux. They are scheduled for deletion or replacement in Phase 2 of the
migration.
