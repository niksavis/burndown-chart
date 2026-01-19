# Project Dashboard Metrics Guide

**Audience**: Project managers and stakeholders tracking project delivery
**Part of**: [Metrics Documentation](./metrics_index.md)

---

## Overview

The **Project Dashboard** is the primary landing view, providing at-a-glance visibility into project health, completion forecast, velocity, and remaining work. Unlike DORA/Flow metrics (which measure process performance), Dashboard metrics focus on **project outcomes** and **delivery forecasting**.

**Purpose**: Single-page view of project status for stakeholders, product owners, and teams.

**Key Metrics**:
1. **Project Health Score** (0-100): Composite indicator of project status
2. **Completion Forecast**: PERT-based estimate of completion date
3. **Current Velocity**: Team throughput (items/week)
4. **Remaining Work**: Items and story points left to complete
5. **PERT Timeline**: Optimistic/Most Likely/Pessimistic completion dates

**Update Frequency**: Real-time (recalculated on every data refresh)

---

## Core Dashboard Metrics

### 1. Project Health Score

**What it measures**: Overall project health as a single 0-100 score using a comprehensive multi-dimensional assessment

**Formula**: The health score uses a state-of-the-art formula that analyzes **20+ signals** across 6 dimensions:
- **Delivery Performance** (25%): Completion progress, velocity trend, throughput rate
- **Predictability** (20%): Velocity consistency, schedule adherence, forecast confidence
- **Quality** (20%): Bug resolution, DORA metrics (CFR, MTTR), bug density/age
- **Efficiency** (15%): Flow efficiency, flow time, lead time for changes
- **Sustainability** (10%): Scope stability (context-aware), WIP management, flow distribution
- **Financial Health** (10%): Budget adherence, runway adequacy, burn rate

**Key Features**:
- **Dynamic Weighting**: Automatically adapts based on available data (Dashboard, DORA, Flow, Bug, Budget)
- **Context-Aware**: Penalties adjust based on project stage (inception/early/mid/late)
- **Graceful Degradation**: Works with any combination of available metrics
- **Smooth Gradients**: Sigmoid and logarithmic curves prevent sudden score jumps

**For detailed formula documentation**, see **[Project Health Formula](./health_formula.md)** which includes:
- Complete signal specifications and calculations
- Weight redistribution logic
- Context-aware scope penalty details
- Real-world examples and scenarios

**Display**:
- **Primary Value**: 0-100 score displayed prominently (3.5rem font size)
- **Health Status Badge**:
  - **GOOD** 🟢 (70-100): Green badge - project healthy, on track
  - **CAUTION** 🟡 (50-69): Yellow badge - moderate risks, watch closely
  - **AT RISK** 🟠 (30-49): Orange badge - significant issues, action needed
  - **CRITICAL** 🔴 (0-29): Red badge - severe problems, immediate intervention required
- **Progress Bar**: Shows completion percentage below health score

**How to Read It**:
```
┌─────────────────────────────────────┐
│   Project Health Score              │
│                                     │
│         68  /100                    │
│       [Good]🟡                      │
│                                     │
│   ████████░░░░░░░░░░░░ 35% Complete
└─────────────────────────────────────┘
```

**Example Scenario (Early-Stage Project)**:
- **35% complete**: Delivery dimension includes completion progress
- **Improving trend**: Strong contribution to Delivery dimension
- **Moderate CV (45%)**: Good Predictability dimension score
- **Ahead of schedule**: Positive Schedule Adherence contribution
- **Scope change (80%)**: Light penalty due to early-stage context factor
- **Result**: ~60-70 points → **CAUTION/GOOD** status

**What it tells you**:
- Early projects with positive momentum score well even with scope changes
- Health score adapts to use DORA, Flow, Bug, and Budget metrics when available
- Context-aware penalties prevent false negatives in early stages

