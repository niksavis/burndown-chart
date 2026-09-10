# Improvement Backlog

Compiled 2026-09-10 from four specialist audits (calculations, visualization, first-run
configuration, engineering health). Findings are merged and de-duplicated across audits —
where several audits hit the same root cause, there is one item here, not three.

**Status: staged, not filed.** `bd` is not installed on this machine and the last
`.beads/issues.jsonl` write was 2026-05-05, so the beads tracker is already inert. These
replay into the basicly ledger via `basicly tracker write` after install
(see `docs/basicly_migration.md`). IDs are local to this file and stable — keep them in the
ledger record titles so evidence stays traceable.

**Confidence.** Items marked **[V]** were independently verified in this session by reading
the code or running the function. Items marked **[A]** come from an audit agent's own
verification and were not re-checked. Nothing here is speculative — items the audits flagged
as suspected-only were dropped.

---

## The four root causes

Most of the 47 items below are symptoms of four underlying problems. Fixing symptoms
individually will not hold.

**A — The same quantity is implemented many times, and the copies have drifted.**
Velocity has 4 implementations; deadline probability 2 (which disagree by ~6pp); velocity CV
3 (two with different `ddof`); the weekly items/points chart family 4 (≈1,900 LOC, drifted in
3); scope calculation 2 (byte-identical, both live). The dashboard, the exported report, and
the recommendation engine routinely disagree about the same number for the same data.

**B — Absent data is laundered into a confident answer.**
Missing weeks become real zeros; missing velocity becomes a hardcoded 75%; one data point
becomes 100% confidence; zero velocity renders as a green "0.0 days" and a completion date of
today; auto-detection of zero fields reports success in green. Nothing looks broken, which is
what makes this the most dangerous class here.

**C — The gates do not gate.**
CI runs no tests. `release.py` gates on lint only. `validate.py` runs `tests/unit/` only.
Therefore `tests/integration/` is executed by nothing automated — and it currently has 18
failures. The dead-code gate is configured to pass, and the coverage number hides 2,992
statements.

**D — Roughly 8% of the tree is dead, including the fix for one of the worst UX problems.**
70 of 490 non-test modules have zero inbound imports. Among them: a complete, working
first-run setup checklist that is never mounted.

---

## Wave 0 — Make the gates real

Cheap, low-risk, and it makes every later wave verifiable. Do this first; nothing else here
is safely measurable until it lands.

| ID | Item | Sev | Eff |
|---|---|---|---|
| IMP-001 **[V]** | **Add pytest to CI.** `.github/workflows/lint.yml` ends at the pyright step — no pytest, no coverage, no pip-audit. Add the suite; mark the known-red integration tests `xfail` in the same change so the gate goes green honestly instead of being ignored. | Critical | S |
| IMP-002 **[V]** | **Gate `release.py` on the full suite.** `release.py:552` runs `validate.py --fast` (ruff + pyright only), so a tag can be cut with a red suite. | Critical | S |
| IMP-003 **[V]** | **Widen `validate.py`'s default gate** (`validate.py:219`) to include `tests/integration/`, add `--cov=callbacks`, and ratchet `--cov-fail-under` from 44 to the measured value. | Critical | S |
| IMP-004 **[A]** | **Fix the integration SQLite fixture.** All 15 errors share one root cause: the temp DB is used before schema init (`sqlite3.OperationalError: no such table: profiles`). One fixture change, no production code. Unblocks 15 tests covering import/export and credential stripping. | Critical | S–M |
| IMP-005 **[A]** | **Fix the 3 real integration failures**: `test_empty_points_field_workflow` (`assert 161 == 30` — unfiltered `total_items`), `test_cache_invalidation_votes_to_empty`, `test_user_story_3_historical_review`. | High | M |
| IMP-006 **[A]** | **Resolve cross-test state leakage.** Serial and `-n auto` produce *different* pass sets (3F/15E vs 4F/1E) on identical code — shared SQLite/profile state. Results are currently untrustworthy in both directions. | High | M |
| IMP-007 **[A]** | **Fix the vulture config so it detects dead code.** `paths` excludes `callbacks/`, `utils/`, `updater/`, `configuration/`, and 14 of 26 `ignore_names` excuse exactly what dead code is. It reports 0 because it is calibrated to. Pair with Wave 5. | High | S |
| IMP-008 **[A]** | **Shrink the coverage `omit` list** (`pyproject.toml`): 45 files ≈ 2,992 statements hidden, and 2 entries point at deleted files. The number will drop below 44% — that is the point. Re-baseline honestly. | High | S |
| IMP-009 **[A]** | **Collect the orphaned tests.** `testpaths` excludes `tests/visual/`, `tests/utils/` and 3 root `tests/test_*.py` — 33 test functions never run. | Medium | S |
| IMP-010 **[A]** | **Hooks fail open.** `install_hooks.py:152,189` `exit 0` silently when `.venv` is absent — the exact state this clone was in — and `.git/hooks/` currently has no hooks installed. The deterministic floor does not exist on a fresh clone. Overlaps the basicly hook migration; see `docs/basicly_migration.md` §3.4. | High | S |

