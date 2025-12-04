# DORA Metrics Guide

**Part of**: [Metrics Documentation Index](./metrics_index.md)

## What Are DORA Metrics?

**DORA = DevOps Research and Assessment**

Research-backed metrics developed by Google's DORA team measuring software delivery performance. Based on 6+ years of research across 31,000+ organizations identifying what separates elite performers from average teams.

**The 4 Key Metrics**:
1. **Deployment Frequency** - How often you ship
2. **Lead Time for Changes** - How fast code reaches production  
3. **Change Failure Rate** - How often deployments fail
4. **Mean Time to Recovery** - How fast you recover from failures

**Why They Matter**: Elite teams deploy 208x more frequently, have 106x faster lead times, recover 2,604x faster from failures, and have 7x lower change failure rates than low performers.

---

## Quick Reference

| Metric                    | Time Unit        | Aggregation              | Elite Tier | Code Location                                                   |
| ------------------------- | ---------------- | ------------------------ | ---------- | --------------------------------------------------------------- |
| **Deployment Frequency**  | deployments/week | Average of weekly counts | ≥30/month  | `data/dora_calculator.py::calculate_deployment_frequency_v2()`  |
| **Lead Time for Changes** | days             | Median of all lead times | <1 hour    | `data/dora_calculator.py::calculate_lead_time_for_changes_v2()` |
| **Change Failure Rate**   | percentage       | Aggregate across weeks   | 0-15%      | `data/dora_calculator.py::calculate_change_failure_rate_v2()`   |
| **MTTR**                  | hours            | Median of recovery times | <1 hour    | `data/dora_calculator.py::calculate_mttr_v2()`                  |

---

## Field Configuration

### Required JIRA Fields

DORA metrics require mapping custom JIRA fields to standard metric fields. Configure via **Settings → Field Mappings → Fields tab**.

> **Important**: DORA metrics use a combination of standard JIRA fields, custom fields, and **changelog-based status transitions**. Many timestamps are extracted from status change history rather than dedicated date fields.

> **See Also**: [Namespace Syntax](namespace_syntax.md) for advanced field path syntax including:
> - `status:StatusName.DateTime` - Extract timestamp from status changelog
> - `customfield_12345=Value` - Filter by field value (e.g., `=PROD`, `=Yes`)

### Field Mapping Syntax

**=Value Filter Syntax**: Many fields support filtering by specific values:

```
customfield_11309=PROD      → Only match issues where field = "PROD"
customfield_12708=Yes       → Only match issues where field = "Yes"
status:In Progress.DateTime → Extract timestamp when status changed to "In Progress"
```

**Required Fields**:

| Internal Field           | Purpose                           | JIRA Field/Syntax                                    | Example Configuration         |
| ------------------------ | --------------------------------- | ---------------------------------------------------- | ----------------------------- |
| **Deployment Date**      | When deployment occurred          | `fixVersions` (uses releaseDate)                     | `fixVersions`                 |
| **Change Failure**       | Identify failed deployments       | Select field with =Value filter                      | `customfield_12708=Yes`       |
| **Code Commit Date**     | When work started (for Lead Time) | Status changelog syntax                              | `status:In Progress.DateTime` |
| **Incident Detected At** | When production bug found         | Standard field                                       | `created`                     |
| **Incident Resolved At** | When bug fixed in production      | `fixVersions` (uses releaseDate) or `resolutiondate` | `fixVersions`                 |
| **Affected Environment** | Filter production bugs for MTTR   | Select field with =Value filter                      | `customfield_11309=PROD`      |

**Optional Fields** (Enhanced Metrics):

| Internal Field         | Purpose                       | JIRA Field Type | Example Configuration             |
| ---------------------- | ----------------------------- | --------------- | --------------------------------- |
| **Target Environment** | Deployment environment filter | Select + =Value | `customfield_11309=PROD`          |
| **Severity Level**     | Incident priority/severity    | Select          | `customfield_11000` or `priority` |

### How =Value Syntax Works

The `=Value` syntax allows filtering issues by specific field values:

