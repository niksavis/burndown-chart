# DORA & Flow Metrics - Complete Explanation

**Created**: November 7, 2025  
**Purpose**: Clarify what each metric calculates, time units, aggregations, and data presentation

## Overview

All DORA and Flow metrics are **calculated weekly** (ISO week: Monday-Sunday) and stored as snapshots in `metrics_snapshots.json`. The UI displays these pre-calculated snapshots for performance.

---

## Quick Start Guide

**New to DORA & Flow Metrics?** Start here:

### Week 1: Focus on These Core Metrics

1. **Deployment Frequency** (DORA) - How often you ship to production
   - **Why first**: Easy to measure, immediate visibility into delivery cadence
   - **Goal**: Aim for at least weekly deployments (Medium tier)
   - **Quick win**: Track current rate, set weekly deployment goal

2. **Flow Load (WIP)** (Flow) - How much work is in progress
   - **Why second**: Single biggest lever for improving speed
   - **Goal**: Keep WIP below calculated healthy threshold (green zone)
   - **Quick win**: Stop starting new work until WIP drops below warning threshold

3. **Flow Velocity** (Flow) - How much work you complete per week
   - **Why third**: Baseline for capacity planning and forecasting
   - **Goal**: Establish consistent, predictable throughput
   - **Quick win**: Track for 4 weeks to establish baseline velocity

### Week 2-4: Add Quality & Speed Metrics

4. **Change Failure Rate** (DORA) - Percentage of deployments that fail
   - **Goal**: Keep below 15% (Elite tier)
   - **Action**: If >30%, pause new features and fix deployment process

5. **Lead Time for Changes** (DORA) - Time from code ready to deployed
   - **Goal**: Under 1 week (Medium tier), under 1 day (High tier)
   - **Action**: If >1 week, investigate deployment bottlenecks

6. **Flow Time** (Flow) - Time from start to completion
   - **Goal**: Consistent, predictable cycle time (varies by team)
   - **Action**: If increasing, check WIP and identify blockers

### Beyond Week 4: Optimize

7. **MTTR** (DORA) - Time to recover from production incidents
8. **Flow Efficiency** (Flow) - Active work time vs. waiting time
9. **Flow Distribution** (Flow) - Balance of feature/defect/tech debt/risk work

**Progressive Approach**: Don't try to optimize all metrics at once. Focus on 2-3 at a time, establish baselines, then expand.

---

## Metric Relationships: How They Connect

Understanding how metrics interact helps you make better decisions:

### The WIP-Speed Connection (Most Important!)

```
High WIP → Slower Flow Time → Slower Lead Time → Lower Deployment Frequency
  ↓
Context Switching + Blocked Items + Lost Focus
```

**Why it matters**: Flow Load (WIP) is your control lever. Reduce WIP → Everything else improves.

**Example**:
- Team has 45 items in WIP (Critical) with 8-day Flow Time
- Reduce WIP to 15 items (Warning) → Flow Time drops to 5 days
- Faster Flow Time → Faster Lead Time → More frequent deployments

### The Quality-Speed Balance

```
Fast Deployment + Low CFR = Elite Performance ✅
Fast Deployment + High CFR = Technical Debt Accumulation ❌
Slow Deployment + Low CFR = Risk Aversion (missing opportunities) ⚠️
```

**Optimal Zone**: Deploy frequently (≥1/week) while maintaining CFR <15%.

**Warning Signs**:
- CFR >30% + Increasing Deployment Frequency = Quality problems, slow down!
- CFR <5% + Low Deployment Frequency = Overengineering, ship more!

### The Efficiency Paradox

```
Flow Efficiency = Active Time / Total Time

100% Efficiency = No buffer time = System overload ❌
  0% Efficiency = All waiting = Process broken ❌
25-40% Efficiency = Healthy balance = Sustainable pace ✅
```

**Counterintuitive**: Lower efficiency (25-40%) is BETTER than higher efficiency (>60%) because:
- Teams need planning time, code review time, testing time
- Buffer capacity prevents cascading delays when issues arise
- Sustainable pace prevents burnout

**Action**: If efficiency >60%, you're likely overloaded (check WIP). If <20%, investigate bottlenecks.

### The Distribution-Quality Connection

```
Feature Work >70% + Defect Work <10% = Future quality problems ⚠️
Feature Work <40% + Defect Work >40% = Already in quality crisis ❌
Balanced: Features 40-60%, Defects 20-40%, Tech Debt 10-20% ✅
```

**Leading Indicator**: Flow Distribution predicts future CFR and MTTR.

**Warning Signs**:
- Skewing toward features (>70%) → Expect CFR to rise in 4-8 weeks
- Skewing toward defects (>40%) → Quality crisis already in progress