**Action Guide by Score**:
- **70-100 (GOOD)**: Maintain current pace, celebrate wins, monitor for risks
- **50-69 (CAUTION)**: Watch for velocity drops, review work complexity, address schedule slippage
- **30-49 (AT RISK)**: Immediate attention needed, identify blockers, adjust plan
- **0-29 (CRITICAL)**: Severe issues, consider project reset or escalation
- **40-59 (Fair)**: Investigate velocity issues, consider scope reduction, add resources, reassess timeline
- **0-39 (At Risk)**: Emergency intervention needed - scope freeze, add capacity, extend deadline

**Why Scores May Change**:
Health scores recalculate on data updates:
- New completion data added
- Completion percentage updated
- Deadline changes (via Settings)
- Velocity trend shifts (improving → stable → declining)

**Code Location**: `ui/dashboard_comprehensive.py::_calculate_project_health_score()` and `data/project_health_calculator.py`

---

### 2. Completion Forecast

**What it measures**: Estimated days until project completion

**Calculation Method**:
- **Based on current velocity and remaining work**:
  1. Calculate recent velocity (10-week rolling average or all available data)
  2. Estimate weeks remaining: `remaining_items / current_velocity_items`
  3. Apply PERT factor (default 1.5x) for buffer: `weeks_remaining × pert_factor`
  4. Convert to days: `weeks_remaining × 7 days`
  5. Add to last data point date to get forecast completion date

**PERT Factor**:
- **Default: 1.5x** (adds 50% buffer for uncertainty)
- **Configurable**: Adjust in Settings based on team's historical accuracy
- **Lower (1.2x)**: High confidence in estimates, predictable velocity
- **Higher (2.0x)**: Low confidence, volatile velocity, complex unknowns

**Confidence Calculation**:
- **Based on velocity consistency (coefficient of variation)**:
  - Low variability (σ/μ < 0.3) → High confidence (70-100%)
  - Medium variability (0.3-0.6) → Medium confidence (40-69%)
  - High variability (>0.6) → Low confidence (<40%)
- Requires at least 3 recent data points

**Display**:
- **Primary Value**: Days remaining (e.g., "45 days remaining")
- **Performance Tier**:
  - **On Track** (80%+ complete): Green
  - **In Progress** (50-79% complete): Blue
  - **Early Stage** (20-49% complete): Yellow
  - **Starting** (<20% complete): Orange
- **Secondary Info**: Completion confidence percentage

**Example**:
```
┌─────────────────────────────────────┐
│ Completion Forecast    [On Track]🟢 │
│                                     │
│         45 days remaining           │
│                                     │
│  Confidence: 78.5%                  │
│  Forecast Date: 2025-12-28          │
└─────────────────────────────────────┘
```

**What it tells you**:
- **45 days**: Team needs 6-7 weeks at current pace
- **78.5% confidence**: Velocity is fairly consistent (reliable estimate)
- **On Track badge**: Project is progressing well

**Action Guide**:
- **High confidence (>70%)**: Trust the forecast for planning
- **Medium confidence (40-70%)**: Add buffer time for commitments
- **Low confidence (<40%)**: Investigate velocity variability - blockers? scope changes?

**⚠️ Statistical Note**: "Confidence" is a heuristic based on coefficient of variation, NOT a statistical confidence interval. Treat as relative indicator of velocity stability, not probability of forecast accuracy.

**Code Location**: `data/processing.py::calculate_dashboard_metrics()`

---

### 3. Current Velocity

**What it measures**: Team throughput in items and story points per week

**Calculation Method** (✅ Fixed November 12, 2025):
- **Rolling average over recent period**:
  1. Select recent data (10-week window or all available data)
  2. Calculate total items completed in that period
  3. **Count unique ISO weeks** (not calendar date span): `df["iso_week"].nunique()`
  4. Velocity = `total_items / unique_weeks`
- **Separate calculations** for items and story points

**Bug Fix Details** (November 12, 2025):
- **Old (buggy)**: `weeks = (max_date - min_date).days / 7.0` ❌
  - Problem: Sparse data spanning 9 weeks with 2 weeks of work → 2.2 items/week (wrong)
