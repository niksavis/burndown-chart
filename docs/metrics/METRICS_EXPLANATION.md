# DORA & Flow Metrics - Complete Explanation

**Created**: November 7, 2025  
**Purpose**: Clarify what each metric calculates, time units, aggregations, and data presentation

## Overview

All DORA and Flow metrics are **calculated weekly** (ISO week: Monday-Sunday) and stored as snapshots in `metrics_snapshots.json`. The UI displays these pre-calculated snapshots for performance.

## Time Periods & Aggregation Strategy

### Weekly Bucketing (ISO Weeks)
- **Week Definition**: Monday to Sunday (ISO 8601 standard)
- **Week Labels**: Format `YYYY-WW` (e.g., "2025-45")
- **Data Points Slider**: Controls how many historical weeks to display (default: 12 weeks)

### When Metrics Are Calculated
- **Manual Trigger**: User clicks "Calculate Metrics" button in Settings
- **Process**: Calculates metrics for last N weeks and saves to `metrics_snapshots.json`
- **Duration**: ~2 minutes for 12 weeks of data
- **Display**: Instant (reads from cache)

---

## DORA Metrics (DevOps Research & Assessment)

### 1. Deployment Frequency

**What it measures**: How often deployments happen to production

**Important Distinction**: 
- **Deployment** = An operational task (deployment activity/process)
- **Release** = A unique fixVersion (the actual code release)
- **Example**: 2 operational tasks with fixVersion `R_20251104_www.example.com` = **2 deployments, 1 release**

**Calculation Method**:
- **Per Week (Deployments)**: COUNT of operational tasks with `fixVersion.releaseDate` in that week
- **Per Week (Releases)**: COUNT of UNIQUE fixVersion names in that week
- **Absolute Count**: Each week shows actual numbers
- **Filtering**:
  - Only tasks where `status IN completion_statuses` (Done, Closed, etc.)
  - Only tasks with `fixVersion.releaseDate <= today` (excludes future deployments)
  - Uses **earliest releaseDate** if multiple fixVersions exist

**Display Value** (Card):
- **Primary Unit**: `deployments/week (avg Nw)`
- **Primary Calculation**: `AVERAGE(weekly_deployment_counts)` across N weeks
- **Secondary Display**: `releases/week` (shown below primary value)
- **Secondary Calculation**: `AVERAGE(weekly_release_counts)` across N weeks
- **Example**: 12 weeks with deployment counts `[2, 3, 4, 2, 5, 3, 2, 4, 3, 2, 3, 4]` and release counts `[1, 2, 3, 1, 3, 2, 1, 2, 2, 1, 2, 3]`
  - Average deployments = 3.1 deployments/week
  - Average releases = 1.9 releases/week

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels (2025-45, 2025-46, etc.)
- **Y-axis**: Absolute deployment count for that week
- **Values**: Each point = actual deployments in that week (NOT cumulative, NOT average)
- **Note**: Currently shows deployments only. Could be enhanced to show both metrics or releases separately.

**Trend Line**:
- Shows progression of weekly deployment frequency over time

**Why Track Both?**:
- Multiple operational tasks (deployments) for one release indicates:
  - Complex deployment process (multiple stages: staging → production)
  - Deployment rollback and retry scenarios
  - Multiple environment deployments tracked separately
- Helps identify deployment efficiency vs. release cadence

**Code Location**: `data/dora_calculator.py::calculate_deployment_frequency_v2()` and `aggregate_deployment_frequency_weekly()`

---

### 2. Lead Time for Changes

**What it measures**: Time from code deployment-ready to deployed in production

**Calculation Method**:
- **Start Time**: First "In Deployment" status timestamp (from changelog)
  - **Fallback**: First "Done" status if never reached "In Deployment"
- **End Time**: Matching operational task's `fixVersion.releaseDate`
  - Matching logic: Development issue fixVersion ID matches operational task fixVersion ID
  - **Fallback**: Issue's `resolutiondate` if no operational task found
- **Time Unit**: **HOURS**
- **Per Week**: All issues where deployment happened in that week
- **Aggregation**: **MEDIAN** of all lead times in that week (not mean - robust to outliers)

**Display Value** (Card):
- **Primary Unit**: `days (16w median avg)`
- **Primary Calculation**: 
  1. Calculate median hours for each week
  2. Convert to days: `median_hours / 24`
  3. Average the weekly medians: `AVERAGE(weekly_median_days)` across 16 weeks
