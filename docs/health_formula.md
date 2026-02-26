# Project Health Formula - Comprehensive Multi-Dimensional Assessment

**Audience**: Project managers and stakeholders who want to understand health score calculation
**Part of**: [Metrics Documentation Index](./metrics_index.md)

## Overview

The project health formula represents a **state-of-the-art assessment** that leverages **all available signals** across the application to provide the most accurate project health status possible.

### Key Features

| Aspect                | Description                                                           |
| --------------------- | --------------------------------------------------------------------- |
| **Data Sources**      | Dashboard + DORA + Flow + Bug Analysis + Scope + Budget (20+ signals) |
| **Dimensions**        | Multi-dimensional (6 categories with sub-signals)                     |
| **Adaptability**      | Dynamic weighting based on available data                             |
| **Missing Data**      | Gracefully redistributes weights                                      |
| **Context Awareness** | Project stage + metric categories                                     |

## Weight Justification (Executive Summary)

**Question**: Why these specific weights (Delivery 25%, Predictability 20%, Quality 20%, Efficiency 15%, Sustainability 10%, Financial 10%)?

**Answer**: Weights reflect **industry research** and **executive priorities** for project success:

| Dimension          | Weight | Rationale                                                                                                                                                                  |
| ------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Delivery**       | 25%    | **Primary value driver**. Research shows 80% of project failures stem from inability to deliver working software. Highest weight reflects "are we shipping?"               |
| **Predictability** | 20%    | **Critical for planning**. Chaos Report (Standish Group) cites poor estimation/unpredictability as #2 project failure cause. Enables stakeholder confidence/roadmap trust. |
| **Quality**        | 20%    | **Risk mitigation**. DORA research correlates quality with organizational performance. Poor quality = technical debt spiral, customer churn, reputational damage.          |
| **Efficiency**     | 15%    | **Cost optimization**. Lean/Kanban research shows 15-20% efficiency gains possible. Lower weight than delivery/quality as speed without quality/predictability is risky.   |
| **Sustainability** | 10%    | **Long-term viability**. Agile Manifesto emphasizes "sustainable pace." Prevents burnout, scope creep, technical debt accumulation. Secondary to immediate delivery.       |
| **Financial**      | 10%    | **Budget adherence**. Important but adaptive - projects can get more budget if delivering value. Lower weight reflects that budget follows value, not vice versa.          |

**Key Research Sources**:

- **DORA State of DevOps Reports** (2015-2024): Quality/efficiency correlation with performance
- **Standish Group Chaos Reports** (1994-2024): Delivery/predictability as top success factors
- **Lean Software Development** (Mary & Tom Poppendieck): Waste elimination, flow efficiency
- **Agile Manifesto Principles**: Working software, sustainable pace, technical excellence

**Dynamic Adjustment**: If dimensions lack data (e.g., no budget tracking), weights redistribute proportionally to available dimensions, always summing to 100%.

## Formula Architecture

### Dimensional Breakdown

```
Project Health (0-100) = Weighted sum of available dimensions

Dimension Categories (max weight %):
├── Delivery Performance (25%)     - Are we delivering?
│   ├── Completion Progress (30 pts)
│   ├── Velocity Trend (35 pts)
│   └── Throughput Rate (35 pts)
│
├── Predictability (20%)           - Can we forecast accurately?
│   ├── Velocity Consistency (50 pts)
│   ├── Schedule Adherence (30 pts)
│   └── Forecast Confidence (20 pts)
│
├── Quality (20%)                  - Are we building it right?
│   ├── Bug Resolution Rate (30 pts)
│   ├── Change Failure Rate (25 pts) [DORA]
│   ├── MTTR (20 pts) [DORA]
│   └── Bug Density/Age (25 pts)
│
├── Efficiency (15%)               - How fast do we deliver?
│   ├── Flow Efficiency (40 pts) [Flow Metrics]
│   ├── Flow Time (35 pts) [Flow Metrics]
│   └── Lead Time for Changes (25 pts) [DORA]
│
├── Sustainability (10%)           - Can we maintain this pace?
│   ├── Scope Stability (40 pts) [Context-aware]
│   ├── WIP Management (35 pts) [Flow Metrics]
│   └── Flow Distribution Balance (25 pts) [Flow Metrics]
│
└── Financial Health (10%)         - Are we within budget?
    ├── Budget Adherence (40 pts)
    ├── Runway Adequacy (35 pts)
    └── Burn Rate Health (25 pts)
```

