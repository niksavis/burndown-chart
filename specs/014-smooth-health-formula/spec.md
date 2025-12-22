# Feature Specification: Smooth Statistical Health Score Formula

**Feature Branch**: `014-smooth-health-formula`  
**Created**: 2024-12-22  
**Status**: Draft  
**Input**: Fix project health score formula to provide smooth continuous 0-100% scoring that works accurately across all project sizes (4-52+ weeks) by replacing threshold-based penalties with statistical functions and excluding incomplete current week data

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate Health Score Without Weekly Sawtooth Pattern (Priority: P1)

As a project manager checking health on Wednesday, I want the health score to reflect actual project status rather than being artificially deflated by an incomplete current week, so I can make accurate decisions any day of the week.

**Why this priority**: Current bug causes health scores to drop 15-30 points mid-week due to incomplete week data, creating false alarms and eroding trust in the metric. This is the most critical issue causing user-reported 25-50% health scores.

**Independent Test**: View project health on different days of the week (Monday through Sunday). Health score should remain stable (±2%) when no actual work changes occur, without artificial drops on Monday-Friday.

**Acceptance Scenarios**:

1. **Given** a 12-week project with stable velocity checked on Sunday evening, **When** I check the same project on Tuesday morning with no new completions, **Then** health score changes by less than 2 points (not 15-30 points)
2. **Given** a project with 10 items completed per week for 8 weeks, **When** current week has 3 days elapsed with 4 items completed (on track), **Then** health score does not penalize for "decreasing velocity"
3. **Given** a 5-week project (4 complete weeks after filtering), **When** I view the dashboard, **Then** health score is calculated using only the 4 complete weeks for velocity metrics

---

### User Story 2 - Smooth Gradual Health Changes (Priority: P1)

As a project manager tracking improvements, I want health score changes to be gradual and proportional to actual changes, so small improvements or declines are visible rather than hidden by threshold jumps.

**Why this priority**: Current step-function penalties (0 → -12 → -25 points) make the score insensitive to gradual changes and create sudden drops that don't reflect reality.

**Independent Test**: Make incremental changes to project status (add 1 day to schedule buffer, complete 1 more item, etc.). Each change should produce visible 1-3% health score adjustments, not zero change followed by sudden 10-15% drops.

**Acceptance Scenarios**:

1. **Given** a project 15 days behind schedule, **When** schedule buffer improves to 14 days behind, **Then** health score increases by 1-2% (not jumps from 0 penalty to -12 penalty)
2. **Given** velocity CV increases from 0.25 to 0.30, **When** health is recalculated, **Then** score decreases by 2-3% (not stays the same)
3. **Given** completion increases from 50% to 55%, **When** health is recalculated, **Then** score increases by approximately 1.5% (30 points * 0.05 = 1.5 points)

---

### User Story 3 - Full 0-100% Health Score Range (Priority: P2)

As a stakeholder reviewing multiple projects, I want to see health scores that use the full 0-100% range, so I can differentiate between excellent (90-100%), good (70-89%), fair (40-69%), and critical (0-39%) projects.

**Why this priority**: Users report health scores clustered at 25-50% even for healthy projects, making the metric less useful for comparative analysis.

**Independent Test**: Create test scenarios representing excellent, good, fair, and critical project states. Verify health scores span from <10% (critical: 10% complete, 60 days behind, erratic velocity) to >90% (excellent: 95% complete, 30 days ahead, stable velocity).

**Acceptance Scenarios**:

1. **Given** a project at 95% completion, 30 days ahead of schedule, stable velocity (CV=0.15), improving trend (+15%), **When** health is calculated, **Then** score is ≥90%
2. **Given** a project at 10% completion, 60 days behind schedule, erratic velocity (CV=1.4), declining trend (-40%), **When** health is calculated, **Then** score is ≤10%
3. **Given** a project at 60% completion, on schedule, normal velocity (CV=0.35), stable trend (±5%), **When** health is calculated, **Then** score is 65-75%

---

### User Story 4 - Health Score Works for All Project Sizes (Priority: P2)

As an organization using this tool for both 4-week sprints and 52-week programs, I want the health score formula to work accurately regardless of project duration, so all teams get consistent metrics.

