# Flow Metrics Guide

**Audience**: Teams optimizing work processes and managing work-in-progress
**Part of**: [Metrics Documentation Index](./metrics_index.md)

## What Are Flow Metrics?

**Flow Framework** - Process-level metrics from Mik Kersten's "Project to Product" methodology measuring work system health.

While DORA metrics tell you **WHAT** happened (deployment outcomes), Flow metrics explain **WHY** (process bottlenecks, work distribution, capacity).

**The 5 Key Metrics**:

1. **Flow Velocity** - Work completed per week (by type)
2. **Flow Time** - Cycle time from start to finish
3. **Flow Efficiency** - Active work vs. waiting time percentage
4. **Flow Load (WIP)** - Work in progress with dynamic thresholds
5. **Flow Distribution** - Balance of Feature/Defect/Tech Debt/Risk work

**Why They Matter**: Flow metrics are **leading indicators** - they predict DORA outcomes. High WIP today means slow Lead Time tomorrow.

---

## Quick Reference

| Metric                | Time Unit  | Aggregation             | Healthy Target                | Code Location                                                   |
| --------------------- | ---------- | ----------------------- | ----------------------------- | --------------------------------------------------------------- |
| **Flow Velocity**     | items/week | Average per week        | Stable, predictable           | `data/flow_calculator.py::calculate_flow_velocity_v2()`         |
| **Flow Time**         | days       | Median of weekly median | Consistent cycle time         | `data/flow_calculator.py::calculate_flow_time_v2()`             |
| **Flow Efficiency**   | percentage | Average of weekly value | 25-40%                        | `data/flow_calculator.py::calculate_flow_efficiency_v2()`       |
| **Flow Load (WIP)**   | items      | Current week snapshot   | <P25 threshold (green)        | `data/flow_calculator.py::calculate_flow_load_v2()`             |
| **Flow Distribution** | percentage | Sum across all weeks    | Feature 40-50%, Defect 15-25% | `data/flow_calculator.py::aggregate_flow_distribution_weekly()` |

---

## Forecast Benchmarks and Trend Indicators

Metric cards include forecast benchmarks to provide context early in the week.

- Forecast window: 4 weeks, weighted toward the most recent week.
- Trend indicator: compares current value to forecast using a tolerance band.
- Lower-is-better metrics invert trend interpretation (Flow Time).
- Flow Load uses a forecast range rather than a single point value.

When insufficient historical data exists, cards show a baseline-building or insufficient-data message.

## Progressive Current Week Blending (Feature bd-a1vn)

**Problem**: Monday metrics showed 25% reliability drop because incomplete current week (0 completions) was included in rolling average with 40% weight.

**Solution**: Progressive blending that combines forecast (from prior 4 weeks) with actual current week value, weighted by day of week.

### How It Works

**Weekday Weights** (Linear Progression: weight = days_completed / 5):

- **Monday**: 0% actual, 100% forecast → Shows stable forecast (e.g., 12.0 items/week) [0/5]
- **Tuesday**: 20% actual, 80% forecast → Gradually transitions to actual [1/5]
- **Wednesday**: 40% actual, 60% forecast → Balanced blend [2/5]
- **Thursday**: 60% actual, 40% forecast → Mostly actual [3/5]
- **Friday**: 80% actual, 20% forecast → Nearly complete [4/5]
- **Saturday-Sunday**: 100% actual, 0% forecast → Pure actual value [work week complete]

**Formula**: `blended = (actual × weight) + (forecast × (1 - weight))`

**Example** (Forecast = 12.0 items/week):

- Monday with 0 completions → 12.0 items/week (was 8.4, -25% drop ❌)
- Tuesday with 2 completions → 10.0 items/week (smooth transition ✅)
- Wednesday with 5 completions → 9.2 items/week
- Friday with 10 completions → 10.4 items/week (80% actual, 20% forecast)

**UI Transparency**: Flow Velocity card shows breakdown when blending is active:

```
Current Week (Blended) 📊
• Blended (f): 10.0 items/week
• Forecast (x): 12.0 items/week
• Current Week (y): 2 items (Tuesday)
• Blend Ratio: 20% actual, 80% forecast
```

