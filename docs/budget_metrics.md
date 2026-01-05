# Budget Metrics Guide

**Part of**: [Metrics Documentation Index](./metrics_index.md)

## What Are Budget Metrics?

**Lean/Agile Budgeting** - Adaptive financial management approach that replaces fixed annual budgets with continuous planning, rolling forecasts, and velocity-driven metrics.

While traditional budgeting uses fixed cost-per-item estimates, Budget metrics adapt to **actual team performance** and support continuous adjustment without annual cycles.

**The 7 Key Metrics**:
1. **Total Budget** - Total financial envelope for the project
2. **Budget Consumed** - Spending based on completed work
3. **Burn Rate** - Average weekly spending rate
4. **Runway** - Weeks remaining at current burn rate
5. **Cost per Item** - Velocity-driven cost per work item
6. **Cost per Point** - Velocity-driven cost per story point
7. **Team Cost** - Weekly team cost rate (single source of truth)

**Why They Matter**: Budget metrics provide **transparency** and **adaptability** - track spending in real-time, adjust forecasts continuously, and align costs with actual team performance rather than fixed estimates.

---

## Quick Reference

| Metric              | Time Unit | Aggregation             | Calculation Method                 | Code Location                                        |
| ------------------- | --------- | ----------------------- | ---------------------------------- | ---------------------------------------------------- |
| **Total Budget**    | currency  | Single value            | Time × Team Cost (or manual)       | `data/budget_calculator.py::get_budget_at_week()`    |
| **Budget Consumed** | currency  | Cumulative sum          | Σ(Items × Cost per Item)           | `data/budget_calculator.py::calculate_consumption()` |
| **Burn Rate**       | /week     | Weekly average          | Avg(Weekly Consumption)            | `data/budget_calculator.py::calculate_consumption()` |
| **Runway**          | weeks     | Calculated from above   | (Total - Consumed) / Burn Rate     | `data/budget_calculator.py::calculate_consumption()` |
| **Cost per Item**   | currency  | Velocity-driven         | Team Cost / Items Completed        | `data/budget_calculator.py::calculate_consumption()` |
| **Cost per Point**  | currency  | Velocity-driven (if SP) | Team Cost / Story Points Completed | `data/budget_calculator.py::calculate_consumption()` |
| **Team Cost**       | /week     | Base rate               | User-configured weekly cost        | `data/database.py::budget_settings`                  |

---

## Configuration

### Budget Settings

Budget metrics require configuration via **Settings → Budget tab**. All settings stored in `budget_settings` table with optional revision history in `budget_revisions` table.

> **Important**: Budget metrics use **velocity-driven costs** - Cost per Item and Cost per Point are calculated from actual team performance (completed items per week) rather than fixed estimates. This adapts to team performance changes over time.

> **See Also**: Configuration guide in Settings panel for field mappings and Parameters panel for enabling Points Tracking.

### Required Settings

| Setting            | Purpose                 | Input Type | Default | Example   |
| ------------------ | ----------------------- | ---------- | ------- | --------- |
| **Time Allocated** | Project duration        | Integer    | None    | 12 weeks  |
| **Team Cost**      | Weekly team cost rate   | Number     | None    | €4,000/wk |
| **Currency**       | Display currency symbol | Text       | €       | $, £, ¥   |

### Optional Settings

| Setting                   | Purpose                          | Input Type | When to Use                                       |
| ------------------------- | -------------------------------- | ---------- | ------------------------------------------------- |
| **Total Budget (Manual)** | Override auto-calculation        | Number     | When budget includes non-team costs (contractors) |
| **Effective Date**        | Backdate budget change           | Date       | For retroactive budget entries                    |
| **Revision Reason**       | Document budget change rationale | Text       | Audit trail for significant changes               |

### Budget Total Calculation Modes

**Auto Mode (Recommended)**:
```
Total Budget = Time Allocated × Team Cost
Example: 12 weeks × €4,000/week = €48,000
```

**Manual Mode**:
```
Total Budget = User-specified amount
Example: €60,000 (includes €48,000 team + €12,000 contractors)
```

> **⚠️ Override Behavior**: Manual budget overrides the auto-calculation completely. Use when your budget includes costs beyond team salary (contractors, licenses, infrastructure).

---

## How Budget Metrics Work

### Lean/Agile Methodology Principles

Budget metrics implement the following lean/agile principles:

