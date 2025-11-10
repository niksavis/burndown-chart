# API Contract: Flow Load Range Calculator

**Module**: `data/metrics_calculator.py`  
**Function**: `calculate_flow_load_range()`  
**Purpose**: Calculate acceptable WIP (Work in Progress) range for Flow Load metric

---

## Function Signature

```python
def calculate_flow_load_range(
    forecast_value: float,
    range_percent: float = 0.20
) -> Dict[str, float]:
    """
    Calculate acceptable WIP range for Flow Load metric.
    
    Flow Load is unique: it's a snapshot metric (not accumulation) that can be
    problematic in both directions:
    - Too high → bottleneck, team overwhelmed
    - Too low → underutilization, risk of running out of work
    
    Args:
        forecast_value: Base forecast from calculate_forecast() (e.g., 15.0 items)
        
        range_percent: Percentage deviation for acceptable range (default: 0.20 = ±20%)
                      Industry standard: ±20% for healthy WIP variance
    
    Returns:
        Dict with "lower" and "upper" bounds for acceptable WIP range
        
    Raises:
        ValueError: If forecast_value is zero or negative
        ValueError: If range_percent is negative or > 1.0
        TypeError: If forecast_value or range_percent not numeric
    """
```

---

## Return Schema

```python
{
    "lower": float,  # Lower bound of acceptable range (forecast * (1 - range_percent))
    "upper": float   # Upper bound of acceptable range (forecast * (1 + range_percent))
}
```

---

## Examples

### Example 1: Standard Range Calculation

```python
from data.metrics_calculator import calculate_flow_load_range

# Forecast: 15 items WIP
result = calculate_flow_load_range(forecast_value=15.0)
```

**Expected Output**:
```python
{
    "lower": 12.0,  # 15 * (1 - 0.20) = 15 * 0.8
    "upper": 18.0   # 15 * (1 + 0.20) = 15 * 1.2
}
```

**Interpretation**:
- WIP 12-18 items: ✅ Healthy range
- WIP > 18 items: ⚠️ Too much work in progress (potential bottleneck)
- WIP < 12 items: ℹ️ Too little work in progress (possible underutilization)

---

### Example 2: Custom Range (±30%)

```python
# Wider tolerance: ±30% instead of ±20%
result = calculate_flow_load_range(
    forecast_value=15.0,
    range_percent=0.30
)
```

**Expected Output**:
```python
{
    "lower": 10.5,  # 15 * 0.7
    "upper": 19.5   # 15 * 1.3
}
```

---

### Example 3: Small Forecast Value

```python
# Very small team with low WIP forecast
result = calculate_flow_load_range(forecast_value=3.0)
```

**Expected Output**:
```python
{
    "lower": 2.4,   # 3 * 0.8
    "upper": 3.6    # 3 * 1.2
}
```

**UI Consideration**: Round to nearest integer for display: "2-4 items"

---

### Example 4: Large Forecast Value

```python
# Large team with high WIP forecast
result = calculate_flow_load_range(forecast_value=50.0)
```

**Expected Output**:
```python
{
    "lower": 40.0,  # 50 * 0.8
    "upper": 60.0   # 50 * 1.2
}
```

---

## Range Interpretation Logic

### WIP Status Determination

```python
current_wip = 24  # Example
forecast_range = calculate_flow_load_range(15.0)  # {lower: 12, upper: 18}

if current_wip > forecast_range["upper"]:
    status = "Above normal range"
    severity = "warning"  # Too much WIP
    color = "text-warning"
    
elif current_wip < forecast_range["lower"]:
    status = "Below normal range"
    severity = "info"  # Possible underutilization
    color = "text-info"
    
else:
    status = "Within normal range ✓"
    severity = "good"
    color = "text-success"
```

### Trend Direction (for Flow Load)

Unlike other metrics, Flow Load trend uses range comparison:

