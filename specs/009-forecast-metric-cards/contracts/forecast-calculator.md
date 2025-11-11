# API Contract: Forecast Calculator

**Module**: `data/metrics_calculator.py`  
**Function**: `calculate_forecast()`  
**Purpose**: Calculate 4-week weighted average forecast from historical metric values

---

## Function Signature

```python
def calculate_forecast(
    historical_values: List[float],
    weights: Optional[List[float]] = None,
    min_weeks: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Calculate 4-week weighted forecast from historical data.
    
    Args:
        historical_values: Metric values from last 2-4 weeks (oldest to newest).
                          Must be non-negative values representing weekly metric data.
        
        weights: Optional weights for each week (oldest to newest).
                Default: [0.1, 0.2, 0.3, 0.4] for 4 weeks
                For <4 weeks: Equal weights (e.g., [0.5, 0.5] for 2 weeks)
        
        min_weeks: Minimum historical weeks required for forecast.
                  Default: 2 (industry standard for basic trend)
    
    Returns:
        Dict with forecast data (see schema below), or None if insufficient data.
        
    Raises:
        ValueError: If weights don't sum to 1.0 within 0.001 tolerance
        ValueError: If weights length doesn't match historical_values length
        ValueError: If any historical value is negative
        TypeError: If historical_values is not a list of numbers
    """
```

---

## Return Schema

**Success Case** (sufficient data):
```python
{
    "forecast_value": float,           # Weighted average (e.g., 13.5)
    "forecast_range": None,            # Reserved for Flow Load (set by caller)
    "historical_values": List[float],  # Echo of input (for transparency)
    "weights_applied": List[float],    # Actual weights used
    "weeks_available": int,            # Actual count (2-4)
    "confidence": str                  # "building" (<4 weeks) or "established" (4 weeks)
}
```

**Insufficient Data Case**:
```python
None  # Returned when len(historical_values) < min_weeks
```

---

## Examples

### Example 1: Standard 4-Week Forecast

```python
from data.metrics_calculator import calculate_forecast

# Last 4 weeks of velocity data (oldest to newest)
historical_values = [10.0, 12.0, 11.0, 13.0]

result = calculate_forecast(historical_values)
```

**Expected Output**:
```python
{
    "forecast_value": 11.9,  # (10*0.1 + 12*0.2 + 11*0.3 + 13*0.4)
    "forecast_range": None,
    "historical_values": [10.0, 12.0, 11.0, 13.0],
    "weights_applied": [0.1, 0.2, 0.3, 0.4],
    "weeks_available": 4,
    "confidence": "established"
}
```

**Calculation Breakdown**:
```
Week W-3: 10.0 * 0.1 = 1.0
Week W-2: 12.0 * 0.2 = 2.4
Week W-1: 11.0 * 0.3 = 3.3
Week W-0: 13.0 * 0.4 = 5.2
                      -----
Forecast:             11.9 items/week
```

---

### Example 2: Building Baseline (2 Weeks)

```python
# Only 2 weeks of data available
historical_values = [10.0, 12.0]

result = calculate_forecast(historical_values)
```

**Expected Output**:
```python
{
    "forecast_value": 11.0,  # (10*0.5 + 12*0.5)
    "forecast_range": None,
    "historical_values": [10.0, 12.0],
    "weights_applied": [0.5, 0.5],  # Equal weights
    "weeks_available": 2,
    "confidence": "building"
}
```

**Note**: Weights automatically switch to equal distribution when <4 weeks available.

---

### Example 3: Insufficient Data

```python
# Only 1 week of data
historical_values = [10.0]

result = calculate_forecast(historical_values, min_weeks=2)
```

**Expected Output**:
```python
None  # Not enough data for forecast
```

**UI Handling**: Display "Insufficient data for forecast" message.

---

### Example 4: Custom Weights (3 Weeks)

```python
# 3 weeks with custom equal weighting
historical_values = [10.0, 11.0, 12.0]
custom_weights = [0.33, 0.33, 0.34]  # Must sum to 1.0

result = calculate_forecast(historical_values, weights=custom_weights)
```