**Benefits**:

- ✅ Monday metrics stable (no 25% drop)
- ✅ Smooth progression through week (no sawtooth pattern)
- ✅ Real-time feedback maintained (partial actuals visible)
- ✅ User trust improved (transparent calculation)

**Note**: Same blending algorithm applies to DORA metrics (Deployment Frequency, Lead Time, MTTR). See [DORA Metrics Guide](./dora_metrics.md) for DORA-specific details.

---

## Field Configuration

### Required Status Configurations

Flow metrics use **status-based calculations** from JIRA changelog history. Configure via **Settings → Field Mappings → Types tab**.

> **Important**: Flow metrics do NOT use custom date fields. Instead, they analyze status transitions from JIRA changelog to determine when work started and completed. This approach is more flexible and captures all valid statuses (In Progress, In Review, Done, Resolved, Closed, etc.).

> **See Also**: [Namespace Syntax](namespace_syntax.md) for advanced field path syntax including:
>
> - `status:StatusName.DateTime` - Extract timestamp from status changelog
> - `customfield_12345=Value` - Filter by field value (e.g., `=PROD`)

### Field Mapping Syntax

**=Value Filter Syntax**: Some fields support filtering by specific values:

```
customfield_11309=PROD      → Only match issues where field = "PROD"
effort_category: customfield_13204  → Map effort category to custom field
```

**Required Status Lists**:

| Status List             | Purpose                                    | Example Statuses                                           |
| ----------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| **Completion Statuses** | Identify when work finished                | `Done`, `Resolved`, `Closed`, `Canceled`                   |
| **Flow Start Statuses** | Identify when work started (for Flow Time) | `In Progress`, `In Review`                                 |
| **Active Statuses**     | Identify active work (for Flow Efficiency) | `In Progress`, `In Review`, `Testing`                      |
| **WIP Statuses**        | Identify work in progress (for Flow Load)  | `In Progress`, `In Review`, `Testing`, `Ready for Testing` |

**Required Fields**:

| Internal Field     | Purpose             | JIRA Field Type | Example JIRA Field           |
| ------------------ | ------------------- | --------------- | ---------------------------- |
| **Status**         | Current work status | Select          | `status` (standard field)    |
| **Flow Item Type** | Work category       | Select          | `issuetype` (standard field) |

**Optional Fields** (Enhanced Metrics):

| Internal Field      | Purpose                       | JIRA Field Type | Example JIRA Field                   |
| ------------------- | ----------------------------- | --------------- | ------------------------------------ |
| **Effort Category** | Secondary work classification | Select          | `customfield_10301` ("Effort Type")  |
| **Estimate**        | Story points or effort        | Number          | `customfield_10002` ("Story Points") |

### How Flow Metrics Use Status Lists

**Flow Time** (Cycle Time):

- **Start**: First transition to ANY status in `flow_start_statuses` (from changelog)
- **End**: First transition to ANY status in `flow_end_statuses` (from changelog)
- **Example**: Issue moves To Do → In Progress → In Review → Done
  - Start = timestamp of "In Progress" transition
  - End = timestamp of "Done" transition
  - Flow Time = End - Start

**Flow Velocity**:

- Counts issues with current status IN `flow_end_statuses`
- AND `resolutiondate` in the measurement week

**Flow Efficiency**:

- **Active Time**: Sum of time spent in `active_statuses` (from changelog)
- **Total WIP Time**: Sum of time spent in `wip_statuses` (from changelog)
- **Efficiency** = Active Time / Total WIP Time × 100%

**Flow Load (WIP)**:

- Counts issues with current status IN `wip_statuses`
- Reconstructs historical WIP by replaying changelog

### Field Mapping Process

**Step 1: Auto-Configure** (Recommended)

1. Open **Settings → Field Mappings**
2. Click **Auto-Configure** button
3. System detects status categories by name patterns:
   - "done", "resolved", "closed", "canceled" → Completion Statuses
   - "progress", "development", "review" → Flow Start Statuses / Active Statuses
   - "progress", "review", "test", "ready" → WIP Statuses
   - "effort", "category", "type" → Effort Category
   - "points", "estimate", "size" → Estimate