**Why this priority**: Small projects (<6 weeks) cannot calculate velocity trends with current threshold, leaving 20% of health score at arbitrary neutral value.

**Independent Test**: Test with projects of 4 weeks, 12 weeks, and 52 weeks. All should produce health scores using all four components (progress, schedule, stability, trend) with appropriate sensitivity for the dataset size.

**Acceptance Scenarios**:

1. **Given** a 4-week project (4 complete weeks after current week filtering), **When** health is calculated, **Then** all four components (progress, schedule, stability, trend) contribute calculated values (not defaults)
2. **Given** a 52-week project, **When** velocity varies by ±2 items/week (typical noise), **Then** stability score is 12-16 points (not 0 or 20)
3. **Given** a 12-week project with recent velocity 10% higher than older velocity, **When** health is calculated, **Then** trend component shows +2 points above neutral

---

### Edge Cases

- **What happens when velocity is zero (no completions)?** Stability component returns neutral 10 points, preventing division by zero
- **What happens with only 2 weeks of data?** Progress and schedule work fully; stability uses 2 weeks (minimal but valid CV calculation); trend uses neutral 10 points
- **What happens if deadline is missing?** Schedule component returns neutral 15 points (half of 30)
- **What happens on Sunday at 23:58?** Current week is treated as incomplete; only included after 23:59:59
- **What happens if today is Monday 00:01?** Previous week (now complete as of Sunday 23:59:59) is included; current week is incomplete
- **What happens with extreme schedule variance (±100 days)?** Tanh function asymptotically approaches 0 or 30 points, preventing scores outside 0-100 range
- **What happens with extreme velocity CV (>2.0)?** Stability score clamps to 0 points minimum
- **What happens with extreme velocity change (>100%)?** Trend score clamps to [0, 20] range

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate health score as continuous function producing any integer value from 0 to 100 (all 101 values possible)
- **FR-002**: System MUST exclude incomplete current week from velocity calculations when current day is not Sunday 23:59:59
- **FR-003**: System MUST use four weighted components: Progress (30%), Schedule (30%), Stability (20%), Trend (20%)
- **FR-004**: Progress component MUST scale linearly from 0-30 points based on completion percentage (0% = 0 points, 100% = 30 points)
- **FR-005**: Schedule component MUST use hyperbolic tangent (tanh) function to map schedule buffer days to 0-30 point range
- **FR-006**: Stability component MUST calculate velocity coefficient of variation (CV) from completed items per week
- **FR-007**: Stability component MUST map CV linearly from 20 points (CV=0, perfect consistency) to 0 points (CV≥1.5, chaotic)
- **FR-008**: Trend component MUST compare recent velocity to older velocity using half-split method
- **FR-009**: Trend component MUST map velocity change percentage linearly: -50% = 0 points, 0% = 10 points, +50% = 20 points
- **FR-010**: System MUST lower minimum data threshold for trend calculation from 6 weeks to 4 weeks to support small projects
- **FR-011**: System MUST use last 10 weeks (or all available if <10) for stability calculation
- **FR-012**: Incomplete week filtering MUST check if current date is in same ISO week as last data point AND not Sunday end-of-day
- **FR-013**: All component scores MUST be clamped to their defined ranges before summing (no component exceeds its weight)
- **FR-014**: Final health score MUST be rounded to nearest integer and clamped to [0, 100]

### Key Entities

- **Health Score**: Composite metric (0-100 integer) representing overall project health, calculated from four weighted components
- **Complete Week**: Week where all 7 days (Monday-Sunday) have elapsed; ends Sunday 23:59:59
- **Coefficient of Variation (CV)**: Statistical measure of velocity consistency; ratio of standard deviation to mean (σ/μ)
- **Schedule Buffer**: Difference between days to deadline and days to completion (positive = ahead, negative = behind)
- **Velocity Trend**: Percentage change in velocity between recent period and older period (split at dataset midpoint)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Health score changes by less than 3% when checked on different days of the same week with no new work completed (eliminates 15-30 point sawtooth)
- **SC-002**: Incrementing schedule buffer by 1 day produces 0.5-2% health score change (smooth gradient, not step function)
- **SC-003**: Health scores for test scenarios span from ≤5% (critical projects) to ≥95% (excellent projects) using the full 0-100 range
- **SC-004**: 4-week projects (minimum viable dataset) calculate all four health components without using default neutral values for trend
- **SC-005**: Health score changes are proportional to metric changes: doubling velocity CV reduces stability score by ~50%
- **SC-006**: Two projects with identical metrics on different days of the week produce health scores within ±1% of each other

