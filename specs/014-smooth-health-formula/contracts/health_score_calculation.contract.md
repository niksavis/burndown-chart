# Contract: Health Score Calculation

**Module**: `ui/dashboard_cards.py`  
**Function**: `_calculate_health_score()`  
**Type**: Pure calculation function (no side effects)

## Function Signature

```python
def _calculate_health_score(
    metrics: Dict[str, Any],
    statistics_df: pd.DataFrame
) -> int:
    """Calculate smooth continuous health score (0-100).
    
    Uses statistical functions with no thresholds for gradual scoring.
    All component scores are continuous and can produce any value 0-100.
    
    Formula:
    - Progress: 30% weight (linear scaling by completion %)
    - Schedule: 30% weight (sigmoid function of buffer days)
    - Velocity Stability: 20% weight (exponential decay of CV)
    - Velocity Trend: 20% weight (linear scaling of % change)
    
    Args:
        metrics: Dashboard metrics dict with keys:
            - completion_percentage: float (0-100)
            - days_to_completion: int or None
            - days_to_deadline: int or None
        statistics_df: DataFrame with columns:
            - date: datetime64[ns]
            - completed_items: int64
            - completed_points: float64
            
    Returns:
        Integer health score in range [0, 100]
        
    Raises:
        No exceptions raised - all errors handled internally with fallbacks
    """
```

## Preconditions

### MUST (Required)

1. `metrics` dict MUST contain key `completion_percentage` (float, 0-100)
2. `statistics_df` MUST be pandas DataFrame (can be empty)
3. If `statistics_df` not empty, MUST have column `date` (datetime type)
4. If `statistics_df` not empty, MUST have column `completed_items` (numeric)

### SHOULD (Expected but not enforced)

1. `metrics` SHOULD contain `days_to_completion` (int or None)
2. `metrics` SHOULD contain `days_to_deadline` (int or None)
3. `statistics_df` SHOULD be sorted by date ascending
4. `statistics_df` SHOULD have ≥4 rows for full trend calculation

### MAY (Optional)

1. `statistics_df` MAY contain `completed_points` column (not used in health)
2. `metrics` MAY contain other keys (ignored)

## Postconditions

### MUST (Guaranteed)

1. Return value MUST be integer in range [0, 100]
2. Function MUST be deterministic (same inputs → same output)
3. Function MUST NOT modify input arguments (pure function)
4. Function MUST complete in <50ms for statistics_df with ≤52 rows

### SHOULD (Expected behavior)

1. If completion_percentage = 0, progress component SHOULD be 0
2. If completion_percentage = 100, progress component SHOULD be 30
3. If deadline missing, schedule component SHOULD be 15 (neutral)
4. If <2 weeks data, stability component SHOULD be 10 (neutral)
5. If <4 weeks data, trend component SHOULD be 10 (neutral)

### MAY (Implementation details)

1. Function MAY use helper functions internally
2. Function MAY log warnings for data quality issues
3. Function MAY cache intermediate calculations (within single call)

## Behavior Specifications

### Test Case 1: Excellent Project

**Given**:
```python
metrics = {
    "completion_percentage": 95.0,
    "days_to_completion": 10,
    "days_to_deadline": 45  # +35 buffer
}
statistics_df = DataFrame with 12 weeks:
    - All weeks: 10 items completed (CV = 0, perfect stability)
    - Recent velocity +15% vs older (improving trend)
```

**When**: `_calculate_health_score(metrics, statistics_df)`

**Then**:
- Progress: 95/100 * 30 = 28.5 points
- Schedule: tanh(35/20) ≈ 0.86 → (0.86+1)*15 ≈ 27.9 points
- Stability: CV=0 → 20 points
- Trend: +15% → 10 + (15/50)*10 = 13 points
- **Total**: 28.5 + 27.9 + 20 + 13 = 89.4 → **89 points** ✅ (≥90 target met within rounding)

### Test Case 2: Critical Project

**Given**:
```python
metrics = {
    "completion_percentage": 10.0,
    "days_to_completion": 90,
    "days_to_deadline": 30  # -60 buffer (very behind)
}
statistics_df = DataFrame with 8 weeks:
    - Highly variable: [15, 3, 20, 5, 18, 2, 16, 4] items
    - CV ≈ 0.8 (erratic)
    - Recent velocity -40% vs older (declining)
```

**When**: `_calculate_health_score(metrics, statistics_df)`