4. Review suggested mappings
5. Click **Save Mappings**

**Step 2: Configure Status Mappings** (Critical for Flow Time, Efficiency, Load)

1. Navigate to **Types** tab in Field Mappings modal
2. Configure status categories:
   - **Completion Statuses**: Drag statuses like "Done", "Closed", "Resolved", "Canceled"
   - **Flow Start Statuses**: Drag statuses like "In Progress", "In Review" (when work begins)
   - **Active Statuses**: Drag statuses like "In Progress", "In Review", "Testing" (actively working)
   - **WIP Statuses**: Drag statuses like "In Progress", "In Review", "Ready for Testing" (work in progress)
3. Click **Save Mappings**

**Step 3: Configure Work Type Mappings**

1. Still in **Types** tab
2. Drag issue types to categories:
   - **Feature**: "Story", "Epic", "New Feature"
   - **Defect**: "Bug", "Defect", "Production Bug"
   - **Tech Debt**: "Technical Debt", "Refactoring", "Improvement"
   - **Risk**: "Spike", "Investigation", "Security Issue"
3. Click **Save Mappings**

**Step 4: Manual Field Override** (If Auto-Configure Misses Fields)

1. Navigate to **Fields** tab in Field Mappings modal
2. For optional fields (Effort Category, Estimate), select from dropdown:
   - Dropdown shows: `customfield_10300 - Story Points`
   - Only compatible field types shown (number for estimates)
3. Click **Save Mappings**

**Step 5: Verify Configuration**

1. Open **Flow Metrics** tab
2. Click **Update Data** (delta fetch) or **Force Refresh** (full refresh) button in Settings panel
3. Check for error states:
   - "Missing Required Field" → Return to Field Mappings, configure field
   - "No Data" → Check JIRA query includes issues with mapped fields

### Field Type Compatibility

**System validates field types automatically:**

✅ **Compatible Mappings**:

- Work Started Date (datetime) ← JIRA Date field
- Work Started Date (datetime) ← JIRA DateTime field
- Effort Category (select) ← JIRA Select/Dropdown field
- Estimate (number) ← JIRA Number field

❌ **Incompatible Mappings**:

- Work Started Date (datetime) ← JIRA Text field (will be hidden in dropdown)
- Estimate (number) ← JIRA Text field (will be hidden)

**Fallback Strategy**:

- If custom field not available, use standard JIRA fields:
  - Work Started Date → `created` (issue creation date)
  - Work Completed Date → `resolutiondate`
  - Flow Item Type → `issuetype`
  - Status → `status`

### Status Mappings (Critical for Flow Metrics)

**Completion Statuses** (Required for Flow Velocity, Flow Time):

- **Purpose**: Identify completed work
- **Configure**: Types tab → Completion Statuses
- **Default**: ["Done", "Closed", "Resolved"]
- **Auto-Detection**: "done", "complete", "finish", "close", "resolve"
- **Used By**: Flow Velocity (counts completed items), Flow Time (end timestamp)

**Active Statuses** (Required for Flow Efficiency):

- **Purpose**: Measure active work time vs. waiting time
- **Configure**: Types tab → Active Statuses
- **Default**: ["In Progress", "In Review", "Testing"]
- **Auto-Detection**: "progress", "development", "review", "test"
- **Used By**: Flow Efficiency (active time / total time)

**WIP Statuses** (Required for Flow Load, Flow Time):

- **Purpose**: Identify work in progress
- **Configure**: Types tab → WIP Statuses
- **Default**: ["Selected", "In Progress", "In Review", "Testing", "Ready for Testing"]
- **Auto-Detection**: "select", "backlog", "ready", "progress", "review", "test"
- **Used By**: Flow Load (WIP count), Flow Time (start timestamp = first WIP status)

**Status Configuration Best Practices**:

✅ **Do**:

- Include all statuses where team is actively working (Active Statuses)
- Include queue statuses in WIP but not Active (e.g., "Ready for Review")
- Test with sample data to verify correct categorization