---

## Common Pitfalls & Anti-Patterns

Avoid these mistakes when using metrics:

### 1. Gaming the Metrics ❌

**Anti-Pattern**: Optimizing one metric at the expense of others.

**Examples**:
- Deploying tiny changes constantly to boost Deployment Frequency (but Lead Time stays high)
- Classifying production bugs as non-PROD to lower MTTR
- Splitting work into tiny tasks to boost Flow Velocity (but nothing valuable ships)

**Solution**: Always view metrics as a **balanced scorecard**. Elite teams excel across ALL metrics, not just one.

### 2. Comparing Across Teams ❌

**Anti-Pattern**: Using metrics to rank teams or individuals.

**Why it fails**:
- Different team contexts (greenfield vs. legacy, microservices vs. monolith)
- Different business constraints (compliance, security requirements)
- Creates perverse incentives (gaming, sandbagging, hiding problems)

**Solution**: Each team competes against their **own historical baseline**, not other teams.

### 3. Setting Arbitrary Targets ❌

**Anti-Pattern**: "All teams must achieve Elite tier in all metrics by Q2."

**Why it fails**:
- Ignores team context and constraints
- Creates pressure to game metrics
- Elite tier may not be necessary or cost-effective for all contexts

**Solution**: Set goals based on **business impact** ("reduce customer-impacting incidents by 50%") and let metrics guide improvement.

### 4. Focusing on Lagging Indicators Only ❌

**Anti-Pattern**: Only tracking DORA metrics (outcomes) without Flow metrics (process).

**Why it fails**:
- DORA metrics tell you WHAT happened, not WHY
- Can't improve what you don't measure at the process level

**Solution**: Use Flow metrics to understand and improve the process. DORA metrics validate that improvements worked.

**Example**:
- DORA: "Lead Time increased 30% this month" ← What happened
- Flow: "WIP increased from 15 to 35 items" ← Why it happened
- Action: "Implement WIP limits to restore Lead Time" ← How to fix

### 5. Analysis Paralysis ❌

**Anti-Pattern**: Calculating every metric, creating dashboards, but never taking action.

**Why it fails**:
- Metrics are a means to improvement, not the end goal
- Data without action is waste

**Solution**: For each metric review, identify 1-2 **actionable experiments**:
- "Try WIP limit of 12 items for 2 weeks, measure impact on Flow Time"
- "Add automated deployment tests, measure impact on CFR"

### 6. Ignoring Outliers ❌

**Anti-Pattern**: Only looking at median/average values.

**Why it fails**:
- P95 values reveal worst-case scenarios that frustrate customers
- Long tail issues indicate systemic problems

**Solution**: Always check P95 alongside median. If P95 is 3x+ higher than median, investigate outliers.

### 7. Short-Term Thinking ❌

**Anti-Pattern**: Reacting to week-to-week fluctuations.

**Why it fails**:
- Metrics naturally vary week to week
- Overreacting creates thrashing

**Solution**: Look for **trends over 4+ weeks**. One bad week is noise. Four bad weeks is a signal.

---

## Reading the Metric Cards (Visual Guide)

Each metric card provides multiple visual signals to help you quickly assess performance:

### Performance Tier Badge
- **Elite** (Green): Top-tier performance per DORA/Flow standards
- **High** (Blue): Above average performance
- **Medium** (Yellow): Average performance, room for improvement
- **Low** (Red): Below average, needs attention
- **Special for Flow Load (WIP)**: Shows health status instead
  - **Healthy** (Green): <10 items in progress
  - **Warning** (Yellow): 10-19 items
  - **High** (Orange): 20-29 items
  - **Critical** (Red): ≥30 items

### Trend Indicators (Below Main Value)
Shows how the current period compares to historical average:

- **→ (Right Arrow, Gray)**: Stable - exactly 0.0% change from previous average
  - Example: "→ 0.0% vs prev avg"
  - Indicates consistent, predictable performance
  
- **↑ (Up Arrow)**: Increase of ≥5% from previous average
  - **Green**: Good improvement (Deployment Frequency)
  - **Red**: Concerning increase (Lead Time, MTTR, CFR, WIP)
  - Example: "↑ 12.5% vs prev avg"
  
- **↓ (Down Arrow)**: Decrease of ≥5% from previous average
  - **Green**: Good improvement (Lead Time, MTTR, CFR, WIP)
  - **Red**: Concerning decrease (Deployment Frequency)
  - Example: "↓ 8.3% vs prev avg"
  
- **− (Minus, Gray)**: Small change (<5%) or insufficient historical data
  - Example: "− 2.1% vs prev avg" or "− No trend data yet"
  - Indicates stability within normal variance