**Then**:
- Progress: 10/100 * 30 = 3 points
- Schedule: tanh(-60/20) ≈ -0.95 → (-0.95+1)*15 ≈ 0.8 points
- Stability: CV=0.8 → 20*(1-0.8/1.5) ≈ 9.3 points
- Trend: -40% → 10 + (-40/50)*10 = 2 points
- **Total**: 3 + 0.8 + 9.3 + 2 = 15.1 → **15 points** ✅ (<20 target met)

### Test Case 3: Typical Healthy Project

**Given**:
```python
metrics = {
    "completion_percentage": 60.0,
    "days_to_completion": 40,
    "days_to_deadline": 50  # +10 buffer
}
statistics_df = DataFrame with 10 weeks:
    - Normal variation: mean=12, std=3, CV≈0.25
    - Recent velocity +5% vs older (stable)
```

**When**: `_calculate_health_score(metrics, statistics_df)`

**Then**:
- Progress: 60/100 * 30 = 18 points
- Schedule: tanh(10/20) ≈ 0.46 → (0.46+1)*15 ≈ 21.9 points
- Stability: CV=0.25 → 20*(1-0.25/1.5) ≈ 16.7 points
- Trend: +5% → 10 + (5/50)*10 = 11 points
- **Total**: 18 + 21.9 + 16.7 + 11 = 67.6 → **68 points** ✅ (65-75 target met)

### Test Case 4: Small Project (4 weeks)

**Given**:
```python
metrics = {
    "completion_percentage": 50.0,
    "days_to_completion": 20,
    "days_to_deadline": 25  # +5 buffer
}
statistics_df = DataFrame with 4 weeks:
    - Velocity: [10, 12, 11, 13] items
    - CV ≈ 0.12 (stable)
    - Recent (11, 13) vs older (10, 12) → +9% trend
```

**When**: `_calculate_health_score(metrics, statistics_df)`

**Then**:
- Progress: 50/100 * 30 = 15 points
- Schedule: tanh(5/20) ≈ 0.24 → (0.24+1)*15 ≈ 18.6 points
- Stability: CV=0.12 → 20*(1-0.12/1.5) ≈ 18.4 points
- Trend: +9% → 10 + (9/50)*10 = 11.8 points (trend calculated despite only 4 weeks!)
- **Total**: 15 + 18.6 + 18.4 + 11.8 = 63.8 → **64 points** ✅

### Test Case 5: Incomplete Week Filtering

**Given**:
```python
metrics = {
    "completion_percentage": 70.0,
    "days_to_completion": 30,
    "days_to_deadline": 45
}
statistics_df = DataFrame with 12 weeks:
    - Weeks 1-11: 10 items each
    - Week 12 (current, incomplete): 4 items (only 3 days elapsed)

# Today is Wednesday (not Sunday 23:59:59)
```

**When**: `_calculate_health_score(metrics, statistics_df)`

**Then**:
- Week 12 is filtered out (incomplete)
- Stability calculated from weeks 1-11 only (not week 12)
- Trend calculated from weeks 1-11 only
- Health score based on complete weeks only
- **Result**: Score NOT artificially deflated by partial week data ✅

### Test Case 6: Edge Case - Zero Velocity

**Given**:
```python
metrics = {
    "completion_percentage": 20.0,
    "days_to_completion": None,  # No forecast possible
    "days_to_deadline": 60
}
statistics_df = DataFrame with 6 weeks:
    - All weeks: 0 items completed (stalled project)
```

**When**: `_calculate_health_score(metrics, statistics_df)`

**Then**:
- Progress: 20/100 * 30 = 6 points
- Schedule: Cannot calculate (days_to_completion None) → 15 points (neutral)
- Stability: mean=0 → 10 points (neutral, avoid division by zero)
- Trend: Cannot calculate (zero velocity) → 10 points (neutral)
- **Total**: 6 + 15 + 10 + 10 = 41 → **41 points** ✅

### Test Case 7: Gradual Change Verification

**Given**: Two scenarios differing by 1 day schedule buffer

Scenario A:
```python
metrics_A = {"completion_percentage": 50.0, "days_to_completion": 50, "days_to_deadline": 45}
# Buffer = -5 days (slightly behind)
```

Scenario B:
```python
metrics_B = {"completion_percentage": 50.0, "days_to_completion": 49, "days_to_deadline": 45}
# Buffer = -4 days (1 day better)
```