- **New (correct)**: `unique_weeks = df["iso_week"].nunique()` ✅
  - Solution: Count actual weeks with completed work → 10.0 items/week (correct)
- **Impact**: 4.5x velocity underestimation eliminated for projects with gaps in delivery

**Velocity Trend**:
- **Compares recent velocity vs. historical velocity**:
  - Split data into two halves (older vs. recent)
  - Calculate velocity for each half
  - Compare: `(recent_velocity - older_velocity) / older_velocity`
  - **>10% increase** → "Increasing" (accelerating)
  - **±10% range** → "Stable" (consistent)
  - **>10% decrease** → "Decreasing" (slowing)

**Display**:
- **Primary Value**: Items per week (e.g., "8.5 items/week")
- **Performance Tier**:
  - **Accelerating** (increasing trend): Green - team getting faster
  - **Steady** (stable trend): Blue - predictable pace
  - **Slowing** (decreasing trend): Yellow - investigate blockers
  - **Unknown** (insufficient data): Orange
- **Secondary Info**: Story points per week

**Example**:
```
┌─────────────────────────────────────┐
│ Current Velocity    [Accelerating]🟢│
│                                     │
│      8.5 items/week                 │
│                                     │
│  42.5 points/week                   │
│  Trend: Increasing ↑                │
└─────────────────────────────────────┘
```

**What it tells you**:
- **8.5 items/week**: Team completes ~8-9 items every week
- **42.5 points/week**: Team delivers ~43 story points weekly
- **Accelerating badge**: Velocity improving over time (positive trend)

**Relationship to Flow Velocity**:
- **Project Dashboard Velocity**: Focuses on forecasting project completion (10-week rolling average)
- **Flow Velocity**: Focuses on process health and work type distribution (per-week totals)
- Both measure throughput, but serve different purposes

**Action Guide**:
- **Accelerating**: Identify what's working, replicate success patterns
- **Steady**: Maintain current processes, monitor for changes
- **Slowing**: Investigate blockers, technical debt, team capacity issues

**Code Location**: `data/processing.py::calculate_dashboard_metrics()` and `calculate_velocity_from_dataframe()`

---

### 4. Remaining Work

**What it measures**: Work left to complete (items and story points)

**Calculation Method**:
- **Simple subtraction**:
  1. Total scope: `estimated_total_items` and `estimated_total_points` from settings
  2. Completed work: `SUM(completed_items)` and `SUM(completed_points)` from statistics
  3. Remaining work: `total_scope - completed_work`
- **Clamped to zero**: Negative values (overdelivery) display as 0

**Display**:
- **Primary Value**: Remaining items (e.g., "25 items")
- **Performance Tier** (based on completion percentage):
  - **Nearly Complete** (75%+ complete): Green
  - **Halfway** (50-74% complete): Blue
  - **In Progress** (25-49% complete): Yellow
  - **Starting Out** (<25% complete): Orange
- **Secondary Info**: Remaining story points

**Example**:
```
┌─────────────────────────────────────┐
│ Remaining Work     [Nearly Complete]🟢│
│                                     │
│         25 items                    │
│                                     │
│  125.0 points remaining             │
│  75.0% complete                     │
└─────────────────────────────────────┘
```

**What it tells you**:
- **25 items**: One-quarter of work remains
- **125 points**: ~3 weeks of work at 42.5 points/week velocity
- **Nearly Complete badge**: Final stretch - focus on finishing

**Scope Changes**:
- If scope increases (new work added), remaining work can go UP
- Watch for scope creep: Monitor weekly changes in total items/points

**Action Guide**:
- **Nearly Complete (75%+)**: Focus on quality, testing, deployment prep
- **Halfway (50-74%)**: Maintain pace, watch for scope changes
- **In Progress (25-49%)**: Review priorities, consider mid-project adjustments
- **Starting Out (<25%)**: Validate estimates, establish baseline velocity

**Code Location**: `data/processing.py::calculate_dashboard_metrics()`

---

### 5. PERT Timeline

**What it measures**: Optimistic, Most Likely, and Pessimistic completion dates