**How to Read Trends**:
- Compare current period's median/average to previous periods' average
- Helps identify improving/degrading trends before they become critical
- Gray indicators (→ and −) mean "stable" - neither good nor bad

### Secondary Metrics (Below Trend)
Provides additional context for deeper analysis:

**For Deployment Frequency & Change Failure Rate**:
- Shows unique releases (vs. deployment tasks)
- Example: "📦 1.9 releases/week"
- Helps distinguish release cadence from deployment process complexity

**For Lead Time & MTTR**:
- **P95**: 95th percentile - worst-case scenarios (5% of issues exceed this)
- **Mean**: Arithmetic average - capacity planning baseline
- Example: "📊 P95: 12.5d • Avg: 8.2d"
- Useful for SLA setting and identifying outliers

### Inline Sparkline
- Mini-chart below secondary metrics shows weekly trend
- Quick visual pattern recognition (upward/downward/stable)
- Colored by performance tier

### Card Height Consistency
All cards maintain uniform height regardless of data availability:
- Cards with trends show trend indicators
- Cards without sufficient data show "No trend data yet" placeholder
- Ensures clean, professional grid layout

### Detail Charts (Click to Expand)
Click any DORA metric card to view detailed weekly breakdown:

**DORA Metrics - Performance Tier Zones**:
- Background zones show Elite/High/Medium/Low thresholds
- Your weekly data points plotted against industry standards
- Helps visualize where you are vs. where you want to be
- Color-coded zones:
  - **Green**: Elite performance (top 10% of teams)
  - **Blue**: High performance (top 25%)
  - **Yellow**: Medium performance (top 50%)
  - **Red**: Low performance (needs improvement)
- Example: Lead Time chart shows zones at <1h (Elite), 1d-1w (High), 1w-1mo (Medium), >1mo (Low)

**Flow Metrics - Trend Analysis**:
- Standard trend charts without zones (no universal Flow standards exist)
- Focus on your team's historical patterns and trends
- Useful for tracking improvements over time

**Work Distribution Breakdown**:
- Stacked area chart shows Feature/Defect/Tech Debt/Risk evolution over time
- **Mobile-First Design**: Target zones clearly visible with 15-18% opacity for immediate value
- **Enhanced Hover**: Shows current percentage, item count, and target range for each work type
- **Progressive Disclosure**: Target ranges shown in subtitle and hover details
- **Responsive Layout**: Horizontal legend below chart (mobile-friendly) vs. vertical sidebar (desktop)
- **Visual Zones**: Color-coded target ranges make it easy to assess healthy work balance
  - **Green Zone (40-60%)**: Feature work - new capabilities and business value
  - **Red Zone (20-40%)**: Defect work - quality maintenance and bug fixes  
  - **Orange Zone (10-20%)**: Tech Debt - infrastructure and sustainability
  - **Yellow Zone (0-10%)**: Risk work - security, compliance, prevention
- Current week summary with recommended ranges and indicators
- Helps maintain healthy work balance and identify portfolio imbalances

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
- **Trend Indicator**: Shows % change vs. previous average (↑ green = good, ↓ red = concerning)
- **Performance Badge**: Elite (≥30/mo) → High (≥7/mo) → Medium (≥1/mo) → Low (<1/mo)
- **Example**: 12 weeks with deployment counts `[2, 3, 4, 2, 5, 3, 2, 4, 3, 2, 3, 4]` and release counts `[1, 2, 3, 1, 3, 2, 1, 2, 2, 1, 2, 3]`
  - Average deployments = 3.1 deployments/week
  - Average releases = 1.9 releases/week
  - Card shows: "3.1 deployments/week" with "📦 1.9 releases/week" below

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels (2025-45, 2025-46, etc.)
- **Y-axis**: Absolute deployment count for that week
- **Values**: Each point = actual deployments in that week (NOT cumulative, NOT average)
- **Background Zones**: Elite/High/Medium/Low performance tiers per DORA standards
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
- **Trend Indicator**: Shows % change vs. previous average (↓ green = improvement, ↑ red = regression)
- **Performance Badge**: Elite (<1h) → High (<1d) → Medium (<1w) → Low (>1w)
- **Example**: 
  - Week 1: Issues with lead times [24h, 48h, 72h] → Median = 48h (2d), Mean = 48h (2d), P95 = 67.2h (2.8d)
  - Week 2: Issues with lead times [36h, 60h] → Median = 48h (2d), Mean = 48h (2d), P95 = 57.6h (2.4d)
  - Averages: Median = 2d, Mean = 2d, P95 = 2.6d