## Wave 1 — Wrong numbers reaching users

Every item is a verified incorrect value on a surface someone plans against. These are the
reason this backlog exists.

| ID | Item | Sev | Eff |
|---|---|---|---|
| IMP-011 **[V]** | **Budget health tiers have inverted polarity.** `budget_calculator_comparison.py:243-245`. `_calculate_health_tier` normalizes "positive = bad", then `inverse=True` negates it. 246% over pace → **green**; 35.8% under budget → **red**; runway 0.0 weeks → **green**. All three tiers wrong. ⚠ Fixing this turns green dashboards red — correctly. Needs a release note. | Critical | S |
| IMP-012 **[A]** | **Budget consumption rewrites spend history.** `budget_calculator_consumption.py:101` multiplies *all-time* completed items by a cost-per-item derived from *trailing-4-week* velocity. True €100k/77% renders as **€420,000 / 323%**. | Critical | M |
| IMP-013 **[A]** | **Budget revisions double-count.** `budget_calculator_core.py:162` replays revision deltas onto settings that `_save.py:187` already updated; the inflated value becomes the next baseline, compounding per edit. ⚠ Stored data is already corrupted — recalculation alone will not repair it; needs a data-repair step. | Critical | M |
| IMP-014 **[A]** | **Absent snapshots averaged in as zero-delivery weeks.** `processing_averages.py:118` + `metrics_snapshots.py:452`: `get_metric_weekly_values` returns 0 for weeks with no snapshot, and the caller only falls back when *all* are 0. 3 weeks of 12 items over a 10-week window → **avg 3.46, median 0.0** instead of 12/12. | Critical | M |
| IMP-015 **[V]** | **Zero-delivery weeks dropped from PERT rates.** `processing_rates.py:132`. Note this is deliberate — there is a comment justifying it — but the rationale covers zeros *synthesized by `_fill_missing_weeks`* and cannot distinguish those from genuine stall weeks. So the forecast assumes the team never stalls, while the velocity card (which does not filter) reports half the rate on the same data. Weeks `[10,0,10,0,10,0,10,0]` → 70-day forecast vs an honest 140. **Decide the intended semantics before editing.** | Critical | M |
| IMP-016 **[A]** | **Health score divides by a constant that ignores absent signals.** `project_health_calculator.py:516` uses a hardcoded `max_points=100` per dimension; Efficiency signal 3 (25 pts, `:559`) was never implemented. Flawless inputs score **55.0**; a perfect project caps at **94**. | Critical | M |
| IMP-017 **[A]** | **On-track probability is a hardcoded literal.** `ui/dashboard/__init__.py:244,255` returns literal `75` or `25` whenever `velocity_std == 0` — always true below 4 stats rows. Rendered as a computed statistic. | Critical | S |
| IMP-018 **[A]** | **NaN survives the guards in the enhanced stats path.** `ui/dashboard_enhanced/stats.py:201`: `std()` of one sample is NaN, which passes `== 0` checks and gets clamped by `max`/`min`. One data point + deadline tomorrow + 500-day forecast → **probability 100.0%**; `ci_80 == ci_95 == 0` while `ci_50 == 500` (monotonicity violated); `velocity_mean == 0` → fabricated 50%. | Critical | M |
| IMP-019 **[A]** | **Deployment frequency has no date filter.** `data/dora/_deploy_frequency.py:169`: numerator counts every deployment ever, denominator is the window length. 3 deploys this week + 7 from last year → **10.0/week, "elite"** instead of 3.0/week, "high". Correct duplicate exists at `data/metrics/_weekly_dora_prep.py:56`. | High | S |
| IMP-020 **[V]** | **Lead-time p95 is one rank too high.** `data/dora/_lead_time.py:196`: `sorted(x)[int(n*0.95)]` returns the maximum for many n. Lead times 1..20 days → p95 = 480h (the max) instead of 457.2h. | High | S |
| IMP-021 **[A]** | **Story points truncated to integers.** `data/jira/scope_calculator.py:264` coerces with `int()`. 2.5+3.5+0.5 → total 5 / completed 2 / remaining 3, instead of 6.5/2.5/4.0. A 23% scope understatement for any team using half-points. | High | S |
| IMP-022 **[A]** | **Change-failure rate counts any non-zero value as a failure.** `data/dora/_change_fail_rate.py:204`: `or bool(change_failure_value)` overrides the configured failure value. Field values `[7, 0]` with failure value 1 → **CFR 50%** instead of 0%. | High | S |
| IMP-023 **[A]** | **Calendar year + ISO week produce colliding bucket keys.** `processing_averages.py:239`, `processing_statistics.py:107`, `processing_weekly_forecast.py:99`, `processing_core.py:223` + 4 mirrors in `visualization/weekly_chart_*.py`. `2019-01-02` and `2019-12-30` both bucket to `2019-W01` — data 52 weeks apart summed into one week. | High | M |
| IMP-024 **[A]** | **Report velocity uses Sunday-based, calendar-year weeks.** `processing_core.py:200` buckets with `strftime("%Y-%U")` despite a docstring claiming ISO/Monday. This is the velocity in the exported HTML report (`data/report/domain_metrics.py:66`), so the report and the app disagree across every week boundary. | High | S |
| IMP-025 **[A]** | **Health card wired to keys the calculator does not read.** `ui/dashboard_cards.py:547` passes `items_completion_pct`/`points_completion_pct`; the calculator reads `completion_percentage`. Completion is therefore always 0 and stage always "inception" — a finished, ahead-of-schedule project scores 57/"inception" against 70/"late" from the correct path. | High | S |
| IMP-026 **[A]** | **Budget signals read a key no producer emits.** `data/recommendations/budget_signals.py:25` reads `utilization_percentage`; the dashboard emits `consumed_pct` and the report `consumed_percentage`. Utilization silently defaults to 0, so `budget_critical`/`budget_alert` are unreachable — 95% consumed renders "budget_healthy / 0% consumed". The test invents the phantom key, so it passes. | High | S |
| IMP-027 **[A]** | **Bug resolution rate mixes populations.** `data/bug_processing.py:339`: denominator is bugs *created* in-window, `open_bugs` is all-time, so `open + closed != total`. | High | S |
| IMP-028 **[A]** | **`generate_week_range` drops the final ISO week.** `data/time_period_calculator.py:268` steps in raw 7-day increments; `(2025-10-04, 2025-10-06)` → `['2025-W40']`, missing W41. | High | S |
| IMP-029 **[A]** | **Flow Time snapshot writes median into the mean field.** `data/metrics/_weekly_flow.py:261` also hardcodes `p85_days: 0` and reports `completed_count` for all completed issues though the median covered only those with both transitions. | High | M |
| IMP-030 **[A]** | **More data yields a less confident forecast.** `data/metrics/forecast_calculator.py:98`: exactly 4 weeks → recency-weighted, labelled "established"; 5+ weeks → unweighted mean, labelled "building". `[10,10,10,40]` → 22.0/"established"; `[10,10,10,10,40]` → 16.0/"building". | Medium | S |
| IMP-031 **[A]** | **Two live scope-baseline formulas disagree.** `data/scope_metrics.py:234` vs `callbacks/.../tab_content.py:348` — 100 vs 80 items, 20.0% vs 25.0% change rate. | High | M |
| IMP-032 **[A]** | **Chart and card use different window boundaries.** `visualization/data_preparation.py:350` filters `>= cutoff`; the three `data/processing_*` filters use `> cutoff`. The same slider gives the chart 11 weeks and the velocity card 10. | Medium | S |
| IMP-033 **[A]** | **`ci_80` is not a percentile.** `ui/dashboard/__init__.py:315` sets `"ci_80": pert_time_items` "for compatibility". Labelled as an 80% confidence bound in the UI. | High | S |
| IMP-034 **[A]** | **Dormant landmines — unreachable today, wrong when reached.** `processing_dashboard.py:138,230` uses `pert_factor` (a sample-window *count*, 3–12) as a *multiplier* (420 days where 70 is correct); `processing_statistics.py:225` `astype(int)` truncates points; `dora_metrics_calculator.py:503,563` swaps hours/days (48h MTTR persists as 2.0). All currently reachable only from tests. Fix or delete — do not leave armed. | Medium | M |