- **Secondary Display**: P95 and Mean averages (shown below primary value)
  - **P95**: 95th percentile - only 5% of issues take longer than this
  - **Mean**: Arithmetic average - useful for capacity planning
  - Both averaged across the same 16-week period
- **Example**: 
  - Week 1: Issues with lead times [24h, 48h, 72h] → Median = 48h (2d), Mean = 48h (2d), P95 = 67.2h (2.8d)
  - Week 2: Issues with lead times [36h, 60h] → Median = 48h (2d), Mean = 48h (2d), P95 = 57.6h (2.4d)
  - Averages: Median = 2d, Mean = 2d, P95 = 2.6d
- **Card Display**:
  - Primary: "2 days (16w median avg)"
  - Secondary: "📊 P95: 2.6d • Avg: 2d"

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Median lead time in **days** for that week
- **Values**: Each point = median of all lead times in that week

**Why Median, Not Mean?**
- Outliers (e.g., 1 issue taking 200 hours) don't skew the metric
- More representative of "typical" lead time

**Why Show P95 and Mean?**
- **P95**: Helps identify outliers and set realistic SLAs (95% of changes complete within this time)
- **Mean**: Useful for capacity planning and resource allocation
- Together they provide a complete picture of lead time distribution

**Code Location**: `data/dora_calculator.py::calculate_lead_time_for_changes_v2()` and `aggregate_lead_time_weekly()`

---

### 3. Change Failure Rate (CFR)

**What it measures**: Percentage of deployments that fail and require remediation

**Calculation Method**:
- **Per Week**: 
  - Total deployments = COUNT(operational tasks with releaseDate in week)
  - Failed deployments = COUNT(operational tasks with `customfield_10001 == "Yes"`)
  - CFR = `(failed / total) × 100`
- **Critical**: ONLY `"Yes"` (case-insensitive) indicates failure
  - `"No"`, `"None"`, `null`, empty = success
- **Filtering**: Same as Deployment Frequency (completion statuses, releaseDate <= today)

**Display Value** (Card):
- **Unit**: `% (agg Nw)` (agg = aggregated)
- **Calculation**: **AGGREGATE** across N weeks, NOT average of weekly rates
  - `total_deployments = SUM(all weekly deployment counts)`
  - `total_failures = SUM(all weekly failure counts)`
  - `CFR = (total_failures / total_deployments) × 100`
- **Example**:
  - Week 1: 10 deployments, 1 failure → 10%
  - Week 2: 20 deployments, 0 failures → 0%
  - Aggregate: (1 / 30) × 100 = 3.3% ✓ (NOT (10% + 0%) / 2 = 5% ✗)

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Failure rate **percentage** for that week
- **Values**: Each point = `(failures / deployments) × 100` for that week

**Why Aggregate, Not Average?**
- Prevents weeks with few deployments from skewing the metric
- More accurate representation of overall failure rate

**Code Location**: `data/dora_calculator.py::calculate_change_failure_rate_v2()` and `aggregate_change_failure_rate_weekly()`

---

### 4. Mean Time to Recovery (MTTR)

**What it measures**: Time from production bug creation to fix deployed

**Calculation Method**:
- **Bug Filtering**: 
  - Issue type = "Bug"
  - `customfield_10002 == "PROD"` (exact match, case-sensitive)
- **Start Time**: `bug.fields.created` (when bug was reported)
- **End Time**: 
  - **Preferred**: Matching operational task's `fixVersion.releaseDate`
  - **Fallback**: Bug's `resolutiondate` if no operational task found
- **Time Unit**: **HOURS**
- **Per Week**: All bugs where fix was deployed in that week
- **Aggregation**: **MEDIAN** of all recovery times in that week

**Display Value** (Card):
- **Primary Unit**: `hours (16w median avg)`
- **Primary Calculation**:
  1. Calculate median hours for each week
  2. Average the weekly medians: `AVERAGE(weekly_median_hours)` across 16 weeks
- **Secondary Display**: P95 and Mean averages (shown below primary value)
  - **P95**: 95th percentile - only 5% of bugs take longer to fix
  - **Mean**: Arithmetic average - useful for capacity planning
  - Both averaged across the same 16-week period
- **Example**:
  - Week 1: Bugs with recovery times [12h, 24h, 48h] → Median = 24h, Mean = 28h, P95 = 44.4h
  - Week 2: Bugs with recovery times [18h, 36h] → Median = 27h, Mean = 27h, P95 = 34.2h
  - Averages: Median = 25.5h, Mean = 27.5h, P95 = 39.3h