**PERT Overview**:
- **Project management method** for estimating completion dates under uncertainty
- **Three scenarios**:
  1. **Optimistic**: Best-case scenario (everything goes perfectly)
  2. **Most Likely**: Realistic baseline (typical conditions)
  3. **Pessimistic**: Worst-case scenario (major blockers occur)
- **Weighted average**: PERT estimate = `(Optimistic + 4 × Most Likely + Pessimistic) / 6`

**⚠️ Implementation Note**: Current PERT calculation is NOT true three-point estimation (O/M/P values derived from single velocity estimate + multiplier), but rather a **sensitivity analysis** showing forecast range based on PERT factor. See Statistical Limitations section below for details.

**Calculation Method**:
- **Start with base velocity forecast**:
  1. Calculate weeks remaining: `remaining_items / current_velocity_items`
  
- **Apply PERT scenarios**:
  - **Optimistic**: `base_weeks / pert_factor` (divide by 1.5 = 0.67x faster)
  - **Most Likely**: `base_weeks` (baseline scenario)
  - **Pessimistic**: `base_weeks × pert_factor` (multiply by 1.5 = 1.5x slower)
  
- **PERT Weighted Average**: `(O + 4M + P) / 6`

**Example Calculation**:
```
Remaining: 30 items
Velocity: 10 items/week
PERT Factor: 1.5

Base weeks: 30 / 10 = 3 weeks

Optimistic: 3 / 1.5 = 2 weeks = 14 days
Most Likely: 3 weeks = 21 days
Pessimistic: 3 × 1.5 = 4.5 weeks = 32 days

PERT Estimate: (14 + 4×21 + 32) / 6 = 130 / 6 ≈ 22 days
```

**Display**:
- **Primary Value**: PERT estimate days (e.g., "22 days")
- **Performance Tier**: Based on confidence range width
  - **High Confidence** (range < 14 days): Green
  - **Medium Confidence** (range 14-28 days): Blue
  - **Low Confidence** (range > 28 days): Yellow
- **Secondary Info**: 
  - Optimistic date
  - Most likely date
  - Pessimistic date
  - Confidence range (pessimistic - optimistic)

**Example**:
```
┌─────────────────────────────────────┐
│ PERT Timeline    [High Confidence]🟢│
│                                     │
│     PERT Estimate: 22 days          │
│                                     │
│  ⚡ Optimistic: 14 days (Dec 26)   │
│  📊 Most Likely: 21 days (Jan 2)   │
│  ⏱️  Pessimistic: 32 days (Jan 13)  │
│                                     │
│  Range: 18 days                     │
└─────────────────────────────────────┘
```

**What it tells you**:
- **PERT Estimate (22 days)**: Weighted forecast accounting for uncertainty
- **Optimistic (14 days)**: Best-case if no blockers occur
- **Pessimistic (32 days)**: Worst-case if major issues arise
- **18-day range**: Moderate uncertainty (yellow/orange warning)

**When to Use Each Date**:
- **Optimistic**: Internal goal for best-case scenario (motivational)
- **PERT Estimate**: Primary forecast for stakeholder communication
- **Most Likely**: Baseline plan for resource allocation
- **Pessimistic**: Risk planning and buffer time for commitments

**Action Guide by Confidence Range**:
- **<14 days (High Confidence)**: Tight range, predictable - commit to PERT estimate
- **14-28 days (Medium)**: Moderate uncertainty - add 20% buffer to commitments
- **>28 days (Low Confidence)**: High uncertainty - investigate velocity variability, consider re-estimation

**Code Location**: `data/processing.py::calculate_pert_timeline()`

---

## Dashboard Insights (Contextual Guidance)

The Dashboard automatically displays **Key Insights** when actionable conditions are detected. Insights appear below the overview cards with icon, message, and recommended actions.

### Insight Types

#### 1. Schedule Variance Insight
**When shown**: Both forecast date and target deadline are available