## Wave 2 — First-run blockers

The maintainer's question was whether novice setup failure is the UI's fault. It largely is,
and mostly because the onboarding path is half-built rather than badly designed.

| ID | Item | Sev | Eff |
|---|---|---|---|
| IMP-035 **[V]** | **Mount the setup checklist that already exists.** `ui/config_status_panel.py` builds a complete "Setup Progress N/5 → Profile → JIRA → Fields → Queries" panel with working buttons, and has **zero importers**. Its feeder callback sits behind `USE_ACCORDION_SETTINGS = False` (`ui/layout.py:50`). Mount it in the Settings flyout and move `update_configuration_status` into `callbacks/tabbed_settings.py`. ≈60 lines, nearly all copy-move. | Blocker | M |
| IMP-036 **[V]** | **Fix the first-profile defaults.** `callbacks/profile_management.py:348` writes `pert_factor: 1.2` into a slider whose `min` is 3, against `DEFAULT_PERT_FACTOR = 6`; downstream `int(min(1.2, …))` → 1, so the first forecast uses one best and one worst week — maximum volatility — while the slider reads "6 (rec)". Same line writes `data_points_count: 20` against a default of 12. Also `data/_profile_crud.py:77` and `callbacks/settings/core_settings.py:290,293`. | Blocker | S |
| IMP-037 **[V]** | **Remove the expired hard-coded deadline.** `"2025-12-31"` is the `deadline is None` fallback in **three** production sites: `ui/parameter_panel/panel_controller.py:42`, `callbacks/settings/parameter_panel.py:156`, and `data/jira/cache_operations.py:104` (this third was missed by the audit). Every new profile draws its deadline line nine months in the past. Render "not set" and omit the marker instead. | High | S |
| IMP-038 **[A]** | **Un-hide the Update Data error path.** `callbacks/settings/data_update.py:286-325` writes a well-worded error into two `display:none` divs (`ui/tabbed_settings_panel.py:75,365-366`) with an empty toast, then `complete_task` renders a **green 100% bar** labelled "❌ JIRA not configured" for 3s. Route to `app-notifications`, use `fail_task`. ≈20 lines; fixes the most common dead end. | Blocker | S |
| IMP-039 **[A]** | **Auto-Configure reads a path that no longer exists.** `callbacks/field_mapping/auto_config.py:114,124,199` opens the deprecated `profiles/<id>/profile.json`; UI-created profiles are SQLite-only. The exception is swallowed → 0 sample issues → every value-based detector finds nothing → user still gets a green "Auto-Configuration Complete". README promises ~90% auto-detection. | Blocker | M |
| IMP-040 **[A]** | **State-aware empty state.** `callbacks/visualization.py:302` renders one grey box ("No data available") styled identically to the *loading* placeholder, with no CTA — and it gates **every** tab including Weekly Data, the only manual-entry surface, so non-JIRA users cannot bootstrap at all. Reuse `ui/empty_states.py:246`; exempt the manual-entry tab. | Blocker | M |
| IMP-041 **[A]** | **Correct the README/quickstart setup path.** `readme.md:107,164` instructs the user to click a **"Fetch Metadata" button that does not exist**, describes a Query field absent from the JIRA modal, and names the wrong navigation path; quickstart cites a non-existent left sidebar and the wrong default API version. | Blocker | S |
| IMP-042 **[A]** | **Surface field-mapping validation.** `callbacks/field_mapping/validation_helpers.py`: every missing *required* mapping is only a warning, shown only if the user clicks Validate; Save shows a plain success toast. `data/config_validation.py`, which treats these as errors, has **zero callers**. | High | M |
| IMP-043 **[A]** | **Propagate JIRA sync errors.** Rich `errorMessages` from `data/jira/main_fetch.py:582-609` are discarded into the single string "Failed to fetch JIRA data" (`scope_sync.py:273`), shown for 3s then auto-hidden — while the unused Test Connection path produces excellent diagnostics. | High | M |
| IMP-044 **[A]** | **Name one setting one thing.** "Forecast Range" / "Range: 6w" / `PERT_FACTOR` / "Confidence Window" are the same control (`expanded_panel.py:286`, `settings.py:38`, `collapsed_bar.py:191`); the slider shows bare integers with no unit, and `ui/profile_selector.py:159` prints "PERT Factor: 1.2". Also add the missing help icon to the **Points Tracking** switch (`expanded_panel.py:370`) — the single most consequential novice choice and the only control in the panel without one, with conflicting defaults across three files. | High | S |
| IMP-045 **[A]** | **Add a reset path.** No reset exists for settings, mappings, or JIRA config; the documented recovery is "delete the profiles folder" (`readme.md:176`), which destroys all profiles and history. | Medium | M |

