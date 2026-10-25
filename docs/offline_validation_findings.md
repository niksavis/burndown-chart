# Offline validation checkpoint

The local environment renders the application and exported HTML without Jira.
This checkpoint does not establish numerical correctness or a visual pass for every surface.
The remaining coverage work is listed in [Offline development](offline_development.md#remaining-coverage-work).

## Browser evidence

The managed capture command completed on October 25, 2026 against a fresh synthetic workspace.
Its manifest records desktop 1440 by 1000 and mobile 390 by 844, each with light and dark browser preferences.
All four contexts visited the exact inventory in `ui.tabs.TAB_CONFIG`:

- Dashboard
- Burndown
- Scope Tracking
- Bug Analysis
- Flow Metrics
- DORA Metrics
- Active Work
- Sprint Tracker
- Weekly Data

Each context downloaded and opened the report through the actual UI.
Browser observations recorded no external requests, failed assets, HTTP errors, page errors or console errors.
The report contains eight sections: health, burndown, scope, bugs, budget, Flow, DORA and recommendations.
The reviewer inspected all nine tab viewport images, budget and all eight report sections in desktop-light and mobile-light.
The reviewer also inspected Dashboard, Active Work and DORA report images in both dark-preference contexts.
That is 42 inspected images. Other dark-preference images remain uninspected.
After the budget capture correction, the reviewer inspected fourteen additional viewport images.
These include all four desktop-light and eight mobile-light budget views, plus one view under each dark preference.
The overlapping budget views cover all six cards, the cost breakdown and the timeline without the previous capture obstruction.
Generated images, HTML and logs remain under the ignored `profiles/` directory.

Tab viewport captures now start at the top.
Report animation is completed before capture, so bar endpoints show four items and eight points consistently.
Fresh data demonstrates 46 epic children and two unparented issues.
Budget displays the latest settings: 9,000 total, ten weeks and 1,100 per week.

## Observed defects and limits

| Surface | Observation | Follow-up |
| --- | --- | --- |
| Mobile HTML report | Budget columns, Flow/DORA right-hand cards and recommendation text clip horizontally | Add a report layout diagnostic and repair responsive layout separately |
| Mobile budget timeline | Labels and dates overlap | Repair timeline layout separately |
| Budget runway comparison | Remaining0.18weeks is compared with all ten allocated weeks, while baseline end is2.4weeks away | Trace remaining-versus-total comparison |
| Dark preference | Both contexts retain the light application presentation | Record preference robustness; a complete dark theme is unavailable |
| Dashboard and scope | UI shows 88 total/64 completed/24 remaining points; recorded creations sum to96 | IMP-021 and IMP-031 |
| Burndown | Point rate has an `items/week` label | Correct point-series labels separately |
| DORA | App lead-time day headline and hour subtitle encode different values | Trace blending and unit presentation |
| DORA | App counts nine deployments; intended production population has eight | Trace the TEST task through the actual producer path |
| DORA recovery | Resolved production incidents render N/A | `burndownchart-qtlipm` |
| Report health | Resolution rate shows10,000%; bug section shows100% | Trace percentage conversion at the health boundary |
| App/report health | App67% and report66% differ | Reconcile window, signals and weights |
| Desktop tabs | Several icons appear as missing glyphs | Trace icon font/class compatibility |
| Mobile tab viewports | Lower charts and the weekly table are below the first screenshot | Add captures after scrolling |
| Sprint Tracker | Default view shows the Show Charts button | Add the burnup and cumulative-flow journey |
| Empty scenario header | Body is empty, but header retains previous remaining scope | IMP-040; keep distinct from corrected Dashboard data routing |
| Sprint future actuals | Completion series extends beyond the January 29 evaluation date | IMP-048 |

The executable numerical diagnostics remain separate from browser rendering assertions.
They compare persisted data through actual calculation producers with independent expected values.
They return failure for known disagreements rather than preserve incorrect values as reference results.

## Expanded review findings

The specialist inspected another 27 images from the expanded desktop-light capture.
These covered lower Dashboard, Burndown, Scope, Flow and DORA content, Active Work, Sprint and Weekly Data,
opened Sprint charts, a four-week history selection and eleven scenario views.
That review found that several scenario headers changed while the completed count still showed 32 items.
Those captures did not validate scenario data.

Three focused regressions reproduced two routing causes: a profile switch reloaded settings without statistics,
and the snapshot cache used only query identity despite profile/query composite storage.
Both causes are corrected. Scenario journeys now assert visible counts and explicitly select full history;
switching from a singleton had otherwise left the one-week selection active for later profiles.
This preserves the distinction between a selected window and the complete eight-week project.

The review also found Sprint timing based on the wall clock rather than the demo evaluation date.
Sprint progress, issue-health timing and remaining forecast date reads now use the controlled business clock.
Operational cache and progress timers still use real time.
Focused regressions assert 75 percent elapsed and 3.5 days remaining for a fourteen-day sprint ending February 2,
evaluated at January 29 noon UTC, and a one-day-old issue remains in the recent-health bucket.

The expanded catalogue has 323 checks with independent derivations.
Missing output fields and calculation errors fail explicitly, including when an expected value is unavailable.
The broader numeric discrepancies remain visible diagnostics and separate backlog work.
The final browser assertion matrix passes all four viewport/preference combinations.
Each context visits all nine registered tabs, nineteen scenarios and eight exported report sections.
The manifest records 73 PNGs per desktop context and 113 per mobile context, with no observed browser errors or external requests.
These are rendering assertions, not a numerical or visual pass for every image.
The adapter coverage audit and final responsive-chart settlement probes remain open.

Persistent journeys exposed another state defect: summary rerenders recreate panel buttons without a click.
The Parameters callback previously returned its captured panel state for that event, overwriting a later close.
It now emits no update for a non-click event. A regression failed before this change and passed afterwards.
Journeys use the dedicated collapse button and assert closure before opening another panel.

The specialist inspected 68 PNGs in this final matrix: all 36 main-tab screenshots,
eight budget viewport samples, sixteen report-section views and eight mobile lower-chart views.
The report samples cover sections 1, 3, 5 and 7 in each viewport/preference combination.
No stale panel overlay appeared on those main tabs.
Lower-chart inspection found different bar-axis ranges and horizontal Sprint-chart clipping between mobile captures.
This does not establish an OS-preference cause: delayed responsive rendering and actual layout defects remain competing explanations.
Check final Plotly geometry and axis settlement before treating those captures as equivalent visual evidence.

The owner explicitly selected validation under both OS preferences.
A complete application and report dark theme is separate work: `burndownchart-8jm662`.