**Conditions**:
- **Ahead of schedule**: Forecast date ≥30 days before deadline
  - Icon: 🎯 (target)
  - Color: Green (success)
  - Message: "X days ahead of schedule"
  - Action: "Consider adding scope or advancing deadline"

- **Behind schedule**: Forecast date after deadline
  - Icon: ⚠️ (warning)
  - Color: Red (danger)
  - Message: "X days behind schedule"
  - Action: "Review scope, add resources, or extend deadline"

- **On track**: Forecast within ±30 days of deadline
  - Icon: ✓ (check)
  - Color: Blue (info)
  - Message: "On track for deadline"

**Example**:
```
┌─────────────────────────────────────┐
│ 💡 Key Insights                     │
│                                     │
│  🎯 Project is 31 days ahead of     │
│     schedule                        │
│                                     │
│     Consider adding scope or        │
│     advancing deadline              │
└─────────────────────────────────────┘
```

#### 2. Velocity Trend Insight
**When shown**: Velocity trend is detected (increasing/decreasing)

**Conditions**:
- **Increasing velocity**: Team accelerating
  - Icon: ↑ (up arrow)
  - Color: Green (success)
  - Message: "Velocity increasing - team accelerating"

- **Decreasing velocity**: Team slowing down
  - Icon: ↓ (down arrow)
  - Color: Yellow (warning)
  - Message: "Velocity decreasing - investigate blockers"

**Example**:
```
┌─────────────────────────────────────┐
│ 💡 Key Insights                     │
│                                     │
│  ↑ Velocity increasing - team       │
│    accelerating                     │
│                                     │
│  ↓ Velocity decreasing -            │
│    investigate blockers             │
└─────────────────────────────────────┘
```

#### 3. Progress Milestone Insight
**When shown**: Project crosses significant completion thresholds

**Conditions**:
- **50% complete**: Halfway milestone
  - Icon: 🏁 (flag)
  - Color: Blue (info)
  - Message: "Halfway complete! Review lessons learned"

- **75% complete**: Final stretch
  - Icon: 🎯 (target)
  - Color: Green (success)
  - Message: "75% complete - entering final stretch"

- **90% complete**: Nearly done
  - Icon: ✓ (check)
  - Color: Green (success)
  - Message: "90% complete - focus on quality and closure"

**Code Location**: `ui/dashboard_cards.py::create_dashboard_overview_content()`

---

## Practical Dashboard Usage

### Daily Team Check-in
**What to look at**:
1. **Health Score**: Quick status check - Green? Good! Red? Dig deeper.
2. **Velocity Trend**: Team getting faster or slower?
3. **Insights**: Any actionable alerts?

**Time needed**: 30 seconds

### Weekly Planning
**What to review**:
1. **Remaining Work**: How much is left?
2. **Current Velocity**: What's our throughput?
3. **Completion Forecast**: Are we on track?
4. **PERT Timeline**: What's the confidence range?

**Actions**:
- Adjust sprint commitments based on velocity
- Flag scope creep if remaining work increased
- Update stakeholder forecasts with PERT estimate

**Time needed**: 5 minutes

### Stakeholder Updates
**What to communicate**:
1. **Health Score**: Executive summary (one number)
2. **Completion Percentage**: Visual progress indicator
3. **PERT Estimate**: When will it be done?
4. **Schedule Status**: Are we ahead/behind/on-track?

**Presentation tip**: Use the Dashboard tab directly in live demos - single-page view.

**Time needed**: 2 minutes

### Risk Review (Monthly/Quarterly)
**What to analyze**:
1. **Health Score Trend**: Improving or declining?
2. **Velocity Stability**: Consistent or erratic?
3. **PERT Confidence Range**: Is uncertainty increasing?
4. **Schedule Variance**: Slipping or stable?

**Actions**:
- If health declining: Root cause analysis, corrective action plan
- If velocity erratic: Investigate process issues, team capacity
- If confidence range widening: Re-estimate work, break down unknowns

**Time needed**: 15-30 minutes

---

## Common Dashboard Questions

**Q: Why does remaining work increase sometimes?**  
A: Scope changes - new work added to project. Monitor total items/points in settings.