1. **Adaptive processes** over fixed annual plans
   - Update budget anytime with revision tracking
   - No locked annual cycles

2. **Velocity-driven targets** over fixed cost estimates
   - Cost per Item = Team Cost / Actual Velocity
   - Adapts to team performance changes

3. **Rolling forecasts** over annual budgets
   - Week-by-week tracking with replay logic
   - Historical budget state reconstruction

4. **Transparency** over control
   - Always-visible budget state
   - Full revision history with audit trail

5. **Empirical measurement** over predictive planning
   - Costs based on completed work
   - Real-time burn rate tracking

### Velocity-Driven Cost Calculation

**Key Concept**: Budget metrics calculate costs from **actual team performance** rather than fixed estimates.

**Weekly Cost per Item**:
```
Velocity = Items Completed This Week
Cost per Item = Team Cost / Velocity

Example Week 1:
- Team Cost: €4,000/week
- Items Completed: 10
- Cost per Item: €4,000 / 10 = €400/item
```

**Why It Matters**: If velocity drops to 8 items/week, Cost per Item automatically adjusts to €500/item. No manual re-estimation needed.

### Budget Consumption Tracking

Budget consumption tracks **cumulative spending** based on completed work:

```
Weekly Consumption = Items Completed × Cost per Item
Budget Consumed = Σ(Weekly Consumption across all weeks)

Example:
Week 1: 10 items × €400 = €4,000
Week 2: 12 items × €333 = €4,000
Week 3: 8 items × €500 = €4,000
Total Consumed: €12,000
```

### Burn Rate and Runway

**Burn Rate** = Average weekly consumption over project lifetime:
```
Burn Rate = Budget Consumed / Weeks Elapsed

Example after 3 weeks:
- Budget Consumed: €12,000
- Weeks Elapsed: 3
- Burn Rate: €12,000 / 3 = €4,000/week
```

**Runway** = Weeks remaining at current burn rate:
```
Runway = (Total Budget - Budget Consumed) / Burn Rate

Example:
- Total Budget: €48,000
- Budget Consumed: €12,000
- Burn Rate: €4,000/week
- Runway: (€48,000 - €12,000) / €4,000 = 9 weeks
```

---

## Budget Revision Tracking

### Revision History Mechanism

Budget changes are tracked using **delta-based revisions** - only changes are stored, not complete snapshots:

```sql
CREATE TABLE budget_revisions (
    profile_id TEXT,
    revision_date TEXT,
    week_label TEXT,
    time_allocated_weeks_delta INTEGER,  -- Δ change
    team_cost_delta REAL,                -- Δ change
    budget_total_delta REAL,             -- Δ change
    revision_reason TEXT
)
```

**Replay Logic**:
```python
# Get budget state at specific week
baseline = budget_settings  # Starting point
for revision in revisions where week_label <= target_week:
    baseline.time_allocated += revision.time_allocated_weeks_delta
    baseline.team_cost += revision.team_cost_delta
    baseline.budget_total += revision.budget_total_delta
return baseline
```

### When to Create Budget Revisions

| Scenario                      | Revision Required? | Example                                     |
| ----------------------------- | ------------------ | ------------------------------------------- |
| Initial budget setup          | No                 | First-time configuration                    |
| Increase time allocation      | Yes                | Project extended from 12 to 16 weeks        |
| Increase team cost            | Yes                | Team member added, cost increases €4k → €5k |
| Change to manual budget total | Yes                | Switch from auto €48k to manual €60k        |
| Update revision reason (no Δ) | No                 | Just documentation, no financial impact     |
| Change currency symbol        | No                 | Display formatting only, no budget impact   |

### Effective Date (Backdating)

Use effective date to backdate budget changes:

```
Scenario: Team member added 2 weeks ago, but budget not updated until now

Configuration:
- Effective Date: 2 weeks ago
- Week Label: Calculated from effective date
- Team Cost Delta: +€1,000/week

Result:
- Budget replay shows increased cost starting 2 weeks ago
- Historical metrics (Consumption, Runway) recalculated accurately
```

---

## Integration with Other Metrics

### Budget + Velocity (Items/Week)

```
Cost per Item = Team Cost / Velocity

If Velocity ↑ → Cost per Item ↓ (more efficient)
If Velocity ↓ → Cost per Item ↑ (less efficient)
```

**Example**:
- Week 1: 10 items completed → €400/item
- Week 2: 12 items completed → €333/item (20% improvement)
- Week 3: 8 items completed → €500/item (25% decline)