```python
# This logic goes in calculate_trend_vs_forecast() when metric is "flow_load"
if current_wip > upper_bound:
    direction = "↗"
    is_good = False  # Too high is bad
    
elif current_wip < lower_bound:
    direction = "↘"
    is_good = False  # Too low is also problematic
    
else:
    direction = "→"
    is_good = True   # Within range is good
```

---

## Edge Cases

### Edge Case 1: Zero Forecast Value (Error)

```python
result = calculate_flow_load_range(forecast_value=0.0)
```

**Expected Behavior**:
```python
raise ValueError("Forecast value cannot be zero")
```

**Rationale**: Cannot calculate percentage range of zero.

---

### Edge Case 2: Negative Forecast Value (Error)

```python
result = calculate_flow_load_range(forecast_value=-5.0)
```

**Expected Behavior**:
```python
raise ValueError("Forecast value cannot be negative: -5.0")
```

**Rationale**: WIP count cannot be negative.

---

### Edge Case 3: Zero Range Percent (Exact Bounds)

```python
# No variance allowed
result = calculate_flow_load_range(
    forecast_value=15.0,
    range_percent=0.0
)
```

**Expected Output**:
```python
{
    "lower": 15.0,  # 15 * (1 - 0) = 15
    "upper": 15.0   # 15 * (1 + 0) = 15
}
```

**Interpretation**: Only exact forecast value is acceptable (unrealistic but mathematically valid)

---

### Edge Case 4: 100% Range Percent

```python
# Very wide tolerance
result = calculate_flow_load_range(
    forecast_value=15.0,
    range_percent=1.0
)
```

**Expected Output**:
```python
{
    "lower": 0.0,   # 15 * (1 - 1.0) = 0
    "upper": 30.0   # 15 * (1 + 1.0) = 30
}
```

**Interpretation**: WIP from 0 to 2× forecast is acceptable (very permissive)

---

### Edge Case 5: Range Percent > 100% (Error)

```python
# Invalid: range cannot exceed 100%
result = calculate_flow_load_range(
    forecast_value=15.0,
    range_percent=1.5
)
```

**Expected Behavior**:
```python
raise ValueError("range_percent must be between 0 and 1.0, got 1.5")
```

---

### Edge Case 6: Negative Range Percent (Error)

```python
result = calculate_flow_load_range(
    forecast_value=15.0,
    range_percent=-0.2
)
```

**Expected Behavior**:
```python
raise ValueError("range_percent cannot be negative: -0.2")
```

---

## Implementation Requirements

### 1. Input Validation

```python
# Pseudo-code
if not isinstance(forecast_value, (int, float)):
    raise TypeError("forecast_value must be numeric")

if not isinstance(range_percent, (int, float)):
    raise TypeError("range_percent must be numeric")

if forecast_value <= 0:
    raise ValueError(f"Forecast value must be positive, got {forecast_value}")

if range_percent < 0:
    raise ValueError(f"range_percent cannot be negative: {range_percent}")

if range_percent > 1.0:
    raise ValueError(f"range_percent must be between 0 and 1.0, got {range_percent}")
```

### 2. Range Calculation

```python
lower_bound = forecast_value * (1 - range_percent)
upper_bound = forecast_value * (1 + range_percent)
```

### 3. Bounds Constraints

```python
# Lower bound cannot be negative (WIP count)
if lower_bound < 0:
    lower_bound = 0.0
```

### 4. Return Structure

```python
return {
    "lower": round(lower_bound, 1),  # 1 decimal precision
    "upper": round(upper_bound, 1)
}
```

---

## Unit Test Requirements

**Test Coverage** (minimum 95%):