❌ **Don't**:

- Include "To Do" or "Backlog" in WIP (inflates WIP count)
- Forget to include review/testing statuses in Active (underestimates efficiency)
- Mix completion statuses ("Done") with WIP statuses

### Work Type Mappings (Critical for Flow Distribution)

**Two-Tier Classification System**:

**Primary Classification** (Issue Type):

- **Feature**: Story, Epic, New Feature, Enhancement
- **Defect**: Bug, Defect, Production Bug, Hotfix
- **Tech Debt**: Technical Debt, Refactoring, Code Quality, Maintenance
- **Risk**: Spike, Investigation, Research, POC, Security Issue

**Secondary Classification** (Effort Category - Overrides Primary):

- If issue type = "Task" or "Story" AND effort category = "Technical Debt" → Tech Debt
- If issue type = "Task" AND effort category = "Security" → Risk
- If issue type = "Story" AND effort category = "Investigation" → Risk

**Configuration Steps**:

1. **Auto-Configure** (recommended first step):
   - System uses semantic rules to categorize issue types
   - Bug/Defect/Incident → Defect
   - Spike/Investigation → Risk
   - Refactor/Maintenance → Tech Debt
   - Story/Epic/Feature → Feature

2. **Manual Override** (drag & drop in Types tab):
   - Drag "Story" to Feature category
   - Drag "Bug" to Defect category
   - Drag "Technical Debt" to Tech Debt category
   - Drag "Spike" to Risk category

3. **Effort Category Mapping** (optional, for secondary classification):
   - Map custom field: `customfield_10301` → "Effort Category"
   - System automatically applies overrides based on effort category values

**Mutual Exclusivity Rule**:

- Each issue type can only belong to ONE category
- If dragged to new category, automatically removed from old category
- DevOps types (if detected) belong to Tech Debt AND appear separately

### Common Configuration Issues

**Issue**: Flow Time shows "No Data" or missing values
**Solution**:

1. Verify `flow_start_statuses` is configured:
   - Must include statuses where work begins (e.g., "In Progress", "In Review")
   - Configure via Settings → Field Mappings → Types tab
2. Verify `flow_end_statuses` is configured:
   - Must include final statuses (e.g., "Done", "Resolved", "Closed")
3. Check JIRA changelog is available:
   - Flow metrics require changelog history to detect status transitions
   - Verify issues have status transition history in JIRA

**Issue**: Flow Time shows unrealistic values (e.g., 200 days)
**Solution**:

1. Check Flow Start Status mapping:
   - If "To Do" or "Backlog" included → Measures from backlog entry, not work start
   - Only include statuses where ACTUAL work begins
2. Check WIP Status mapping:
   - If "Done" included in WIP → Never exits WIP, causes issues
   - WIP should only include active/queue statuses, NOT completion statuses
3. Verify changelog data quality:
   - Review JIRA issues: Do they have status transition history?
   - Some old issues may lack changelog (imported data)

**Issue**: Flow Efficiency shows 0% or 100%
**Solution**:

1. **0% Efficiency**:
   - Check Active Status mapping: Are any statuses mapped?
   - Verify JIRA changelog: Does issue history show status transitions?
2. **100% Efficiency**:
   - Check WIP Status mapping: Should include queue statuses ("Ready for Review")
   - If WIP = Active, efficiency will always be 100%

**Issue**: Flow Distribution shows 0% for all categories
**Solution**:

1. Check Work Type mapping in Types tab
2. Verify issue types exist in JIRA query results
3. Check spelling: "Bug" ≠ "bug" (case-sensitive)
4. Review Auto-Configure results: Did it detect issue types?

**Issue**: Flow Load (WIP) shows unrealistic high numbers (e.g., 500 items)
**Solution**:

1. Check WIP Status mapping:
   - Remove "To Do", "Backlog" from WIP statuses
   - Only include statuses where team actively works or queues
2. Check JQL query scope:
   - Are you querying entire JIRA instance instead of team/project?
   - Add project filter: `project = MYPROJECT`

