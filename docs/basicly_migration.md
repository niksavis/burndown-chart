# basicly Migration Plan

**Status**: preparation only. Nothing is installed yet.
**Blocked on**: a stable `basicly` release being cut. The engine's own session on
this machine has been asked to notify when a tag lands.
**Scanned against**: the `basicly` working tree at `../basicly`, README pin `v0.11.0`.

This document is the pre-flight for replacing this repository's hand-authored,
Copilot-centric agent configuration with a `basicly`-projected one, and for moving
issue tracking off `bd` (beads) onto the basicly-owned ledger.

Re-verify the "What install does" section against the actual release before running
install — it was read from the engine source, not from a shipped artifact.

---

## 1. What `basicly install` actually does

One idempotent command covers first install and every upgrade. From
`cli.cmd_install`, in execution order:

| # | Step | Writes | Overwrite risk |
|---|---|---|---|
| 1 | sync managed core | `.basicly/core/**` | none (new path) |
| 2 | migrate legacy layouts | — | none (no prior basicly install) |
| 3 | record install state | `.basicly/…` state file | none |
| 4 | create overlay + stubs | `.basicly-local/fragments/user/**` | **never overwrites** existing |
| 5 | scaffold config | `basicly.toml` | **only when absent** |
| 6 | scaffold local ignore | ignore entry for local config | additive |
| 7 | set up tracker | `.basicly/ledger/**` | none (new path) |
| 8 | scaffold VS Code tasks | `.vscode/tasks.json` | **only when absent** — see §3.6 |
| 9 | scaffold CI workflow | `.github/workflows/basicly-gates.yml` | **only when absent** |
| 10 | `build` | `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md` | **OVERWRITES** — see §3.1 |
| 11 | `skills-build` | `.claude/skills/**`, `.agents/skills/**` | per-skill-name |
| 12 | `agents-build` | `.claude/agents/*.md`, `.github/agents/*.agent.md` | per-slug |
| 13 | `hooks-build` | `.pre-commit-config.yaml` managed block + installs git hooks | merge — see §3.4 |
| 14 | `permissions-build` | `.claude/settings.json` deny-list | ensure-present, additive |

### Deletion safety

Projected agent and skill files carry a generated marker. Pruning
(`agents.orphaned_projections`, `skills._prune_skill_dir`) only ever deletes files
carrying that marker — *"a file a consumer hand-authored under a projected name is
theirs"*. So our 12 hand-authored `.github/agents/*.agent.md` and 16
`.github/skills/**` are **not at risk of deletion**.

They *are* at risk of **overwrite on a name collision**, because the write path for a
selected agent calls `sync_file` unconditionally. Collision check performed:

- basicly agent slugs: `architect auditor curator decider decomposer implementer
  researcher retrospector reviewer tester validator`
- ours: `beast-mode-agnostic context7-expert critical-thinking custom-agent-foundry
  development-environment-bootstrap github-actions-expert janitor layering-enforcer
  refactor-execution release-readiness repo-quality-guardian test-strategy`
- **No overlap.** Same result for skills (`release-process` vs our
  `release-management`, `repair-in-place` vs our `refactor` — near, but distinct).

Note: `.github/skills/` is in basicly's `RETIRED_SKILL_ROOTS`. It is scanned for
pruning, but again marker-guarded, so our hand-authored skills survive. Whether
Copilot still reads that root is a separate question to settle in §4.

### Prerequisites (already satisfied here)

- Python **3.14+** — this machine has 3.14.6; `pyproject.toml` already targets `py314`.
- `uv` on `PATH` — 0.12.5 present.
- Every committer needs both, because the projected git hooks shell out to
  `uv run python`. `basicly hooks-check` diagnoses a missing `uv`.

---

## 2. Current state inventory

### Agent configuration surface (all hand-authored, Copilot-centric)