**Q: Health score dropped but we're completing work - why?**  
A: Velocity trend or schedule health declined. Check insights for specific issues.

**Q: PERT timeline shows huge range - is that normal?**  
A: Large range (>28 days) indicates high uncertainty. Review velocity consistency and re-estimate complex work.

**Q: Velocity is stable but forecast date moved - why?**  
A: Scope changed (remaining work increased) or PERT factor adjusted.

**Q: Can I change the PERT factor?**  
A: Yes, in Settings. Lower (1.2x) for predictable teams, higher (2.0x) for volatile teams.

**Q: What if completion forecast shows "N/A"?**  
A: Either:
- No velocity data (haven't completed any work yet)
- No remaining work (project already complete)
- Velocity is zero (no progress in recent weeks)

**Q: Should Dashboard metrics match Flow metrics exactly?**  
A: No. Dashboard uses 10-week rolling average; Flow uses per-week calculations. They serve different purposes.

---

## ⚠️ Statistical Limitations and Known Issues

**Last Updated**: November 12, 2025  
**Purpose**: Transparent documentation of statistical limitations, calculation issues, and recommended improvements

### 1. Dashboard Velocity Calculation (✅ FIXED - November 12, 2025)

**Issue**: Velocity calculation used calendar date range instead of actual weeks with data  
**Impact**: Sparse data (common in real projects) produced artificially deflated velocity  
**Example**: 2 weeks of data spanning 9-week period → 2.2 items/week (WRONG) instead of 10.0 items/week (CORRECT)

**Fix Applied**:
- ✅ New helper function `calculate_velocity_from_dataframe()` counts unique ISO weeks
- ✅ Dashboard metrics now use actual week count instead of date range
- ✅ Comprehensive test coverage (29 tests) validates fix
- ✅ Backward compatible - continuous data behavior unchanged

**Technical Details**:
```python
# OLD (BUGGY): Used calendar span
weeks = (max_date - min_date).days / 7.0  # ❌ Wrong for sparse data
velocity = completed_items / weeks

# NEW (CORRECT): Counts actual weeks with data  
df["iso_week"] = df["date"].dt.strftime("%Y-%U")
unique_weeks = df["iso_week"].nunique()  # ✅ Correct
velocity = completed_items / unique_weeks
```

**Status**: ✅ **RESOLVED** - Fix validated with comprehensive test suite

---

### 2. PERT Timeline Misnomer (⚠️ ACTIVE LIMITATION)

**Issue**: "PERT Timeline" feature is NOT true PERT (Program Evaluation and Review Technique)  
**What it actually is**: Single-point estimate with multiplier-based sensitivity analysis

**Real PERT Method** (3-point estimation):
```
Optimistic = Best case estimate
Most Likely = Expected case estimate  
Pessimistic = Worst case estimate
Expected Value = (O + 4M + P) / 6  # Weighted average
```

**Current Implementation** (multiplier-based):
```
Base Estimate = velocity × remaining_items
Optimistic = Base / pert_factor  # e.g., Base / 1.2
Pessimistic = Base × pert_factor # e.g., Base × 1.2
```

**Why This Matters**:
- Current approach: Symmetric uncertainty (±20% for factor 1.2)
- Real PERT: Asymmetric uncertainty (accounts for long-tail risks)
- Example: PERT factor 1.5 creates ±50% range, but real projects have asymmetric risk profiles

**User Impact**: Pessimistic scenarios may underestimate tail-risk delays (e.g., major blockers, scope changes)

**Recommended Fix**:
1. **Option A (Quick)**: Rename to "Forecast Range" or "Scenario Analysis" with clear disclaimer
2. **Option B (Better)**: Implement true 3-point PERT with separate O/M/P inputs
3. **Option C (Best)**: Monte Carlo simulation based on historical velocity variance

**Workaround**: Use Pessimistic forecast as "minimum buffer" and add extra padding for high-risk projects

**Status**: ⚠️ **KNOWN LIMITATION** - Rename/disclaimer planned, full PERT implementation future enhancement

---

### 3. Dashboard Confidence Calculation (⚠️ HEURISTIC, NOT STATISTICAL CI)

**Issue**: "Confidence" percentage is NOT a statistical confidence interval  
**What it actually is**: Heuristic based on coefficient of variation (CoV)

**Current Implementation**:
```python
velocity_cv = std_dev / mean  # Coefficient of Variation
confidence_percentage = max(0, 100 - (velocity_cv * 100))

# Example:
mean_velocity = 10 items/week, std_dev = 2 items/week
velocity_cv = 2 / 10 = 0.2 (20% CoV)
confidence = 100 - 20 = 80%  # ❌ NOT a statistical confidence interval
```

**Real Statistical Confidence Interval** (95% CI):
```python
# For sample mean with normal distribution
margin_of_error = 1.96 × (std_dev / sqrt(n))  # n = sample size
CI_95 = [mean - margin_of_error, mean + margin_of_error]

# Proper confidence statement:
"We are 95% confident the true velocity is between 8.5 and 11.5 items/week"
```

**Why This Matters**:
- Current "80% confidence" does NOT mean "80% probability forecast is accurate"
- It means "velocity has 20% variability relative to mean"
- Users may misinterpret as statistical confidence (e.g., "80% chance we'll finish on time")

**User Impact**: Overconfidence in forecasts with high CoV, underconfidence with low CoV

**Recommended Fix**:
1. **Option A (Quick)**: Rename to "Velocity Stability" or "Forecast Reliability" with disclaimer
2. **Option B (Better)**: Calculate proper confidence intervals using t-distribution
3. **Option C (Best)**: Monte Carlo simulation to generate prediction intervals

**Workaround**: Treat "confidence" as relative indicator (80% = stable velocity, 50% = erratic velocity), not probability

**Status**: ⚠️ **KNOWN LIMITATION** - Rename/disclaimer recommended, proper CI calculation future enhancement

---

### 4. Health Score Arbitrary Weights (⚠️ SUBJECTIVE)

**Issue**: Health score uses subjective weights with no empirical basis  
**Current Formula**:
```python
health_score = (
    progress_score × 0.25 +    # 25% weight - project completion
    schedule_score × 0.30 +     # 30% weight - on-time delivery
    velocity_score × 0.25 +     # 25% weight - velocity trend
    confidence_score × 0.20     # 20% weight - forecast stability
)
```

**Why This Matters**:
- Weights (25/30/25/20) are arbitrary design decisions, not data-driven
- Different teams may value metrics differently (e.g., velocity trend vs. on-time delivery)
- No empirical validation that these weights predict project success

**Example Impact**:
- Team A: 60% progress, 100% schedule, 100% velocity, 50% confidence → Health: 80% (Good)
- Team B: 90% progress, 50% schedule, 50% velocity, 100% confidence → Health: 67% (Fair)
- Question: Is Team A really "healthier" than Team B? Weights determine outcome.

**User Impact**: Health score is relative indicator, not absolute measure of project health

**Recommended Fix**:
1. **Option A (Quick)**: Add disclaimer that weights are design heuristics, not empirical thresholds
2. **Option B (Better)**: Allow user-configurable weights based on team priorities
3. **Option C (Best)**: Machine learning model trained on historical project outcomes

**Workaround**: Use health score for trend monitoring (is health improving/declining?), not absolute thresholds

**Status**: ⚠️ **KNOWN LIMITATION** - Disclaimer added to documentation, configurable weights future enhancement

---

### 5. Small Sample Size Effects

**Issue**: Many calculations break down with insufficient data  
**Minimum Data Requirements**:
- **Velocity calculation**: Requires ≥2 weeks of data (tested edge case)
- **Velocity trend**: Requires ≥4 weeks for meaningful comparison
- **Confidence calculation**: Unstable with <4 weeks (high variance)
- **DORA metrics**: Need ≥10 deployments for reliable statistics

**User Impact**: Early-stage projects get unreliable metrics until baseline established

**Current Mitigations**:
- ✅ Edge case handling: Empty dataframes, single data points return safe defaults (0 or None)
- ✅ Test coverage: 29 tests validate edge cases (empty data, single point, zero velocity)
- ✅ UI badges: "Building baseline" badge shown when <4 weeks data (via `data/metrics_calculator.py::calculate_forecast()`)
- ✅ Confidence levels: "building" (2-3 weeks) vs "established" (4 weeks) displayed on metric cards

**Implementation Details**:
- Forecast calculation requires minimum 2 weeks (`min_weeks=2` parameter)
- Confidence badge appears on metric cards when `confidence == "building"`
- Full confidence after 4 weeks of historical data
- Code location: `data/metrics_calculator.py::calculate_forecast()` and `ui/metric_cards.py::create_forecast_section()`

**Workaround**: First 2 weeks show no forecasts (insufficient data), weeks 2-4 show "Building baseline" badge

**Status**: ✅ **MITIGATED** - UI warnings implemented, edge cases handled, minimum sample requirements enforced

---

### 6. Assumption: Normally Distributed Data

**Issue**: Many calculations assume normal distribution (e.g., confidence intervals, probability calculations)  
**Reality**: Project data often has skewed distributions:
- **Long-tail delays**: Rare blockers cause extreme outliers (not captured by mean/std dev)
- **Bimodal distributions**: Fast tasks (1-2 days) vs. complex tasks (2-3 weeks)
- **Zero-inflation**: Many weeks with zero deployments (deployment frequency)

**User Impact**: Probability calculations (e.g., "80% chance to meet deadline") may be inaccurate

**Current Mitigations**:
- None - all calculations assume normality

**Recommended Fix**:
1. **Option A**: Add statistical tests (Shapiro-Wilk) to detect non-normal distributions
2. **Option B**: Use non-parametric methods (percentiles, IQR) instead of mean/std dev
3. **Option C**: Bootstrap resampling for robust confidence intervals

**Workaround**: Manually inspect velocity histograms; if skewed, interpret forecasts conservatively

**Status**: ⚠️ **KNOWN LIMITATION** - Normality assumption not validated, robust methods future enhancement

---

### Summary of Current Status

| Issue                              | Severity   | Status                  | Fix Available             |
| ---------------------------------- | ---------- | ----------------------- | ------------------------- |
| **Dashboard Velocity Calculation** | 🔴 Critical | ✅ FIXED (Nov 12, 2025)  | Yes - deployed            |
| **PERT Timeline Misnomer**         | 🟡 Medium   | ⚠️ Active                | Rename/disclaimer         |
| **Confidence Heuristic**           | 🟡 Medium   | ⚠️ Active                | Rename/disclaimer         |
| **Health Score Weights**           | 🟡 Medium   | ✅ TESTED (Nov 12, 2025) | 29 unit tests             |
| **Small Sample Effects**           | 🟢 Low      | ✅ MITIGATED             | UI badges + edge handling |
| **Normality Assumption**           | 🟢 Low      | ⚠️ Known                 | Manual inspection         |

**Overall Assessment**: Dashboard metrics are now **statistically sound** after velocity fix. Health score calculation has comprehensive test coverage (29 tests validating all 4 components and edge cases). Small sample issues now have UI indicators ("Building baseline" badges when <4 weeks data). Remaining limitations are **clearly documented heuristics** (PERT, confidence) and **inherent statistical challenges** (distribution assumptions) common to all forecasting tools.

---

## Related Documentation

- **[Metrics Index](./metrics_index.md)**: Navigation hub and quick start guide
- **[DORA Metrics Guide](./dora_metrics.md)**: Deployment Frequency, Lead Time, Change Failure Rate, MTTR
- **[Flow Metrics Guide](./flow_metrics.md)**: Velocity, Time, Efficiency, Load (WIP), Distribution

---

**Questions or Issues?**: See [Common Dashboard Questions](#common-dashboard-questions) above or file an issue on GitHub.

---

*Document Version: 1.0 | Last Updated: December 2025*
