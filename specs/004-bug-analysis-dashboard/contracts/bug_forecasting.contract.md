# Contract: Bug Resolution Forecasting

**Feature**: Bug Analysis Dashboard  
**Module**: `data/bug_processing.py`  
**Phase**: 1 - Design & Architecture

## Function Signature

```python
def forecast_bug_resolution(
    open_bugs: int,
    weekly_stats: List[WeeklyBugStatistics],
    confidence_level: float = 0.95
) -> BugForecast:
    """
    Forecast when open bugs will be resolved based on historical closure rates.
    
    Args:
        open_bugs: Current count of open bugs
        weekly_stats: Historical weekly statistics (min 4 weeks recommended)
        confidence_level: Statistical confidence level (0.0-1.0)
    
    Returns:
        Bug forecast with optimistic/pessimistic/likely estimates
        
    Raises:
        ValueError: If open_bugs < 0
        ValueError: If confidence_level not in (0.0, 1.0]
    """
```

## Contract Specification

### Preconditions

- `open_bugs` must be >= 0
- `weekly_stats` must have at least 2 weeks of data (4+ recommended)
- `weekly_stats` must be chronologically ordered
- `confidence_level` must be between 0.0 (exclusive) and 1.0 (inclusive)
- Each week in `weekly_stats` must have `bugs_resolved` field

### Postconditions

- Returns BugForecast dictionary with all required fields
- If `open_bugs == 0`, forecast shows 0 weeks with current date
- If insufficient data (< 4 weeks), sets `insufficient_data = true`
- `optimistic_weeks <= most_likely_weeks <= pessimistic_weeks`
- All date fields are ISO format strings in the future (or None)
- `avg_closure_rate` is non-negative

### Input Validation

```python
# Validate open bugs
assert isinstance(open_bugs, int), "open_bugs must be an integer"
assert open_bugs >= 0, "open_bugs cannot be negative"

# Validate weekly stats
assert isinstance(weekly_stats, list), "weekly_stats must be a list"
assert len(weekly_stats) >= 2, "weekly_stats must have at least 2 weeks"

for week in weekly_stats:
    assert "bugs_resolved" in week, f"Week {week.get('week')} missing bugs_resolved"
    assert week["bugs_resolved"] >= 0, "bugs_resolved cannot be negative"

# Verify chronological order
for i in range(len(weekly_stats) - 1):
    assert weekly_stats[i]["week"] < weekly_stats[i+1]["week"], "weekly_stats must be ordered"

# Validate confidence level
assert isinstance(confidence_level, float), "confidence_level must be a float"
assert 0.0 < confidence_level <= 1.0, "confidence_level must be in (0.0, 1.0]"
```

### Output Guarantees

```python
# Verify output structure
assert isinstance(result, dict), "Result must be a dict"
assert "open_bugs" in result, "Result missing open_bugs"
assert result["open_bugs"] == open_bugs, "open_bugs mismatch"

# Verify required fields
required_fields = [
    "open_bugs", "avg_closure_rate", "optimistic_weeks", "pessimistic_weeks",
    "most_likely_weeks", "optimistic_date", "pessimistic_date", "most_likely_date",
    "confidence_level", "insufficient_data"
]
for field in required_fields:
    assert field in result, f"Result missing required field: {field}"

# Verify week ordering (if all present)
if result["optimistic_weeks"] and result["most_likely_weeks"] and result["pessimistic_weeks"]:
    assert result["optimistic_weeks"] <= result["most_likely_weeks"] <= result["pessimistic_weeks"]

# Verify dates are in future (if present)
from datetime import datetime
for date_field in ["optimistic_date", "pessimistic_date", "most_likely_date"]:
    if result[date_field]:
        forecast_date = datetime.fromisoformat(result[date_field])
        assert forecast_date >= datetime.now().date(), f"{date_field} must be in future"

# Verify confidence level matches input
assert result["confidence_level"] == confidence_level
```

### Forecasting Algorithm