| Path | Lines / count | Disposition |
|---|---|---|
| `.github/copilot-instructions.md` | 273 | **port to overlay fragments, then let install own the path** |
| `agents.md` (lowercase) | 215 | mostly obsolete beads boilerplate — delete; see §3.2 |
| `repo_rules.md` | 151 | split: durable rules → fragments; the rest → delete |
| `.github/instructions/*.instructions.md` | 16 | map to path-scoped rules or overlay fragments |
| `.github/agents/*.agent.md` | 12 | keep as-is initially; cull against basicly's 11 later |
| `.github/skills/**/SKILL.md` | 16 | keep; several are beads-specific and die with beads |
| `.github/prompts/*.prompt.md` | 8 | keep; no basicly equivalent |
| `.github/hooks/**` | 8 profiles | review against basicly's agent hooks |
| `.github/copilot_customization.md` | 144 | index of the above; regenerate or delete |
| `.github/copilot_capability_map.md` | 206 | same |
| `.github/context-routing-map.md` | 356 | same |

### Tracker

`.beads/issues.jsonl` — 702 records: **691 closed, 8 open, 3 in_progress**.

### Quality gates

- `.pre-commit-config.yaml`: ruff-check, ruff-format, bandit, djlint-jinja, prettier,
  markdownlint, detect-secrets.
- `install_hooks.py` writes hooks directly into Git's hooks dir (pre-commit,
  commit-msg, pre-push, post-merge, post-rewrite, post-checkout,
  prepare-commit-msg). **Currently not installed in this checkout.**
- `validate.py` is the pre-push gate (ruff, djlint, pyright, markdownlint, pytest).
- `.github/workflows/`: `lint.yml`, `release.yml`.

---

## 3. Collisions and how each is handled

### 3.1 `.github/copilot-instructions.md` — overwritten

This is the only true content-loss risk. Install's `build` step owns this path and
renders it from fragments.

**Action before install**: port the durable content into
`.basicly-local/fragments/user/**` overlay fragments (install never touches the
overlay). Content triage:

| Section | Destination |
|---|---|
| Core Axioms 5 (layering), 6 (no customer data), 7 (test isolation), 8 (no emoji) | overlay fragment — durable repo policy |
| Layered Architecture, Architecture Guides table (file/function size limits) | overlay fragment, `category: boundaries` |
| Code Standards (type hints, naming, logging, perf budgets) | overlay fragment |
| Security and Data Safety | overlay fragment, `category: security` |
| Dependency Onboarding (`pip-compile` workflow) | overlay fragment, `category: commands` |
| Testing (pytest paths, Playwright not Selenium) | overlay fragment, `category: testing` |
| Documentation Index | overlay fragment, `category: project` |
| Venv Rule, Terminal Behavior, platform/shell tables | **drop** — basicly ships tool skills and `uv`-based invocation; the Windows/Git Bash tables are stale here |
| Axiom 4 (CONTEXT7 mandatory) | decide — see §5 open questions |
| Orchestration Workflow, Default Subagent Routing, Self-Evolving Loop | **drop** — basicly's loop replaces this wholesale |
| Copilot Customization Precedence / Inventory / Discoverability | **drop** — projection replaces the precedence model |
| Beads Workflow, Commit Rules `(bd-XXX)`, Priority System | **drop** — replaced by the ledger and basicly's commit envelope |
| Context Metrics Source | decide — basicly has its own measured-context machinery |

Known drift to fix while porting, not carry over: the header says **"Python 3.13 …
Platform: Windows"**; the repo targets **py314** and is being worked on WSL/Linux.
The file also declares a `<1200 tokens` budget and is 273 lines.

### 3.2 `agents.md` vs generated `AGENTS.md` — case collision

On this case-sensitive filesystem both would coexist and both would be read, giving
agents two conflicting instruction files. `agents.md` is already 60% beads
boilerplate that dies with the tracker migration, and it self-describes as a
compatibility shim for a file basicly will now generate.

**Action**: delete `agents.md` in the same change that installs basicly. Note this
also breaks the repo's own "no uppercase letters in repository filenames" rule from
`copilot-instructions.md` — basicly's `AGENTS.md` is a fixed, tool-mandated name, so
that rule needs an explicit carve-out when it is ported.