## Wave 3 — Presentation honesty

| ID | Item | Sev | Eff |
|---|---|---|---|
| IMP-046 **[V]** | **Restore the forecast chart's axis titles.** `visualization/forecast_chart_layout.py` sets all three to `title=""` with `# No axis title`. The correct strings still exist in the dead `visualization/elements.py:305,315`. The app's most important chart currently has two differently-scaled, entirely unlabeled y-axes. One-line-each fix, highest leverage in the layer. | Critical | S |
| IMP-047 **[V]** | **Stop manufacturing correlation on the dual axis.** Same file: `scale_factor = max_points / max_items` is applied so items and points fill the same height — the comment says "align visually". Either split into two stacked charts or index both to a common base. | Critical | M |
| IMP-048 **[A]** | **Sprint burnup draws synthetic future days as solid actuals.** `sprint_burnup_chart.py:140`: snapshots are emitted for every day to sprint end and future days inherit today's status, so the line runs flat to the end with no `today` marker. Reads as "we have stalled". Truncate at `min(today, end)` and add a today vline. | Critical | M |
| IMP-049 **[A]** | **Zero velocity renders as green success.** `data_preparation.py:396` → `forecast_chart_layout.py:256` + `charts.py:404`: `pert_time_items == 0` prints "Est. Days (Items): 0.0 days" in **green** with a completion date of **today**. Render "n/a (insufficient data)" in neutral gray. Same root cause as IMP-014/015. | Critical | S |
| IMP-050 **[V]** | **The low-confidence caveat is unreachable.** `bug_charts_forecast.py:41` early-returns on `insufficient_data`, so the "Limited data — forecast may be less accurate" annotation at `:150` can never render. The warning was written and is dead. | High | S |
| IMP-051 **[A]** | **Error bars understate risk ~4×.** `weekly_chart_items.py:343` / `weekly_chart_points.py:269`: `error_y = 0.25 × PERT spread`, disclosed only in hover, on a pessimistic bound that already excludes zero-delivery weeks. Draw the full opt–pes whisker and label the legend entry. | High | M |
| IMP-052 **[A]** | **DORA tier color painted on the wrong trace.** `metric_trends.py:668`: `primary_color` (the tier color) is applied to Releases while Deployments gets a hardcoded Elite green — so a "Low performance" card shows its deployment line in success green. | Critical | S |
| IMP-053 **[A]** | **Points bars plotted on the count axis.** `bug_charts_distribution.py:88,308`: points are multiplied by a per-range `scale_factor` and drawn as bars on the shared axis, disclosed only in the axis title. Tick values are wrong for those bars and heights change when the range filter moves. | Critical | M |
| IMP-054 **[A]** | **Mobile optimization clips the metrics panel and drops the legend.** `callbacks/visualization.py:185` → `charts.py:get_mobile_chart_layout` replaces the forecast chart's `height=700, margin.b=220` with 500/100 (desktop) and 300/40 (mobile), clipping the 12-metric annotation grid — all four rows on mobile — and sets `showlegend=False` on a 10-trace chart. Merge rather than replace. | High | S |
| IMP-055 **[A]** | **Sparkline hover shows the wrong per-point value.** `sprint_burnup_chart.py:159,240`: `customdata` holds one element for the whole series, so `%{customdata[0]}` resolves only for point 0. | High | S |
| IMP-056 **[A]** | **"Next 4 Weeks" draws one bar.** `weekly_chart_items_forecast.py:236`, `weekly_chart_points_forecast.py:321`: `forecast_weeks=1` is never overridden. | High | S |
| IMP-057 **[A]** | **Pace threshold defaults to red below 4 weeks.** `weekly_chart_items.py:46`: `current_velocity` is `None` until `len(weekly_df) >= 4`, and the `else` branch paints red "Behind Pace" regardless of actual velocity. | High | S |
| IMP-058 **[A]** | **Palette fails CVD and normal-vision separation.** Measured on the live 8-series forecast palette: `#B8860B`↔`#FF7F0E` ΔE 3.2 (protan) and `#B8860B`↔`#8a6d3b` ΔE 11.4 (normal vision) both fail; contrast warnings on `#14A896` and `#FF7F0E`. Dash/symbol coding partly rescues it. 8 series on one chart also exceeds the all-pairs cap — splitting items and points (IMP-047) fixes both. | High | M |
| IMP-059 **[A]** | **CFD bands are indistinguishable.** `sprint_cfd_chart.py:21-31`: Done/Closed/Resolved share one green, To Do/Backlog/Open share one grey, and every *unmapped* status falls back to that same grey, with 0.5px same-color separators. In a project with custom statuses the bottleneck the CFD exists to reveal is invisible. | High | M |
| IMP-060 **[A]** | **Out-of-range indicator is invisible where it matters.** `flow_charts.py:75`: the warning is a red border drawn on slices already filled red or orange; `:422-492` gives four threshold lines `showlegend=False`, so they are labeled nowhere. | Medium | S |
| IMP-061 **[A]** | **Warning rects overwrite the forecast divider.** `bug_charts_trend.py:510` assigns `shapes=warning_shapes` after `add_vline`; Plotly merges arrays element-wise, so rect 0 replaces the divider line. | Medium | S |
| IMP-062 **[A]** | **`titlefont` is removed from Plotly's axis schema.** `bug_charts_forecast.py:126,132`, against a plotly 6.6.0 pin. Smoke-test before release. | Medium | S |