- **Card Display**:
  - Primary: "25.5 hours (16w median avg)"
  - Secondary: "📊 P95: 39.3h • Avg: 27.5h"

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Median MTTR in **hours** for that week
- **Values**: Each point = median of all recovery times in that week

**Why Show P95 and Mean?**
- **P95**: Helps set incident response SLAs (95% of bugs fixed within this time)
- **Mean**: Useful for team capacity planning and on-call rotations
- Together they help identify both typical recovery time and worst-case scenarios

**Code Location**: `data/dora_calculator.py::calculate_mttr_v2()` and `aggregate_mttr_weekly()`

---

## Flow Metrics (Flow Framework - Mik Kersten)

### 1. Flow Velocity

**What it measures**: Number of work items completed per time period

**Calculation Method**:
- **Per Week**: COUNT of issues with `status IN completion_statuses` AND `resolutiondate` in that week
- **Classification**: Two-tier system using `flow_type_mappings` from `app_settings.json`:
  - **Primary**: Issue type (Bug → Defect, Story/Task → Feature by default)
  - **Secondary**: Effort category (overrides primary for Task/Story only)
    - "Technical debt" → Technical Debt
    - "Security", "GDPR", etc. → Risk
    - Otherwise → Feature
- **Absolute Count**: Each week shows actual number of completed items

**Display Value** (Card):
- **Unit**: `items/week` (current week only, NOT average)
- **Calculation**: Total items completed in the **most recent week**
- **Example**: Week 2025-45 completed 25 items → Display: "25 items/week"

**Breakdown**:
- Feature: X items
- Defect: Y items
- Tech Debt: Z items
- Risk: W items

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Absolute count of completed items for that week
- **Values**: Each point = actual completions in that week

**Stacked Area Chart** (Work Distribution Over Time):
- Shows how work types (Feature/Defect/Tech Debt/Risk) evolved week by week
- Hover shows percentages for each work type

**Code Location**: `data/flow_calculator.py::calculate_flow_velocity_v2()` and `aggregate_flow_velocity_weekly()`

---

### 2. Flow Time

**What it measures**: Average time from work start to completion

**Calculation Method**:
- **Start Time**: First transition to ANY `wip_statuses` (from changelog)
  - Example wip_statuses: ["Selected", "In Progress", "In Review", "Testing"]
- **End Time**: `resolutiondate` field
- **Time Unit**: **DAYS** (calculated as hours / 24)
- **Per Week**: All issues that completed (resolutiondate) in that week
- **Aggregation**: **MEDIAN** of all flow times in that week

**Display Value** (Card):
- **Unit**: `days (avg Nw)`
- **Calculation**:
  1. Calculate median days for each week
  2. Average the weekly medians: `AVERAGE(weekly_median_days)` across N weeks
- **Example**:
  - Week 1: Issues with flow times [2d, 4d, 6d] → Median = 4d
  - Week 2: Issues with flow times [3d, 5d] → Median = 4d
  - Average = (4 + 4) / 2 = 4 days

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Median flow time in **days** for that week
- **Values**: Each point = median of all flow times in that week

**Code Location**: `data/flow_calculator.py::calculate_flow_time_v2()` and `aggregate_flow_time_weekly()`

---

### 3. Flow Efficiency

**What it measures**: Percentage of time spent actively working vs. waiting

**Calculation Method**:
- **Active Time**: Total time in `active_statuses` (from changelog)
  - Example: ["In Progress", "In Review", "Testing"]
- **Total WIP Time**: Total time in `wip_statuses` (from changelog)
  - Example: ["Selected", "In Progress", "In Review", "Testing", "Ready for Testing"]
- **Efficiency**: `(active_time / wip_time) × 100`
- **Per Week**: All issues that completed in that week
- **Aggregation**: 
  1. Sum all active hours across all issues in week
  2. Sum all WIP hours across all issues in week
  3. `(total_active / total_wip) × 100`

**Display Value** (Card):
- **Unit**: `%` (current week only, NOT average)
- **Calculation**: Efficiency percentage for the **most recent week**
- **Example**: Week 2025-45 had 420h active, 720h WIP → (420/720)×100 = 58.3%

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Efficiency percentage for that week
- **Values**: Each point = `(total_active / total_wip) × 100` for that week

**Healthy Range**: 25-40% (higher = less waiting, but 100% = no buffer/planning time)

**Code Location**: `data/flow_calculator.py::calculate_flow_efficiency_v2()` and `aggregate_flow_efficiency_weekly()`