### Validation Tests *(for implementation)*

- **VT-001**: Sunday evening health = 75%, Tuesday morning (same data) health = 74-76% (not 60%)
- **VT-002**: Schedule buffer test: [-45, -30, -15, 0, +15, +30, +45] days maps to [0.3, 2.0, 7.8, 15.0, 22.2, 28.0, 29.7] points (smooth sigmoid)
- **VT-003**: CV test: [0, 0.3, 0.6, 0.9, 1.2, 1.5] maps to [20, 16, 12, 8, 4, 0] points (linear decay)
- **VT-004**: Velocity change test: [-50%, -25%, 0%, +25%, +50%] maps to [0, 5, 10, 15, 20] points (linear scaling)
- **VT-005**: Extreme case: 100% complete, +60 days buffer, CV=0.05, +60% velocity → health ≥98%
- **VT-006**: Extreme case: 5% complete, -60 days buffer, CV=1.8, -60% velocity → health ≤5%

## Assumptions

- **A-001**: Project completion data is aggregated by ISO week (Monday-Sunday)
- **A-002**: Velocity calculations require minimum 2 data points; below this, stability defaults to neutral (10 points)
- **A-003**: Most real-world projects have velocity CV between 0.2-0.8; values above 1.5 indicate severe dysfunction
- **A-004**: Schedule buffers beyond ±60 days are rare; tanh function handles these asymptotically
- **A-005**: Velocity changes exceeding ±100% are outliers; trend score clamps at boundaries
- **A-006**: Current week is only "complete" at Sunday 23:59:59 or later (ISO week end)
- **A-007**: Users check dashboards throughout the week, not just on Sundays
- **A-008**: Small projects (4-12 weeks) need all components active for useful health scores
- **A-009**: Health score is comparative tool for trend monitoring, not absolute project assessment

## Dependencies

- **D-001**: Velocity calculation function `calculate_velocity_from_dataframe()` in `data/processing.py`
- **D-002**: Dashboard metrics calculation in `calculate_dashboard_metrics()` provides velocity trend, completion %, days to deadline/completion
- **D-003**: Statistics data filtered to complete weeks only for stability/trend calculations
- **D-004**: Math library functions: `math.tanh()`, `math.sqrt()`, `math.exp()`

## Out of Scope

- Changing velocity calculation method itself (already fixed to use actual week count, not date range)
- Modifying how statistics data is generated from JIRA (already uses ISO weeks Monday-Sunday)
- Adding new health components beyond the four specified (progress, schedule, stability, trend)
- Customizable health score weights (30/30/20/20 weights are fixed heuristics)
- Alerting or notifications based on health score thresholds
- Historical health score tracking (future enhancement)
- Health score explanations showing component breakdown (future enhancement)

## Technical Constraints

- Must work with existing pandas DataFrame statistics structure (date, completed_items, completed_points columns)
- Must integrate with existing `_calculate_health_score()` function signature in `ui/dashboard_cards.py`
- Must not break existing unit tests in `tests/unit/ui/test_dashboard_cards.py` (update assertions, not remove tests)
- Performance: Health calculation must complete in <50ms for datasets up to 52 weeks
- Must handle missing data gracefully (no exceptions for None values, zeros, or empty datasets)

## Risks & Mitigations

| Risk                                                                 | Impact | Likelihood | Mitigation                                                                |
| -------------------------------------------------------------------- | ------ | ---------- | ------------------------------------------------------------------------- |
| Tanh/exponential functions produce unexpected edge case values       | Medium | Low        | Comprehensive unit tests covering CV [0-2.0] and buffer [-60, +60] days   |
| Changed formula alters historical health scores (breaks comparisons) | Low    | High       | Document in release notes; this is intentional bug fix improving accuracy |
| Users expect old threshold-based scoring                             | Low    | Medium     | Update documentation/help text explaining continuous scoring              |
| Small projects (<4 weeks) still lack trend component                 | Medium | Low        | Accept limitation; document minimum 4 weeks for full health analysis      |
| Float rounding causes health score to flip between adjacent integers | Low    | Medium     | Round consistently using `int(round())` after all calculations            |

