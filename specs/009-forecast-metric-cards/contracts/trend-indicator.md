# API Contract: Trend Indicator Calculator

**Module**: `data/metrics_calculator.py`  
**Function**: `calculate_trend_vs_forecast()`  
**Purpose**: Calculate trend direction and status comparing current metric value to forecast benchmark

---

## Function Signature

```python
def calculate_trend_vs_forecast(
    current_value: float,
    forecast_value: float,
    metric_type: Literal["higher_better", "lower_better"],
    threshold: float = 0.10
) -> Dict[str, Any]:
    """
    Calculate trend indicator comparing current metric to forecast.
    
    Args:
        current_value: Current week's metric value (e.g., 15 items completed)
        
        forecast_value: Forecasted value from calculate_forecast() (e.g., 13 items)
        
        metric_type: Interpretation direction
            - "higher_better": Flow Velocity, Flow Efficiency, Deployment Frequency
              (↗ above forecast is good, ↘ below forecast is bad)
            - "lower_better": Flow Time, Lead Time, CFR, MTTR
              (↘ below forecast is good, ↗ above forecast is bad)
        
        threshold: Percentage threshold for neutral zone (default: 0.10 = ±10%)
                  Within threshold → direction="→" (on track)
    
    Returns:
        Dict with trend indicator data (see schema below)
        
    Raises:
        ValueError: If forecast_value is zero or negative
        ValueError: If metric_type not in ["higher_better", "lower_better"]
        TypeError: If current_value or forecast_value not numeric
    """
```

---

## Return Schema

```python
{
    "direction": str,          # "↗" | "→" | "↘" (Unicode arrows)
    "deviation_percent": float, # Percentage difference from forecast
    "status_text": str,        # Human-readable status
    "color_class": str,        # CSS class for styling
    "is_good": bool            # Directional interpretation
}
```

---

## Examples

### Example 1: Higher Better - Above Forecast (Good)

```python
from data.metrics_calculator import calculate_trend_vs_forecast

# Flow Velocity: current 15, forecast 13
result = calculate_trend_vs_forecast(
    current_value=15.0,
    forecast_value=13.0,
    metric_type="higher_better"
)
```

**Expected Output**:
```python
{
    "direction": "↗",
    "deviation_percent": 15.4,  # ((15-13)/13 * 100)
    "status_text": "+15% above forecast",
    "color_class": "text-success",
    "is_good": True
}
```

**Calculation**: `(15 - 13) / 13 * 100 = 15.4%`  
**Interpretation**: Above forecast for velocity is good → green

---

### Example 2: Higher Better - Below Forecast (Bad)

```python
# Flow Velocity: current 5, forecast 13
result = calculate_trend_vs_forecast(
    current_value=5.0,
    forecast_value=13.0,
    metric_type="higher_better"
)
```

**Expected Output**:
```python
{
    "direction": "↘",
    "deviation_percent": -61.5,  # ((5-13)/13 * 100)
    "status_text": "-62% vs forecast",
    "color_class": "text-danger",
    "is_good": False
}
```

**Calculation**: `(5 - 13) / 13 * 100 = -61.5%`  
**Interpretation**: Below forecast for velocity is bad → red

---

### Example 3: Higher Better - On Track (Neutral)

```python
# Flow Velocity: current 14, forecast 13 (within ±10%)
result = calculate_trend_vs_forecast(
    current_value=14.0,
    forecast_value=13.0,
    metric_type="higher_better"
)
```

**Expected Output**:
```python
{
    "direction": "→",
    "deviation_percent": 7.7,
    "status_text": "On track",
    "color_class": "text-secondary",
    "is_good": True
}
```

**Calculation**: `(14 - 13) / 13 * 100 = 7.7%` (within ±10% threshold)  
**Interpretation**: On track is always good → gray

---

### Example 4: Lower Better - Below Forecast (Good)

```python
# Lead Time: current 2 days, forecast 3 days
result = calculate_trend_vs_forecast(
    current_value=2.0,
    forecast_value=3.0,
    metric_type="lower_better"
)
```

**Expected Output**:
```python
{
    "direction": "↘",
    "deviation_percent": -33.3,
    "status_text": "-33% vs forecast",
    "color_class": "text-success",
    "is_good": True
}
```

**Calculation**: `(2 - 3) / 3 * 100 = -33.3%`  
**Interpretation**: Below forecast for lead time is good → green

---

### Example 5: Lower Better - Above Forecast (Bad)

```python
# Change Failure Rate: current 25%, forecast 15%
result = calculate_trend_vs_forecast(
    current_value=25.0,
    forecast_value=15.0,
    metric_type="lower_better"
)
```

**Expected Output**:
```python
{
    "direction": "↗",
    "deviation_percent": 66.7,
    "status_text": "+67% vs forecast",
    "color_class": "text-danger",
    "is_good": False
}
```

**Calculation**: `(25 - 15) / 15 * 100 = 66.7%`  
**Interpretation**: Above forecast for CFR is bad → red

---

### Example 6: Custom Threshold (±5%)