- **Card Display**:
  - Primary: "2 days (16w median avg)"
  - Trend: "↓ 5.2% vs prev avg" (green = improving)
  - Secondary: "📊 P95: 2.6d • Avg: 2d"

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Median lead time in **days** for that week
- **Values**: Each point = median of all lead times in that week
- **Background Zones**: Elite/High/Medium/Low performance tiers per DORA standards

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
- **Trend Indicator**: Shows % change vs. previous average (↓ green = improvement, ↑ red = regression)
- **Performance Badge**: Elite (0-15%) → High (16-30%) → Medium (31-45%) → Low (>45%)
- **Special Case**: Shows "→ 0.0% vs prev avg" when stable at 0% (no failures)
- **Example**:
  - Week 1: 10 deployments, 1 failure → 10%
  - Week 2: 20 deployments, 0 failures → 0%
  - Aggregate: (1 / 30) × 100 = 3.3% ✓ (NOT (10% + 0%) / 2 = 5% ✗)
  - Card shows: "3.3%" with "→ 0.0% vs prev avg" if stable

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Failure rate **percentage** for that week
- **Values**: Each point = `(failures / deployments) × 100` for that week
- **Background Zones**: Elite/High/Medium/Low performance tiers per DORA standards

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
- **Trend Indicator**: Shows % change vs. previous average (↓ green = improvement, ↑ red = regression)
- **Performance Badge**: Elite (<1h) → High (<1d) → Medium (<1w) → Low (>1w)
- **Example**:
  - Week 1: Bugs with recovery times [12h, 24h, 48h] → Median = 24h, Mean = 28h, P95 = 44.4h
  - Week 2: Bugs with recovery times [18h, 36h] → Median = 27h, Mean = 27h, P95 = 34.2h
  - Averages: Median = 25.5h, Mean = 27.5h, P95 = 39.3h
- **Card Display**:
  - Primary: "25.5 hours (16w median avg)"
  - Trend: "↓ 3.8% vs prev avg" (green = improving)
  - Secondary: "📊 P95: 39.3h • Avg: 27.5h"

**Scatter Chart** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: Median MTTR in **hours** for that week
- **Values**: Each point = median of all recovery times in that week
- **Background Zones**: Elite/High/Medium/Low performance tiers per DORA standards

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
- **wip_statuses** from config (e.g., ["Selected", "In Progress", "Testing", "Ready for Testing", "In Deployment"])

**Historical Reconstruction**:
For historical weeks, the system reconstructs what WIP was at that specific point in time:

1. **Load All Issues** from cache (development project only, excludes operational projects)
2. **Determine Week End Time**:
   - Historical weeks: Sunday 23:59:59 of that week
   - Current week: NOW (running total)
3. **Reconstruct Status for Each Issue**:
   - **Current Week**: Use current status directly (faster, includes issues without changelog)
   - **Historical Weeks**: Replay changelog history
     - Find LAST status change BEFORE week end
     - If issue was in WIP status at that time → count it
     - If no changelog exists → use current status (assumes issue stayed in same status)
4. **Count Issues** where reconstructed status is in `wip_statuses` AND resolution is empty

**Example Timeline**:
```
Issue DEV-123 (Task):
├─ Created: Week 10 (status: "To Do")
├─ Week 15: Moved to "Selected" ← WIP starts, counted in W15+
├─ Week 20: Moved to "In Progress" ← Still in WIP
├─ Week 25: Moved to "Done" ← WIP ends, not counted from W25+

Week-by-week WIP count for this issue:
W10-W14: NOT counted (status = "To Do", not in wip_statuses)
W15-W24: COUNTED (status in wip_statuses)
W25+: NOT counted (status = "Done", in completion_statuses)
```

**Issue Filtering**:
- ✅ **Development Project** issues only (e.g., project key "DEV")
- ✅ **Issue Types**: Task, Story, Bug (configurable)
- ❌ **Operational/DevOps** projects excluded (used only for DORA deployment tracking)
- ❌ **Operational Task** issue type excluded

