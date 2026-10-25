# Fractional story points

Story-point calculations retain decimals through Jira extraction, SQLite storage, statistics preparation, scope, forecasts and report data.
Item counts remain integers.
Scope and forecast labels no longer format point totals as whole numbers.
Dashboard and report cards keep their existing presentation precision.
Calculations use the underlying fractional values before presentation rounding.

## Changed numerical behavior

The independent offline catalogue supplies the expected values.
A fresh baseline and candidate were each run with `dev.py diagnose` against separate synthetic workspaces.

| Population and output | Before | After |
| --- | ---: | ---: |
| One completed 2.5-point issue and unfinished 3.5- and 0.5-point issues: total | 5 | 6.5 |
| Same population: completed | 2 | 2.5 |
| Same population: remaining | 3 | 4 |
| Default demo: total points | 72 | 96 |
| Default demo: completed points | 48 | 64 |
| Default demo: remaining points | 24 | 32 |
| Default demo: point forecast, days | 21 | 28 |
| Default report: total points | 88 | 96 |
| Default report: completion percentage by points | 72.73% | 66.67% |
| Dedicated fractional demo: three completed issues, total points | 5 | 6.5 |

These corrections increase scope when individual estimates contained fractions.
Forecasts can move later when the corrected remaining scope increases against an already fractional delivery rate.
A team's exact change depends on its source estimates and delivery history.

The extraction rule is shared by scope, weekly statistics, issue storage and point re-normalization.
It accepts numeric values, numeric strings and supported numeric wrappers.
Non-finite, negative, boolean and malformed values now raise a field-specific error instead of becoming a fabricated zero.
Missing estimates remain unestimated; an explicit zero remains a zero estimate.
The existing estimation policy for missing points is unchanged.

## Stored data and the offline demo

Existing saved aggregates cannot recover fractions that an earlier version discarded.
Refresh the Jira data to recalculate scope and statistics from source estimates.
Point re-normalization can recover issue estimates from stored custom fields.
It does not repair every saved aggregate by itself.
No database schema migration is needed.

Existing demo workspaces retain their saved data.
Use a new workspace for the corrected demo, for example:

```sh
.venv/bin/python dev.py diagnose --workspace profiles/fractional-review
.venv/bin/python dev.py serve --workspace profiles/fractional-review
```

## Verification and separate discrepancies

`tests/integration/test_fractional_points.py` covers extraction, estimation, persistence, re-normalization, imports, scope, report history and forecasts.
Its expected totals are enumerated independently.
The browser journey also asserts the fractional Dashboard's 6.5 completed points and zero remaining points.
The dedicated fractional demo contains three completed issues; the mixed-status regression uses one completed and two unfinished issues.

The catalogue now contains 539 checks.
All 29 checks linked to `burndownchart-imp021` pass.
The fresh baseline had 102 discrepancies; the corrected candidate has 84.
The scope week-label formatting failure also prevented fractional growth charts from rendering.
The regression now checks its ISO week label and fractional growth values (`burndownchart-0tv1mh`).

The remaining diagnostic failures stay explicit.
They include budget consumption and revisions (IMP-012/013), sparse observations (IMP-014), zero-delivery PERT samples (IMP-015),
health normalization (IMP-016), fixed probability (IMP-017) and singleton statistics (IMP-018).
Production deployment eligibility, recovery timestamps, fractional bug durations and other existing metric findings remain separate records.
A passing software gate does not establish that those numerical discrepancies are resolved.

The application still uses its light presentation under both OS color preferences (`burndownchart-8jm662`).
Mobile report overflow remains a separate product finding.

## Visual review

The offline capture completed desktop (1440 by 1000) and mobile (390 by 844) journeys with light and dark OS preferences.
Each combination covered all nine registered tabs, all 20 scenarios and all eight default report sections.
A separate fractional journey checked Dashboard, Burndown, Scope Tracking, Weekly Data and the downloaded HTML report.
Its seven report sections match the existing template's omission of scope analysis for insufficient history.

The reviewed images show 6.5 points in the Dashboard, scope indicators, weekly table, forecast annotations and exported report.
The mobile point cards and scope labels remain readable.
The artifacts and browser manifests are under `profiles/fractional-images` and `profiles/fractional-targeted-images-v3` in the review workspace.
They contain synthetic data and remain outside Git.

Separate observations remain explicit:

- Desktop tab glyphs show missing boxes (`burndownchart-1vosgm`).
- The orange point trend card retains its incorrect items title and unit; narrow charts also have crowded date labels (IMP-046).
- The fractional Dashboard health score is 54%, while the report shows 55% (IMP-016).
- The historical fractional report labels its period as the current week (`burndownchart-mr0jy2`).
- The report anchors calendar forecasts at the last recorded Monday; daily simulation starts at the evaluation time (IMP-064).
- Both OS preferences retain the existing light presentation. Mobile report overflow remains separate.