### Dynamic Weighting

**Key Innovation**: Weights automatically adjust when metrics are unavailable, **always summing to 100%** to allow perfect scores to reach 100% overall health.

**How it works**:

1. **Base weights**: Each dimension has a max_weight representing its relative importance (Delivery: 25%, Predictability: 20%, Quality: 20%, Efficiency: 15%, Sustainability: 10%, Financial: 10%)

2. **Missing dimensions**: When dimensions lack data (weight = 0), their max_weights are proportionally redistributed to available dimensions

3. **Cap enforcement**: No dimension can exceed its proportionally adjusted max_weight, maintaining relative importance

4. **100% target**: Weights always sum to 100%, ensuring perfect scores across all available dimensions yield 100% overall health

**Example scenarios**:

1. **Full Data Available** (Dashboard + DORA + Flow + Bug + Budget):
   - All dimensions at base max_weights
   - Delivery: 25%, Predictability: 20%, Quality: 20%, Efficiency: 15%, Sustainability: 10%, Financial: 10%
   - Perfect scores → 100% overall health ✓

2. **No Financial Data** (Dashboard + DORA + Flow + Bug):
   - Financial's 10% redistributed proportionally
   - Delivery: 25% + (25/90 × 10%) = 27.8%
   - Predictability: 20% + (20/90 × 10%) = 22.2%
   - Quality: 20% + (20/90 × 10%) = 22.2%
   - Efficiency: 15% + (15/90 × 10%) = 16.7%
   - Sustainability: 10% + (10/90 × 10%) = 11.1%
   - Total: 100% ✓
   - Perfect scores → 100% overall health ✓

3. **Only Dashboard** (Delivery, Predictability, Sustainability available):
   - Missing 55% (Quality + Efficiency + Financial) redistributed
   - Delivery: 25% + (25/55 × 55%) = 45.5%
   - Predictability: 20% + (20/55 × 55%) = 36.4%
   - Sustainability: 10% + (10/55 × 55%) = 18.2%
   - Total: 100% ✓
   - Perfect scores → 100% overall health ✓

**Key principle**: A project with perfect performance across all available metrics deserves 100% health, regardless of which dimensions have data.

## Detailed Signal Specifications

### 1. Delivery Performance (25%)

#### 1a. Completion Progress (30 points)

**Source**: Dashboard completion percentage  
**Calculation**: Linear mapping `(completion_% / 100) × 30`

```python
# Examples:
0% complete    → 0 points
25% complete   → 7.5 points
50% complete   → 15 points
75% complete   → 22.5 points
100% complete  → 30 points
```

#### 1b. Velocity Trend (35 points)

**Source**: Dashboard velocity analysis (comparing recent vs older half)  
**Calculation**: Categorical scoring based on trend direction

```python
# Scoring:
if trend == "improving" or recent_change > 10%:
    score = 35  # Full points
elif trend == "stable" or abs(recent_change) <= 10%:
    score = 25  # 71% of max
else:  # declining
    score = 10  # 29% of max (credit for still delivering)
```

**Rationale**: Improving velocity indicates team learning and process optimization. Even declining teams get credit for continued delivery.

#### 1c. Throughput Rate (35 points)

**Source**: Flow velocity (items/week) or Dashboard velocity  
**Calculation**: Sigmoid normalization `1 / (1 + e^(-(velocity-midpoint)/scale))`

```python
# Sigmoid parameters:
# - Midpoint: 5 items/week (50% score)
# - Scale: 2 (controls curve steepness)

Examples:
1 item/week    → 6 points (17%)
3 items/week   → 15 points (43%)
5 items/week   → 18 points (50%)
7 items/week   → 25 points (71%)
10+ items/week → 32 points (91%+)
```

**Rationale**: Sigmoid provides smooth scaling. Low throughput signals capacity issues, high throughput signals strong delivery capability.

### 2. Predictability (20%)

#### 2a. Velocity Consistency (50 points)

**Source**: Dashboard CV (Coefficient of Variation)  
**Calculation**: Sigmoid with floor `(1/(1+e^((CV-70)/20))) × 47 + 3`