---

### 4. Flow Load (WIP)

**What it measures**: Current work-in-progress count

**Calculation Method**:
- **Per Week**: COUNT of issues where `status IN wip_statuses` at end of that week
- **Snapshot**: Point-in-time measurement (not cumulative)
- **wip_statuses** from config (e.g., ["Selected", "In Progress", "Testing", etc.])

**Display Value** (Card):
- **Unit**: `items` (current week only)
- **Calculation**: WIP count for the **most recent week**
- **Example**: Week 2025-45 had 15 items in progress → Display: "15 items"

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: WIP count for that week
- **Values**: Each point = actual WIP at end of that week

**Code Location**: `data/flow_calculator.py::calculate_flow_load_v2()` and `aggregate_flow_load_weekly()`

---

### 5. Flow Distribution

**What it measures**: Percentage breakdown of work by type

**Calculation Method**:
- **Per Week**: For all completed items in that week:
  - Count by Flow type (Feature, Defect, Tech Debt, Risk)
  - Calculate percentages: `(count / total) × 100`
- **Recommended Ranges**:
  - Feature: 40-60%
  - Defect: 20-40%
  - Tech Debt: 10-20%
  - Risk: 0-10%

**Display Value** (Card shows Stacked Area Chart):
- **X-axis**: Week labels
- **Y-axis**: Count of items by type (stacked)
- **Hover**: Shows percentage for each type
- **Current Week Summary**: Shows counts and percentages with range indicators

**Code Location**: `data/flow_calculator.py::aggregate_flow_distribution_weekly()`

---

## Summary Table: Time Units & Aggregations

| Metric                   | Time Unit        | Per-Week Aggregation         | Card Display                               | Secondary Info | Chart Y-Axis   |
| ------------------------ | ---------------- | ---------------------------- | ------------------------------------------ | -------------- | -------------- |
| **Deployment Frequency** | N/A (count)      | SUM (absolute count)         | AVERAGE of weekly counts (16w median avg)  | Releases/week  | Absolute count |
| **Lead Time**            | Hours → Days     | MEDIAN of all lead times     | AVERAGE of weekly medians (16w median avg) | P95 + Mean     | Median days    |
| **Change Failure Rate**  | N/A (percentage) | % of failures                | AGGREGATE % across all weeks (16w agg)     | Releases/week  | Weekly %       |
| **MTTR**                 | Hours            | MEDIAN of all recovery times | AVERAGE of weekly medians (16w median avg) | P95 + Mean     | Median hours   |
| **Flow Velocity**        | N/A (count)      | SUM (absolute count)         | Current week count                         | None           | Absolute count |
| **Flow Time**            | Hours → Days     | MEDIAN of all flow times     | AVERAGE of weekly medians                  | None           | Median days    |
| **Flow Efficiency**      | N/A (percentage) | % active/WIP                 | Current week %                             | None           | Weekly %       |
| **Flow Load**            | N/A (count)      | COUNT at week end            | Current week count                         | None           | Absolute count |
| **Flow Distribution**    | N/A (percentage) | % by type                    | Stacked area chart                         | None           | Count by type  |

**Notes**:
- **16w median avg**: Primary values average the weekly medians over a 16-week rolling window
- **16w agg**: CFR aggregates failures/deployments across all 16 weeks (not averaged)
- **P95 + Mean**: Secondary statistics shown below primary value for Lead Time and MTTR
- **Releases/week**: Secondary metric for Deployment Frequency and CFR cards

---

## Integration with Other App Statistics

### Weekly Statistics (`project_data.json`)
- **Burndown Metrics**: Uses same ISO week bucketing
- **Velocity Tracking**: Completed items and story points per week
- **Scope Changes**: Weekly additions to backlog
- **Consistency**: All weekly metrics share same Monday-Sunday boundaries

### Data Points Slider
- **Purpose**: Control historical depth (how many weeks to display)
- **Default**: 12 weeks
- **Applies To**: Both DORA and Flow metrics
- **Performance**: Reading cached snapshots is instant regardless of N

---

## Fallback Behavior & Logging

### When Data is Missing

**Deployment Frequency**:
- No operational tasks → 0 deployments
- Future releaseDate → Excluded (logged)
- No releaseDate → Excluded (logged)

**Lead Time**:
- No "In Deployment" status → Falls back to "Done" status
- No operational task → Falls back to issue's resolutiondate
- No deployment date → Excluded (logged as "no_operational_task_count")