1. ✅ Test standard range (±20%) with forecast 15
2. ✅ Test custom range (±30%)
3. ✅ Test custom range (±10%)
4. ✅ Test small forecast value (3 items)
5. ✅ Test large forecast value (50 items)
6. ✅ Test zero forecast value raises ValueError
7. ✅ Test negative forecast value raises ValueError
8. ✅ Test zero range_percent (exact bounds)
9. ✅ Test 100% range_percent
10. ✅ Test negative range_percent raises ValueError
11. ✅ Test range_percent > 1.0 raises ValueError
12. ✅ Test non-numeric forecast_value raises TypeError
13. ✅ Test non-numeric range_percent raises TypeError
14. ✅ Test rounding to 1 decimal place
15. ✅ Test lower bound clamped to 0 if negative

**Test File**: `tests/unit/data/test_metrics_calculator.py::TestCalculateFlowLoadRange`

---

## Integration with Forecast Display

### In `data/metrics_calculator.py`

```python
# Example usage flow
forecast = calculate_forecast([14, 15, 13, 16])  # Returns 14.8
forecast["forecast_range"] = calculate_flow_load_range(forecast["forecast_value"])

# Result:
{
    "forecast_value": 14.8,
    "forecast_range": {"lower": 11.8, "upper": 17.8},
    "weeks_available": 4,
    "confidence": "established"
}
```

### In UI Display

```python
# Metric card displays range instead of point estimate
if metric_key == "flow_load" and forecast_range is not None:
    forecast_text = (
        f"Forecast: ~{round(forecast_value)} items "
        f"({round(forecast_range['lower'])}-{round(forecast_range['upper'])})"
    )
else:
    forecast_text = f"Forecast: ~{round(forecast_value)} {unit}"
```

**Example Display**:
```
Flow Load (WIP)        [Warning Badge]
24 items work in progress
↗ +60% vs prev avg

Forecast: ~15 items (12-18)
↗ +60% above normal ⚠️
```

---

## Performance Requirements

- **Time Complexity**: O(1) - simple arithmetic
- **Space Complexity**: O(1) - return dict with 2 fields
- **Execution Time**: <5μs per call

---

## Integration Points

### Called By
- `data/metrics_snapshots.py::save_metrics_snapshot()` - Only for Flow Load metric
- `callbacks/dora_flow_metrics.py` - When calculating Flow Load forecast

### Dependencies
- Requires `calculate_forecast()` output as input (`forecast_value`)

### Output Consumed By
- `calculate_trend_vs_forecast()` - Uses range for Flow Load trend logic
- `ui/metric_cards.py::create_metric_card()` - Displays range in UI

---

## Why Flow Load is Special

### Accumulation Metrics (Most Metrics)
- **Behavior**: Values accumulate over time (e.g., items completed per week)
- **Direction**: Higher or lower is definitively better
- **Forecast**: Point estimate (single value)
- **Examples**: Velocity, Deploy Frequency, Lead Time

### Snapshot Metric (Flow Load Only)
- **Behavior**: Point-in-time measurement (current WIP count)
- **Direction**: Too high OR too low is problematic (bidirectional concern)
- **Forecast**: Range with upper and lower bounds
- **Example**: Work in Progress (WIP)

### WIP Health Matrix

| Current WIP | Forecast Range | Status      | Concern                               |
| ----------- | -------------- | ----------- | ------------------------------------- |
| 24 items    | 12-18 items    | Above range | Bottleneck, team overwhelmed          |
| 14 items    | 12-18 items    | In range    | Healthy flow                          |
| 9 items     | 12-18 items    | Below range | Underutilization, may run out of work |

---

## Configuration

**Constants** (defined in `configuration/metrics_config.py`):

```python
FLOW_LOAD_RANGE_PERCENT = 0.20  # ±20% standard deviation for WIP
FLOW_LOAD_DECIMAL_PRECISION = 1  # 1 decimal place for bounds
```

**Industry Standards**:
- ±20% is common threshold for "healthy" WIP variance
- Tighter ranges (±10%) may be overly restrictive
- Wider ranges (±30%) may mask flow problems

---

## Contract Version

**Version**: 1.0.0  
**Date**: November 10, 2025  
**Status**: Proposed (awaiting implementation)  
**Breaking Changes**: N/A (new function)
