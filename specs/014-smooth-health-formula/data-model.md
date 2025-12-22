# Data Model: Smooth Statistical Health Score Formula

**Phase**: 1 - Design & Contracts  
**Date**: 2024-12-22  
**Status**: Complete

## Entities

### HealthScore

**Description**: Composite metric (0-100 integer) representing overall project health

**Attributes**:
```python
{
    "value": int,                    # 0-100 final score
    "components": {
        "progress": float,           # 0-30 points
        "schedule": float,           # 0-30 points
        "stability": float,          # 0-20 points
        "trend": float               # 0-20 points
    }
}
```

**Relationships**:
- Computed from `DashboardMetrics` (completion %, days to deadline, velocity trend)
- Computed from `StatisticsDataFrame` (for stability and trend components)

**Validation Rules**:
- `value` must be integer in range [0, 100]
- Sum of components must equal `value` (within rounding tolerance ±1)
- Each component must be within its defined range

---

### StatisticsDataFrame

**Description**: Pandas DataFrame containing weekly completion data

**Schema**:
```python
DataFrame columns:
- date: datetime64[ns]           # Week start date (Monday)
- completed_items: int64         # Items completed this week
- completed_points: float64      # Story points completed this week
- created_items: int64           # Items created this week (not used in health)
- created_points: float64        # Points added this week (not used in health)
```

**Constraints**:
- `date` must be datetime type (not string)
- Sorted by date ascending
- No duplicate dates (one row per week)
- Week boundaries: Monday-Sunday (ISO week)

**Operations**:
- Filter incomplete current week: `df.iloc[:-1]` if week not complete
- Tail for recent data: `df.tail(n)` for last n weeks
- Midpoint split: `df.iloc[:mid]` and `df.iloc[mid:]` for trend comparison

---

### ProgressComponent

**Description**: Health component based on project completion percentage

**Calculation**:
```python
progress_score = (completion_percentage / 100) * 30
```

**Inputs**:
- `completion_percentage`: float, 0-100 (from `DashboardMetrics`)

**Output**:
- `progress_score`: float, 0-30 points

**Properties**:
- Linear scaling (no thresholds)
- Continuous (every % completion yields unique score)
- Deterministic (same input always produces same output)

---

### ScheduleComponent

**Description**: Health component based on schedule buffer (ahead/behind schedule)

**Calculation**:
```python
buffer_days = days_to_deadline - days_to_completion
normalized = buffer_days / 20  # Scale factor
schedule_score = (math.tanh(normalized) + 1) * 15
```

**Inputs**:
- `days_to_deadline`: int (from `DashboardMetrics`, can be None)
- `days_to_completion`: int (from `DashboardMetrics`, can be None)

**Output**:
- `schedule_score`: float, 0-30 points (or 15 if deadline missing)

**Properties**:
- Smooth sigmoid using hyperbolic tangent
- Symmetric around 0 days buffer (on time = 15 points)
- Asymptotic at extremes (never reaches exactly 0 or 30)
- Range: [0.01, 29.99] for buffer in [-60, +60] days

**Edge Cases**:
- Both inputs None → return 15 (neutral)
- One input None → return 15 (neutral)
- Buffer > +60 days → asymptotically approaches 30
- Buffer < -60 days → asymptotically approaches 0

---

### StabilityComponent

**Description**: Health component based on velocity consistency (coefficient of variation)

**Calculation**:
```python
# From last N weeks (N = min(10, len(filtered_df)))
items = [week.completed_items for week in recent_weeks]
mean = sum(items) / len(items)
variance = sum((x - mean)^2 for x in items) / len(items)
std_dev = sqrt(variance)
CV = std_dev / mean  # Coefficient of variation

stability_score = 20 * max(0, 1 - (CV / 1.5))
```

**Inputs**:
- `filtered_df`: StatisticsDataFrame with incomplete week removed
- `recent_weeks`: Last 10 weeks (or all available if <10)

**Output**:
- `stability_score`: float, 0-20 points (or 10 if insufficient data)