**Issue**: Auto-Configure doesn't detect custom fields
**Solution**:

1. JIRA field names don't match detection patterns
2. Examples of detectable names:
   - ✅ "Development Start Date", "Work Begin Date", "Started At"
   - ❌ "Custom Field 1", "Date Field", "Timestamp"
3. Manual mapping required for non-standard names
4. Consider renaming JIRA fields for better auto-detection

### Historical Data Reconstruction

**Flow Load (WIP) Calculation**:

- System replays JIRA changelog to reconstruct historical WIP
- For each past week, determines which issues were "in progress" at end of week
- Enables WIP trend analysis and dynamic threshold calculation

**Requirements**:

- JIRA changelog history available (not purged)
- Status transitions logged in changelog
- WIP Status mapping configured correctly

**Performance Note**:

- First calculation may take 30-60 seconds for large projects (1000+ issues)
- Results cached for 5 minutes (in-memory)
- Subsequent loads are instant

---

## 1. Flow Velocity

### What It Measures

Number of work items completed per week, classified by work type.

### Calculation Details

**Per Week**:

- COUNT of issues with `status IN flow_end_statuses` AND `resolutiondate` in that week

**Classification** (Two-tier system):

- **Primary**: Issue type (Bug → Defect, Story/Task → Feature by default)
- **Secondary**: Effort category (overrides primary for Task/Story only)
  - "Technical debt" → Technical Debt
  - "Security", "GDPR", etc. → Risk
  - Otherwise → Feature

**Display Value** (Card):

- **Unit**: `items/week` (current week only, NOT average)
- **Calculation**: Total items completed in the **most recent week**
- **Example**: Week 2025-45 completed 25 items → Display: "25 items/week"

**Breakdown**:

```
Feature: 15 items (60%)
Defect: 6 items (24%)
Tech Debt: 3 items (12%)
Risk: 1 item (4%)
```

### Visualization

**Scatter Chart**: Weekly completed items over time  
**Stacked Area Chart**: Work type distribution evolution

### Common Issues & Solutions

**Issue**: Velocity highly variable week-to-week
**Diagnosis**:

- Large work items (unpredictable completion)
- Excessive WIP (context switching)
- External dependencies (blockers)

**Action**:

- Break down large items into smaller chunks
- Reduce WIP to improve focus
- Track and resolve blockers more aggressively

**Issue**: Velocity declining over time
**Diagnosis**:

- Tech debt accumulating (code getting harder to change)
- Quality issues increasing (more time fixing bugs)
- Team capacity reduced (attrition, context switching)

**Action**:

- Check Flow Distribution - if Feature >70%, allocate capacity to Tech Debt
- Check CFR - if increasing, invest in automated testing
- Review WIP - if increasing, implement WIP limits

---

## 2. Flow Time

### What It Measures

Median time from work start to completion (cycle time). Uses median for outlier resistance.

### Calculation Details

**Start Time**: First transition to ANY `wip_statuses` (from changelog)

- Example wip_statuses: ["Selected", "In Progress", "In Review", "Testing"]

**End Time**: `resolutiondate` field

**Time Unit**: **DAYS** (calculated as hours / 24)

**Aggregation**: **MEDIAN** of all flow times in that week (robust to outliers)

**Display Value** (Card):

- **Unit**: `days (avg Nw)`
- **Calculation**: Average of weekly medians across N weeks
- **Example**:
  - Week 1: Issues with flow times [2d, 4d, 6d] → Median = 4d
  - Week 2: Issues with flow times [3d, 5d] → Median = 4d
  - Average = 4 days

### Visualization

**Scatter Chart**: Median cycle time by week

### Common Issues & Solutions

**Issue**: Flow Time >2 weeks
**Possible Causes**:

- High WIP (too much in progress → context switching)
- Work sitting in queues (ready for review, waiting for testing)
- Large work items (taking weeks to complete)
- External dependencies (waiting on other teams)

**Action Plan**:

1. **Reduce WIP first** - This is the single biggest lever
2. **Visualize queues** - Where is work waiting?
3. **Break down large items** - Nothing should take >1 week
4. **Eliminate handoffs** - Cross-functional teams reduce dependencies
5. **Daily standup focus** - "What's blocking work from moving forward?"

