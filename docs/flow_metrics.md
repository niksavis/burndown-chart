# Flow Metrics Guide

**Last Updated**: November 12, 2025  
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

| Metric                | Time Unit  | Aggregation               | Healthy Target                | Code Location                                                   |
| --------------------- | ---------- | ------------------------- | ----------------------------- | --------------------------------------------------------------- |
| **Flow Velocity**     | items/week | Current week count        | Stable, predictable           | `data/flow_calculator.py::calculate_flow_velocity_v2()`         |
| **Flow Time**         | days       | Average of weekly medians | Consistent cycle time         | `data/flow_calculator.py::calculate_flow_time_v2()`             |
| **Flow Efficiency**   | percentage | Current week aggregate    | 25-40%                        | `data/flow_calculator.py::calculate_flow_efficiency_v2()`       |
| **Flow Load (WIP)**   | items      | Current week snapshot     | <P25 threshold (green)        | `data/flow_calculator.py::calculate_flow_load_v2()`             |
| **Flow Distribution** | percentage | Current week breakdown    | Feature 40-60%, Defect 20-40% | `data/flow_calculator.py::aggregate_flow_distribution_weekly()` |

---

## 1. Flow Velocity

### What It Measures
Number of work items completed per week, classified by work type.

### Calculation Details

**Per Week**:
- COUNT of issues with `status IN completion_statuses` AND `resolutiondate` in that week

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
Average time from work start to completion (cycle time).

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
Feature:   40-60%  │██████████████░░░░░░│ - New business value
Defect:    20-40%  │████████░░░░░░░░░░░░│ - Quality maintenance
Tech Debt: 10-20%  │████░░░░░░░░░░░░░░░░│ - Infrastructure health
Risk:       0-10%  │██░░░░░░░░░░░░░░░░░░│ - Security, compliance
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
8. Adjust work mix to hit target ranges (40-60% Feature, 20-40% Defect)
9. Monitor Flow Efficiency - aim for 25-40%

**Progressive Approach**: WIP first, distribution second, efficiency third.

---

## Additional Resources

- **Shared Concepts**: See [Metrics Index](./metrics_index.md) for metric relationships and common pitfalls
- **Related Metrics**: See [DORA Metrics](./dora_metrics.md) for deployment outcome metrics that Flow predicts
- **Project Forecasting**: See [Dashboard Metrics](./dashboard_metrics.md) for completion forecasts

---

## Documentation Verification

**Last Verified**: November 12, 2025  
**Verified Against**: `data/flow_calculator.py` implementations

All calculations, formulas, and behaviors documented above match the actual code implementation.