## Wave 4 — Consolidation (root cause A)

Do these **after** Wave 0, and settle the behavioural question in each before deduping —
collapsing two implementations requires first deciding which is correct.

| ID | Item | Sev | Eff |
|---|---|---|---|
| IMP-063 **[A]** | **One color and threshold table.** Optimistic/likely/pessimistic has 3 mappings (`charts.py:640`, `bug_charts_forecast.py:78`, `forecast_chart_traces.py:134`); "Testing" is cyan in the CFD and orange in the progress bars on the same page; DORA Elite/High/Medium boundaries are defined 3 incompatible ways (`dora_charts.py:374`, `chart_config.get_performance_zones`, `configuration/dora_config.py:20`). Move to `configuration/settings.py`; closes six visualization findings at once. | High | M |
| IMP-064 **[A]** | **Reconcile the items/points forecast divergence, then collapse the family.** `weekly_chart_points_forecast.py` has a weighted 4-week average and ±25% PERT bounds; `weekly_chart_items_forecast.py` has neither. The pair is reimplemented 4× (`weekly_chart_*`, `*_forecast`, `ui/cards/forecast_cards.py:353,539`, `data/report/chart_burndown_pert.py:16,230`) ≈1,900 LOC, drifted in 3. Decide correct behaviour first, dedupe behind a `metric_kind` parameter second. | High | M then L |
| IMP-065 **[A]** | **Deduplicate scope calculation.** All 6 functions in `data/persistence/adapters/scope.py` are byte-identical to `legacy_data.py`, including a 47-LOC `calculate_project_scope_from_jira`. Both live, 3 importers each. | High | M |
| IMP-066 **[A]** | **Make the exported report import the app's palette and pace logic.** `data/report/chart_burndown_pert.py:95,153` and `chart_burndown_daily.py:160-192` are a third implementation with different blues and oranges, an always-red required-velocity line, a green items forecast, independently autoscaled axes and no uncertainty at all. The same project reads "on pace" in the app and "behind" in the PDF. | High | M |
| IMP-067 **[A]** | **Collapse the remaining cross-layer duplicates.** `ui/jira_link_helper.py` ↔ `utils/jira_link_utils.py` (3 byte-identical functions); `ui/loading_utils_core.py:345` ↔ `utils/loading_overlay_utils.py:37` at 0.999; 3 independent sparkline builders; `format_hover_template` byte-identical ×3. | Medium | M |
| IMP-068 **[A]** | **Unify the two deadline-probability implementations.** scipy `norm.cdf` vs a hand-rolled logistic `100/(1+2.718**(-1.7z))`, diverging up to ~6pp on identical inputs. Related: `ui/dashboard/__init__.py:216` uses population `std(ddof=0)` where `stats.py:42` and `velocity_signals.py:116` use sample `ddof=1` — CV differs 13.4% at n=4. | High | M |

