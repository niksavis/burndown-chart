# Offline development

The demo contains synthetic data. Its numerical diagnostics deliberately fail when application calculations disagree with independent expectations.
Do not use a rendered chart or a passing browser journey as proof of numerical correctness.

## Provision once while connected

Use Python 3.14 and the committed dependency files. From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
```

On Windows, replace `.venv/bin/python` with `.venv/Scripts/python.exe` in every command.
Provision the operating system libraries required by Chromium before disconnecting.
Playwright documents its [browser prerequisites](https://playwright.dev/python/docs/browsers).
The repository already declares Playwright as a development dependency.

The pinned browser ran on the inspected Ubuntu 26.04 host with `PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64`.
This is a measured workaround for an unsupported host, rather than a supported operating system claim.
NSPR, NSS and ALSA packages were extracted into a local tool cache with explicit user approval.
No system package or project dependency was changed.
Other developers should provision dependencies for their own operating system.
When a browser cache is shared, set `PLAYWRIGHT_SKIP_BROWSER_GC=1` before additional browser provisioning.

For the local extraction layout used on this Linux host, set the runtime paths before browser commands:

```sh
export LD_LIBRARY_PATH="$HOME/.cache/burndown-browser-runtime/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64
```

The cache was provisioned with `apt-get download libnspr4 libnss3 libasound2t64` in a dedicated directory.
`dpkg-deb -x` extracted each downloaded archive into its `root` subdirectory.
These commands download and extract libraries without a system package installation.
Use the supported operating system prerequisites when this workaround does not apply.

## Start and preserve the local workspace

```sh
.venv/bin/python dev.py
```

Open <http://127.0.0.1:8050>. The first launch generates `profiles/demo/burndown.db`.
Later launches preserve database edits. Select an `Acme Corp` scenario through the normal profile controls.
The launcher selects paths before application imports. Its database, logs and callback cache use the selected workspace.
Ordinary application startup still uses its ordinary workspace.
Everything below `profiles/` remains local and uncommitted.

The business evaluation date is January 29, 2026 at noon UTC.
Business calculations use that date. Cache expiry, task progress, readiness and shutdown use live operational time.
The blue demo banner identifies synthetic data and its evaluation date.
The launcher suppresses updater startup and rejects non-loopback Python socket traffic before DNS resolution.
Demo Jira synchronization is refused before a forced refresh can erase data.

Additional lifecycle commands:

```sh
.venv/bin/python dev.py seed
.venv/bin/python dev.py serve --port 8060
.venv/bin/python dev.py seed --workspace profiles/demo-empty --empty
.venv/bin/python dev.py serve --workspace profiles/demo-empty
.venv/bin/python dev.py reset --confirm-demo-reset
```

Stop the server before reset. Reset requires the demo marker and refuses a live workspace owner.
An unmarked populated directory is refused. Reset removes only the owned demo database and callback cache.
The next launch generates a new database. Use reset or a new workspace after changing generation scripts.
The seed never silently replaces an existing database with newer data.
A failed seed leaves its candidate unpublished. A later launch can retry initialization.
The lock rejects a second server for the same workspace.

## Data and independent expectations

`data/demo/config.py` lists all selectable scenarios.
`data/demo/issues.py` generates source issues and changelog from December 8, 2025 through January 29, 2026.
`data/demo/seed.py` uses SQLite persistence and the application's scope, statistics and historical metric producers.
It includes release links, production and test environments, incidents, four sprints, parent relationships and dated budget revisions.
Stored budget settings represent the latest revision, as the normal save path does.

The complete development population has 48 items and 96 points.
Each week has four completed items and eight completed points, plus six created items and twelve created points.
The independent remaining totals are 16 items and 32 points.
The issue mix contains one completed Feature, Defect, Technical Debt and Risk per week.
Other scenarios cover empty, singleton, zero delivery, stalled, sparse history, fractional points, completed/reopened work,
missing signals, unmapped fields, no points, scope changes and deadline variants.
Accelerating and declining scenarios exercise trend signals.
The variable-points scenario keeps item throughput constant while point throughput changes.
The `unreleased-version` scenario isolates a completed operational task with an elapsed release date and a false version flag.
Nominal recorded releases have consistent flags. Unknown scenario names are refused rather than treated as complete data.

Run the independent contracts:

```sh
.venv/bin/python dev.py diagnose > profiles/demo-diagnostics.json
```

Standard output is JSON. Progress and logs go to standard error.
Exit status 1 means at least one calculation differs from its expectation.
Every result names its producer, rendering surface, selected population, expected value and derivation.
It also names the exact output field. A missing field fails even when an unavailable value was expected.
Arithmetic and shape exceptions remain named failures in the JSON report, with an unsuccessful exit status.
`data/demo/contracts.py` is the current executable manifest.
`devtools/calculation_sources.py` calls the real producers against persisted synthetic data.
The runner restores the selected profile and query after diagnosis.

Known failing contracts cover fractional truncation (IMP-021), sparse snapshot padding (IMP-014),
zero-week exclusion (IMP-015), singleton NaN (IMP-018) and budget revisions (IMP-013).
Separate findings track missing recovery timestamps (`burndownchart-qtlipm`) and fractional bug duration (`burndownchart-lokdeu`).
Broader arithmetic repairs remain separate work. Do not change an expected value to make a wrong result pass.

## Verify and capture

```sh
.venv/bin/python validate.py
.venv/bin/python -m pytest tests/e2e/test_demo_browser.py -q
.venv/bin/python -m devtools.capture --workspace profiles/demo-review --output profiles/demo-review-images
```

The default validation command now reads `tests/`, including unit, integration, visual and browser tests.
It preserves the coverage threshold and excludes only tests marked `performance` in push mode.
The offline pytest entry point rejects external socket connections in its process and runs without parallel workers.
It creates a temporary workspace before collection, routes default SQLite, logs and application cache there,
and refuses connections to the normal database. Each invocation gets its own workspace and child process.
Ordinary tests retain the live business clock; the runner removes inherited demo settings.
Automatic cleanup of shared updater files is suppressed during verification.
Managed demo child servers install their own socket policy.
`validate.py --full` retains the existing additional checks, including the online dependency audit.
Use that audit while connected. The default test gate does not require Jira or a package registry.

The capture command owns server startup and shutdown.
It refuses an existing output directory, preserves its selected workspace and writes a manifest after successful browser assertions.
It visits the nine tabs in `ui.tabs.TAB_CONFIG`, captures budget content, downloads HTML through the real report button,
and opens the exported file offline. Report captures cover all eight rendered sections.
Overlapping viewport captures include lower tab content and the opened Sprint chart.
The journey switches through `data.demo.config.SCENARIOS` and changes the history range through the actual slider.
Scenario captures explicitly select their full available history.
Empty, singleton, zero-delivery, stalled, completed and default scenarios assert visible data counts or absence.
Changing the profile header alone cannot satisfy those assertions.
It tests desktop and mobile viewports with both browser color preferences.
Browser assertions reject external requests, failed assets, HTTP errors, page errors and console errors.
Report captures passively wait for Chart.js element positions to reach their targets and remain stable.
Overlapping fixed viewport images preserve that state during capture; section images retain the first viewport for compatibility.

Inspect the resulting PNG files separately. The manifest records browser assertions; it does not certify visual correctness.
The application currently uses its light presentation under both browser color preferences.
Capturing a dark preference does not establish a complete dark theme.
The owner chose to validate both OS preferences and track a complete theme separately as `burndownchart-8jm662`.
Do not inject replacement colors to hide this limitation.

For the bounded chart-readiness investigation:

```sh
.venv/bin/python -m devtools.plotly_settlement --workspace profiles/demo-plotly --output profiles/demo-plotly-stages
```

This captures two mobile graphs under both OS preferences at three stages: current readiness,
passive settlement and a separate resize diagnostic. Each of the twelve PNGs has before/after geometry and figure-state JSON.
Canonical journeys wait for loaded fonts, completed collapse transitions, no Dash loading marker,
and 500 milliseconds of continuous stable graph identity, geometry, axes and trace data, bounded by ten seconds.
A new loading interval restarts that quiet interval. Named graphs must exist and be visible.
Page settlement also handles card/table surfaces that have no visible Plotly graph.
The observation adapter reads Plotly runtime layout fields and refuses missing layouts; it does not change figures.
Forced resize remains diagnostic and is never used to make canonical screenshots fit.

## Calculation coverage and known discrepancies

The catalogue contains 530 independent checks across the scenario inventory. The latest diagnostic run reports 102 discrepancies; these remain explicit failures linked to backlog records, separate from the green software verification gate.
Positive Quality/Financial scores, the conditional health composite, budget/pace/correlation recommendations,
work timing, sprint scope changes and four-week report adapters now have executable contracts.
The composite calibration uses explicit corrected inputs and expects 72; it does not certify the mounted Dashboard result.
Recommendation zero-value failures are tracked by `burndownchart-ftzd2n`.
Production lead eligibility remains a separate semantic defect; the controlled completed-item calibration remains explicit.
Dormant forecast-history widgets have no stored producer and must not receive fabricated history.

The bounded report probe showed that stopping animations did not establish settled elements.
A full-section screenshot could change Chart.js geometry during capture.
Canonical journeys now wait passively and capture overlapping fixed viewports.
The regression checks populated weekly bar baselines before and after every report screenshot under both OS preferences.
The earlier floating bars and January forecast-marker observations were capture artifacts, not demonstrated calculation defects.
Mobile report overflow remains a recorded product defect.

## Gate execution

`basicly verify --mode fast` runs the configured project static checks.
`basicly verify --mode full` runs those checks and the complete offline unit, integration and browser inventory.
The native content cache reuses only trusted equivalent passing inputs; changed inputs invalidate that evidence.
Standalone Ruff and Prettier checks reuse the consumer hook's file-selection policy, so generated basicly files are treated consistently.
The optional `validate.py --full` additionally runs dependency audit, dead-code analysis and performance tests.