**Expected Output**:
```python
{
    "forecast_value": 11.0,  # (10*0.33 + 11*0.33 + 12*0.34)
    "forecast_range": None,
    "historical_values": [10.0, 11.0, 12.0],
    "weights_applied": [0.33, 0.33, 0.34],
    "weeks_available": 3,
    "confidence": "building"
}
```

---

### Example 5: Error - Negative Values

```python
# Invalid: negative metric value
historical_values = [10.0, 12.0, -5.0, 13.0]

result = calculate_forecast(historical_values)
```

**Expected Behavior**:
```python
raise ValueError("Historical values cannot be negative: -5.0")
```

---

### Example 6: Error - Weight Mismatch

```python
# Invalid: weights don't match historical_values length
historical_values = [10.0, 12.0, 11.0, 13.0]
custom_weights = [0.5, 0.5]  # Only 2 weights for 4 values

result = calculate_forecast(historical_values, weights=custom_weights)
```

**Expected Behavior**:
```python
raise ValueError("Weights length (2) must match historical_values length (4)")
```

---

## Edge Cases

### Edge Case 1: Zero Values in History

```python
# Week with no completions (e.g., holiday week)
historical_values = [10.0, 0.0, 11.0, 13.0]

result = calculate_forecast(historical_values)
```

**Expected Output**:
```python
{
    "forecast_value": 8.5,  # (10*0.1 + 0*0.2 + 11*0.3 + 13*0.4)
    # ... rest of schema
}
```

**Note**: Zero is valid (different from None/null). Represents weeks with no activity.

---

### Edge Case 2: All Zeros

```python
# All historical weeks have zero completions
historical_values = [0.0, 0.0, 0.0, 0.0]

result = calculate_forecast(historical_values)
```

**Expected Output**:
```python
{
    "forecast_value": 0.0,
    "confidence": "established",
    # ... rest of schema
}
```

**UI Handling**: Show "Forecast: ~0 items/week" with note "No recent activity"

---

### Edge Case 3: Very Large Values

```python
# Edge case: large metric values (performance testing)
historical_values = [1000.0, 1200.0, 1100.0, 1300.0]

result = calculate_forecast(historical_values)
```

**Expected Output**:
```python
{
    "forecast_value": 1190.0,  # Normal calculation applies
    # ... rest of schema
}
```

**Note**: No special handling needed - weighted average scales linearly.

---

### Edge Case 4: Floating Point Precision

```python
# Weights that sum to ~1.0 due to floating point
historical_values = [10.0, 12.0, 11.0]
weights = [0.333333, 0.333333, 0.333334]  # Sum: 1.000000

result = calculate_forecast(historical_values, weights=weights)
```

**Expected Output**:
```python
{
    "forecast_value": 11.0,
    "weights_applied": [0.333333, 0.333333, 0.333334],
    # ... rest of schema
}
```

**Validation**: Use tolerance of 0.001 for weight sum check (`abs(sum(weights) - 1.0) < 0.001`)

---

## Implementation Requirements

### 1. Input Validation

```python
# Pseudo-code for validation logic
if not isinstance(historical_values, list):
    raise TypeError("historical_values must be a list")

if any(not isinstance(v, (int, float)) for v in historical_values):
    raise TypeError("All historical values must be numbers")

if any(v < 0 for v in historical_values):
    raise ValueError(f"Historical values cannot be negative: {min(historical_values)}")

if len(historical_values) < min_weeks:
    return None  # Insufficient data

if weights is not None:
    if len(weights) != len(historical_values):
        raise ValueError(f"Weights length ({len(weights)}) must match historical_values length ({len(historical_values)})")
    
    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError(f"Weights must sum to 1.0 (got {sum(weights)})")
```

### 2. Weight Selection Logic