## Wave 5 — Dead code, hygiene, supply chain

| ID | Item | Sev | Eff |
|---|---|---|---|
| IMP-069 **[A]** | **Bump the 8 vulnerable production dependencies.** 40 unsuppressed advisories in `requirements.txt` (pillow ×20 is the bulk, plus urllib3, requests, pytest, pygments, click, idna, diskcache). `validate.py --full`'s pip-audit gate currently fails. Then wire pip-audit into CI. | High | S |
| IMP-070 **[A]** | **Regenerate `.pip-audit-baseline.json`.** It records `dash 3.1.1` / `flask 3.1.2` / `werkzeug 3.1.3`, predating the dash-4 upgrade; 9 of 10 baselined CVEs are already fixed by current pins, and it suppresses by CVE-id while pip-audit now emits PYSEC-ids — so it suppresses nothing. Risk acceptance theatre. | High | S |
| IMP-071 **[A]** | **Test `updater/` to non-zero and resolve `updater.py`.** 517 statements at **0%** coverage on the one path whose failure is unrecoverable in the field. `updater/updater.py` (448 LOC) has zero inbound references — likely a half-finished rewrite still shipping. `file_ops.copy_executable` and `support_files.replace_support_file` are a 0.987-similar drifted clone of the retry/lock logic, so a lock fix reaches only one. | Critical | M |
| IMP-072 **[A]** | **Verify third-party asset downloads.** `download_vendor_dependencies.py` / `download_report_dependencies.py` fetch from jsdelivr/cdnjs with **no SHA/SRI verification** and feed a signed Windows release. Also skewed: Bootstrap 5.3.3 (app) vs 5.3.0 (reports), FontAwesome 6.5.1 vs 6.7.2. | High | M |
| IMP-073 **[A]** | **Delete verified-dead modules in tranches.** 70 of 490 non-test modules ≈ 15,936 LOC with zero inbound imports. Start with `ui/pert_components/` (4 of 6 dead, 1,469 LOC), `ui/error_states.py` (741 LOC), and `visualization/elements.py` — but take the axis-title strings out first (IMP-046). Defer `callbacks/` until Dash auto-registration is confirmed per module. | High | L |
| IMP-074 **[A]** | **Fix the layering breaches.** Only 10 statements in 7 files, so this is cheap: `configuration/logging_config.py:32` imports `data.installation_context` at module level *and executes it at import time*; 6 function-local `import app` reads of a mutable global (`callbacks/app_update.py:48,160,293,372`, `version_update_notification.py:80`, `ui/layout.py:119`); `utils/jira_link_utils.py:9` imports `data.persistence`. | Medium | S |
| IMP-075 **[A]** | **Prune the `# noqa: PLC0415` noise.** 149 in production; only 5 name a cycle as the rules require; 84 suppress plain stdlib lazy imports that cannot be cycle-breaks. The legitimate guards are unfindable. | Medium | M |
| IMP-076 **[A]** | **Remove `tests_stderr.txt`** — an empty file committed at repo root that invites trusting stale output. | Low | S |
| IMP-077 **[A]** | **Add the missing high-value math tests** (do alongside Wave 1): a velocity assertion crossing Sunday→Monday and Dec→Jan (catches IMP-023 and IMP-024 together); a `calculate_rates` case containing zero weeks; a `calculate_weekly_averages` case where the window exceeds available history; any budget assertion with a known expected euro value; a lead-time p95 with a known expected value; deadline probability at n=1 and n=3. Note `test_processing.py:66` re-implements the PERT formula it tests and uses all-nonzero data, so it structurally cannot see IMP-015. | Critical | M |