### 3.3 `.beads/` → `.basicly/ledger/`

basicly deleted its own `.beads/` after a bespoke one-time import; the
`external`→`dual`→`owned` ladder collapsed to `owned` and the other two modes were
removed. **Assume no supported importer exists** (confirmation requested from the
engine session).

**Plan**: freeze, don't convert.

1. Keep `.beads/issues.jsonl` as frozen history (rename to make it obviously inert,
   or leave in place and stop writing to it).
2. Re-file only the **11 live records** by hand via `basicly tracker write`,
   preserving the one dependency chain:
   `xmd7 → ldjf → h322 → af47` (Flow Analysis).
3. Retire `bd` from all guidance: `agents.md`, `copilot-instructions.md`,
   `repo_rules.md`, `.github/skills/beads-schema-repair`,
   `.github/skills/beads-workflow`, `.github/instructions/beads-onboarding.*`,
   `.github/prompts/beads-setup.prompt.md`, and the beads hooks in `install_hooks.py`
   (`post-checkout`, `prepare-commit-msg`).
4. Commit convention changes from `type(scope): description (bd-XXX)` to whatever
   `basicly commit` assembles — the commit-msg hook is the enforcement point, so this
   must land together with the hook change, not before it.

**Live records to re-file** (frozen 2026-09-10):

```
in_progress p1 chore   burndown-chart-2rm1  Prepare and publish release
in_progress p2 task    burndown-chart-v053  Introduce domain exception hierarchy in data layer
in_progress p3 task    burndown-chart-dbgp  Eliminate lazy imports to fix circular dependencies
open        p1 feature burndown-chart-xmd7  Flow Analysis: per-item status path computation      (3 dependents)
open        p1 feature burndown-chart-ldjf  Flow Analysis: UI components for item path view
open        p1 feature burndown-chart-h322  Flow Analysis: callback, tab registration, wire-up
open        p1 feature burndown-chart-af47  Flow Analysis: report section for manager narrative
open        p1 feature burndown-chart-kup9  Make dramatic visual changes to theme
open        p1 feature burndown-chart-17xv  Configurable Working Schedule for Teams
open        p1 feature burndown-chart-gkdo  Extend MTTR card with Lead Time and Cycle Time metrics
open        p4 task    burndown-chart-lquw  Add per-layer coverage targets to CI gate
```

### 3.4 Git hooks — two competing installers

basicly's `hooks-build` wires gates through the pre-commit framework and installs the
git hooks. This repo installs hooks directly via `install_hooks.py`. Both want to own
`.git/hooks/pre-commit`, `commit-msg`, and `pre-push`.

`hooks-build` *merges a managed block into the hook config preserving foreign hooks*,
so the seven existing `.pre-commit-config.yaml` entries survive. The conflict is the
hook **installer**, not the config.

**Action**: basicly wins on the three shared stages. Port what `install_hooks.py`
uniquely provides:

- pre-push `validate.py` → declare as a check in basicly's verify gate
  (`basicly verify --mode full`), which is the intended seam.
- `post-merge` / `post-rewrite` hook self-refresh → obsolete; re-running install is
  the upgrade path.
- `post-checkout` / `prepare-commit-msg` → beads-only; delete with §3.3.

Then retire `install_hooks.py`. Do this as a separate, verifiable commit — a
half-migrated hook set is worse than either end state.

### 3.5 `.pre-commit-config.yaml` — low risk

Managed-block merge, foreign hooks preserved. Verify with `basicly hooks-check` after
install; no prep needed.

### 3.6 `.vscode/tasks.json` — silently skipped

We already have one, so install prints *"left unchanged"* and **we do not get the
basicly tasks**. This is easy to miss.

**Action**: after install, manually merge the basicly task entries into our
`tasks.json`. (Diff against a scratch `basicly install` in an empty repo to see what
we would have got.)

### 3.7 CI — additive

