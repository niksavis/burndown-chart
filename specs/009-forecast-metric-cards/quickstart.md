# Quickstart: Implementing Forecast-Based Metric Cards

**Feature**: 009-forecast-metric-cards  
**Estimated Time**: ~2 hours  
**Prerequisites**: Branch `009-forecast-metric-cards`, Python 3.13 venv activated

---

## Overview

This guide walks you through implementing 4-week weighted forecast benchmarks for all Flow and DORA metric cards. You'll add forecast calculation logic, enhance metric snapshots, update UI components, and wire callbacks.

**What You'll Build**:
- ✅ Forecast calculator with 3 functions
- ✅ Unit tests with >95% coverage
- ✅ Enhanced metric snapshots with forecast data
- ✅ Updated metric cards showing forecast + trend
- ✅ Integration with existing DORA/Flow callbacks

---

## Step 1: Create Forecast Calculator (15 min)

### 1.1 Create Module

```powershell
# Create new file
New-Item -Path "data\metrics_calculator.py" -ItemType File
```

### 1.2 Implement Functions

**File**: `data/metrics_calculator.py`

```python
"""Forecast calculation for metric cards with trend indicators."""

from typing import List, Optional, Dict, Any, Literal


def calculate_forecast(
    historical_values: List[float],
    weights: Optional[List[float]] = None,
    min_weeks: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Calculate 4-week weighted forecast from historical data.
    
    See contracts/forecast-calculator.md for full specification.
    """
    # Input validation
    if not isinstance(historical_values, list):
        raise TypeError("historical_values must be a list")
    
    if any(not isinstance(v, (int, float)) for v in historical_values):
        raise TypeError("All historical values must be numbers")
    
    if any(v < 0 for v in historical_values):
        raise ValueError(f"Historical values cannot be negative: {min(historical_values)}")
    
    # Check minimum data requirement
    if len(historical_values) < min_weeks:
        return None  # Insufficient data
    
    # Determine weights
    if weights is None:
        if len(historical_values) == 4:
            weights = [0.1, 0.2, 0.3, 0.4]
            confidence = "established"
        else:
            # Equal weights for 2-3 weeks
            equal_weight = 1.0 / len(historical_values)
            weights = [equal_weight] * len(historical_values)
            confidence = "building"
    else:
        # Validate custom weights
        if len(weights) != len(historical_values):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"historical_values length ({len(historical_values)})"
            )
        if abs(sum(weights) - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0 (got {sum(weights)})")
        
        confidence = "established" if len(historical_values) == 4 else "building"
    
    # Calculate weighted forecast
    forecast_value = sum(v * w for v, w in zip(historical_values, weights))
    
    return {
        "forecast_value": round(forecast_value, 2),
        "forecast_range": None,  # Set by caller for Flow Load
        "historical_values": historical_values.copy(),
        "weights_applied": weights.copy(),
        "weeks_available": len(historical_values),
        "confidence": confidence
    }


def calculate_trend_vs_forecast(
    current_value: float,
    forecast_value: float,
    metric_type: Literal["higher_better", "lower_better"],
    threshold: float = 0.10
) -> Dict[str, Any]:
    """
    Calculate trend indicator comparing current metric to forecast.
    
    See contracts/trend-indicator.md for full specification.
    """
    # Input validation
    if not isinstance(current_value, (int, float)):
        raise TypeError("current_value must be numeric")
    
    if not isinstance(forecast_value, (int, float)):
        raise TypeError("forecast_value must be numeric")
    
    if forecast_value == 0:
        raise ValueError("Forecast value cannot be zero (division by zero)")
    
    if forecast_value < 0:
        raise ValueError(f"Forecast value cannot be negative: {forecast_value}")
    
    if metric_type not in ["higher_better", "lower_better"]:
        raise ValueError(
            f"metric_type must be 'higher_better' or 'lower_better', "
            f"got '{metric_type}'"
        )
    
    # Calculate deviation
    deviation_percent = ((current_value - forecast_value) / forecast_value) * 100
    threshold_percent = threshold * 100
    
    # Determine direction
    if deviation_percent > threshold_percent:
        direction = "↗"
    elif deviation_percent < -threshold_percent:
        direction = "↘"
    else:
        direction = "→"
    
    # Special case: Monday morning (zero value)
    if current_value == 0 and deviation_percent == -100.0:
        status_text = "Week starting..."
        color_class = "text-secondary"
        is_good = True
    
    # Neutral (on track)
    elif direction == "→":
        status_text = "On track"
        color_class = "text-secondary"
        is_good = True
    
    # Positive deviation
    elif deviation_percent > threshold_percent:
        status_text = f"+{abs(round(deviation_percent))}% above forecast"
        
        if metric_type == "higher_better":
            color_class = "text-success"
            is_good = True
        else:  # lower_better
            color_class = "text-danger"
            is_good = False
    
    # Negative deviation
    else:  # deviation_percent < -threshold_percent
        status_text = f"-{abs(round(deviation_percent))}% vs forecast"
        
        if metric_type == "lower_better":
            color_class = "text-success"
            is_good = True
        else:  # higher_better
            color_class = "text-danger"
            is_good = False
    
    return {
        "direction": direction,
        "deviation_percent": round(deviation_percent, 1),
        "status_text": status_text,
        "color_class": color_class,
        "is_good": is_good
    }


def calculate_flow_load_range(
    forecast_value: float,
    range_percent: float = 0.20
) -> Dict[str, float]:
    """
    Calculate acceptable WIP range for Flow Load metric.
    
    See contracts/flow-load-range.md for full specification.
    """
    # Input validation
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
    
    # Calculate bounds
    lower_bound = forecast_value * (1 - range_percent)
    upper_bound = forecast_value * (1 + range_percent)
    
    # Clamp lower bound to 0 (WIP cannot be negative)
    if lower_bound < 0:
        lower_bound = 0.0
    
    return {
        "lower": round(lower_bound, 1),
        "upper": round(upper_bound, 1)
    }
```