**Step 1: Calculate Historical Closure Rate**

```python
# Use last 8 weeks if available, otherwise all available weeks
history_window = min(8, len(weekly_stats))
recent_weeks = weekly_stats[-history_window:]

closure_rates = [week["bugs_resolved"] for week in recent_weeks]
avg_closure_rate = sum(closure_rates) / len(closure_rates)
std_dev = calculate_standard_deviation(closure_rates)
```

**Step 2: Calculate Estimates**

```python
# Optimistic: avg + 1 standard deviation
optimistic_rate = avg_closure_rate + std_dev
optimistic_weeks = ceil(open_bugs / optimistic_rate) if optimistic_rate > 0 else None

# Pessimistic: avg - 1 standard deviation (floor at 0.1 to avoid division by zero)
pessimistic_rate = max(avg_closure_rate - std_dev, 0.1)
pessimistic_weeks = ceil(open_bugs / pessimistic_rate)

# Most likely: use average
most_likely_weeks = ceil(open_bugs / avg_closure_rate) if avg_closure_rate > 0 else None
```

**Step 3: Calculate Completion Dates**

```python
def calculate_future_date(weeks: Optional[int]) -> Optional[str]:
    """Calculate ISO date N weeks from now."""
    if weeks is None:
        return None
    
    from datetime import datetime, timedelta
    future_date = datetime.now() + timedelta(weeks=weeks)
    return future_date.date().isoformat()

optimistic_date = calculate_future_date(optimistic_weeks)
pessimistic_date = calculate_future_date(pessimistic_weeks)
most_likely_date = calculate_future_date(most_likely_weeks)
```

**Step 4: Assess Data Sufficiency**

```python
insufficient_data = len(weekly_stats) < 4 or avg_closure_rate == 0
```

### Example Usage

**Example 1: Normal Forecast**

```python
# Setup
open_bugs = 23
weekly_stats = [
    {"week": "2025-W01", "bugs_resolved": 5},
    {"week": "2025-W02", "bugs_resolved": 6},
    {"week": "2025-W03", "bugs_resolved": 4},
    {"week": "2025-W04", "bugs_resolved": 5},
    {"week": "2025-W05", "bugs_resolved": 7},
    {"week": "2025-W06", "bugs_resolved": 4}
]

# Execute
forecast = forecast_bug_resolution(open_bugs, weekly_stats)

# Expected results
assert forecast["open_bugs"] == 23
assert forecast["avg_closure_rate"] == 5.17  # mean of [5,6,4,5,7,4]
assert forecast["insufficient_data"] is False

# With std_dev ≈ 1.17:
# optimistic_rate ≈ 6.34 → optimistic_weeks = ceil(23/6.34) = 4
# pessimistic_rate ≈ 4.0 → pessimistic_weeks = ceil(23/4.0) = 6
# most_likely_rate = 5.17 → most_likely_weeks = ceil(23/5.17) = 5

assert forecast["optimistic_weeks"] == 4
assert forecast["most_likely_weeks"] == 5
assert forecast["pessimistic_weeks"] == 6
```

**Example 2: Zero Open Bugs**

```python
# Setup
open_bugs = 0
weekly_stats = [{"week": "2025-W01", "bugs_resolved": 5}]

# Execute
forecast = forecast_bug_resolution(open_bugs, weekly_stats)

# Expected: Immediate completion
assert forecast["open_bugs"] == 0
assert forecast["optimistic_weeks"] == 0
assert forecast["most_likely_weeks"] == 0
assert forecast["pessimistic_weeks"] == 0
assert forecast["optimistic_date"] == datetime.now().date().isoformat()
```

**Example 3: Insufficient Data**

```python
# Setup
open_bugs = 15
weekly_stats = [
    {"week": "2025-W01", "bugs_resolved": 2},
    {"week": "2025-W02", "bugs_resolved": 3}
]  # Only 2 weeks

# Execute
forecast = forecast_bug_resolution(open_bugs, weekly_stats)

# Expected: Flag insufficient data but still provide estimate
assert forecast["insufficient_data"] is True
assert forecast["avg_closure_rate"] == 2.5
assert forecast["most_likely_weeks"] == ceil(15 / 2.5)  # 6 weeks
```