### Budget + Story Points

Enable **Points Tracking** in Parameters panel to track Cost per Point:

```
Cost per Point = Team Cost / Points Completed

Example:
- Team Cost: €4,000/week
- Points Completed: 40 SP
- Cost per Point: €100/SP
```

### Budget + Flow Distribution

Calculate **cost breakdown by work type**:

```
Cost by Type = Σ(Items of Type × Cost per Item)

Example Week:
- Features: 6 items × €400 = €2,400 (60%)
- Defects: 3 items × €400 = €1,200 (30%)
- Tech Debt: 1 item × €400 = €400 (10%)
Total: €4,000
```

### Budget + DORA Metrics

Track **deployment costs**:

```
Cost per Deployment = Total Consumed / Total Deployments

Example:
- Budget Consumed: €12,000
- Deployments: 24
- Cost per Deployment: €500
```

---

## Dashboard Display

### Budget Cards on Dashboard

Budget metrics appear in the **Budget Section** when configured:

1. **Total Budget Card**
   - Displays: Total budget, consumption %, visual gauge
   - Color: Green (<70%), Yellow (70-90%), Red (>90%)

2. **Burn Rate Card**
   - Displays: Weekly burn rate, runway
   - Visual: Trend indicator (stable/increasing/decreasing)

3. **Cost Efficiency Cards**
   - Cost per Item (always shown)
   - Cost per Point (if Points Tracking enabled)

### Budget Section Visibility Rules

| Condition                 | Display Behavior                        |
| ------------------------- | --------------------------------------- |
| Budget not configured     | Section hidden completely               |
| Budget configured, no WIP | Show placeholder "No statistics yet"    |
| Budget configured + WIP   | Show all budget cards with live data    |
| Points disabled           | Show Cost per Item, hide Cost per Point |

---

## Calculation Examples

### Example 1: Basic Budget Setup (Auto Mode)

**Configuration**:
- Time Allocated: 12 weeks
- Team Cost: €4,000/week
- Mode: Auto-calculate

**Results**:
```
Total Budget = 12 × €4,000 = €48,000

After Week 1 (10 items completed):
- Velocity: 10 items/week
- Cost per Item: €4,000 / 10 = €400
- Budget Consumed: 10 × €400 = €4,000
- Burn Rate: €4,000 / 1 week = €4,000/week
- Runway: (€48,000 - €4,000) / €4,000 = 11 weeks
```

### Example 2: Budget with Manual Override

**Configuration**:
- Time Allocated: 12 weeks
- Team Cost: €4,000/week
- Mode: Manual override
- Total Budget: €60,000 (includes €12,000 contractors)

**Results**:
```
Total Budget = €60,000 (user-specified)

After Week 1 (10 items completed):
- Cost per Item: €400 (based on team cost, not total budget)
- Budget Consumed: €4,000 (team work only)
- Burn Rate: €4,000/week
- Runway: (€60,000 - €4,000) / €4,000 = 14 weeks
```

> **Note**: Manual budget affects consumption % and runway, but Cost per Item still derives from Team Cost (not total budget).

### Example 3: Mid-Project Budget Increase

**Initial Configuration**:
- Time Allocated: 12 weeks
- Team Cost: €4,000/week
- Total Budget: €48,000 (auto)

**After 6 weeks** (scope increase):
- Time Allocated: +4 weeks (12 → 16)
- Revision Reason: "Additional features approved"

**Results**:
```
New Total Budget = 16 × €4,000 = €64,000

Budget Consumed (first 6 weeks): €24,000
Remaining: €64,000 - €24,000 = €40,000
Runway: €40,000 / €4,000 = 10 weeks (correct)
```

### Example 4: Historical Budget Replay

**Scenario**: View budget state at Week 3

**Revision History**:
- Week 1: Baseline (12 weeks, €4,000/week)
- Week 5: +4 weeks time allocation
- Week 8: +€1,000/week team cost

**Budget at Week 3**:
```
get_budget_at_week(profile_id, query_id, "2026-W03")
Returns:
- Time Allocated: 12 weeks (Week 5 change not applied yet)
- Team Cost: €4,000/week (Week 8 change not applied yet)
- Total Budget: €48,000
```

---

## Best Practices

### When to Use Auto vs Manual Budget

**Use Auto Mode When**:
- Budget covers team costs only
- Simple project with predictable costs
- Want automatic updates when time changes

