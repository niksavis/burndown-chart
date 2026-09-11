# basicly Migration Plan

**Status**: preparation complete, install **blocked pending `v0.12.1`**.
**Target version**: **`v0.12.1`** — not yet tagged; the engine session is cutting it
2026-09-11. **Pin the tag, not `@main`.**

> **Do not install `v0.12.0`.** No-go from the engine session, 2026-09-11, for three
> reasons:
>
> - Its **release page never published**, so `gh release view v0.12.0` 404s. The tag and
>   the `uvx` pin resolve fine — only the page is missing — but the project's rule is
>   that every release has one.
> - It is missing a **P0 fix** (`281ee287`): install left a retired managed hook wired
>   to a deleted script, after which **every commit in the consumer repo failed**. That
>   is precisely the blast radius we would have taken here.
> - It is missing `6e0663fd`, a build-time cap sized on a developer machine that fails
>   on `ubuntu-latest` — the reason the release workflow never reached its publish step.

**Scanned against**: the `basicly` working tree at `../basicly`, plus answers verified
empirically by the engine's own session, re-confirmed against `main` on 2026-09-11
(§6).

This document is the pre-flight for replacing this repository's hand-authored,
Copilot-centric agent configuration with a `basicly`-projected one, and for moving
issue tracking off `bd` (beads) onto the basicly-owned ledger.

Re-verify the "What install does" section against the actual release before running
install — it was read from the engine source, not from a shipped artifact.

**Upstream defects this plan is waiting on or working around** (filed by the engine
session; all tracked on their side, none to be patched locally):

| Id | Defect | Our exposure |
|---|---|---|
| `basicly-nv5qfl6` | `build` overwrites a pre-existing hand-authored `.github/copilot-instructions.md` silently | 273 lines; mitigated by the Phase 0b out-of-repo copy |
| `basicly-mmcqg8a` | `catalog lint` refuses until `[catalog] rank1_floor` is hand-set, and it is a pre-commit hook, so a fresh install cannot commit | blocks the first post-install commit until we edit `basicly.toml` |
| `basicly-npiudkl` | importer carried the source's `created_by` / `source_repo_path` into the ledger verbatim, which `tracker-path-scan` then refused | **fixed on `main`**; should not reach us on `v0.12.1` |

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

**Confirmed empirically against v0.12.0** by the engine session: install overwrites
this path **silently — no warning, no backup**. On a first install there is no manifest
entry, so install cannot distinguish "my own stale output" from "a file it has never
seen", and it does not try. The engine maintainers have raised this as a defect on their
side; it is **not fixed in v0.12.0**.

**Copy the file somewhere outside the repo before running install.** The git history is
a fallback, but an out-of-repo copy costs nothing and removes the "which commit was it
again" step. Then port the durable content into
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

> **Corrected 2026-09-10.** This section previously assumed no importer survived, and
> planned to hand re-file the 11 live records. **That was wrong, in our favour.**
> `basicly tracker import` is new in v0.12.0. The importer existed in the kit but had
> zero production callers and no CLI verb, which is why it read as unreachable from
> outside; v0.12.0 wires it up. **Do not re-file by hand.**

**Plan**: import the whole export, all 702 records.

```sh
basicly tracker import .beads/issues.jsonl --source beads --dry-run   # writes nothing
basicly tracker import .beads/issues.jsonl --source beads
```

Verified by the engine session against a beads-shaped export:

- **Source ids are preserved verbatim** — the property that matters most here, because
  our git history and commit-msg references (`burndown-chart-2rm1` etc.) keep resolving.
- `title`, `status`, `priority`, `issue_type`, `created_at`, `created_by`, `source_repo`
  and `compaction_level` carry over; unknown fields are imported verbatim, not dropped.
- Comments and dependency edges survive, edges keeping their type.
- Every event records `provenance: EXTRACTED`, `imported_from: <label>`, and the
  export's sha256 on each `created` event.
- **Replay-safe**: a re-run appended 0 events, so an import torn off at the tail
  completes rather than doubling.

Three deliberate refusals to plan around:

- It is an **upsert, never a sync**. A record the ledger already holds is not
  re-created; a field disagreement is reported and left alone.
- **Absence is never a deletion.** A record the snapshot no longer holds is named, not
  tombstoned. Use `--deleted <id>` for one confirmed out of band.
- An id the commit gate would refuse is **rejected by name**, not renumbered, with the
  rest of the export still landing. Read the report *and* the exit code — non-zero when
  anything was refused.

Gotcha: dependency edges must use `depends_on_id`, not `id`. Check what beads actually
exported before trusting the edge count, and always `--dry-run` first — it applies the
same id rule as the write, so it reports how many of our 702 would be refused before
anything is committed.

Import everything, not just the live records: the 691 closed records carry the history
we want, they **import as closed**, and the fold handles the statuses.

Two further properties, confirmed 2026-09-11:

- **Comment text is capped per field at write time** (`MAX_TEXT_BYTES`). A cut comment
  is not silently clipped: it is marked `<key>_truncated` with the original byte length
  recorded beside it, so the loss is visible as evidence.
- **`--dry-run` now exits non-zero when it reports a refusal**, which makes it usable as
  a scripted preflight rather than something whose output has to be read by eye.
- If a redaction problem ever does surface, `basicly tracker scrub` is now a
  first-class verb that repairs it in place (see `basicly-npiudkl`).

Then retire `bd` from all guidance: `agents.md`, `copilot-instructions.md`,
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

> **Version-critical.** `v0.12.0` shipped a P0 in exactly this area — install left a
> retired managed hook pointing at a deleted script, and **every subsequent commit in
> the consumer repo failed**. Fixed on `main` by `281ee287` and expected in `v0.12.1`.
> This is the single strongest reason not to install `v0.12.0` here.

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

**Action**: v0.12.0 adds `basicly install --overwrite-scaffolds`, which replaces
`.vscode/tasks.json` and `.github/workflows/basicly-gates.yml` with the current
templates and keeps each previous copy as a `.basicly-bak` sibling. Either run that as a
second pass and merge our own tasks back in from the `.basicly-bak`, or merge by hand.
Do **not** pass it on the first install — the first install has nothing to replace, and
we want our existing `tasks.json` intact as the merge base.

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
   Install will not overwrite them. **Done** — **12 fragments**, validated three ways:
   through basicly's own `load_fragments_from_roots` (the function `build` calls),
   against the shipped `fragment.schema.json`, and for id collisions against the
   packaged catalog's 23 core ids (no overlap).

   > **Schema validation alone is not sufficient — it gave a false pass.** `applies_to`
   > must be `all` or a registered target (`claude`, `codex`, `copilot`), but the JSON
   > schema accepts any string and `catalog lint` never checks it. Six of the original
   > eight fragments used routing-ish values (`rules`, `quality`, `style`, `review`,
   > `security`, `testing`) and were **unloadable** — they would have failed `install`
   > at step 10. Those values now live in `tags`. Reported upstream; validate any new
   > fragment through the loader, not the schema.

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
   | `python-environment` | commands | **new** — mandatory venv, direct-interpreter calls, no persisted shell state |
   | `data-architecture` | project | **new** — SQLite topology, the `jira_query_manager` seam, `profiles/` boundary |
   | `trunk-based-workflow` | commands | **new** — `main`-only, rebase locally, no remote PRs, never bypass a gate |
   | `app-release-process` | commands | **new** — changelog before `release.py`, and why the order matters |

   Two of these (`calculation-integrity`, `chart-presentation`) have no equivalent in
   the old instruction set. They encode the two areas this repo is most sensitive in,
   which the Copilot instructions never stated.

   The four added on 2026-09-11 carry durable content that was only ever recorded in
   files scheduled for deletion — the venv rule and terminal discipline from
   `copilot-instructions.md` §61-79 and §188-202, the data topology from
   `repo_rules.md` §94-101, the branch strategy from §222-234, and the release order
   from §235-244. Without them, deleting those files in Phase 2 loses real knowledge.

   Deliberately **not** ported, because basicly core or projection replaces them: the
   Copilot precedence and canonical-source policy, the customization inventory and the
   three discoverability index files, customization self-healing, the orchestration and
   subagent-routing sections, the self-evolving specialization loop, the beads workflow
   and priority system, and the mandatory-Context7 axiom (core's `external-facts`
   fragment covers its intent without naming a specific MCP server). The commit-format
   axiom is dropped too — core's `git-discipline` owns that, and the `bd-XXX` trailer it
   mandated is retired.