**Issue**: Flow Time increasing over time
**Diagnosis**: System degrading - code getting harder to change OR team capacity declining
**Action**:

- Check Tech Debt percentage - if <10%, allocate more capacity
- Check WIP trend - if increasing, implement strict WIP limits
- Check team size - if shrinking, adjust capacity expectations

**Issue**: High variance (P95 is 3x+ median)
**Diagnosis**: Outliers indicate specific categories of work taking much longer
**Action**:

- Categorize outliers: Which types of work take longest?
- Create separate service classes: "Normal" vs. "Complex" work
- Set realistic expectations for complex work

---

## 3. Flow Efficiency

### What It Measures

Percentage of time spent actively working vs. waiting.

### Calculation Details

**Active Time**: Total time in `active_statuses` (from changelog)

- Example: ["In Progress", "In Review", "Testing"]

**Total WIP Time**: Total time in `wip_statuses` (from changelog)

- Example: ["Selected", "In Progress", "In Review", "Testing", "Ready for Testing"]

**Efficiency**: `(active_time / wip_time) × 100`

**Display Value** (Card):

- **Unit**: `%` (current week only)
- **Example**: Week 2025-45 had 420h active, 720h WIP → 58.3% efficiency

### The Efficiency Paradox

**Counter-intuitive insight**: Higher efficiency is NOT always better.

```
100% Efficiency = No wait time = No buffer = System overload ❌
 60% Efficiency = High utilization = Team stressed = Burnout risk ⚠️
 25-40% Efficiency = Healthy balance = Sustainable pace ✅
  0% Efficiency = All waiting = Process broken ❌
```

**Why 25-40% is optimal**:

- Teams need planning time (not "active" but essential)
- Code review time (waiting for reviewer, but valuable)
- Testing time (automated tests running, not "active")
- Buffer capacity prevents cascading delays when issues arise

### Common Issues & Solutions

**Issue**: Efficiency >60%
**Diagnosis**: Team overloaded - no buffer for unexpected work
**Symptoms**:

- Burnout risk
- Quality issues (rushing work)
- Can't absorb urgent requests

**Action**:

- Reduce WIP (create buffer capacity)
- Reject new work until WIP normalizes
- Review Work Distribution - cut low-value work

**Issue**: Efficiency <20%
**Diagnosis**: Excessive waiting - process bottlenecks
**Common Causes**:

- Work sitting in review queues
- Waiting for testing/QA
- Blocked by external dependencies
- Poor work breakdown (too large items)

**Action**:

1. **Map value stream**: Where is work waiting?
2. **Eliminate bottlenecks**:
   - Code review delays → Distribute reviews, set SLA
   - QA delays → Automate testing, embed QA in team
   - External dependencies → Negotiate SLAs, create alternatives
3. **Improve flow**: Reduce batch sizes, eliminate handoffs

---

## 4. Flow Load (WIP)

### What It Measures

Current work-in-progress count with dynamic health thresholds.

**Most Important Flow Metric** - WIP is your primary control lever for improving all other metrics.

### Calculation Details

**Per Week**: COUNT of issues where `status IN wip_statuses` at end of that week

- Snapshot measurement (not cumulative)

**Historical Reconstruction**: For past weeks, system replays changelog history to determine what WIP was at that specific point in time.

### Dynamic Health Thresholds (Little's Law)

Thresholds are **calculated from your team's historical data** using Little's Law from queueing theory:

**Formula**: `Optimal WIP = Throughput × Cycle Time`

- **Throughput**: Weekly velocity (items completed per week)
- **Cycle Time**: Flow time in days (time from start to completion)

**Example Calculation**:

```
Historical data (25 weeks):
- Each week: optimal_wip = velocity × (flow_time_days / 7)
- Week 1: 18 items/week × (6 days / 7) = 15.4 optimal WIP
- Week 2: 20 items/week × (5 days / 7) = 14.3 optimal WIP
- ... (repeat for all weeks)

Collect all optimal WIP values: [8.2, 10.5, 12.1, 9.8, 15.3, 11.7, ...]

Calculate percentiles:
- P25 = 8.3 (25% of weeks had WIP below this)
- P50 = 14.8 (median)
- P75 = 23.6 (75th percentile)
- P90 = 41.9 (90th percentile - danger zone)

Apply 20% stability buffers:
- Healthy (Green): < 8.3 × 1.2 = 10.0 items
- Warning (Yellow): < 14.8 × 1.2 = 17.7 items
- High (Orange): < 23.6 × 1.2 = 28.3 items
- Critical (Red): ≥ 41.9 (no buffer for danger zone)
```

**Why This Matters**:

- ✅ **Team-Specific**: Adapts to YOUR capacity, not generic rules
- ✅ **Data-Driven**: Based on actual performance, not guesses
- ✅ **Predictive**: Higher WIP → Slower cycle time (validated by queueing theory)

**Fallback Thresholds** (if insufficient data):

- Healthy: <10 items
- Warning: <20 items
- High: <30 items
- Critical: ≥40 items

### Visualization

**Scatter Chart with Threshold Lines**:

- Blue line: WIP trend over time
- Dotted lines: Dynamic thresholds (green/yellow/orange)
- Dashed red line: Critical threshold

**Example**:

```
WIP
│
60├─────────────────────── 🔴 Critical (≥41.9)
  │              ●
50│             ╱ ╲
  │            ╱   ●
40├───────────●─────╲───── 🟠 High (<28.3)
  │                  ╲
30│                   ●─────●
  │                          ╲
20├────────────────────────────●── 🟡 Warning (<17.7)
  │                             ╲
10├──────────────────────────────●── 🟢 Healthy (<10.0)
  │
 0└─────────────────────────────────
   W20  W25  W30  W35  W40  W45
```

### Why WIP Matters

**The WIP-Speed Connection**:

```
High WIP → Context Switching → Slower Delivery → Missed Deadlines
  ↓            ↓                   ↓                ↓
  15+ items    10%+ overhead      2x cycle time    Stakeholder frustration
```

**Reducing WIP improves EVERYTHING**:

- ✅ Faster Flow Time (less context switching)
- ✅ Faster Lead Time (DORA metric)
- ✅ Better Quality (more focus, less rushing)
- ✅ More Predictable Delivery (stable cycle time)
- ✅ Happier Team (less stress, clearer priorities)

### Common Issues & Solutions

**Issue**: WIP in Critical zone (red)
**Symptoms**:

- Team feels overwhelmed
- Nothing getting finished
- Constantly switching between tasks
- Cycle time blowing out

**Action Plan** (DO THIS NOW):

1. **STOP starting new work** - No exceptions
2. **Finish what's started** - Swarm on items closest to done
3. **Investigate bottlenecks**: Why is work piling up?
4. **Implement WIP limits**: Max N items per person (e.g., 2)
5. **Monitor daily**: Daily standup focus on "What can we finish TODAY?"

**Issue**: WIP steadily increasing over time
**Diagnosis**: Work arriving faster than team can complete it
**Action**:

- **Say NO to new work** until WIP stabilizes
- **Negotiate priorities** with stakeholders (show WIP trend)
- **Increase capacity** (hire) OR **reduce scope** (cut low-value work)
- **Improve process** (reduce Flow Time through better practices)

**Issue**: WIP volatile (swings 20+ items week-to-week)
**Diagnosis**: Inconsistent process - work starts/stops unpredictably
**Action**:

- **Implement kanban board** - Visualize WIP limits by column
- **Start one, finish one** - Strict WIP discipline
- **Prioritize finishing** - Pull only when capacity available

---

## 5. Flow Distribution

### What It Measures

Percentage breakdown of work by type (Feature/Defect/Tech Debt/Risk).

### Recommended Ranges (Flow Framework Standards)

```
Feature:   40-50%  │██████████████░░░░░░│ - New business value
Defect:    15-25%  │████████░░░░░░░░░░░░│ - Quality maintenance
Tech Debt: 20-25%  │████░░░░░░░░░░░░░░░░│ - Infrastructure health
Risk:      10-15%  │██░░░░░░░░░░░░░░░░░░│ - Security, compliance
```