### 1.3 Add Configuration Constants

**File**: `configuration/metrics_config.py` (create if doesn't exist)

```python
"""Configuration constants for metrics calculations."""

# Forecast weights (oldest to newest week)
FORECAST_WEIGHTS_4_WEEK = [0.1, 0.2, 0.3, 0.4]

# Minimum weeks required for forecast
FORECAST_MIN_WEEKS = 2

# Decimal precision for forecast values
FORECAST_DECIMAL_PRECISION = 2

# Trend threshold (±10% neutral zone)
FORECAST_TREND_THRESHOLD = 0.10

# Flow Load range deviation (±20%)
FLOW_LOAD_RANGE_PERCENT = 0.20

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

### 1.4 Verify Implementation

```powershell
.\.venv\Scripts\activate; python -c "from data.metrics_calculator import calculate_forecast; print(calculate_forecast([10, 12, 11, 13]))"
```

**Expected Output**:
```python
{'forecast_value': 11.9, 'forecast_range': None, 'historical_values': [10, 12, 11, 13], 'weights_applied': [0.1, 0.2, 0.3, 0.4], 'weeks_available': 4, 'confidence': 'established'}
```

---

## Step 2: Write Unit Tests (30 min)

### 2.1 Create Test File

```powershell
New-Item -Path "tests\unit\data\test_metrics_calculator.py" -ItemType File
```

### 2.2 Implement Tests

**File**: `tests/unit/data/test_metrics_calculator.py`

```python
"""Unit tests for forecast calculation functions."""

import pytest
from data.metrics_calculator import (
    calculate_forecast,
    calculate_trend_vs_forecast,
    calculate_flow_load_range
)


class TestCalculateForecast:
    """Tests for calculate_forecast function."""
    
    def test_standard_4_week_forecast(self):
        """Test standard 4-week forecast with default weights."""
        result = calculate_forecast([10.0, 12.0, 11.0, 13.0])
        
        assert result is not None
        assert result["forecast_value"] == 11.9
        assert result["weeks_available"] == 4
        assert result["confidence"] == "established"
        assert result["weights_applied"] == [0.1, 0.2, 0.3, 0.4]
    
    def test_building_baseline_2_weeks(self):
        """Test 2-week forecast with equal weights."""
        result = calculate_forecast([10.0, 12.0])
        
        assert result is not None
        assert result["forecast_value"] == 11.0
        assert result["weeks_available"] == 2
        assert result["confidence"] == "building"
        assert result["weights_applied"] == [0.5, 0.5]
    
    def test_building_baseline_3_weeks(self):
        """Test 3-week forecast with equal weights."""
        result = calculate_forecast([10.0, 11.0, 12.0])
        
        assert result is not None
        assert abs(result["forecast_value"] - 11.0) < 0.01
        assert result["weeks_available"] == 3
        assert result["confidence"] == "building"
    
    def test_insufficient_data_1_week(self):
        """Test that 1 week returns None."""
        result = calculate_forecast([10.0])
        assert result is None
    
    def test_insufficient_data_empty(self):
        """Test that empty list returns None."""
        result = calculate_forecast([])
        assert result is None
    
    def test_zero_values_in_history(self):
        """Test forecast with zero values (holiday weeks)."""
        result = calculate_forecast([10.0, 0.0, 11.0, 13.0])
        
        assert result is not None
        assert result["forecast_value"] == 8.5
    
    def test_all_zeros(self):
        """Test forecast with all zero values."""
        result = calculate_forecast([0.0, 0.0, 0.0, 0.0])
        
        assert result is not None
        assert result["forecast_value"] == 0.0
    
    def test_negative_values_raise_error(self):
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_forecast([10.0, 12.0, -5.0, 13.0])
    
    def test_non_numeric_values_raise_error(self):
        """Test that non-numeric values raise TypeError."""
        with pytest.raises(TypeError, match="must be numbers"):
            calculate_forecast([10.0, "12", 11.0, 13.0])
    
    def test_custom_weights_valid(self):
        """Test forecast with custom weights."""
        result = calculate_forecast(
            [10.0, 11.0, 12.0],
            weights=[0.33, 0.33, 0.34]
        )
        
        assert result is not None
        assert result["weights_applied"] == [0.33, 0.33, 0.34]
    
    def test_custom_weights_length_mismatch(self):
        """Test that weight length mismatch raises ValueError."""
        with pytest.raises(ValueError, match="must match"):
            calculate_forecast([10.0, 12.0, 11.0, 13.0], weights=[0.5, 0.5])
    
    def test_custom_weights_sum_not_one(self):
        """Test that weights not summing to 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            calculate_forecast([10.0, 12.0], weights=[0.4, 0.5])


class TestCalculateTrendVsForecast:
    """Tests for calculate_trend_vs_forecast function."""
    
    def test_higher_better_above_threshold(self):
        """Test higher_better metric above forecast (good)."""
        result = calculate_trend_vs_forecast(15.0, 13.0, "higher_better")
        
        assert result["direction"] == "↗"
        assert result["deviation_percent"] == 15.4
        assert result["status_text"] == "+15% above forecast"
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True
    
    def test_higher_better_below_threshold(self):
        """Test higher_better metric below forecast (bad)."""
        result = calculate_trend_vs_forecast(5.0, 13.0, "higher_better")
        
        assert result["direction"] == "↘"
        assert abs(result["deviation_percent"] - (-61.5)) < 0.1
        assert "-62% vs forecast" in result["status_text"]
        assert result["color_class"] == "text-danger"
        assert result["is_good"] is False
    
    def test_higher_better_on_track(self):
        """Test higher_better metric on track (neutral)."""
        result = calculate_trend_vs_forecast(14.0, 13.0, "higher_better")
        
        assert result["direction"] == "→"
        assert result["status_text"] == "On track"
        assert result["color_class"] == "text-secondary"
        assert result["is_good"] is True
    
    def test_lower_better_below_threshold(self):
        """Test lower_better metric below forecast (good)."""
        result = calculate_trend_vs_forecast(2.0, 3.0, "lower_better")
        
        assert result["direction"] == "↘"
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True
    
    def test_lower_better_above_threshold(self):
        """Test lower_better metric above forecast (bad)."""
        result = calculate_trend_vs_forecast(25.0, 15.0, "lower_better")
        
        assert result["direction"] == "↗"
        assert result["color_class"] == "text-danger"
        assert result["is_good"] is False
    
    def test_zero_current_value_monday(self):
        """Test Monday morning with zero completions."""
        result = calculate_trend_vs_forecast(0.0, 13.0, "higher_better")
        
        assert result["status_text"] == "Week starting..."
        assert result["color_class"] == "text-secondary"
        assert result["is_good"] is True
    
    def test_current_equals_forecast(self):
        """Test current value exactly at forecast."""
        result = calculate_trend_vs_forecast(13.0, 13.0, "higher_better")
        
        assert result["direction"] == "→"
        assert result["deviation_percent"] == 0.0
        assert result["status_text"] == "On track"
    
    def test_custom_threshold(self):
        """Test custom threshold (±5%)."""
        result = calculate_trend_vs_forecast(
            14.0, 13.0, "higher_better", threshold=0.05
        )
        
        assert result["direction"] == "↗"  # 7.7% exceeds 5% threshold
    
    def test_zero_forecast_raises_error(self):
        """Test that zero forecast raises ValueError."""
        with pytest.raises(ValueError, match="cannot be zero"):
            calculate_trend_vs_forecast(10.0, 0.0, "higher_better")
    
    def test_negative_forecast_raises_error(self):
        """Test that negative forecast raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_trend_vs_forecast(10.0, -5.0, "higher_better")
    
    def test_invalid_metric_type_raises_error(self):
        """Test that invalid metric_type raises ValueError."""
        with pytest.raises(ValueError, match="must be"):
            calculate_trend_vs_forecast(10.0, 13.0, "unknown_type")


class TestCalculateFlowLoadRange:
    """Tests for calculate_flow_load_range function."""
    
    def test_standard_range_calculation(self):
        """Test standard ±20% range."""
        result = calculate_flow_load_range(15.0)
        
        assert result["lower"] == 12.0
        assert result["upper"] == 18.0
    
    def test_custom_range_30_percent(self):
        """Test custom ±30% range."""
        result = calculate_flow_load_range(15.0, range_percent=0.30)
        
        assert result["lower"] == 10.5
        assert result["upper"] == 19.5
    
    def test_small_forecast_value(self):
        """Test range with small forecast value."""
        result = calculate_flow_load_range(3.0)
        
        assert result["lower"] == 2.4
        assert result["upper"] == 3.6
    
    def test_zero_forecast_raises_error(self):
        """Test that zero forecast raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_flow_load_range(0.0)
    
    def test_negative_forecast_raises_error(self):
        """Test that negative forecast raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_flow_load_range(-5.0)
    
    def test_negative_range_percent_raises_error(self):
        """Test that negative range_percent raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_flow_load_range(15.0, range_percent=-0.2)
    
    def test_range_percent_over_one_raises_error(self):
        """Test that range_percent > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0 and 1.0"):
            calculate_flow_load_range(15.0, range_percent=1.5)
```

### 2.3 Run Tests

```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_metrics_calculator.py -v
```

**Expected**: All tests pass with >95% coverage.

---

## Step 3: Enhance Metric Snapshots (20 min)

### 3.1 Modify Snapshot Function

**File**: `data/metrics_snapshots.py`

**Find** the `save_metrics_snapshot()` function and add forecast calculation logic.

**Pseudo-code for modification**:
```python
from data.metrics_calculator import (
    calculate_forecast,
    calculate_trend_vs_forecast,
    calculate_flow_load_range
)
from configuration.metrics_config import (
    HIGHER_BETTER_METRICS,
    LOWER_BETTER_METRICS
)

def save_metrics_snapshot(...):
    # ... existing code ...
    
    # For each metric, calculate forecast
    for metric_key in ["deployment_frequency", "flow_velocity", ...]:
        metric_data = snapshot[metric_key]
        
        # Get last 4 weeks of this metric from previous snapshots
        historical_values = get_last_4_weeks_values(metric_key)
        
        # Calculate forecast
        forecast = calculate_forecast(historical_values)
        
        if forecast:
            # Add Flow Load range if applicable
            if metric_key == "flow_load":
                forecast["forecast_range"] = calculate_flow_load_range(
                    forecast["forecast_value"]
                )
            
            # Calculate trend vs forecast
            metric_type = (
                "higher_better" if metric_key in HIGHER_BETTER_METRICS
                else "lower_better"
            )
            
            trend = calculate_trend_vs_forecast(
                current_value=metric_data["value"],
                forecast_value=forecast["forecast_value"],
                metric_type=metric_type
            )
            
            # Add to snapshot
            metric_data["forecast"] = forecast
            metric_data["trend_vs_forecast"] = trend
```

### 3.2 Verify Snapshot Schema

```powershell
# Run app and trigger snapshot save
.\.venv\Scripts\activate; python app.py

# In browser: Change time period to trigger snapshot
# Check metrics_snapshots.json for forecast fields
```

---

## Step 4: Update Metric Cards UI (25 min)

### 4.1 Modify Card Component

**File**: `ui/metric_cards.py`

Find `create_metric_card()` function and add forecast display section.

**Add after existing trend indicator**:
```python
def create_metric_card(..., forecast_data=None, trend_vs_forecast=None):
    # ... existing code ...
    
    card_body_children = [
        html.H2(metric_value),
        html.P(metric_unit, className="text-muted"),
        existing_trend_indicator
    ]
    
    # NEW: Add forecast section
    if forecast_data and trend_vs_forecast:
        forecast_section = create_forecast_section(
            forecast_data, trend_vs_forecast, metric_unit, metric_key
        )
        card_body_children.append(forecast_section)
    
    # ... rest of function ...

def create_forecast_section(forecast_data, trend_vs_forecast, unit, metric_key):
    """Create forecast display section for metric card."""
    
    # Format forecast text
    forecast_value = forecast_data["forecast_value"]
    
    if metric_key == "flow_load" and forecast_data.get("forecast_range"):
        # Flow Load: show range
        lower = round(forecast_data["forecast_range"]["lower"])
        upper = round(forecast_data["forecast_range"]["upper"])
        forecast_text = f"Forecast: ~{round(forecast_value)} items ({lower}-{upper})"
    else:
        # Other metrics: show point estimate
        forecast_text = f"Forecast: ~{round(forecast_value)} {unit}"
    
    # Add "building baseline" note if <4 weeks
    if forecast_data["confidence"] == "building":
        forecast_text += f" (based on {forecast_data['weeks_available']} weeks)"
    
    return html.Div([
        html.P(
            forecast_text,
            className="text-muted small mb-1"
        ),
        html.P(
            [
                html.Span(trend_vs_forecast["direction"] + " "),
                html.Span(trend_vs_forecast["status_text"])
            ],
            className=f"{trend_vs_forecast['color_class']} small mb-2"
        ),
        # Show "building baseline" badge if applicable
        html.P(
            "🆕 Building baseline...",
            className="text-muted small mb-0"
        ) if forecast_data["confidence"] == "building" else None
    ], className="mt-2")
```

---

## Step 5: Update Callbacks (15 min)

### 5.1 Modify DORA Metrics Callback

**File**: `callbacks/dora_flow_metrics.py`

```python
from data.metrics_calculator import calculate_forecast, calculate_trend_vs_forecast

@callback(...)
def update_dora_metrics(...):
    # ... existing metric calculation ...
    
    # Get historical weeks for forecast
    historical_values = get_last_4_weeks_for_metric("deployment_frequency")
    
    # Calculate forecast
    forecast = calculate_forecast(historical_values)
    
    # Calculate trend vs forecast
    if forecast:
        trend = calculate_trend_vs_forecast(
            current_value=deployment_freq_value,
            forecast_value=forecast["forecast_value"],
            metric_type="higher_better"
        )
    else:
        forecast, trend = None, None
    
    # Pass to UI component
    deployment_freq_card = create_metric_card(
        ...,
        forecast_data=forecast,
        trend_vs_forecast=trend
    )
```

### 5.2 Modify Flow Metrics Callback

Similar pattern for Flow metrics in same file.

---

## Step 6: Integration Testing (20 min)

### 6.1 Create Integration Test

**File**: `tests/integration/test_metric_cards_with_forecast.py`

```python
"""Integration tests for metric cards with forecast display."""

import pytest
from playwright.sync_api import sync_playwright


def test_current_week_shows_forecast(live_server):
    """Test that current week cards display forecast benchmarks."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(live_server)
        page.wait_for_selector("#flow-velocity-card")
        
        # Verify forecast text is visible
        forecast_text = page.locator("text=Forecast:")
        assert forecast_text.is_visible()
        
        browser.close()
```

### 6.2 Run Integration Tests

```powershell
.\.venv\Scripts\activate; pytest tests/integration/test_metric_cards_with_forecast.py -v
```

---

## Verification Checklist

✅ **Unit Tests**:
- All `test_metrics_calculator.py` tests pass
- Coverage >95% for `data/metrics_calculator.py`

✅ **Data Persistence**:
- `metrics_snapshots.json` contains `forecast` and `trend_vs_forecast` fields
- Legacy snapshots without forecast fields don't cause errors

✅ **UI Display**:
- All 9 metric cards show forecast below current value
- Flow Load shows range format "~15 items (12-18)"
- Trend arrows (↗ → ↘) display correctly
- "Building baseline" message appears when <4 weeks data

✅ **Mobile Responsive**:
- Cards render correctly on 320px viewport
- Text wraps gracefully, no horizontal scroll

✅ **Performance**:
- Dashboard loads in <2 seconds
- No noticeable delay from forecast calculations

---

## Troubleshooting

### Issue: Tests fail with "Module not found"
**Solution**: Ensure venv is activated before running tests

### Issue: Forecast not showing in UI
**Solution**: Check browser console for errors, verify forecast data in snapshot JSON

### Issue: Trend arrows not displaying
**Solution**: Ensure Unicode arrow characters (↗ → ↘) are supported, check CSS styling

### Issue: Mobile layout broken
**Solution**: Test on actual mobile device or use browser DevTools mobile emulation

---

## Next Steps

1. **Run full test suite**: `.\.venv\Scripts\activate; pytest tests/ -v`
2. **Manual QA**: Test all 9 metrics with various data scenarios
3. **Performance profiling**: Verify <50ms overhead per dashboard load
4. **Documentation**: Update user help content to explain forecast feature
5. **Merge to main**: Create PR with implementation

---

## Estimated Time Breakdown

| Step      | Task                       | Time         |
| --------- | -------------------------- | ------------ |
| 1         | Create forecast calculator | 15 min       |
| 2         | Write unit tests           | 30 min       |
| 3         | Enhance metric snapshots   | 20 min       |
| 4         | Update metric cards UI     | 25 min       |
| 5         | Update callbacks           | 15 min       |
| 6         | Integration testing        | 20 min       |
| **Total** |                            | **~2 hours** |

---

**Ready to implement!** Follow each step in sequence, committing after each major milestone.