**Dynamic Health Thresholds (Little's Law)**:

The health badge thresholds are **calculated from your team's historical data** using Little's Law from queueing theory:

**Formula**: `Optimal WIP = Throughput × Cycle Time`
- **Throughput**: Weekly velocity (items completed per week)
- **Cycle Time**: Flow time in days (time from start to completion)

**Calculation Process**:
1. For each historical week with data:
   - `optimal_wip = velocity × (flow_time_days / 7)`
   - Example: 18 items/week × (6 days / 7) = 15.4 optimal WIP
2. Collect all optimal WIP values across historical period
3. Calculate percentiles from distribution:
   - **P25** (25th percentile): 25% of weeks had WIP below this
   - **P50** (median): 50% of weeks had WIP below this
   - **P75** (75th percentile): 75% of weeks had WIP below this
   - **P90** (90th percentile): Only 10% of weeks exceeded this
4. Apply 20% stability buffers to create zones:
   - **Healthy** (Green): < P25 × 1.2 (below 25th percentile with buffer)
   - **Warning** (Yellow): < P50 × 1.2 (below median with buffer)
   - **High** (Orange): < P75 × 1.2 (below 75th percentile with buffer)
   - **Critical** (Red): ≥ P90 (at or above 90th percentile - danger zone)

**Example Calculation**:
```
Historical data (25 weeks):
- Optimal WIP values: [8.2, 10.5, 12.1, 9.8, 15.3, 11.7, ...]
- P25 = 8.3, P50 = 14.8, P75 = 23.6, P90 = 41.9

Thresholds with buffers:
- Healthy: 8.3 × 1.2 = 10.0 items
- Warning: 14.8 × 1.2 = 17.7 items
- High: 23.6 × 1.2 = 28.3 items
- Critical: 41.9 (no buffer for danger zone)
```

**Why This Matters**:
- ✅ **Team-Specific**: Adapts to YOUR actual capacity and cycle time
- ✅ **Data-Driven**: Based on historical performance, not arbitrary numbers
- ✅ **Context-Aware**: Accounts for team size and work complexity
- ✅ **Predictive**: Higher WIP correlates with slower cycle time (validated by queueing theory)

**Fallback Thresholds**:
If insufficient historical data or NumPy unavailable:
- Healthy: <10 items
- Warning: <20 items
- High: <30 items
- Critical: ≥40 items

(These defaults are reasonable for teams of 5-10 people)

**Display Value** (Card):
- **Unit**: `items (current WIP)` - shows most recent week
- **Calculation**: WIP count for the **most recent week**
- **Health Badge**: Dynamic thresholds from Little's Law (or fallback if needed)
- **Trend Indicator**: Shows % change vs. previous average (↓ green = improvement, ↑ red = growing WIP)
- **Tooltip**: Explains Little's Law methodology and threshold calculation
- **Example**: Current week has 59 items with thresholds Healthy<10.0, Warning<17.7, High<28.3, Critical≥41.9
  - Display: "59 items" with "Critical" badge (red)
  - Indicates: Team has too much WIP, focus on finishing before starting new work

**Scatter Chart with Threshold Lines** (Weekly Data Points):
- **X-axis**: Week labels
- **Y-axis**: WIP count for that week
- **Main Line**: Blue line showing WIP trend over time
- **Threshold Lines** (Hoverable):
  - 🟢 **Green dotted line**: Healthy threshold (hover shows exact value)
  - 🟡 **Yellow dotted line**: Warning threshold (hover shows exact value)
  - 🟠 **Orange dotted line**: High threshold (hover shows exact value)
  - 🔴 **Red dashed line**: Critical threshold (hover shows exact value)
- **Values**: Each point = actual WIP at end of that week
- **Hover**: Shows exact threshold values and WIP count for each week

**Interpreting the Chart**:
```
WIP
│
60├─────────────────────────────────── 🔴 Critical (≥41.9)
  │              ●
50│             ╱ ╲
  │            ╱   ●
40├───────────●─────╲───────────────── 🟠 High (<28.3)
  │                  ╲
30│                   ●─────●
  │                          ╲
20├────────────────────────────●────── 🟡 Warning (<17.7)
  │                             ╲
10├──────────────────────────────●─── 🟢 Healthy (<10.0)
  │
 0└─────────────────────────────────────
   W20  W25  W30  W35  W40  W45

Analysis:
- Weeks 20-30: WIP climbing from healthy to critical (red flag!)
- Week 35: Peak at 52 items - team severely overloaded
- Weeks 35-45: Declining trend (good!) but still in warning zone
- Goal: Get below green line (10 items) for optimal flow
```

**Why WIP Matters**:
- **Context Switching**: High WIP = team juggling too many items = slower delivery
- **Focus**: Low WIP = team finishes work faster with fewer interruptions
- **Predictability**: Stable WIP = predictable cycle time = reliable planning
- **Team Health**: Critical WIP (red) = burnout risk, quality issues, missed deadlines

**Recommended Actions by Zone**:
- 🟢 **Healthy**: Maintain current WIP limit, team is operating optimally
- 🟡 **Warning**: Review WIP limit, start finishing before starting new work
- 🟠 **High**: Implement strict WIP limits, focus on completing in-flight work
- 🔴 **Critical**: STOP starting new work, swarm to finish existing items, investigate bottlenecks

**Code Location**: `data/flow_calculator.py::calculate_flow_load_v2()`, `calculate_wip_thresholds_from_history()`, and `aggregate_flow_load_weekly()`

---

### 5. Flow Distribution

**What it measures**: Percentage breakdown of work by type

**Calculation Method**:
- **Per Week**: For all completed items in that week:
  - Count by Flow type (Feature, Defect, Tech Debt, Risk)
  - Calculate percentages: `(count / total) × 100`
- **Recommended Ranges** (Flow Framework standards):
  - **Feature: 40-60%** - New business value and capabilities (growth)
  - **Defect: 20-40%** - Quality maintenance and bug fixes (stability)  
  - **Tech Debt: 10-20%** - Infrastructure improvements and sustainability
  - **Risk: 0-10%** - Security, compliance, and operational risk mitigation

**Display Value** (Card shows Stacked Area Chart):
- **X-axis**: Week labels
- **Y-axis**: Count of items by type (stacked)
- **Hover**: Shows percentage for each type
- **Current Week Summary**: Shows counts and percentages with range indicators

**Actionable Guidance by Distribution Pattern**:

### Healthy Balance (✅ Sustainable Growth)
```
Features: 40-60%  │████████████░░░░░░░░│
Defects:  20-30%  │████████░░░░░░░░░░░░│
Tech Debt: 10-20% │████░░░░░░░░░░░░░░░░│
Risk:      5-10%  │██░░░░░░░░░░░░░░░░░░│
```
**What it means**: Team is delivering value while maintaining quality and addressing technical health.
**Action**: Maintain current balance. Monitor for shifts.

### Feature-Heavy (⚠️ Quality Debt Accumulating)
```
Features: >70%    │██████████████████░░│
Defects:  <15%    │███░░░░░░░░░░░░░░░░░│
Tech Debt: <5%    │█░░░░░░░░░░░░░░░░░░░│
Risk:      <5%    │█░░░░░░░░░░░░░░░░░░░│
```
**What it means**: Short-term velocity at expense of quality. Expect CFR and MTTR to increase in 4-8 weeks.
**Warning Signs**: 
- Code getting harder to change
- Bug count increasing
- Team velocity slowing despite more features
**Action**: 
- Allocate 20% capacity to Tech Debt immediately
- Increase automated test coverage
- Schedule architecture review

### Defect Crisis (❌ Quality Problems Manifested)
```
Features: <30%    │██████░░░░░░░░░░░░░░│
Defects:  >50%    │██████████████████░░│
Tech Debt: <10%   │██░░░░░░░░░░░░░░░░░░│
Risk:      <5%    │█░░░░░░░░░░░░░░░░░░░│
```
**What it means**: Team overwhelmed with bugs, little progress on new value.
**Warning Signs**:
- Customer complaints increasing
- Team morale declining
- Velocity collapsing
**Action**: 
- **STOP starting new features** until defect rate drops below 40%
- Implement bug rotation (dedicated person per day/week)
- Root cause analysis: Why are so many bugs being created?
- Consider quality freeze: Fix top 10 most painful bugs before anything else

### Tech Debt Cleanup Mode (⚠️ Investment Period)
```
Features: 20-30%  │██████░░░░░░░░░░░░░░│
Defects:  15-25%  │█████░░░░░░░░░░░░░░░│
Tech Debt: 40-50% │██████████████░░░░░░│
Risk:      5-10%  │██░░░░░░░░░░░░░░░░░░│
```
**What it means**: Deliberate investment in technical health (refactoring, upgrades, migrations).
**When appropriate**:
- After major release
- Before starting new major initiative
- When velocity has slowed due to technical issues
**Action**: 
- Set time-box (e.g., "Tech Debt sprint for 2 weeks")
- Define clear outcomes (e.g., "Upgrade to Node 20", "Eliminate deprecated API calls")
- Return to balanced distribution after time-box ends

### Risk-Heavy (⚠️ Compliance/Security Focus)
```
Features: 20-30%  │██████░░░░░░░░░░░░░░│
Defects:  20-30%  │██████░░░░░░░░░░░░░░│
Tech Debt: 10-15% │███░░░░░░░░░░░░░░░░░│
Risk:      30-40% │████████████░░░░░░░░│
```
**What it means**: Heavy security/compliance work (audits, certifications, vulnerability remediation).
**When appropriate**:
- Pre-audit preparation
- Post-security incident response
- Regulatory compliance deadlines
**Action**: 
- Set time-box for risk work
- Communicate impact to stakeholders (reduced feature velocity)
- Return to balanced distribution after compliance achieved

**Pro Tip**: Use 4-week rolling average to smooth weekly fluctuations. React to trends, not individual weeks.

**Code Location**: `data/flow_calculator.py::aggregate_flow_distribution_weekly()`

---

## Summary Table: Time Units & Aggregations

| Metric                   | Time Unit        | Per-Week Aggregation         | Card Display                               | Secondary Info   | Trend Direction | Chart Y-Axis   |
| ------------------------ | ---------------- | ---------------------------- | ------------------------------------------ | ---------------- | --------------- | -------------- |
| **Deployment Frequency** | N/A (count)      | SUM (absolute count)         | AVERAGE of weekly counts (16w median avg)  | Releases/week    | ↑ green ↓ red   | Absolute count |
| **Lead Time**            | Hours → Days     | MEDIAN of all lead times     | AVERAGE of weekly medians (16w median avg) | P95 + Mean       | ↓ green ↑ red   | Median days    |
| **Change Failure Rate**  | N/A (percentage) | % of failures                | AGGREGATE % across all weeks (16w agg)     | Releases/week    | ↓ green ↑ red   | Weekly %       |
| **MTTR**                 | Hours            | MEDIAN of all recovery times | AVERAGE of weekly medians (16w median avg) | P95 + Mean       | ↓ green ↑ red   | Median hours   |
| **Flow Velocity**        | N/A (count)      | SUM (absolute count)         | Current week count                         | Work type counts | ↑ green ↓ red   | Absolute count |
| **Flow Time**            | Hours → Days     | MEDIAN of all flow times     | AVERAGE of weekly medians                  | None             | ↓ green ↑ red   | Median days    |
| **Flow Efficiency**      | N/A (percentage) | % active/WIP                 | Current week %                             | None             | ↑ green ↓ red   | Weekly %       |
| **Flow Load (WIP)**      | N/A (count)      | COUNT at week end            | Current week count                         | Health badge     | ↓ green ↑ red   | Absolute count |
| **Flow Distribution**    | N/A (percentage) | % by type                    | Stacked area chart                         | Range indicators | N/A             | Count by type  |

**Notes**:
- **16w median avg**: Primary values average the weekly medians over a 16-week rolling window
- **16w agg**: CFR aggregates failures/deployments across all 16 weeks (not averaged)
- **P95 + Mean**: Secondary statistics shown below primary value for Lead Time and MTTR
- **Releases/week**: Secondary metric for Deployment Frequency and CFR cards
- **Trend Direction**: Shows which arrow color indicates improvement (green) vs. regression (red)
- **→ (Right Arrow)**: Always gray, indicates exactly 0.0% change (stable)
- **− (Minus)**: Always gray, indicates <5% change or no historical data

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
   - `deployment_date`: Field containing deployment/release date (e.g., "fixVersions")
   - `change_failure`: Custom field indicating deployment success/failure
   - `affected_environment`: Field identifying production vs. non-production bugs
   - `effort_category`: Field for work classification (Feature, Tech Debt, Risk)

2. **Check Project Config**:
   - `devops_projects`: List of operational/DevOps project keys
   - `development_projects`: List of development project keys
   - `production_environment_values`: Values that identify production environment (e.g., ["PROD", "Production"])

3. **Check Status Config**:
   - `completion_statuses`: Statuses that indicate work is complete
   - `wip_statuses`: Statuses that indicate work is in progress
   - `active_statuses`: Subset of WIP statuses where work is actively being worked on

4. **Check Flow Type Mappings**:
   - Verify `flow_type_mappings` correctly classifies work types
   - Test with sample issues to ensure classification works as expected

5. **Verify Calculations**:
   - Pick one week and manually verify calculations
   - Compare calculated values with expected results
   - Check excluded counts in logs for unexpected filtering

---
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

## Practical Examples: Reading the UI

### Example 1: Healthy Team Performance

**Deployment Frequency Card**:
```
┌─────────────────────────────────────┐
│ Deployment Frequency      [Elite]🟢 │
│                                     │
│         12.5 deployments/week       │
│         (16w median avg)            │
│                                     │
│  ↑ 8.3% vs prev avg        [green] │
│  📦 8.2 releases/week              │
│  ━━━━━━━━━━ [sparkline] ━━━━━━━━━ │
└─────────────────────────────────────┘
```
**What it tells you**:
- Elite tier = deploying ≥30/month (on track!)
- ↑ 8.3% (green) = deployment frequency increasing (good!)
- 12.5 deployments for 8.2 releases = 1.5x deployment-to-release ratio
- Ratio >1 indicates: staging deployments, rollbacks, or multi-environment tracking

**Lead Time Card**:
```
┌─────────────────────────────────────┐
│ Lead Time for Changes      [High]🔵 │
│                                     │
│            3.2 days                 │
│         (16w median avg)            │
│                                     │
│  ↓ 12.1% vs prev avg      [green]  │
│  📊 P95: 5.8d • Avg: 4.1d          │
│  ━━━━━━━━━━ [sparkline] ━━━━━━━━━ │
└─────────────────────────────────────┘
```
**What it tells you**:
- High tier = 1d-1w lead time (solid performance)
- ↓ 12.1% (green) = getting faster (great trend!)
- P95 at 5.8d = 95% of changes deploy within a week
- Gap between median (3.2d) and mean (4.1d) = some outliers pulling average up

**Flow Load Card**:
```
┌─────────────────────────────────────┐
│ Flow Load (WIP)       [Healthy]🟢   │
│                                     │
│            8 items                  │
│         (current week)              │
│                                     │
│  ↓ 5.9% vs prev avg       [green]  │
│  ━━━━━━━━━━ [sparkline] ━━━━━━━━━ │
└─────────────────────────────────────┘
```
**What it tells you**:
- Healthy badge (<10 items) = team not overloaded
- ↓ 5.9% (green) = WIP decreasing (less multitasking)
- Low WIP typically correlates with faster flow time

---

### Example 2: Warning Signs

**Change Failure Rate Card**:
```
┌─────────────────────────────────────┐
│ Change Failure Rate      [Medium]🟡 │
│                                     │
│            18.5%                    │
│            (16w agg)                │
│                                     │
│  ↑ 22.7% vs prev avg       [red]   │
│  📦 7.8 releases/week              │
│  ━━━━━━━━━━ [sparkline] ━━━━━━━━━ │
└─────────────────────────────────────┘
```
**What it tells you**:
- Medium tier (16-30%) = room for improvement
- ↑ 22.7% (red) = failure rate increasing (concerning!)
- Action needed: Review testing processes, deployment procedures
- Investigate: Are failures clustered around specific releases?

**Flow Load Card**:
```
┌─────────────────────────────────────┐
│ Flow Load (WIP)        [Critical]🔴 │
│                                     │
│            32 items                 │
│         (current week)              │
│                                     │
│  ↑ 18.2% vs prev avg       [red]   │
│  ━━━━━━━━━━ [sparkline] ━━━━━━━━━ │
└─────────────────────────────────────┘
```
**What it tells you**:
- Critical badge (≥30 items) = team overloaded
- ↑ 18.2% (red) = WIP growing rapidly (danger!)
- High WIP = context switching, slower delivery, burnout risk
- Action needed: Stop starting, start finishing! Implement WIP limits

---

### Example 3: Stable Performance

**MTTR Card**:
```
┌─────────────────────────────────────┐
│ Mean Time to Recovery    [Elite]🟢  │
│                                     │
│           0.8 hours                 │
│         (16w median avg)            │
│                                     │
│  → 0.0% vs prev avg       [gray]   │
│  📊 P95: 1.2h • Avg: 0.9h          │
│  ━━━━━━━━━━ [sparkline] ━━━━━━━━━ │
└─────────────────────────────────────┘
```
**What it tells you**:
- Elite tier (<1h) = bugs fixed quickly (excellent!)
- → 0.0% (gray right arrow) = perfectly stable, no change
- Consistent performance = predictable, reliable processes
- P95 at 1.2h = even worst-case bugs fixed in ~1 hour

---

### Example 4: Insufficient Historical Data

**Lead Time Card** (New Project):
```
┌─────────────────────────────────────┐
│ Lead Time for Changes    [Medium]🟡 │
│                                     │
│            5.2 days                 │
│            (3w data)                │
│                                     │
│  − No trend data yet      [gray]   │
│  📊 P95: 8.1d • Avg: 6.3d          │
│  ━━ [short sparkline] ━━           │
└─────────────────────────────────────┘
```
**What it tells you**:
- − (minus, gray) = not enough history for trend comparison
- Still shows current performance tier and statistics
- Sparkline is short (only 3 weeks of data)
- Wait for more data before analyzing trends

---

### How to Use These Signals for Team Decisions

**Daily Standup**:
- Glance at WIP health badge → Red/Orange = focus on finishing over starting
- Check Flow Velocity trend → Declining? Discuss blockers

**Sprint Planning**:
- Review Lead Time P95 → Set realistic sprint commitments
- Check Flow Distribution → Rebalance if needed (e.g., 80% features, 5% tech debt = unhealthy)

**Retrospective**:
- Compare trend indicators across all metrics
- Green arrows = what's working? (double down!)
- Red arrows = what needs attention? (action items!)

**Leadership Reviews**:
- Performance tier badges = quick executive summary
- Detail charts with zones = show progress toward Elite performance
- Trend indicators = demonstrate continuous improvement (or need for support)

---

**Last Updated**: November 7, 2025  
**Maintained By**: Development Team