```python
# Sigmoid + 3-point floor ensures high-CV teams still get credit
Examples:
0% CV (perfect)   → 50 points (100%)
25% CV (good)     → 43 points (86%)
70% CV (moderate) → 26.5 points (53%)
100% CV (high)    → 11 points (22%)
150% CV (extreme) → 3.1 points (6% - floor prevents zero)
```

**Rationale**: 3-point floor critical for real-world projects. High-CV teams can still deliver value (should get some credit vs zero in aggressive formulas).

#### 2b. Schedule Adherence (30 points)

**Source**: Dashboard schedule variance (forecast_days - deadline_days)  
**Calculation**: Tanh normalization `(tanh(buffer/20) + 1) / 2 × 30`

```python
# Buffer = -schedule_variance (positive = ahead, negative = behind)
Examples:
+40 days ahead  → 30 points (100%)
+20 days ahead  → 28 points (93%)
On time (0)     → 15 points (50%)
-20 days behind → 2 points (7%)
-40 days behind → 0 points (0%)
```

**Rationale**: Tanh provides symmetric curve. Being ahead is good, being behind penalizes proportionally.

**Reference Date**: Both app and report use the **last statistics date** (most recent Monday data point) as the reference for calculating `days_to_deadline`, not the current datetime. This ensures the health score remains stable between data updates and only changes when new weekly statistics arrive.

#### 2c. Forecast Confidence (20 points)

**Source**: Dashboard completion confidence (0-100%)  
**Calculation**: Linear `(confidence / 100) × 20`

```python
Examples:
100% confident → 20 points
75% confident  → 15 points
50% confident  → 10 points
25% confident  → 5 points
```

### 3. Quality (20%)

#### 3a. Bug Resolution Rate (30 points)

**Source**: Bug Analysis resolution rate (%)  
**Calculation**: Linear `(resolution_rate × 100 / 100) × 30`

```python
Examples:
100% resolved → 30 points
85% resolved  → 25.5 points
70% resolved  → 21 points (warning threshold)
50% resolved  → 15 points (critical threshold)
```

#### 3b. Change Failure Rate - CFR (25 points)

**Source**: DORA metrics CFR (%)  
**Calculation**: Inverted linear `max(0, 25 × (1 - min(cfr/30, 1)))`

```python
# Inverted: lower CFR = better
Examples:
0% CFR    → 25 points (Elite)
5% CFR    → 21 points
15% CFR   → 12.5 points (warning)
30%+ CFR  → 0 points (critical)
```

#### 3c. Mean Time To Recovery - MTTR (20 points)

**Source**: DORA metrics MTTR (hours)  
**Calculation**: Logarithmic `20 × (1 - log10(mttr/1) / log10(168))`

```python
# Logarithmic scaling: severity increases non-linearly
Examples:
< 1 hour    → 20 points (Elite)
4 hours     → 15 points
24 hours    → 10 points (Medium)
72 hours    → 5 points
168+ hours  → 0 points (Low)
```

**Rationale**: Log scale because 1→24hr jump more critical than 24→72hr. Aligns with DORA performance tiers.

#### 3d. Bug Density/Age (25 points)

**Source**: Bug Analysis capacity consumed + avg age  
**Calculation**: Combined density (15pts) + age (10pts)

```python
# Density sub-signal (capacity consumed by bugs):
0% capacity    → 15 points
20% capacity   → 7.5 points
40%+ capacity  → 0 points

# Age sub-signal (average bug resolution time):
< 3 days   → 10 points
7 days     → 7 points
30+ days   → 0 points

Total = density_score + age_score (max 25)
```

### 4. Efficiency (15%)

#### 4a. Flow Efficiency (40 points)

**Source**: Flow metrics efficiency (%)  
**Calculation**: Linear capped `min(40, (efficiency_% / 50) × 40)`

```python
# Target: 25-40% is healthy (Lean manufacturing research)
Examples:
50%+ efficiency → 40 points (exceptional)
35% efficiency  → 28 points (healthy)
25% efficiency  → 20 points (acceptable)
10% efficiency  → 8 points (poor)
```

**Rationale**: 25-40% efficiency is industry standard for knowledge work. Higher is exceptional but rare.

#### 4b. Flow Time (35 points)

**Source**: Flow metrics median flow time (days)  
**Calculation**: Inverted sigmoid `1/(1+e^((flow_time-7)/5)) × 35`