---

## Deliberately deferred

- **Re-splitting `data/field_detector*` (6 files, 1,358 LOC) and `data/budget_calculator*`
  (4 files).** Correctly diagnosed as size-splits rather than responsibility-splits, but they
  sit in `data/` at 53% coverage with heavy internal coupling: high effort, real regression
  risk, no user-visible payoff. Revisit once Wave 0 gives a suite worth trusting.
- **Dark theme / `aria-label` coverage on `dcc.Graph`.** Real gaps, but the app is light-mode
  only today, so the accessibility work should follow a theme decision rather than precede it.

## Verified non-problems

Recorded so nobody spends effort here:

- **pandas 3.0.1 / numpy 2.4.3 / dash 4.0.0 are genuinely installed and the suite passes on
  them.** No removed-API usage: no `DataFrame.append`, no `np.float_`/`np.NaN`, no
  `run_server`, no `dash_core_components`. The 918 `.append(` hits are all `list.append`.
- **Circular imports are fully contained.** All 493 first-party modules imported in isolated
  interpreters: 0 failures. The documented cycle map and lazy-wrapper guards are accurate and
  being followed. This partly closes the in-progress `burndown-chart-dbgp`.
- **Core layering is genuinely respected.** Zero `data→ui/callbacks/visualization`,
  `visualization→ui/callbacks`, or `ui→callbacks` edges across 669 files; all hard violations
  are the 10 statements in IMP-074.
- **Lint is honestly green** on the configured rule set: ruff 0, pyright 0, bandit 0 over
  112,081 LOC. (A `--select ALL` probe surfaces 342 blind-excepts and 261 naive datetimes, but
  that is a scope decision, not a regression.)

---

## Measured baseline (2026-09-10)

Recorded so later work can be compared against it.

- `pytest -q`: **3 failed, 1876 passed, 5 skipped, 15 errors** in 63.9s. All 18 problems are
  in `tests/integration/`.
- `pytest tests/unit`: **1786 passed, 0 failed**, 12.9s, 45.82% coverage.
- Under `-n auto`: **4 failed, 1888 passed, 6 skipped, 1 error** — a *different* result set on
  identical code (IMP-006).
- Coverage: **TOTAL 44%** (31,933 statements) — `data/` 53.3%, `callbacks/` 21.2%, `ui/`
  44.6%, `visualization/` 47.2%, `updater/` **0.0%**. Flattered by the `omit` list (IMP-008).
- ruff 0 · ruff-format 674 clean · pyright 0/0 across 635 files · bandit 0 · vulture 0
  (miscalibrated, IMP-007).
- **No `.venv` in the repo**, and `.git/hooks/` has no hooks installed.