**Use Manual Mode When**:
- Budget includes non-team costs (contractors, infrastructure)
- Fixed budget constraint (cannot exceed total)
- Budget determined by client/funding, not team cost

### Budget Update Frequency

**Recommended**:
- Initial setup: Before project starts
- Major changes: When scope/team/timeline changes significantly
- Regular reviews: Monthly or per sprint

**Avoid**:
- Weekly micro-adjustments (creates noisy revision history)
- Retroactive changes without effective dates (distorts historical view)

### Revision Reason Guidelines

**Good Examples**:
- "Additional funding approved for Phase 2 features"
- "Team member added, increasing weekly cost"
- "Project timeline extended by 4 weeks due to scope increase"

**Bad Examples**:
- "Update" (no context)
- "Change" (what changed?)
- "" (empty - always provide reason for audit trail)

### Effective Date Usage

**When to Use**:
- Team member joined 2 weeks ago, updating budget now
- Scope change decided last week, documenting today
- Retroactive budget approval for past period

**When NOT to Use**:
- Future changes (budget should reflect current reality)
- Correcting errors (delete revision instead, start fresh)

---

## Troubleshooting

### Issue: Budget Consumed Shows 0% Despite Work Completed

**Possible Causes**:
1. Budget not configured (Total Budget = 0)
2. Velocity = 0 (no items completed)
3. Statistics not calculated yet (run query first)

**Solution**:
- Verify budget configuration in Settings → Budget
- Check Statistics panel for completed items
- Ensure JIRA query has completion status mapping

### Issue: Cost per Item Changes Dramatically Week-to-Week

**Possible Causes**:
1. Variable velocity (some weeks 5 items, others 15)
2. Team cost changed mid-project
3. Natural variation in work complexity

**Solution**:
- Expected behavior for velocity-driven costs
- Review velocity trends in Flow Velocity card
- Consider smoothing by looking at multi-week averages

### Issue: Runway Calculation Seems Wrong

**Possible Causes**:
1. Burn rate includes early ramp-up weeks (low velocity)
2. Recent budget increase not reflected in calculation
3. Manual budget total lower than team cost × time

**Solution**:
- Burn rate averages all weeks (includes slow starts)
- Verify revision effective dates are correct
- Check manual budget vs auto-calculated amount

### Issue: Budget Revision History Missing

**Possible Causes**:
1. Revision history deleted (danger zone action)
2. Database connection issue
3. Budget reconfigured (resets baseline)

**Solution**:
- Revision deletion is permanent (no undo)
- Check logs for database errors
- Reconfigure mode resets history (use Update mode instead)

---

## Database Schema

### budget_settings Table

```sql
CREATE TABLE budget_settings (
    profile_id TEXT PRIMARY KEY,
    time_allocated_weeks INTEGER,
    team_cost_per_week_eur REAL,
    budget_total_eur REAL,           -- Can be NULL (auto-calc) or set (manual)
    currency_symbol TEXT DEFAULT '€',
    cost_rate_type TEXT DEFAULT 'weekly',
    created_at TEXT,
    updated_at TEXT
)
```

### budget_revisions Table

```sql
CREATE TABLE budget_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    revision_date TEXT NOT NULL,      -- When revision created
    week_label TEXT NOT NULL,         -- Effective week (e.g., 2026-W03)
    time_allocated_weeks_delta INTEGER DEFAULT 0,
    team_cost_delta REAL DEFAULT 0.0,
    budget_total_delta REAL DEFAULT 0.0,
    revision_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
)
```

---

## Code Reference

### Key Functions

| Function                             | Purpose                             | Returns                                                   |
| ------------------------------------ | ----------------------------------- | --------------------------------------------------------- |
| `get_budget_at_week()`               | Get budget state at specific week   | Dict with time_allocated, team_cost, budget_total         |
| `calculate_consumption()`            | Calculate all budget metrics        | Dict with consumed, burn_rate, runway, cost_per_item, etc |
| `calculate_cost_breakdown_by_type()` | Cost breakdown by Flow Distribution | Dict with feature_cost, defect_cost, etc                  |
| `_get_velocity()`                    | Get velocity for cost calculation   | Float (items/week)                                        |
| `save_budget_revision()`             | Create budget revision record       | None (updates database)                                   |

### Calculation Flow