```python
# Sigmoid inverted: lower flow time = better
Examples:
3 days flow time   → 28 points
7 days flow time   → 17.5 points (midpoint)
14 days flow time  → 7 points
21+ days flow time → 0 points
```

#### 4c. Lead Time for Changes (25 points)

**Source**: DORA metrics lead time (days)  
**Calculation**: Similar inverted sigmoid

```python
# Target based on DORA tiers:
< 1 day (Elite)    → 25 points
7 days (High)      → 15 points
30 days (Medium)   → 5 points
90+ days (Low)     → 0 points
```

### 5. Sustainability (10%)

#### 5a. Scope Stability (40 points) - **CONTEXT-AWARE**

**Source**: Scope metrics change rate (%)  
**Calculation**: Logarithmic penalty with **context multiplier**

**Note**: For health scoring, scope_change_rate is calculated as created items divided by (remaining + completed) within the selected time window. This differs from the baseline-at-window-start formula used in scope tracking views.

```python
# Context factor based on project maturity:
if completion < 25%:
    context_factor = 0.2  # Inception: 80% penalty reduction
elif completion < 50%:
    context_factor = 0.3  # Early: 70% penalty reduction
elif completion < 75%:
    context_factor = 0.6  # Mid: 40% penalty reduction
else:
    context_factor = 1.0  # Late: full penalties

# Penalty calculation:
if scope_change_rate <= 100%:
    penalty = (scope_change_rate / 100) × 12 × context_factor
else:
    penalty = (12 + log10(scope_change_rate/100) × 28) × context_factor

scope_score = max(0, 40 - penalty)
```

**Examples with 200% scope change**:

| Stage     | Completion | Context Factor | Penalty | Score   |
| --------- | ---------- | -------------- | ------- | ------- |
| Inception | 20%        | 0.2            | 3.8     | 36.2/40 |
| Early     | 35%        | 0.3            | 5.7     | 34.3/40 |
| Mid       | 60%        | 0.6            | 11.4    | 28.6/40 |
| Late      | 85%        | 1.0            | 19.0    | 21.0/40 |

**Rationale**: Early-stage projects naturally have high scope volatility (requirements discovery). Penalizing heavily for this creates false negatives. As projects mature, scope should stabilize.

#### 5b. WIP Management (35 points)

**Source**: Flow metrics WIP (count) vs velocity  
**Calculation**: Bell curve around ideal WIP

```python
# Ideal WIP = 1.5 × velocity (Little's Law with buffer)
wip_ratio = actual_wip / ideal_wip

# Scoring:
if 0.8 <= wip_ratio <= 1.2:  # Within 20% of ideal
    score = 35  # Perfect
elif wip_ratio < 0.8:  # Underutilized
    score = 35 × (wip_ratio / 0.8)
else:  # Overloaded (wip_ratio > 1.2)
    score = max(0, 35 × (1 - (wip_ratio - 1.2) / 1.3))
```

**Examples**:

| Velocity | Ideal WIP | Actual WIP | Ratio | Score                 |
| -------- | --------- | ---------- | ----- | --------------------- |
| 5/week   | 7.5       | 8          | 1.07  | 35/35 ✓               |
| 5/week   | 7.5       | 5          | 0.67  | 29/35 (underutilized) |
| 5/week   | 7.5       | 15         | 2.0   | 11/35 (overloaded)    |

**Rationale**: Too little WIP = idle capacity. Too much WIP = context switching, delays.

#### 5c. Flow Distribution Balance (25 points)

**Source**: Flow metrics work distribution by type  
**Calculation**: Deviation from ideal mix

```python
# Ideal distribution (Lean/Agile best practices):
# - Features: 50-70% (value delivery)
# - Defects: 10-30% (quality maintenance)
# - Tech Debt: 10-20% (sustainability)

feature_score = 10 × (1 - abs(feature_% - 60) / 60)    # 10pts
defect_score = 8 × (1 - abs(defect_% - 20) / 50)       # 8pts
tech_debt_score = 7 × (1 - abs(tech_debt_% - 15) / 50) # 7pts

total_score = max(0, feature_score + defect_score + tech_debt_score)
```

**Examples**:

| Mix           | Feature % | Defect % | Tech Debt % | Score                   |
| ------------- | --------- | -------- | ----------- | ----------------------- |
| Ideal         | 60%       | 20%      | 15%         | 25/25 ✓                 |
| Feature-heavy | 85%       | 10%      | 5%          | 15/25 (neglecting debt) |
| Firefighting  | 30%       | 60%      | 10%         | 8/25 (quality crisis)   |

### 6. Financial Health (10%)

#### 6a. Budget Adherence (40 points)

**Source**: Budget metrics burn rate variance (%)  
**Calculation**: Tiered penalties around ±10% target

```python
abs_variance = abs(burn_rate_variance_%)

if abs_variance < 10%:
    score = 40 - (abs_variance / 10) × 8  # 32-40 pts
elif abs_variance < 50%:
    score = 32 × (1 - (abs_variance - 10) / 40)  # 0-32 pts
else:
    score = 0

# Examples:
±5% variance  → 36 points
±10% variance → 32 points
±25% variance → 16 points
±50% variance → 0 points
```

#### 6b. Runway Adequacy (35 points)

**Source**: Budget metrics runway vs baseline (%)  
**Calculation**: Linear adjustment from baseline

```python
if runway_vs_baseline > 0:  # Ahead of plan
    score = min(35, 20 + (runway_vs_baseline / 10) × 15)
else:  # Behind plan
    score = max(0, 20 + (runway_vs_baseline / 25) × 20)

# Examples:
+20% ahead  → 35 points
+10% ahead  → 35 points
On track    → 20 points
-10% behind → 12 points
-25% behind → 0 points
```

#### 6c. Burn Rate Health (25 points)

**Source**: Budget metrics utilization vs pace (%)  
**Calculation**: Similar to budget adherence

```python
abs_util_variance = abs(utilization_vs_pace_%)

if abs_util_variance < 10%:
    score = 25 - (abs_util_variance / 10) × 5  # 20-25 pts
elif abs_util_variance < 50%:
    score = 20 × (1 - (abs_util_variance - 10) / 40)  # 0-20 pts
else:
    score = 0
```

## Health Status Thresholds

| Score Range | Status          | Color  | Interpretation                                   |
| ----------- | --------------- | ------ | ------------------------------------------------ |
| 70-100      | **GOOD** 🟢     | Green  | Project healthy, on track                        |
| 50-69       | **CAUTION** 🟡  | Yellow | Moderate risks, watch closely                    |
| 30-49       | **AT RISK** 🟠  | Orange | Significant issues, action needed                |
| 0-29        | **CRITICAL** 🔴 | Red    | Severe problems, immediate intervention required |

## Example Calculation

### Scenario: Early-Stage Project

```yaml
Dashboard:
  completion_percentage: 35%
  velocity_cv: 45%
  trend_direction: improving
  scope_change_rate: 80%
  schedule_variance: +5 days (ahead)

Extended Metrics:
  DORA: Available (CFR: 8%, MTTR: 12h)
  Flow: Available (Efficiency: 30%, WIP: optimal)
  Bug: Available (Resolution: 85%)
  Budget: Available (On track)
```

### Calculation with Full Metrics

```
Delivery Performance (25%):
  - Progress: 10.5/30 pts (35% complete)
  - Trend: 35/35 pts (improving)
  - Throughput: 22/35 pts (healthy velocity)
  → Dimension: 67.5/100 pts × 25% = 16.9% contribution

Predictability (20%):
  - Consistency: 38/50 pts (45% CV - good)
  - Schedule: 22/30 pts (ahead of schedule)
  - Confidence: 15/20 pts (75% confidence)
  → Dimension: 75.0/100 pts × 20% = 15.0% contribution

Quality (20%):
  - Bug Resolution: 25.5/30 pts (85%)
  - CFR: 18/25 pts (8% - good)
  - MTTR: 15/20 pts (12h - strong)
  - Density/Age: 18/25 pts (healthy)
  → Dimension: 76.5/100 pts × 20% = 15.3% contribution

Efficiency (15%):
  - Flow Efficiency: 24/40 pts (30%)
  - Flow Time: 20/35 pts (optimal)
  → Dimension: 62.9/100 pts × 15% = 9.4% contribution

Sustainability (10%):
  - Scope: 35/40 pts (80% change with context-aware penalty)
  - WIP: 35/35 pts (optimal)
  - Distribution: 22/25 pts (balanced)
  → Dimension: 92.0/100 pts × 10% = 9.2% contribution

Financial (10%):
  - Budget Adherence: 38/40 pts (on track)
  - Runway: 25/35 pts (adequate)
  - Burn Rate: 23/25 pts (healthy)
  → Dimension: 86.0/100 pts × 10% = 8.6% contribution

Total: 16.9 + 15.0 + 15.3 + 9.4 + 9.2 + 8.6 = 74.4 → 74/100
Status: GOOD 🟢
```