```python
# Stricter threshold: ±5% instead of ±10%
result = calculate_trend_vs_forecast(
    current_value=14.0,
    forecast_value=13.0,
    metric_type="higher_better",
    threshold=0.05
)
```

**Expected Output**:
```python
{
    "direction": "↗",  # 7.7% exceeds 5% threshold
    "deviation_percent": 7.7,
    "status_text": "+8% above forecast",
    "color_class": "text-success",
    "is_good": True
}
```

---

## Trend Direction Logic

### Deviation Calculation
```python
deviation_percent = ((current_value - forecast_value) / forecast_value) * 100
```

### Direction Determination
```python
if deviation_percent > threshold * 100:
    direction = "↗"  # Rising / Above forecast
elif deviation_percent < -threshold * 100:
    direction = "↘"  # Falling / Below forecast
else:
    direction = "→"  # Neutral / On track
```

### Interpretation Matrix

| Metric Type       | Direction | Deviation | Is Good? | Color Class    | Status Text          |
| ----------------- | --------- | --------- | -------- | -------------- | -------------------- |
| **higher_better** | ↗         | >+10%     | ✅ True   | text-success   | "+X% above forecast" |
| higher_better     | →         | ±10%      | ✅ True   | text-secondary | "On track"           |
| higher_better     | ↘         | <-10%     | ❌ False  | text-danger    | "-X% vs forecast"    |
| **lower_better**  | ↗         | >+10%     | ❌ False  | text-danger    | "+X% vs forecast"    |
| lower_better      | →         | ±10%      | ✅ True   | text-secondary | "On track"           |
| lower_better      | ↘         | <-10%     | ✅ True   | text-success   | "-X% vs forecast"    |

---

## Status Text Formatting Rules

### Positive Deviation
```python
if deviation_percent > threshold * 100:
    status_text = f"+{abs(round(deviation_percent))}% above forecast"
```

### Negative Deviation
```python
if deviation_percent < -threshold * 100:
    status_text = f"-{abs(round(deviation_percent))}% vs forecast"
```

### Neutral (On Track)
```python
if abs(deviation_percent) <= threshold * 100:
    status_text = "On track"
```

**Rounding**: Always round to nearest integer for display (`round(deviation_percent)`)

**Sign Display**:
- Positive: Use "+" prefix and "above forecast"
- Negative: Use "-" prefix and "vs forecast"
- Neutral: No sign, use "On track"

---

## Edge Cases

### Edge Case 1: Zero Current Value (Monday Morning)

```python
# Week just started, no completions yet
result = calculate_trend_vs_forecast(
    current_value=0.0,
    forecast_value=13.0,
    metric_type="higher_better"
)
```

**Expected Output**:
```python
{
    "direction": "↘",
    "deviation_percent": -100.0,
    "status_text": "Week starting...",  # Special case
    "color_class": "text-secondary",
    "is_good": True  # Week starting is not "bad"
}
```

**Special Handling**: When `current_value == 0` and `deviation_percent == -100.0`, use "Week starting..." instead of "-100% vs forecast"

---

### Edge Case 2: Current Equals Forecast

```python
# Exactly at forecast
result = calculate_trend_vs_forecast(
    current_value=13.0,
    forecast_value=13.0,
    metric_type="higher_better"
)
```

**Expected Output**:
```python
{
    "direction": "→",
    "deviation_percent": 0.0,
    "status_text": "On track",
    "color_class": "text-secondary",
    "is_good": True
}
```

---

### Edge Case 3: Very Small Forecast Value

```python
# Forecast is 0.5 items/week (rare but possible)
result = calculate_trend_vs_forecast(
    current_value=1.0,
    forecast_value=0.5,
    metric_type="higher_better"
)
```

**Expected Output**:
```python
{
    "direction": "↗",
    "deviation_percent": 100.0,
    "status_text": "+100% above forecast",
    "color_class": "text-success",
    "is_good": True
}
```

---

### Edge Case 4: Zero Forecast Value (Error)

```python
# Invalid: cannot calculate percentage of zero
result = calculate_trend_vs_forecast(
    current_value=10.0,
    forecast_value=0.0,
    metric_type="higher_better"
)
```

**Expected Behavior**:
```python
raise ValueError("Forecast value cannot be zero (division by zero)")
```

---

### Edge Case 5: Negative Forecast Value (Error)

```python
# Invalid: forecast should never be negative
result = calculate_trend_vs_forecast(
    current_value=10.0,
    forecast_value=-5.0,
    metric_type="higher_better"
)
```

**Expected Behavior**:
```python
raise ValueError("Forecast value cannot be negative: -5.0")
```

---

### Edge Case 6: Invalid Metric Type (Error)

```python
# Invalid metric type
result = calculate_trend_vs_forecast(
    current_value=10.0,
    forecast_value=13.0,
    metric_type="unknown_type"
)
```

**Expected Behavior**:
```python
raise ValueError("metric_type must be 'higher_better' or 'lower_better', got 'unknown_type'")
```

---

## Implementation Requirements

### 1. Input Validation