```
User Query → JIRA Data → Statistics Calculation
                               ↓
                    Budget Settings (current or historical)
                               ↓
                    Velocity Calculation (completed items/time)
                               ↓
                    Cost per Item = Team Cost / Velocity
                               ↓
                    Budget Consumed = Σ(Items × Cost per Item)
                               ↓
                    Burn Rate = Budget Consumed / Weeks Elapsed
                               ↓
                    Runway = (Total - Consumed) / Burn Rate
                               ↓
                    Dashboard Display
```

---

## Report Generation

### Budget Section in Reports

Budget metrics appear in generated reports when configured:

**Included Metrics**:
- Total Budget
- Budget Consumed (amount and %)
- Burn Rate
- Runway
- Cost per Item
- Cost per Point (if Points Tracking enabled)
- Cost Breakdown by Work Type

**Report Structure**:
```html
<section id="budget-overview">
    <h2>Budget Overview</h2>
    <div class="budget-summary">
        <!-- Summary cards with key metrics -->
    </div>
    <div class="budget-details">
        <!-- Detailed breakdown and trends -->
    </div>
</section>
```

### Report Data Source

```python
# data/report_generator.py::_calculate_budget_metrics()

def _calculate_budget_metrics(profile_id: str, query_id: str) -> Dict:
    budget = get_budget_at_week(profile_id, query_id, latest_week)
    consumption = calculate_consumption(profile_id, query_id, latest_week)
    breakdown = calculate_cost_breakdown_by_type(profile_id, query_id)
    
    return {
        "total_budget": budget["budget_total_eur"],
        "consumed": consumption["consumed_eur"],
        "consumed_pct": consumption["consumed_pct"],
        "burn_rate": consumption["burn_rate"],
        "runway": consumption["runway_weeks"],
        "cost_per_item": consumption["cost_per_item"],
        "breakdown": breakdown
    }
```

---

## Migration Guide

### Upgrading from Legacy Budget System

If your project previously tracked budgets manually:

1. **Export existing budget data** (if stored externally)
2. **Configure initial budget** in Settings → Budget
   - Enter historical baseline values
   - Use effective date = project start date
3. **Create revisions for past changes**
   - One revision per significant budget change
   - Use effective dates matching when change occurred
4. **Verify calculations** against manual tracking
   - Compare Budget Consumed
   - Verify Burn Rate matches expectations

### Data Preservation

**What's Preserved**:
- All budget revision history (unless explicitly deleted)
- Historical budget states via replay mechanism
- Audit trail with revision reasons

**What's Not Preserved**:
- Deleted revision history (permanent deletion)
- Budget configurations before system implementation
- Manual calculations outside the system

---

## FAQ

### Q: Can I use Budget metrics without Story Points?

**A**: Yes! Budget metrics work with **item counts** (items completed per week). Story Points are optional - if enabled, you get Cost per Point in addition to Cost per Item.

### Q: What happens if I delete revision history?

**A**: All budget revisions are permanently deleted. Your current budget baseline (in `budget_settings`) is preserved, but you lose the audit trail of how the budget evolved over time.

### Q: How accurate is the Runway calculation?

**A**: Runway assumes current burn rate continues. It's a **forecast**, not a guarantee. Factors that affect accuracy:
- Variable velocity (causes burn rate fluctuations)
- Scope changes mid-project
- Team composition changes

### Q: Can I track multiple budgets (e.g., dev budget + infrastructure)?

**A**: Not directly. Budget metrics track a single budget per project. Workaround:
- Use Manual budget mode to include all costs in total
- Track Cost per Item (reflects only team work)
- Document in revision reasons which costs are included

### Q: Why does Cost per Item change when velocity changes?

**A**: This is **intended behavior** for velocity-driven budgeting:
- High velocity week (12 items) → Lower cost per item (€333)
- Low velocity week (8 items) → Higher cost per item (€500)
- Team cost stays constant (€4,000/week)

This reflects reality: fixed weekly cost distributed across variable output.

---

## Related Documentation

- **[Flow Metrics Guide](./flow_metrics.md)** - Velocity and cycle time metrics
- **[DORA Metrics Guide](./dora_metrics.md)** - Deployment and quality metrics
- **[Dashboard Guide](./dashboard_metrics.md)** - Overview of all dashboard cards
- **[Namespace Syntax](./namespace_syntax.md)** - Field mapping syntax reference

---

**Last Updated**: January 2026  
**Version**: 2.0.0  
**Methodology**: Lean/Agile Budgeting (Adaptive, Velocity-Driven)