```python
# Pseudo-code for weight selection
if weights is None:
    if len(historical_values) == 4:
        weights = [0.1, 0.2, 0.3, 0.4]
        confidence = "established"
    else:  # 2 or 3 weeks
        equal_weight = 1.0 / len(historical_values)
        weights = [equal_weight] * len(historical_values)
        confidence = "building"
else:
    # Use provided custom weights
    confidence = "established" if len(historical_values) == 4 else "building"
```

### 3. Calculation

```python
# Weighted average calculation
forecast_value = sum(v * w for v, w in zip(historical_values, weights))
```

### 4. Return Structure

```python
return {
    "forecast_value": round(forecast_value, 2),  # 2 decimal precision
    "forecast_range": None,
    "historical_values": historical_values.copy(),  # Defensive copy
    "weights_applied": weights.copy(),
    "weeks_available": len(historical_values),
    "confidence": confidence
}
```

---

## Unit Test Requirements

**Test Coverage** (minimum 95%):

1. ✅ Test standard 4-week forecast with default weights
2. ✅ Test 2-week forecast with equal weights
3. ✅ Test 3-week forecast with equal weights
4. ✅ Test custom weights (valid)
5. ✅ Test insufficient data (1 week) returns None
6. ✅ Test empty list returns None
7. ✅ Test zero values in history
8. ✅ Test all zeros
9. ✅ Test negative values raise ValueError
10. ✅ Test non-numeric values raise TypeError
11. ✅ Test weight length mismatch raises ValueError
12. ✅ Test weights sum != 1.0 raises ValueError
13. ✅ Test weights sum ~1.0 (within tolerance) succeeds
14. ✅ Test large values (performance)
15. ✅ Test rounding to 2 decimal places

**Test File**: `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast`

---

## Performance Requirements

- **Time Complexity**: O(n) where n = len(historical_values) ≤ 4, effectively O(1)
- **Space Complexity**: O(n) for return dict
- **Execution Time**: <5μs per call (negligible)

**Benchmark**: 9 metrics × 100 calls = <5ms total overhead

---

## Integration Points

### Called By
- `data/metrics_snapshots.py::save_metrics_snapshot()` - For all 9 metrics
- `callbacks/dora_flow_metrics.py` - For real-time forecast display

### Dependencies
- None (uses only Python standard library)

### Output Consumed By
- `calculate_flow_load_range()` - Adds range to forecast
- `calculate_trend_vs_forecast()` - Uses forecast_value for comparison
- `ui/metric_cards.py::create_metric_card()` - Displays forecast in UI

---

## Backward Compatibility

**N/A** - This is a new function with no existing callers.

**Future Compatibility**:
- Reserve `forecast_range` field for Flow Load enhancement
- Return dict (not dataclass) for JSON serialization compatibility
- Use optional parameters for future extensibility (e.g., outlier filtering)

---

## Security Considerations

- **Input Sanitization**: Validate all inputs to prevent TypeError/ValueError propagation
- **No External Data**: Function operates on in-memory data only (no file/network access)
- **No Side Effects**: Pure function - no state modification

---

## Configuration

**Constants** (defined in `configuration/metrics_config.py`):

```python
FORECAST_WEIGHTS_4_WEEK = [0.1, 0.2, 0.3, 0.4]
FORECAST_MIN_WEEKS = 2
FORECAST_DECIMAL_PRECISION = 2
```

**Usage in Function**:
```python
from configuration.metrics_config import (
    FORECAST_WEIGHTS_4_WEEK,
    FORECAST_MIN_WEEKS,
    FORECAST_DECIMAL_PRECISION
)

def calculate_forecast(
    historical_values: List[float],
    weights: Optional[List[float]] = None,
    min_weeks: int = FORECAST_MIN_WEEKS
) -> Optional[Dict[str, Any]]:
    # Use FORECAST_WEIGHTS_4_WEEK as default
    # Use FORECAST_DECIMAL_PRECISION for rounding
    ...
```

---

## Contract Version

**Version**: 1.0.0  
**Date**: November 10, 2025  
**Status**: Proposed (awaiting implementation)  
**Breaking Changes**: N/A (new function)