```python
# Pseudo-code
if not isinstance(current_value, (int, float)):
    raise TypeError("current_value must be numeric")

if not isinstance(forecast_value, (int, float)):
    raise TypeError("forecast_value must be numeric")

if forecast_value == 0:
    raise ValueError("Forecast value cannot be zero (division by zero)")

if forecast_value < 0:
    raise ValueError(f"Forecast value cannot be negative: {forecast_value}")

if metric_type not in ["higher_better", "lower_better"]:
    raise ValueError(f"metric_type must be 'higher_better' or 'lower_better', got '{metric_type}'")
```

### 2. Deviation Calculation

```python
deviation_percent = ((current_value - forecast_value) / forecast_value) * 100
```

### 3. Direction Logic

```python
threshold_percent = threshold * 100

if deviation_percent > threshold_percent:
    direction = "↗"
elif deviation_percent < -threshold_percent:
    direction = "↘"
else:
    direction = "→"
```

### 4. Status Text

```python
# Special case: Monday morning (zero value, -100%)
if current_value == 0 and deviation_percent == -100.0:
    status_text = "Week starting..."
# Neutral
elif abs(deviation_percent) <= threshold_percent:
    status_text = "On track"
# Positive deviation
elif deviation_percent > threshold_percent:
    status_text = f"+{abs(round(deviation_percent))}% above forecast"
# Negative deviation
else:
    status_text = f"-{abs(round(deviation_percent))}% vs forecast"
```

### 5. Color and Interpretation

```python
# Neutral always "on track"
if direction == "→":
    color_class = "text-secondary"
    is_good = True

# Higher better metrics
elif metric_type == "higher_better":
    if direction == "↗":
        color_class = "text-success"
        is_good = True
    else:  # ↘
        color_class = "text-danger"
        is_good = False

# Lower better metrics
elif metric_type == "lower_better":
    if direction == "↘":
        color_class = "text-success"
        is_good = True
    else:  # ↗
        color_class = "text-danger"
        is_good = False
```

### 6. Return Structure

```python
return {
    "direction": direction,
    "deviation_percent": round(deviation_percent, 1),  # 1 decimal precision
    "status_text": status_text,
    "color_class": color_class,
    "is_good": is_good
}
```

---

## Unit Test Requirements

**Test Coverage** (minimum 95%):

1. ✅ Test higher_better above threshold (good)
2. ✅ Test higher_better below threshold (bad)
3. ✅ Test higher_better on track (neutral)
4. ✅ Test lower_better below threshold (good)
5. ✅ Test lower_better above threshold (bad)
6. ✅ Test lower_better on track (neutral)
7. ✅ Test zero current value (Monday morning)
8. ✅ Test current equals forecast
9. ✅ Test custom threshold (±5%)
10. ✅ Test very small forecast value
11. ✅ Test zero forecast value raises ValueError
12. ✅ Test negative forecast value raises ValueError
13. ✅ Test invalid metric_type raises ValueError
14. ✅ Test non-numeric current_value raises TypeError
15. ✅ Test percentage rounding (1 decimal place)

**Test File**: `tests/unit/data/test_metrics_calculator.py::TestCalculateTrendVsForecast`

---

## Metric Type Mapping

**Higher Better Metrics**:
- Flow Velocity (`flow_velocity`)
- Flow Efficiency (`flow_efficiency`)
- Deployment Frequency (`deployment_frequency`)

**Lower Better Metrics**:
- Flow Time (`flow_time`)
- Lead Time for Changes (`lead_time_for_changes`)
- Change Failure Rate (`change_failure_rate`)
- Mean Time to Recovery (`mean_time_to_recovery`)

**Special Case**:
- Flow Load (`flow_load`) - handled separately by `calculate_flow_load_range()`
- Flow Distribution (`flow_distribution`) - uses custom logic (not simple higher/lower)

---

## Performance Requirements

- **Time Complexity**: O(1) - simple arithmetic operations
- **Space Complexity**: O(1) - return dict with fixed fields
- **Execution Time**: <10μs per call

**Benchmark**: 9 metrics × 100 calls = <10ms total overhead

---

## Integration Points

### Called By
- `data/metrics_snapshots.py::save_metrics_snapshot()` - For all metrics
- `callbacks/dora_flow_metrics.py` - For real-time trend display

### Dependencies
- Requires `calculate_forecast()` output as input (`forecast_value`)

### Output Consumed By
- `ui/metric_cards.py::create_metric_card()` - Displays trend in UI
- `data/metrics_snapshots.py` - Stores in `trend_vs_forecast` field

---

## Configuration

**Constants** (defined in `configuration/metrics_config.py`):

```python
FORECAST_TREND_THRESHOLD = 0.10  # ±10% neutral zone
TREND_DECIMAL_PRECISION = 1      # 1 decimal place for percentages

# Metric type classifications
HIGHER_BETTER_METRICS = [
    "flow_velocity",
    "flow_efficiency",
    "deployment_frequency"
]

LOWER_BETTER_METRICS = [
    "flow_time",
    "lead_time_for_changes",
    "change_failure_rate",
    "mean_time_to_recovery"
]
```

---

## Contract Version

**Version**: 1.0.0  
**Date**: November 10, 2025  
**Status**: Proposed (awaiting implementation)  
**Breaking Changes**: N/A (new function)