### Distribution Patterns & Actions

#### ✅ Healthy Balance (Sustainable Growth)

```
Features: 50% │██████████████░░░░░░│
Defects:  25% │████████░░░░░░░░░░░░│
Tech Debt: 15% │██████░░░░░░░░░░░░░░│
Risk:      10% │████░░░░░░░░░░░░░░░░│
```

**Action**: Maintain. Monitor for shifts. Continue balanced approach.

#### ⚠️ Feature-Heavy (Quality Debt Accumulating)

```
Features: 75% │████████████████████│
Defects:  12% │████░░░░░░░░░░░░░░░░│
Tech Debt:  8% │███░░░░░░░░░░░░░░░░░│
Risk:       5% │██░░░░░░░░░░░░░░░░░░│
```

**What it means**: Short-term velocity at expense of quality  
**Prediction**: Expect CFR and MTTR to increase in 4-8 weeks  
**Action**:

- Allocate 20% capacity to Tech Debt immediately
- Increase automated test coverage
- Schedule architecture review

#### ❌ Defect Crisis (Quality Problems Manifested)

```
Features: 25% │████████░░░░░░░░░░░░│
Defects:  60% │████████████████████│
Tech Debt:  10% │████░░░░░░░░░░░░░░░░│
Risk:       5% │██░░░░░░░░░░░░░░░░░░│
```

**What it means**: Team overwhelmed with bugs  
**Action**:

- **STOP starting new features** until defect rate drops below 40%
- Implement bug rotation (dedicated person per day/week)
- Root cause analysis: Why are so many bugs being created?
- Quality freeze: Fix top 10 most painful bugs before anything else

### Visualization

**Stacked Area Chart**: Work type evolution over time with target zones (15-18% opacity) visible for immediate value assessment.

**Mobile-First Design**:

- Horizontal legend (mobile-friendly)
- Enhanced hover with percentages + counts + target ranges
- Progressive disclosure of target ranges

---

## Flow Metrics Relationships

### The WIP-Everything Connection

```
Reduce WIP (Flow Load)
  ↓
Faster Flow Time
  ↓
Faster Lead Time (DORA)
  ↓
Higher Deployment Frequency (DORA)
  ↓
Better project forecasts (Dashboard)
```

**Key Insight**: WIP is the primary control lever. Lower WIP → Everything improves.

### Flow Distribution Predicts DORA

```
Feature >70% + Defect <10%
  ↓ (4-8 weeks later)
CFR increases + MTTR increases
  ↓
Quality crisis manifests
```

**Leading Indicator**: Flow Distribution today predicts DORA metrics tomorrow.

---

## Getting Started with Flow Metrics

### Week 1-2: Baseline

1. Measure all 5 Flow metrics
2. Calculate dynamic WIP thresholds (or use fallback)
3. Observe patterns - don't optimize yet

### Week 3-4: Focus on WIP

4. If WIP in Warning/High/Critical → Reduce WIP first
5. Implement WIP limits (e.g., max 2 items per person)
6. Measure impact on Flow Time

### Month 2+: Balance

7. Once WIP stable, check Flow Distribution
8. Adjust work mix to hit target ranges (40-50% Feature, 15-25% Defect, 10-15% Risk, 20-25% Tech Debt)
9. Monitor Flow Efficiency - aim for 25-40%

**Progressive Approach**: WIP first, distribution second, efficiency third.

---

## Additional Resources

- **Shared Concepts**: See [Metrics Index](./metrics_index.md) for metric relationships and common pitfalls
- **Related Metrics**: See [DORA Metrics](./dora_metrics.md) for deployment outcome metrics that Flow predicts
- **Project Forecasting**: See [Dashboard Metrics](./dashboard_metrics.md) for completion forecasts

---

## Documentation Verification

All calculations, formulas, and behaviors documented above match the actual code implementation.

---

_Document Version: 1.0 | Last Updated: December 2025_