**Properties**:
- Linear decay from 20 (CV=0) to 0 (CV≥1.5)
- Uses coefficient of variation (CV = σ/μ) for scale-invariant consistency measure
- Requires minimum 2 weeks of data

**Edge Cases**:
- Mean velocity = 0 → return 10 (neutral)
- < 2 weeks data → return 10 (neutral)
- CV > 1.5 → clamp to 0
- All weeks identical (CV=0) → return 20

---

### TrendComponent

**Description**: Health component based on velocity change (recent vs older)

**Calculation**:
```python
# Split at midpoint
mid = len(filtered_df) // 2
older_half = filtered_df.iloc[:mid]
recent_half = filtered_df.iloc[mid:]

older_velocity = calculate_velocity_from_dataframe(older_half, "completed_items")
recent_velocity = calculate_velocity_from_dataframe(recent_half, "completed_items")

velocity_change_pct = ((recent_velocity - older_velocity) / older_velocity) * 100

trend_score = 10 + (velocity_change_pct / 50) * 10
trend_score = max(0, min(20, trend_score))  # Clamp to [0, 20]
```

**Inputs**:
- `filtered_df`: StatisticsDataFrame with incomplete week removed
- Requires minimum 4 weeks of data (2 vs 2 comparison)

**Output**:
- `trend_score`: float, 0-20 points (or 10 if insufficient data)

**Properties**:
- Linear scaling centered at 10 (0% change = neutral)
- Maps [-50%, +50%] velocity change to [0, 20] points
- Clamped at boundaries (changes > ±50% treated as ±50%)

**Edge Cases**:
- < 4 weeks data → return 10 (neutral)
- Older velocity = 0 → return 10 (neutral)
- Change < -50% → clamp to 0
- Change > +50% → clamp to 20

---

### WeekCompleteness

**Description**: State indicating whether a week's data is complete (all 7 days elapsed)

**States**:
- `COMPLETE`: Week has ended (date ≤ last Sunday 23:59:59)
- `INCOMPLETE`: Week is current week (date > last Sunday 23:59:59)

**Detection Logic**:
```python
def is_week_complete(last_date: datetime, today: datetime) -> bool:
    """Check if week containing last_date is complete."""
    days_apart = (today.date() - last_date.date()).days
    
    # Different weeks (>6 days apart) → week is complete
    if days_apart > 6:
        return True
    
    # Same week → check if Sunday end-of-day reached
    is_sunday = today.weekday() == 6  # 0=Mon, 6=Sun
    is_end_of_day = today.hour >= 23
    
    return is_sunday and is_end_of_day
```

**Usage**:
- Applied before stability and trend calculations
- If incomplete: remove last row from DataFrame (`df.iloc[:-1]`)
- If complete: use all data (no filtering)

---

## Data Flow

```
Input: DashboardMetrics + StatisticsDataFrame
  │
  ├─► Filter incomplete current week (if needed)
  │    └─► filtered_df
  │
  ├─► Calculate Progress Component
  │    ├─ Input: completion_percentage
  │    └─ Output: progress_score (0-30)
  │
  ├─► Calculate Schedule Component
  │    ├─ Input: days_to_deadline, days_to_completion
  │    └─ Output: schedule_score (0-30)
  │
  ├─► Calculate Stability Component
  │    ├─ Input: filtered_df.tail(10)
  │    ├─ Compute: CV from completed_items
  │    └─ Output: stability_score (0-20)
  │
  ├─► Calculate Trend Component
  │    ├─ Input: filtered_df (split at midpoint)
  │    ├─ Compute: velocity_change_pct
  │    └─ Output: trend_score (0-20)
  │
  └─► Sum Components & Round
       └─ Output: HealthScore (0-100)
```

---

## State Transitions

### Health Score Lifecycle

