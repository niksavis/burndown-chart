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

The executable numerical diagnostics remain separate from browser rendering assertions.
They compare persisted data through actual calculation producers with independent expected values.
They return failure for known disagreements rather than preserve incorrect values as reference results.