## Implementation Status

| Component              | Status         | Notes                                                  |
| ---------------------- | -------------- | ------------------------------------------------------ |
| **Core Calculator**    | ✅ Implemented | `data/project_health_calculator.py`                    |
| **UI Integration**     | ✅ Implemented | `ui/dashboard.py`                                      |
| **Adaptive Mode**      | ✅ Implemented | Automatic adjustment when extended metrics unavailable |
| **Dynamic Weighting**  | ✅ Implemented | Weights redistribute across available dimensions       |
| **Context Awareness**  | ✅ Implemented | Project stage adjusts scope penalties                  |
| **DORA Integration**   | ✅ Implemented | Fetched in `callbacks/visualization.py`                |
| **Flow Integration**   | ✅ Implemented | Calculated from filtered df in callback                |
| **Bug Integration**    | ✅ Implemented | Fetched from bug_processing cache                      |
| **Budget Integration** | ✅ Implemented | Already available, passed to health calculator         |

## Usage

### Current Behavior (Automatic Multi-Dimensional)

```python
# callbacks/visualization.py::update_dashboard()
# Step 1: Calculate extended metrics once in callback (~50-80ms)
extended_metrics = {}

# DORA metrics from cache
dora_data = load_dora_metrics_from_cache(n_weeks=data_points_count)
if dora_data:
    extended_metrics["dora"] = extract_latest_dora_metrics(dora_data)

# Flow metrics from filtered df
flow_velocity = calculate_flow_velocity(df, profile_id, query_id)
flow_efficiency = calculate_flow_efficiency(df, profile_id, query_id)
# ... other flow metrics
extended_metrics["flow"] = {"velocity": flow_velocity, "efficiency": flow_efficiency, ...}

# Bug metrics from cache
bug_data = calculate_bug_metrics_summary(profile_id, query_id)
extended_metrics["bug"] = extract_bug_metrics(bug_data)

# Step 2: Pass via additional_context
create_comprehensive_dashboard(..., additional_context={"extended_metrics": extended_metrics})

# dashboard.py::create_executive_summary_section()
# Step 3: Extract and use (no fetching, just math ~1ms)
extended_metrics = settings.get("extended_metrics", {})
dora_metrics = extended_metrics.get("dora")
flow_metrics = extended_metrics.get("flow")
bug_metrics = extended_metrics.get("bug")

health_score = _calculate_project_health_score(
    health_metrics,
    dora_metrics=dora_metrics,      # ✓ Auto-populated when available
    flow_metrics=flow_metrics,      # ✓ Auto-populated when available
    bug_metrics=bug_metrics,        # ✓ Auto-populated when available
    budget_metrics=budget_metrics,  # ✓ Auto-populated when available
    scope_metrics=scope_metrics,
)
# Result:
# - If all metrics available → comprehensive multi-dimensional calculation
# - If only dashboard → focuses on core dimensions with weight redistribution
# - Graceful degradation for any combination of available metrics
```

## Data Requirements

1. **Backward Compatible**: Automatically adapts to dashboard-only mode when extended metrics unavailable
2. **No Breaking Changes**: Works with any combination of available metrics
3. **Gradual Enhancement**: As data sources connect, health becomes more accurate
4. **Logging**: Look for `[HEALTH]` prefix in logs to see formula activity and available metrics

## References

- **DORA Metrics**: https://dora.dev/devops-capabilities/
- **Flow Metrics**: "Actionable Agile Metrics" by Daniel Vacanti
- **Context-Aware Penalties**: Research on agile scope volatility patterns
- **Sigmoid/Tanh Normalization**: Statistical methods for non-linear scoring
- **Related Documentation**: `docs/dashboard_metrics.md`, `docs/metrics_index.md`, `docs/dora_metrics.md`, `docs/flow_metrics.md`

---

**Last Updated**: January 2026  
**Status**: Fully Implemented and Operational