**Example 4: Zero Closure Rate**

```python
# Setup
open_bugs = 10
weekly_stats = [
    {"week": "2025-W01", "bugs_resolved": 0},
    {"week": "2025-W02", "bugs_resolved": 0},
    {"week": "2025-W03", "bugs_resolved": 0},
    {"week": "2025-W04", "bugs_resolved": 0}
]

# Execute
forecast = forecast_bug_resolution(open_bugs, weekly_stats)

# Expected: Cannot forecast, mark as insufficient data
assert forecast["avg_closure_rate"] == 0.0
assert forecast["insufficient_data"] is True
assert forecast["optimistic_weeks"] is None
assert forecast["most_likely_weeks"] is None
assert forecast["pessimistic_weeks"] is None
```

### Edge Cases

| Case                    | Input                         | Expected Output                        | Handling                        |
| ----------------------- | ----------------------------- | -------------------------------------- | ------------------------------- |
| Zero open bugs          | open_bugs = 0                 | All weeks = 0, dates = today           | Immediate completion            |
| Zero closure rate       | All weeks have 0 resolved     | insufficient_data = true, weeks = None | Cannot forecast                 |
| Single bug left         | open_bugs = 1                 | Forecast normally                      | Normal calculation              |
| Very high closure rate  | avg > open_bugs               | optimistic_weeks = 1                   | Minimum 1 week                  |
| Negative std dev result | avg - std_dev < 0             | pessimistic_rate = 0.1 floor           | Prevent division by zero        |
| Large open bugs         | open_bugs = 1000              | Forecast normally                      | May result in large week counts |
| Inconsistent closures   | High variance in weekly rates | Wide optimistic-pessimistic range      | Reflects uncertainty            |

### Performance Requirements

- **Time Complexity**: O(n) where n = length of weekly_stats
- **Space Complexity**: O(1) - fixed size output
- **Benchmark**: Calculate forecast for 52 weeks in < 10ms

### Statistical Notes

**Standard Deviation Calculation**:
```python
def calculate_standard_deviation(values: List[float]) -> float:
    """Calculate sample standard deviation."""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5
```

**Confidence Interval Interpretation**:
- 95% confidence (default): Use ±1 standard deviation
- 99% confidence: Use ±2 standard deviations
- For simplicity, current implementation uses ±1 std dev regardless

### Error Messages

```python
# Error message templates
ERROR_NEGATIVE_BUGS = "open_bugs cannot be negative: {open_bugs}"
ERROR_INVALID_CONFIDENCE = "confidence_level must be in (0.0, 1.0], got {confidence_level}"
ERROR_INSUFFICIENT_HISTORY = "weekly_stats must have at least 2 weeks, got {weeks}"
ERROR_MISSING_FIELD = "Week {week} missing required field: bugs_resolved"
```

### Testing Requirements

- ✅ Unit test with normal historical data
- ✅ Unit test with zero open bugs
- ✅ Unit test with zero closure rate
- ✅ Unit test with insufficient data (< 4 weeks)
- ✅ Unit test with high variance in closure rates
- ✅ Unit test with consistent closure rates (low variance)
- ✅ Unit test week ordering validation
- ✅ Unit test date calculation accuracy
- ✅ Property test with random open bugs and closure rates
- ✅ Integration test with real bug data

---

## Contract Verification

This contract will be verified by:

1. **Type Checking**: MyPy static analysis with datetime types
2. **Unit Tests**: pytest with 100% branch coverage
3. **Property Testing**: Hypothesis with random inputs
4. **Statistical Validation**: Verify std dev calculations match numpy
5. **Date Validation**: Verify all dates are correct and in future

**Contract Status**: ✅ **APPROVED** - Ready for implementation