3. Freeze the beads live-record list (captured in §3.3 above). **Done.**

**Phase 0b — immediately before install. Done 2026-09-11.**

Recorded state at completion, all verified rather than assumed: backups taken at commit
`375ff70a`; `__pycache__/` present at `.gitignore:2` (step 5 was the predicted no-op);
`.basicly/`, `basicly.toml` and `AGENTS.md` all absent, confirming a genuine first
install; `.vscode/tasks.json` present, so step 8 of §1 will be skipped; `.venv` built
on Python 3.14.6 (the hooks refuse to run without one) and ignored at `.gitignore:139`;
8 overlay fragments intact. Pre-install test baseline captured green and matching the
documented figure — `1922 passed, 5 skipped, 3 xfailed` — so any post-install red is
attributable to the install rather than to pre-existing state.

4. Back up **every generated target that already exists**, outside the repo. Install
   destroys each silently (§3.1) — there is no manifest entry on a first install, so it
   cannot tell its own stale output from a file it has never seen:

   ```sh
   mkdir -p ~/burndown-chart-preinstall
   cp .github/copilot-instructions.md CLAUDE.md .vscode/tasks.json \
      ~/burndown-chart-preinstall/
   ```

   `.vscode/tasks.json` is backed up too. Install should only skip it, never touch it —
   the copy costs nothing and makes that assumption falsifiable instead of trusted.

   `CLAUDE.md` was added on 2026-09-10 as the interim agent entry point and is a
   `build` target, so it is exposed to the same defect. `AGENTS.md` does not exist yet
   (we have lowercase `agents.md`, a separate file — see §3.2).
5. Add `__pycache__/` to `.gitignore` if not already covered. The projected hook scripts
   are Python, and the `.gitignore` entry basicly writes covers only
   `basicly.local.toml`, so the first commit after install otherwise fails on modified
   files. *(Our `.gitignore` already has `__pycache__/` at line 2 — verify it still does,
   then this is a no-op.)*

**Phase 1 — install**

6. `uvx --from git+https://github.com/niksavis/basicly@v0.12.1 basicly install
   --technologies python,node`

   Confirmed correct as written by the engine session, including the decision **not** to
   pass `--overwrite-scaffolds` on a first run.
7. Set `[catalog] rank1_floor` in `basicly.toml` to **the number our own run prints** —
   not a value from basicly's docs, because the rate depends on the catalog this install
   lays down. Re-confirmed 2026-09-11: `catalog lint` refuses until it is set, and it
   runs as a **pre-commit hook**, so the first post-install commit is blocked until this
   is hand-edited (`basicly-mmcqg8a`). For calibration only — **do not copy these
   numbers** — the engine repo measures 41/46 = 89.1% against a floor of 85.0%, and
   their canary measured an identical rate, which suggests the shipped catalog dominates
   the figure rather than the consumer's own fragments. The engine session will confirm
   before the tag whether a scaffold-at-install fix makes `v0.12.1`; if it does, this
   step disappears.
8. Inspect the diff before staging anything. Confirm: nothing hand-authored was
   overwritten; `basicly check`, `basicly hooks-check`, `basicly status` all clean.

   **Watch `.pre-commit-config.yaml` specifically.** `hooks-build` writes the managed
   block *and activates it*, and this repo already has its own config plus its own
   `install_hooks.py`. The engine session flagged this as the highest-uncertainty
   interaction of the install and asked for the diff if it is not what we expect.
9. Merge basicly's VS Code tasks into ours (§3.6).

**Phase 2 — reorganize instructions**