## Formula Specification

### Mathematical Definitions

**Health Score Calculation:**
```
HEALTH = Progress + Schedule + Stability + Trend
Range: [0, 100]
```

**Component 1: Progress (0-30 points)**
```
Progress = (completion_percentage / 100) * 30
```
- Linear scaling
- 0% complete → 0 points
- 100% complete → 30 points

**Component 2: Schedule Health (0-30 points)**
```
buffer_days = days_to_deadline - days_to_completion
normalized = buffer_days / 20
Schedule = (tanh(normalized) + 1) * 15
```
- Uses hyperbolic tangent for smooth sigmoid
- tanh range: [-1, +1] maps to [0, 30] points
- Scale factor 20 provides sensitivity: ±20 days = ±63% of range
- -45 days behind → 0.3 points (near zero)
- 0 days (on time) → 15.0 points (middle)
- +45 days ahead → 29.7 points (near maximum)

**Component 3: Velocity Stability (0-20 points)**
```
mean = sum(completed_items) / count
std_dev = sqrt(sum((x - mean)^2) / count)
CV = std_dev / mean

Stability = 20 * max(0, 1 - (CV / 1.5))
```
- Linear decay from 20 to 0
- CV = 0 (perfect) → 20 points
- CV = 0.75 (typical) → 10 points
- CV ≥ 1.5 (chaotic) → 0 points
- Uses last 10 weeks or all available data

**Component 4: Velocity Trend (0-20 points)**
```
velocity_change_pct = ((recent_velocity - older_velocity) / older_velocity) * 100

Trend = 10 + (velocity_change_pct / 50) * 10
Trend = clamp(Trend, 0, 20)
```
- Linear scaling centered at 10 (neutral)
- -50% decline → 0 points
- 0% (stable) → 10 points
- +50% growth → 20 points
- Requires minimum 4 weeks of complete data

**Incomplete Week Filtering:**
```
last_date = statistics[-1].date
today = current_datetime
days_elapsed = (today - last_date).days

if days_elapsed <= 6 AND NOT (today.weekday == 6 AND today.hour >= 23):
    exclude statistics[-1]  # Remove incomplete current week
```
- Checks if last data point is in current week
- Only includes current week if it's Sunday 23:59:59 or later
- Applies before stability and trend calculations

### Range Verification

**Minimum Health (Critical Project):**
- Progress: 0% → 0 points
- Schedule: -45 days → 0.3 points
- Stability: CV=1.5 → 0 points
- Trend: -50% → 0 points
- **Total: 0.3 ≈ 0%**

**Maximum Health (Excellent Project):**
- Progress: 100% → 30 points
- Schedule: +45 days → 29.7 points
- Stability: CV=0 → 20 points
- Trend: +50% → 20 points
- **Total: 99.7 ≈ 100%**

**Typical Healthy Project (75th percentile):**
- Progress: 70% → 21 points
- Schedule: +10 days → 19.2 points
- Stability: CV=0.3 → 16 points
- Trend: +10% → 12 points
- **Total: 68.2 ≈ 68%**

✅ **Formula achieves true 0-100% range with smooth transitions**

## Documentation Updates Required

- Update `docs/dashboard_metrics.md` Section 1 (Project Health Score) with new formula explanation
- Update `configuration/help_content.py` health score help text to describe continuous scoring
- Add formula specification to `docs/METRICS_EXPLANATION.md` 
- Update statistical limitations section noting this fix addresses the arbitrary weights concern
- Add "What changed in v2.1" release notes explaining health score formula improvement

- **SC-002**: Incrementing schedule buffer by 1 day produces 0.5-2% health score change (smooth gradient, not step function)
- **SC-003**: Health scores for test scenarios span from ≤5% (critical projects) to ≥95% (excellent projects) using the full 0-100 range
- **SC-004**: 4-week projects (minimum viable dataset) calculate all four health components without using default neutral values for trend
- **SC-005**: Health score changes are proportional to metric changes: doubling velocity CV reduces stability score by ~50%
- **SC-006**: Two projects with identical metrics on different days of the week produce health scores within ±1% of each other