**Change Failure Rate**:
- No change failure field → Uses placeholder, all treated as success
- Non-"Yes" values → Treated as success

**MTTR**:
- Not "PROD" environment → Excluded (logged as "not_production_count")
- No fix deployed date → Excluded (logged as "no_fix_deployed_count")
- Case mismatch ("prod" vs "PROD") → Included but warning logged

**Flow Metrics**:
- No changelog → Issue excluded from Flow Time and Flow Efficiency
- Never entered WIP → Excluded from Flow Time (logged as "no_wip_transition_count")

---

## Logging Strategy

### Current Issues
- **Volume**: Verbose logging during calculation (INFO level for every issue)
- **Duration**: 2-minute calculation generates 10,000+ log lines
- **Difficulty**: Hard to track fallbacks and excluded issues

### Recommended Optimization
1. **Reduce Per-Issue Logging**: Use DEBUG level for individual issues
2. **Summary Logging**: INFO level for week-level summaries
3. **Structured Exclusion Counts**: Log counts at end of each week
4. **Progress Indicators**: Show "Week X/N" instead of per-issue progress

Example optimized log:
```
INFO: Week 2025-45: Deployment Frequency: 12 deployments (excluded 2: 1 future, 1 no releaseDate)
INFO: Week 2025-45: Lead Time: Median 48.0h from 25 issues (excluded 8: 3 no deployment, 5 no changelog)
INFO: Week 2025-45: CFR: 8.3% (1/12 failed) (excluded 0)
INFO: Week 2025-45: MTTR: Median 24.0h from 3 bugs (excluded 5: 2 not PROD, 3 no fix)
```

---

## Verification Checklist

To verify metrics are correct:

1. **Check Field Mappings** (`app_settings.json`):
   - `deployment_date`: "fixVersions"
   - `change_failure`: "customfield_10001" (or your field)
   - `affected_environment`: "customfield_10002" (or your field)
   - `effort_category`: "customfield_10003" (or your field)

2. **Check Project Config**:
   - `devops_projects`: ["RI"] (operational tasks project)
   - `development_projects`: ["A935"] (development issues project)
   - `production_environment_values`: ["PROD"]

3. **Check Status Config**:
   - `completion_statuses`: ["Done", "Resolved", "Closed", "Canceled"]
   - `wip_statuses`: ["Selected", "In Progress", "Testing", ...]
   - `active_statuses`: ["In Progress", "In Review", "Testing"]

4. **Check Flow Type Mappings**:
   - Verify `flow_type_mappings` has correct effort category values
   - Test with sample issues to ensure classification works

5. **Verify Calculations**:
   - Pick one week
   - Manually count deployments from operational tasks
   - Compare with metric value
   - Check excluded counts in logs

---

## Performance Optimization Opportunities

### Current Performance
- **Calculation**: ~2 minutes for 12 weeks
- **Display**: Instant (reads from cache)
- **Bottleneck**: Changelog processing for Flow Time/Efficiency

### Optimization Ideas
1. **Parallel Processing**: Calculate weeks in parallel (ThreadPoolExecutor)
2. **Changelog Caching**: Pre-process changelog once, reuse for all metrics
3. **Incremental Updates**: Only recalculate changed weeks
4. **Reduced Logging**: Switch to DEBUG for per-issue logs
5. **Batch JIRA Queries**: Fetch all needed data in one query

Estimated improvement: 2 minutes → 30 seconds

---

## Questions & Clarifications

**Q: Why median instead of mean for Lead Time/MTTR?**  
A: Median is robust to outliers. One issue taking 200 hours shouldn't skew the "typical" lead time.

**Q: Why aggregate CFR instead of average?**  
A: Weeks with few deployments would skew the average. Aggregate is more accurate.

**Q: Why is Flow Velocity showing current week, not average?**  
A: Flow Velocity is a "current state" metric (like WIP). For trends, use the scatter chart.

**Q: How do I know if field mapping is wrong?**  
A: Check "excluded_count" in logs. High exclusions = likely mapping issue.

**Q: Can I change the week boundaries?**  
A: Yes, but requires code change in `data/time_period_calculator.py`. ISO weeks are standard.

**Q: Why are DORA metrics showing "N/A"?**  
A: No data found for that metric in the time period. Check:

- Operational tasks exist with fixVersions
- releaseDate is populated and in the past
- Field mappings are correct
- Issues match completion statuses

---

**Last Updated**: November 7, 2025  
**Maintained By**: Development Team