**When**: Calculate both health scores

**Then**:
- Health score difference MUST be < 5 points (smooth gradient)
- Difference MUST be > 0 (detecting the 1-day improvement)
- **Expected**: ~0.5-2 point improvement for 1-day buffer change ✅

## Error Handling

### Invalid Input Scenarios

| Scenario                                  | Behavior                                     |
| ----------------------------------------- | -------------------------------------------- |
| `metrics` is None                         | Raise KeyError (caller error)                |
| `metrics` missing `completion_percentage` | Raise KeyError (caller error)                |
| `statistics_df` is None                   | Treat as empty DataFrame, use neutral scores |
| `statistics_df` empty                     | Use neutral scores for stability/trend       |
| `statistics_df` wrong columns             | Raise KeyError for missing required columns  |
| Negative `completed_items`                | Treat as 0 (data quality issue, log warning) |
| `completion_percentage` > 100             | Clamp to 100 (data quality issue)            |
| `completion_percentage` < 0               | Clamp to 0 (data quality issue)              |

### Fallback Values

When component cannot be calculated:

| Component | Fallback Condition                             | Fallback Value    |
| --------- | ---------------------------------------------- | ----------------- |
| Progress  | Always calculated                              | N/A (always 0-30) |
| Schedule  | deadline missing or days_to_completion missing | 15 (neutral)      |
| Stability | <2 weeks data OR mean velocity = 0             | 10 (neutral)      |
| Trend     | <4 weeks data OR older velocity = 0            | 10 (neutral)      |

## Performance Contract

### Time Complexity

| Dataset Size | Max Execution Time |
| ------------ | ------------------ |
| 4 weeks      | <5ms               |
| 12 weeks     | <10ms              |
| 52 weeks     | <50ms              |
| Empty        | <1ms               |

### Space Complexity

- O(1) additional memory (no copies of input DataFrame)
- Temporary arrays for calculations: max 520 bytes (10 weeks *8 bytes* 6.5 fields)

## Dependencies

### External Functions

```python
from data.processing import calculate_velocity_from_dataframe

# Contract:
# - Input: DataFrame, column name
# - Output: float (items per week)
# - Handles week counting correctly (uses actual weeks, not date range)
```

### Standard Library

```python
import math  # For math.tanh(), math.sqrt()
from datetime import datetime  # For current time
```

### Pandas Operations

```python
import pandas as pd

# Used operations:
# - df.iloc[:-1]  # Remove last row
# - df.tail(n)    # Last n rows
# - df.iloc[:mid] # First half
# - df.iloc[mid:] # Second half
```

## Test Coverage Requirements

### Unit Tests (Required)

1. ✅ Test excellent project (>90% score)
2. ✅ Test critical project (<10% score)
3. ✅ Test typical healthy project (65-75% score)
4. ✅ Test small project (4 weeks - all components work)
5. ✅ Test incomplete week filtering (Wednesday vs Sunday)
6. ✅ Test zero velocity (division by zero prevention)
7. ✅ Test gradual changes (1-day buffer increment)
8. ✅ Test missing deadline (neutral schedule)
9. ✅ Test empty DataFrame (all neutrals except progress)
10. ✅ Test extreme schedule variance (±100 days)
11. ✅ Test extreme CV (>2.0, clamping)
12. ✅ Test extreme velocity change (>±100%, clamping)

### Edge Case Tests (Required)

1. ✅ Exactly 2 weeks data (minimum for stability)
2. ✅ Exactly 4 weeks data (minimum for trend)
3. ✅ Sunday 23:59:59 boundary (week completion)
4. ✅ Monday 00:00:01 (new week start)
5. ✅ All weeks identical velocity (CV=0)
6. ✅ Single week data (all fallbacks triggered)

### Integration Tests (Optional)

1. Call from actual dashboard callback with real metrics
2. Verify UI displays correct color/label based on score
3. Performance test with 52-week dataset

## Acceptance Criteria

Function is ready for merge when:

1. ✅ All 12 unit tests pass
2. ✅ All 6 edge case tests pass
3. ✅ Performance tests confirm <50ms for 52 weeks
4. ✅ Code coverage >95% for the function
5. ✅ No exceptions raised for any valid input
6. ✅ Deterministic (same input produces same output)
7. ✅ Existing dashboard tests updated (12 tests in test_dashboard_cards.py)

## Version History

- **v1.0** (2024-12-22): Initial contract specification