```
1. Dashboard Load
   └─► Request metrics from calculate_dashboard_metrics()
       └─► DashboardMetrics available

2. Health Calculation Triggered
   └─► _calculate_health_score(metrics, statistics_df)
       ├─► Check week completeness
       ├─► Filter if needed
       ├─► Calculate 4 components in parallel
       └─► Sum and round

3. Display Update
   └─► HealthScore displayed in UI
       ├─► Color/label based on value
       └─► Progress bar shows completion %
```

No persistent state - health is calculated on-demand from current data.

---

## Validation Rules

### Component Sum Validation

```python
def validate_health_components(components: dict, final_score: int) -> bool:
    """Verify component sum matches final score (within rounding tolerance)."""
    component_sum = sum(components.values())
    return abs(component_sum - final_score) <= 1  # Allow ±1 for rounding
```

### Range Validation

```python
def validate_component_ranges(components: dict) -> bool:
    """Verify each component is within its defined range."""
    checks = [
        0 <= components["progress"] <= 30,
        0 <= components["schedule"] <= 30,
        0 <= components["stability"] <= 20,
        0 <= components["trend"] <= 20
    ]
    return all(checks)
```

### Data Quality Checks

```python
def validate_statistics_df(df: pd.DataFrame) -> bool:
    """Verify DataFrame has required structure and valid data."""
    required_columns = ["date", "completed_items"]
    has_columns = all(col in df.columns for col in required_columns)
    
    if not has_columns:
        return False
    
    # Check date column is datetime type
    is_datetime = pd.api.types.is_datetime64_any_dtype(df["date"])
    
    # Check no negative values in completed_items
    no_negatives = (df["completed_items"] >= 0).all()
    
    return is_datetime and no_negatives
```

---

## Error Handling

### Graceful Degradation

When component calculation fails, return neutral score for that component:

| Component | Error Condition                   | Fallback Value      |
| --------- | --------------------------------- | ------------------- |
| Progress  | completion_percentage missing     | 0 points            |
| Schedule  | deadline missing or invalid       | 15 points (neutral) |
| Stability | <2 weeks data or mean=0           | 10 points (neutral) |
| Trend     | <4 weeks data or older_velocity=0 | 10 points (neutral) |

**Total Minimum Score**: 0 + 15 + 10 + 10 = 35 points (when only progress is available)

### Exception Handling

```python
try:
    health_score = _calculate_health_score(metrics, statistics_df)
except Exception as e:
    logger.error(f"Health calculation failed: {e}")
    health_score = 50  # Fallback to neutral score
```

No exceptions should propagate to UI - always return valid integer in [0, 100].

---

## Performance Considerations

### Time Complexity

- Week filtering: O(1) - single DataFrame slice
- Progress: O(1) - simple division
- Schedule: O(1) - tanh calculation
- Stability: O(n) where n = min(10, weeks) - mean, variance calculations
- Trend: O(n) where n = weeks - two velocity calculations

**Total**: O(n) where n ≤ 52 weeks → ~10-20ms typical

### Space Complexity

- No additional DataFrame copies (use views where possible)
- Component scores: 4 floats → 32 bytes
- Temporary lists for stability: max 10 integers → 80 bytes

**Total**: O(1) additional space (excluding input DataFrame)

---

## Migration Notes

### Backward Compatibility

**Function Signature**: Unchanged
```python
def _calculate_health_score(metrics: Dict[str, Any]) -> int:
```

**New Signature** (for future enhancement):
```python
def _calculate_health_score(
    metrics: Dict[str, Any],
    statistics_df: pd.DataFrame = None
) -> int:
```

Currently, statistics_df must be obtained from caller context. Future refactor can pass explicitly.

### Breaking Changes

None - output is still integer 0-100. Only calculation method changes (internal implementation).

### Data Migration

Not applicable - no persisted health scores. Calculated on-demand.

---

## Summary

✅ **Data model complete** - All entities, relationships, and validation rules defined.

**Key Entities**:
1. HealthScore (composite result)
2. 4 Components (progress, schedule, stability, trend)
3. StatisticsDataFrame (input data structure)
4. WeekCompleteness (filtering logic)

**Ready for**: Contract specification (Phase 1 continued)