`basicly-gates.yml` is a new filename; `lint.yml` and `release.yml` are untouched.
Expect overlap between `lint.yml` and the basicly drift/verify gate — dedupe after
install, not before.

---

## 4. Sequencing

Each step is a separate commit; the repo stays working at every boundary.

**Phase 0 — before install (can be done now)**

1. This document. **Done.**
2. Author overlay fragments under `.basicly-local/fragments/user/` per §3.1 triage.
   Install will not overwrite them. **Done** — 8 fragments, all validated against
   `fragment.schema.json`:

   | Fragment | Category | Carries |
   |---|---|---|
   | `project-overview` | project | stack, entry point, what each package is for |
   | `layered-architecture` | boundaries | the four-layer rule + allowed import direction |
   | `calculation-integrity` | boundaries | **new** — no fabricated numbers, degenerate-case rules, one-metric-one-implementation |
   | `chart-presentation` | design | **new** — forecast vs actual distinguishability, zero baselines, empty states |
   | `repo-code-standards` | code-style | size limits, typing, logging, no-emoji, `validate.py` |
   | `testing-standards` | testing | pytest, tempdir isolation, Playwright, assert-the-value |
   | `dependency-onboarding` | commands | the `pip-compile` workflow |
   | `data-safety` | security | customer-data ban, placeholders, parameterized SQL |

   Two of these (`calculation-integrity`, `chart-presentation`) have no equivalent in
   the old instruction set. They encode the two areas this repo is most sensitive in,
   which the Copilot instructions never stated.

3. Freeze the beads live-record list (captured in §3.3 above). **Done.**

**Phase 1 — install (blocked on release)**

4. `uvx --from git+https://github.com/niksavis/basicly@<tag> basicly install
   --technologies python,node`
5. Inspect the diff before staging anything. Confirm: nothing hand-authored was
   overwritten; `basicly check`, `basicly hooks-check`, `basicly status` all clean.
6. Merge basicly's VS Code tasks into ours (§3.6).

**Phase 2 — reorganize instructions**

7. Delete `agents.md` (§3.2).
8. Reduce `repo_rules.md` to whatever the fragments do not cover; delete if empty.
9. Retire the three discoverability index files
   (`copilot_customization.md`, `copilot_capability_map.md`, `context-routing-map.md`)
   — they index a precedence model that projection replaces.
10. Rebuild and confirm the generated instruction files read correctly.

**Phase 3 — tracker cutover**

11. Re-file the 11 live records (§3.3).
12. Switch hooks (§3.4), retire `install_hooks.py`, remove beads skills/instructions/
    prompts.
13. Freeze `.beads/`.

**Phase 4 — dedupe CI** (§3.7).

---

## 5. Open questions

Sent to the basicly engine session; answer before Phase 1.

1. Is there any supported import path from an external `.beads/issues.jsonl` into
   `.basicly/ledger/`, or is hand re-filing the intended route?
2. Confirm `build` owns `.github/copilot-instructions.md` on a repo that already has
   a hand-authored one (i.e. port-first is required).
3. Which release tag to pin, and whether that release changes any consumer-repo
   install behaviour listed in §1.

Not blocking, decide locally:

4. ~~Keep the mandatory-Context7 axiom?~~ **Resolved.** basicly core ships a
   `decisions` fragment — *"Fetch a third-party interface fact instead of recalling
   it"* — plus an `interface-facts` skill, which covers the axiom's intent without
   naming a specific MCP server. Drop our version; keep the `context7-expert` agent
   if the MCP server stays wired up.
5. Keep the repo's `codebase_context_metrics` artifacts, or defer to basicly's own
   measured-context machinery?
6. Cull our 12 Copilot agents against basicly's 11 projected ones — several look
   redundant (`repo-quality-guardian` ≈ `auditor`, `test-strategy` ≈ `tester`,
   `refactor-execution` ≈ `implementer`), but the projected set is loop-shaped and
   ours are Copilot-shaped, so this needs a real read, not a name match.