10. Delete `agents.md` (§3.2).
11. Reduce `repo_rules.md` to whatever the fragments do not cover; delete if empty.
12. Retire the three discoverability index files
    (`copilot_customization.md`, `copilot_capability_map.md`, `context-routing-map.md`)
    — they index a precedence model that projection replaces.
13. Rebuild and confirm the generated instruction files read correctly.

**Phase 3 — tracker cutover**

14. `basicly tracker import .beads/issues.jsonl --source beads --dry-run`, read the
    report, then run it for real (§3.3). Check the exit code.
15. Replay `docs/improvement_backlog.md` (77 items) into the ledger via
    `basicly tracker write`, keeping the `IMP-###` ids in the record titles so the
    evidence in that document stays traceable.
16. Switch hooks (§3.4), retire `install_hooks.py`, remove beads skills/instructions/
    prompts.
17. Freeze `.beads/`.

**Phase 4 — dedupe CI** (§3.7). Note our own `lint.yml` now runs tests (as of
`dfa76aca`), so the overlap with `basicly-gates.yml` is larger than when this plan was
written — reconcile rather than run both.

---

## 5. Open questions

Questions 1–3 were answered empirically by the basicly engine session against v0.12.0
and are folded into the sections above.

1. ~~Is there a supported beads import path?~~ **Yes** — `basicly tracker import`, new in
   v0.12.0. See the corrected §3.3.
2. ~~Does `build` own `.github/copilot-instructions.md`?~~ **Yes, and it overwrites
   silently with no backup.** See §3.1.
3. ~~Which tag, and what changes for consumers?~~ **`v0.12.0`.** See §6.

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

---

## 6. What v0.12.0 changes for a consumer repo

Reported by the basicly engine session for this release. Items marked *unconfirmed* were
not verified by them and should not be treated as guarantees.

- **New**: `basicly tracker import` — the beads import path (§3.3). This is the change
  that most affects our plan.
- **New**: `basicly install --overwrite-scaffolds` replaces `.vscode/tasks.json` and
  `.github/workflows/basicly-gates.yml` with current templates, keeping each previous
  copy as a `.basicly-bak` sibling. Do not use on first install (§3.6).
- **New managed paths**: a `sessionstart` hook projects to both Claude Code and Copilot,
  plus a `headroom-guard` PreToolUse hook. A fresh install reports `git 11 / claude 6 /
  copilot 2` hook specs.
- **Renamed**: `.basicly/core/hooks/beads-commit-msg.py` → `tracker-commit-msg.py`.
  First install, so this costs us nothing.
- **Scoped**: `catalog-lint` is no longer `always_run` — it runs only when
  `.basicly/core/`, the overlay, or `basicly.toml` changed.
- **Changed**: `basicly check` now refuses outright when the installed catalog's version
  differs from the running engine, rather than comparing across versions and advising
  `basicly build`. Relevant when we upgrade later: pin consistently.
- **Ledger/tracker schema**: unchanged in this release *(unconfirmed — not verified
  across versions)*.
- **Engine dependencies**: four beyond jinja2/pyyaml — `markdown-it-py`, `jsonschema`,
  `rich`, `ruamel.yaml`. A missing one fails with a bare `ModuleNotFoundError`, so if
  install dies that way, this is why.

### Known defect — still open, tracked as `basicly-nv5qfl6`

Install overwrites a pre-existing hand-authored `.github/copilot-instructions.md`
silently — no warning, no backup, no manifest entry to distinguish it from stale
generated output. Unfixed as of 2026-09-11 and **next in the engine's queue**; the
engine session will confirm here when it lands.

The fix on the record is the one this session proposed: when a build target path already
exists and carries **no manifest entry**, write the existing bytes to
`<path>.basicly-bak` before overwriting. That covers `.github/copilot-instructions.md`,
`AGENTS.md` and `.claude/CLAUDE.md`, and correctly writes no backup on a repeat install,
where a manifest entry proves the file is basicly's own prior output.

Until it ships, the Phase 0b out-of-repo copy remains the mitigation — and it stays
worth keeping even afterwards, since `.basicly-bak` lives inside the repo.