**Example 1: Production Bug Filtering (MTTR)**
```
affected_environment: customfield_11309=PROD
```
- Field `customfield_11309` contains environment (DEV, SIT, PROD)
- Only bugs where environment = "PROD" are counted for MTTR
- Bugs in DEV or SIT environments are excluded

**Example 2: Failed Deployment Detection (CFR)**
```
change_failure: customfield_12708=Yes
```
- Field `customfield_12708` is a checkbox/select for "Deployment Failed?"
- Deployments where this field = "Yes" are counted as failures
- Used to calculate Change Failure Rate

**Example 3: Status Changelog Syntax (Lead Time)**
```
code_commit_date: status:In Progress.DateTime
```
- Extracts timestamp from JIRA changelog when issue transitioned to "In Progress"
- No custom date field required - uses status history
- More accurate than custom fields (can't be manually edited incorrectly)

### Field Mapping Process

**Step 1: Auto-Configure** (Recommended)
1. Open **Settings → Field Mappings**
2. Click **Auto-Configure** button
3. System detects JIRA fields by name patterns:
   - "environment", "affected" → Affected Environment
   - "failure", "failed", "rollback" → Change Failure
   - "severity", "priority", "impact" → Severity Level
4. Review suggested mappings
5. Click **Save Mappings**

**Step 2: Configure =Value Filters** (Critical for MTTR and CFR)
1. Navigate to **Fields** tab in Field Mappings modal
2. For environment/failure fields, add the =Value suffix:
   - Select field from dropdown: `customfield_11309`
   - Add value filter: `=PROD` or `=Yes`
   - Final mapping: `customfield_11309=PROD`
3. Click **Save Mappings**

**Step 3: Configure Status-Based Mappings** (For Lead Time)
1. For Code Commit Date, use status changelog syntax:
   - Enter: `status:In Progress.DateTime`
   - This extracts the timestamp when work started
2. Click **Save Mappings**

**Step 4: Verify Configuration**
1. Open **DORA Metrics** tab
2. Click **Calculate Metrics** button (Settings panel, top right)
3. Check for error states:
   - "Missing Required Field" → Return to Field Mappings, configure field
   - "No Data" → Check JIRA query includes issues with mapped fields
   - "0 production bugs" → Verify =Value filter matches actual field values

### Field Type Compatibility

**System validates field types automatically:**

✅ **Compatible Mappings**:
- Deployment Date ← `fixVersions` (extracts releaseDate)
- Change Failure ← Select field with =Value syntax
- Affected Environment ← Select field with =Value syntax
- Code Commit Date ← `status:StatusName.DateTime` syntax

❌ **Common Mistakes**:
- Using checkbox field without =Value (use `customfield_123=Yes`)
- Forgetting =Value filter (counts ALL issues instead of filtered)
- Case mismatch in =Value (use exact case: `=PROD` not `=prod`)

**Fallback Strategy**:
- If custom field not available, use standard JIRA fields:
  - Incident Detected At → `created`
  - Incident Resolved At → `resolutiondate` or `fixVersions`
  - Code Commit Date → `status:In Progress.DateTime`

### Status & Work Type Mappings

**Completion Statuses** (Required for all metrics):
- Configure via **Types** tab → **Completion Statuses**
- Default: ["Done", "Closed", "Resolved"]
- Auto-Configure detects: "done", "complete", "finish", "close", "resolve"
- Used to identify deployed/completed work

**Active Statuses** (Required for Flow metrics):
- Configure via **Types** tab → **Active Statuses**
- Default: ["In Progress", "In Review", "Testing"]
- Auto-Configure detects: "progress", "development", "review", "test"
- Used to calculate Flow Time active periods

**WIP Statuses** (Required for Flow Load):
- Configure via **Types** tab → **WIP Statuses**
- Default: ["Selected", "In Progress", "In Review", "Testing"]
- Auto-Configure detects: "select", "backlog", "ready", "progress", "review", "test"
- Used to identify work in progress

**Work Type Mappings** (Required for Flow Distribution):
- Configure via **Types** tab → Drag issue types to categories
- Categories: Feature, Defect, Tech Debt, Risk
- Auto-Configure uses semantic rules:
  - Defect: "bug", "defect", "incident"
  - Risk: "spike", "investigation", "security"
  - Tech Debt: "refactor", "maintenance", "improvement"
  - Feature: "story", "epic", "feature" (default)

### DevOps Projects Configuration

**Purpose**: Separate deployment tracking from development work

**Configuration**:
1. Open **Settings → Field Mappings → Environment tab**
2. Configure **DevOps Projects** field:
   - Multi-select JIRA projects that track deployments
   - Example: ["RI"] (Release Infrastructure project)
3. Configure **Development Projects** field:
   - Multi-select JIRA projects with development work
   - Example: ["A935"] (Main development project)
4. Click **Save Mappings**

**Impact on Metrics**:
- **Deployment Frequency**: Counts Operational Tasks from DevOps projects with matching fixVersions
- **Lead Time**: Measures time from development issue start to operational task deployment
- **CFR**: Counts failed deployments in DevOps projects
- **MTTR**: Uses bugs from Development projects filtered by production environment

**How It Works**:
1. Operational Tasks (deployments) live in DevOps project (e.g., "RI")
2. Development issues live in Development project (e.g., "A935")
3. Both share `fixVersions` to link deployments to features
4. Deployment date comes from Operational Task's fixVersion releaseDate

### Production Environment Configuration

**Purpose**: Filter production bugs for MTTR calculation

**Configuration**:
1. Open **Settings → Field Mappings → Fields tab**
2. Map **Affected Environment** to JIRA custom field with =Value filter:
   - Example: `customfield_11309=PROD`
   - This ensures only bugs affecting production are counted
3. Configure **Production Environment Values** in Environment tab:
   - Example: ["PROD", "Production", "Live"]
   - Used as fallback if =Value syntax not specified
4. Click **Save Mappings**

**Impact on Metrics**:
- **MTTR**: Only counts bugs where affected environment matches production identifier
- Bugs in DEV, SIT, UAT environments are excluded

**Example**:
```
Affected Environment: customfield_11309=PROD

JIRA Bug with customfield_11309 = "PROD" → Counted in MTTR
JIRA Bug with customfield_11309 = "SIT"  → Excluded from MTTR
JIRA Bug with customfield_11309 = null   → Excluded from MTTR
```

### Common Configuration Issues

**Issue**: "0 production bugs found" for MTTR
**Solution**: 
1. Verify Affected Environment field mapping includes =Value filter
2. Check that JIRA bugs have values in the mapped field
3. Ensure =Value matches exactly (case-sensitive): `=PROD` not `=prod`
4. Check bugs exist in the Development projects (not DevOps projects)

**Issue**: "No Data" despite having deployments
**Solution**:
1. Verify DevOps project is configured and contains Operational Tasks
2. Check Operational Tasks have `fixVersions` with `releaseDate` populated
3. Verify `flow_end_statuses` includes the task completion status (e.g., "Done")
4. Check Development project issues share `fixVersions` with Operational Tasks

**Issue**: Lead Time shows very large values (e.g., 200+ days)
**Solution**:
1. Check Code Commit Date mapping uses status changelog: `status:In Progress.DateTime`
2. Verify issues actually transitioned through "In Progress" status
3. Check for issues stuck in workflow (never reached "Done")

**Issue**: CFR always shows 0%
**Solution**:
1. Verify Change Failure field mapping includes =Value filter
2. Check some deployments actually have failure flag set
3. Example: `customfield_12708=Yes` - are any tasks marked "Yes"?

**Issue**: Metrics show wrong performance tier
**Solution**:
1. Verify field mappings use correct =Value filters
2. Check DevOps vs Development project separation is correct
3. Verify `devops_task_types` includes your deployment task type (e.g., "Operational Task")
4. Check `bug_types` includes your bug issue types

---

## 1. Deployment Frequency

### What It Measures
How often deployments happen to production.

### Important Distinction
- **Deployment** = An operational task (deployment activity/process)
- **Release** = A unique fixVersion (the actual code release)
- **Example**: 2 operational tasks with fixVersion `R_20251104_example` = **2 deployments, 1 release**

### Calculation Details

**Per Week**:
- **Deployments**: COUNT of operational tasks with `fixVersion.releaseDate` in that week
- **Releases**: COUNT of UNIQUE fixVersion names in that week

**Filtering**:
- Only tasks where `status IN flow_end_statuses` (Done, Closed, etc.)
- Only tasks with `fixVersion.releaseDate <= today` (excludes future deployments)
- Uses **earliest releaseDate** if multiple fixVersions exist

**Display Value** (Card):
- **Primary**: `deployments/week (avg Nw)`
- **Calculation**: `AVERAGE(weekly_deployment_counts)` across N weeks
- **Secondary**: `releases/week` (shown below primary value)
- **Trend**: % change vs. previous average (↑ green = good, ↓ red = concerning)

**Example**:
```
12 weeks with deployment counts: [2, 3, 4, 2, 5, 3, 2, 4, 3, 2, 3, 4]
12 weeks with release counts: [1, 2, 3, 1, 3, 2, 1, 2, 2, 1, 2, 3]

Average deployments = 3.1 deployments/week
Average releases = 1.9 releases/week

Card shows: "3.1 deployments/week" with "📦 1.9 releases/week" below
```

### Performance Tiers

| Tier       | Threshold             | Color  | Meaning                         |
| ---------- | --------------------- | ------ | ------------------------------- |
| **Elite**  | ≥30/month (~7/week)   | Green  | On-demand deployment capability |
| **High**   | ≥7/month (~1.6/week)  | Blue   | Weekly+ deployment cadence      |
| **Medium** | ≥1/month (~0.25/week) | Yellow | Monthly deployment cadence      |
| **Low**    | <1/month              | Red    | Deployment friction exists      |

### Why Track Both Deployments AND Releases?

Multiple operational tasks (deployments) for one release indicates:
- Complex deployment process (multiple stages: staging → production)
- Deployment rollback and retry scenarios
- Multiple environment deployments tracked separately

**Action**: If deployments >> releases (e.g., 5 deployments per 1 release), investigate deployment complexity.

### Scatter Chart Visualization

- **X-axis**: Week labels (2025-45, 2025-46, etc.)
- **Y-axis**: Absolute deployment count for that week
- **Values**: Each point = actual deployments in that week (NOT cumulative, NOT average)
- **Background Zones**: Elite/High/Medium/Low performance tiers

### Common Issues & Solutions

**Issue**: Low deployment frequency (<1/month)
**Possible Causes**:
- Manual deployment process (time-consuming, error-prone)
- Lack of automated testing (fear of breaking production)
- Complex release approval process
- Large batch sizes (waiting to accumulate changes)

**Action Plan**:
1. Automate deployment pipeline (CI/CD)
2. Implement automated testing (unit, integration, smoke tests)
3. Reduce batch size (deploy smaller, more frequent changes)
4. Streamline approval process (automated gates, post-deployment reviews)

**Issue**: High deployment frequency but slow Lead Time
**Diagnosis**: Deploying frequently but changes sit in queue before deployment
**Action**: Investigate bottlenecks BEFORE deployment (code review, testing, approval stages)

---

## 2. Lead Time for Changes

### What It Measures
Time from code deployment-ready to deployed in production.

### Calculation Details

**Start Time**: 
- **Primary**: First "In Deployment" status timestamp (from changelog)
- **Fallback**: First "Done" status if never reached "In Deployment"

**End Time**:
- **Primary**: Matching operational task's `fixVersion.releaseDate`
  - Matching logic: Development issue fixVersion ID matches operational task fixVersion ID
- **Fallback**: Issue's `resolutiondate` if no operational task found

**Time Unit**: **HOURS** (displayed as days after conversion)

**Aggregation**: **MEDIAN** of all lead times in that week (not mean - robust to outliers)

**Display Value** (Card):
- **Primary**: `days (16w median avg)`
- **Calculation**: 
  1. Calculate median hours for each week
  2. Convert to days: `median_hours / 24`
  3. Average the weekly medians across 16 weeks
- **Secondary**: P95 and Mean averages
  - **P95**: 95th percentile - only 5% of issues take longer
  - **Mean**: Arithmetic average - useful for capacity planning

**Example**:
```
Week 1: Issues with lead times [24h, 48h, 72h]
  → Median = 48h (2d), Mean = 48h (2d), P95 = 67.2h (2.8d)
  
Week 2: Issues with lead times [36h, 60h]
  → Median = 48h (2d), Mean = 48h (2d), P95 = 57.6h (2.4d)

Averages: Median = 2d, Mean = 2d, P95 = 2.6d

Card Display:
- Primary: "2 days (16w median avg)"
- Trend: "↓ 5.2% vs prev avg" (green = improving)
- Secondary: "📊 P95: 2.6d • Avg: 2d"
```

### Performance Tiers

| Tier       | Threshold | Color  | Meaning                    |
| ---------- | --------- | ------ | -------------------------- |
| **Elite**  | <1 hour   | Green  | Near-instant deployment    |
| **High**   | <1 day    | Blue   | Same-day deployment        |
| **Medium** | <1 week   | Yellow | Weekly deployment cycle    |
| **Low**    | >1 week   | Red    | Significant deployment lag |

### Why Median, Not Mean?

- Outliers (e.g., 1 issue taking 200 hours) don't skew the metric
- More representative of "typical" lead time
- Mean still shown for capacity planning

### Why Show P95 and Mean?

- **P95**: Helps identify outliers and set realistic SLAs (95% of changes complete within this time)
- **Mean**: Useful for capacity planning and resource allocation
- Together they provide a complete picture of lead time distribution

### Common Issues & Solutions

**Issue**: Lead Time >1 week (Low tier)
**Possible Causes**:
- Code review bottlenecks (reviewers overloaded, slow turnaround)
- Testing delays (manual QA, slow test suites)
- Deployment approval queues (change advisory boards, release managers)
- Batching deployments (waiting for scheduled release windows)

**Action Plan**:
1. **Reduce batch size**: Deploy smaller changes more frequently
2. **Automate testing**: Replace manual QA with automated test suites
3. **Parallelize reviews**: Distribute code reviews across team
4. **Streamline approvals**: Automate deployment gates, trust automated tests
5. **Eliminate release windows**: Move to continuous deployment

**Issue**: Large gap between Median and P95 (e.g., Median 2d, P95 20d)
**Diagnosis**: Outliers indicate systemic bottlenecks affecting some changes
**Action**: 
1. Investigate outliers: Why did 5% of changes take 10x longer?
2. Common causes: Complex changes, cross-team dependencies, specific reviewers
3. Address root causes: Break down large changes, improve collaboration, distribute expertise

**Issue**: Lead Time improving but Deployment Frequency not improving
**Diagnosis**: Faster deployment process, but not deploying more often
**Action**: Cultural change needed - encourage frequent small deployments over large batches

---

## 3. Change Failure Rate (CFR)

### What It Measures
Percentage of deployments that fail and require remediation.

### Calculation Details

**Per Week**:
- Total deployments = COUNT(operational tasks with releaseDate in week)
- Failed deployments = COUNT(operational tasks with `customfield_10001 == "Yes"`)
- CFR = `(failed / total) × 100`

**Critical**: ONLY `"Yes"` (case-insensitive) indicates failure
- `"No"`, `"None"`, `null`, empty = success

**Display Value** (Card):
- **Unit**: `% (agg Nw)` (agg = aggregated)
- **Calculation**: **AGGREGATE** across N weeks, NOT average of weekly rates
  - `total_deployments = SUM(all weekly deployment counts)`
  - `total_failures = SUM(all weekly failure counts)`
  - `CFR = (total_failures / total_deployments) × 100`
- **Trend**: % change vs. previous average (↓ green = improvement, ↑ red = regression)

**Why Aggregate, Not Average?**
- Prevents weeks with few deployments from skewing the metric
- More accurate representation of overall failure rate

**Example**:
```
Week 1: 10 deployments, 1 failure → 10%
Week 2: 20 deployments, 0 failures → 0%

Aggregate: (1 / 30) × 100 = 3.3% ✓
(NOT (10% + 0%) / 2 = 5% ✗)

Card shows: "3.3%" with "→ 0.0% vs prev avg" if stable
```

### Performance Tiers

| Tier       | Threshold | Color  | Meaning                          |
| ---------- | --------- | ------ | -------------------------------- |
| **Elite**  | 0-15%     | Green  | High deployment quality          |
| **High**   | 16-30%    | Blue   | Acceptable failure rate          |
| **Medium** | 31-45%    | Yellow | Quality concerns emerging        |
| **Low**    | >45%      | Red    | Quality crisis - action required |

### Common Issues & Solutions

**Issue**: CFR shows 0% but you know there are production bugs
**Possible Causes**:
- Change failure field not mapped correctly (e.g., `customfield_12708=Yes`)
- Environment filter not matching bug values (check exact value: `PROD` vs `Production`)
- JIRA field values are different from expected (case sensitivity matters)

**Diagnosis**:
1. Check field mapping: `change_failure` should use `=Value` syntax like `customfield_12708=Yes`
2. Run JQL in JIRA: `project = XXX AND customfield_12708 = Yes AND created >= -30d`
3. Check logs for "Failed deployment issues count: X" messages

**Issue**: CFR >30% (Medium/Low tier)
**Possible Causes**:
- Insufficient automated testing (bugs slip through)
- Rushing deployments (skipping QA steps)
- Complex, tightly coupled architecture (changes break dependencies)
- Poor rollback mechanisms (failures not caught quickly)

**Action Plan**:
1. **Expand test coverage**: Add unit, integration, and smoke tests
2. **Implement deployment gates**: Require passing tests before deployment
3. **Add monitoring/observability**: Catch failures quickly with alerts
4. **Improve rollback process**: Automated rollback on failure detection
5. **Reduce coupling**: Break monolith into loosely coupled services

**Issue**: CFR <5% but Deployment Frequency <1/week
**Diagnosis**: Over-engineering, risk aversion slowing deployment cadence
**Action**: 
1. Trust your testing - you're clearly catching issues before production
2. Deploy more frequently to reduce batch size and risk per deployment
3. Consider feature flags for gradual rollouts

**Issue**: CFR increasing alongside Deployment Frequency
**Diagnosis**: Deploying faster but sacrificing quality
**Action**:
1. STOP - don't trade speed for quality
2. Invest in automated testing to maintain quality at higher velocity
3. Implement deployment gates to catch failures before production

---

## 4. Mean Time to Recovery (MTTR)

### What It Measures
Time from production bug creation to fix deployed.

### Calculation Details

**Bug Filtering**:
- Issue type = "Bug"
- `customfield_10002 == "PROD"` (exact match, case-sensitive)

**Start Time**: `bug.fields.created` (when bug was reported)

**End Time**:
- **Primary**: Matching operational task's `fixVersion.releaseDate`
- **Fallback**: Bug's `resolutiondate` if no operational task found

**Time Unit**: **HOURS**

**Aggregation**: **MEDIAN** of all recovery times in that week

**Display Value** (Card):
- **Primary**: `hours (16w median avg)`
- **Calculation**:
  1. Calculate median hours for each week
  2. Average the weekly medians across 16 weeks
- **Secondary**: P95 and Mean averages
  - **P95**: 95th percentile - only 5% of bugs take longer to fix
  - **Mean**: Arithmetic average - useful for capacity planning

**Example**:
```
Week 1: Bugs with recovery times [12h, 24h, 48h]
  → Median = 24h, Mean = 28h, P95 = 44.4h
  
Week 2: Bugs with recovery times [18h, 36h]
  → Median = 27h, Mean = 27h, P95 = 34.2h

Averages: Median = 25.5h, Mean = 27.5h, P95 = 39.3h

Card Display:
- Primary: "25.5 hours (16w median avg)"
- Trend: "↓ 3.8% vs prev avg" (green = improving)
- Secondary: "📊 P95: 39.3h • Avg: 27.5h"
```

### Performance Tiers

| Tier       | Threshold | Color  | Meaning                      |
| ---------- | --------- | ------ | ---------------------------- |
| **Elite**  | <1 hour   | Green  | Immediate incident response  |
| **High**   | <1 day    | Blue   | Same-day incident resolution |
| **Medium** | <1 week   | Yellow | Weekly incident resolution   |
| **Low**    | >1 week   | Red    | Slow incident response       |

### Why Show P95 and Mean?

- **P95**: Helps set incident response SLAs (95% of bugs fixed within this time)
- **Mean**: Useful for team capacity planning and on-call rotations
- Together they help identify both typical recovery time and worst-case scenarios

### Common Issues & Solutions

**Issue**: MTTR shows "No data" but you have production bugs
**Possible Causes**:
- Environment filter not matching bug values (e.g., `=PROD` but bugs have `Production`)
- Missing `fixVersions` release date on resolved bugs
- Bug field extraction failing

**Diagnosis**:
1. Check field mapping syntax: Use `customfield_11309=PROD` with exact value match
2. Verify JIRA field values: Run JQL `project = XXX AND customfield_11309 = PROD` in JIRA
3. Check logs for "Environment filter: Found X bugs" messages

**Issue**: MTTR >1 week (Low tier)
**Possible Causes**:
- No on-call rotation (bugs wait for business hours)
- Complex rollback process (manual, error-prone)
- Poor monitoring (bugs not detected quickly)
- Slow deployment pipeline (fix takes hours to deploy)

**Action Plan**:
1. **Implement on-call rotation**: 24/7 incident response team
2. **Automate rollback**: One-click rollback to last known good state
3. **Add monitoring/alerting**: Detect production issues within minutes
4. **Optimize deployment pipeline**: Deploy fixes in <1 hour
5. **Practice incident response**: Regular fire drills to improve muscle memory

**Issue**: Large gap between Median and P95 (e.g., Median 6h, P95 48h)
**Diagnosis**: Some bugs take 8x longer to fix - investigate why
**Action**:
1. Categorize outliers: Database issues? Third-party dependencies? Complex logic?
2. Create runbooks for common incident types
3. Invest in observability to reduce debugging time
4. Consider dedicated incident response team for complex issues

**Issue**: MTTR improving but CFR increasing
**Diagnosis**: Fixing bugs faster but introducing more bugs
**Action**:
1. Root cause analysis: Why are bugs being introduced?
2. Expand automated testing to catch bugs before production
3. Balance speed of recovery with prevention

---

## DORA Metric Relationships

### The Speed-Stability Balance

Elite teams achieve BOTH high velocity AND high stability:

```
Elite Performance:
✅ High Deployment Frequency (≥30/month)
✅ Fast Lead Time (<1 hour)
✅ Low Change Failure Rate (<15%)
✅ Fast Recovery (MTTR <1 hour)
```

**Anti-Patterns to Avoid**:
```
❌ Fast Deployment + High CFR = Moving fast, breaking things
❌ Low CFR + Slow Deployment = Risk aversion stifling innovation
❌ Fast Deployment + Slow MTTR = Creating problems faster than fixing them
```

### How DORA Metrics Connect

```
Improve Lead Time
  → Smaller batch sizes
  → More frequent deployments (Deployment Frequency ↑)
  → Less risk per deployment (CFR ↓)
  → Faster to fix if something breaks (MTTR ↓)
```

**Key Insight**: All 4 metrics improve together when you optimize for small, frequent deployments.

---

## Getting Started with DORA Metrics

### Week 1-2: Baseline
1. Start measuring all 4 metrics
2. Don't optimize yet - just observe
3. Identify which tier you're in for each metric

### Week 3-4: Focus Area
4. Pick ONE metric to improve (usually Deployment Frequency)
5. Implement small improvements
6. Measure impact on other metrics

### Month 2+: Iterate
7. Once Deployment Frequency improves, tackle Lead Time
8. Then CFR and MTTR
9. Continuous improvement cycle

**Progressive Approach**: Don't try to reach Elite tier in all metrics at once. Focus on one at a time.

---

## Additional Resources

- **Shared Concepts**: See [Metrics Index](./metrics_index.md) for metric relationships, common pitfalls, and getting started guides
- **Related Metrics**: See [Flow Metrics](./flow_metrics.md) for process-level insights that complement DORA outcomes
- **Project Forecasting**: See [Dashboard Metrics](./dashboard_metrics.md) for project completion forecasts

---

## Documentation Verification

All calculations, formulas, and behaviors documented above match the actual code implementation.

---

*Document Version: 1.0 | Last Updated: December 2025*
