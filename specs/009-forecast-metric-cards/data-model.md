# Data Model: Forecast-Based Metric Cards

**Date**: November 10, 2025  
**Feature**: 009-forecast-metric-cards  
**Purpose**: Define data structures for forecast calculation, storage, and display

---

## Entity Definitions

### 1. ForecastData

**Purpose**: Encapsulates calculated forecast value and metadata for a single metric

**Schema**:
```python
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class ForecastData:
    """Forecast calculation result with historical context."""
    
    forecast_value: float
    """Weighted average forecast value (e.g., 13.5 items/week)"""
    
    forecast_range: Optional[dict[str, float]] = None
    """Range bounds for Flow Load only: {"lower": 12.0, "upper": 18.0}"""
    
    historical_values: List[float] = None
    """Last 2-4 weeks used in calculation (oldest to newest)"""
    
    weights_applied: List[float] = None
    """Weights used in calculation (e.g., [0.1, 0.2, 0.3, 0.4])"""
    
    weeks_available: int = 0
    """Actual number of historical weeks used (2-4)"""
    
    confidence: str = "established"
    """Forecast confidence: "building" (<4 weeks) or "established" (≥4 weeks)"""
```

**JSON Representation**:
```json
{
  "forecast_value": 13.5,
  "forecast_range": null,
  "historical_values": [10.0, 12.0, 11.0, 13.0],
  "weights_applied": [0.1, 0.2, 0.3, 0.4],
  "weeks_available": 4,
  "confidence": "established"
}
```

**Validation Rules**:
- `forecast_value >= 0` (cannot forecast negative values)
- `weeks_available in [2, 3, 4]` (minimum 2 required, maximum 4 used)
- `len(historical_values) == weeks_available`
- `len(weights_applied) == weeks_available`
- `sum(weights_applied) == 1.0` (weights must sum to 100%)
- `confidence in ["building", "established"]`
- `forecast_range` only present when metric is "flow_load"
- If `forecast_range` exists: `forecast_range["lower"] < forecast_value < forecast_range["upper"]`

**Usage Examples**:
```python
# Standard 4-week forecast
forecast = ForecastData(
    forecast_value=13.5,
    historical_values=[10.0, 12.0, 11.0, 13.0],
    weights_applied=[0.1, 0.2, 0.3, 0.4],
    weeks_available=4,
    confidence="established"
)

# Building baseline (2 weeks)
forecast = ForecastData(
    forecast_value=11.0,
    historical_values=[10.0, 12.0],
    weights_applied=[0.5, 0.5],
    weeks_available=2,
    confidence="building"
)

# Flow Load with range
forecast = ForecastData(
    forecast_value=15.0,
    forecast_range={"lower": 12.0, "upper": 18.0},
    historical_values=[14.0, 15.0, 13.0, 16.0],
    weights_applied=[0.1, 0.2, 0.3, 0.4],
    weeks_available=4,
    confidence="established"
)
```

---

### 2. TrendIndicator

**Purpose**: Represents comparison between current value and forecast benchmark

**Schema**:
```python
from typing import Literal
from dataclasses import dataclass

@dataclass
class TrendIndicator:
    """Trend analysis comparing current metric to forecast."""
    
    direction: Literal["↗", "→", "↘"]
    """Visual arrow indicator: ↗ rising, → neutral, ↘ falling"""
    
    deviation_percent: float
    """Percentage difference from forecast (e.g., 23.5 for +23.5%)"""
    
    status_text: str
    """Human-readable status: "+23% above forecast", "On track", "-15% vs forecast" """
    
    color_class: str
    """CSS class for styling: "text-success", "text-secondary", "text-danger" """
    
    is_good: bool
    """Whether direction is favorable for this metric type"""
```

**JSON Representation**:
```json
{
  "direction": "↗",
  "deviation_percent": 23.5,
  "status_text": "+23% above forecast",
  "color_class": "text-success",
  "is_good": true
}
```

**Validation Rules**:
- `direction in ["↗", "→", "↘"]` (only these three Unicode arrows)
- `deviation_percent` can be positive or negative
- `color_class in ["text-success", "text-secondary", "text-danger"]`
- `is_good` is boolean (no null values)
- `status_text` must not be empty string

**Interpretation Matrix**:

| Metric Type                                       | Current vs Forecast | Direction | Is Good? | Color Class    |
| ------------------------------------------------- | ------------------- | --------- | -------- | -------------- |
| Higher Better (Velocity, Efficiency, Deploy Freq) | >+10%               | ↗         | ✅ True   | text-success   |
| Higher Better                                     | ±10%                | →         | ⚠️ True   | text-secondary |
| Higher Better                                     | <-10%               | ↘         | ❌ False  | text-danger    |
| Lower Better (Time, CFR, MTTR)                    | >+10%               | ↗         | ❌ False  | text-danger    |
| Lower Better                                      | ±10%                | →         | ⚠️ True   | text-secondary |
| Lower Better                                      | <-10%               | ↘         | ✅ True   | text-success   |
| Flow Load (bidirectional)                         | Above range         | ↗         | ❌ False  | text-warning   |
| Flow Load                                         | Within range        | →         | ✅ True   | text-success   |
| Flow Load                                         | Below range         | ↘         | ⚠️ False  | text-info      |

**Usage Examples**:
```python
# Velocity: current 15, forecast 13 → above forecast is good
trend = TrendIndicator(
    direction="↗",
    deviation_percent=15.4,
    status_text="+15% above forecast",
    color_class="text-success",
    is_good=True
)

# Lead Time: current 5 days, forecast 3 days → above forecast is bad
trend = TrendIndicator(
    direction="↗",
    deviation_percent=66.7,
    status_text="+67% vs forecast",
    color_class="text-danger",
    is_good=False
)

# On track (within ±10%)
trend = TrendIndicator(
    direction="→",
    deviation_percent=5.2,
    status_text="On track",
    color_class="text-secondary",
    is_good=True
)
```

---

### 3. MetricSnapshot (Enhanced)

**Purpose**: Weekly snapshot of all DORA and Flow metrics with forecast context

**Existing Schema** (from `data/metrics_snapshots.py`):
```python
{
  "timestamp": "2025-11-03T00:00:00Z",
  "time_period_days": 7,
  "deployment_frequency": {
    "value": 18.0,
    "unit": "deployments/month",
    "performance_tier": "High",
    "trend_direction": "up",
    "trend_percentage": 15.3
  },
  # ... other DORA metrics ...
  "flow_velocity": {
    "value": 12.0,
    "unit": "items/week",
    "breakdown": {...},
    "trend_direction": "up",
    "trend_percentage": 8.5
  },
  # ... other Flow metrics ...
}
```

**Enhanced Schema** (with forecast fields):
```python
{
  "timestamp": "2025-11-03T00:00:00Z",
  "time_period_days": 7,
  
  # DORA Metrics (each enhanced with forecast)
  "deployment_frequency": {
    "value": 18.0,
    "unit": "deployments/month",
    "performance_tier": "High",
    "trend_direction": "up",      # Existing: vs previous period
    "trend_percentage": 15.3,     # Existing: vs previous period
    
    # NEW FIELDS BELOW
    "forecast": {
      "forecast_value": 13.0,
      "historical_values": [10.0, 12.0, 11.0, 13.0],
      "weights_applied": [0.1, 0.2, 0.3, 0.4],
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "↗",
      "deviation_percent": 38.5,
      "status_text": "+38% above forecast",
      "color_class": "text-success",
      "is_good": true
    }
  },
  
  # Flow Metrics (same enhancement pattern)
  "flow_velocity": {
    "value": 12.0,
    "unit": "items/week",
    "breakdown": {...},
    "trend_direction": "up",
    "trend_percentage": 8.5,
    
    "forecast": {
      "forecast_value": 11.5,
      "historical_values": [10.0, 11.0, 11.0, 12.0],
      "weights_applied": [0.1, 0.2, 0.3, 0.4],
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "→",
      "deviation_percent": 4.3,
      "status_text": "On track",
      "color_class": "text-secondary",
      "is_good": true
    }
  },
  
  # Flow Load (special case: range forecast)
  "flow_load": {
    "value": 22.0,
    "unit": "items",
    "trend_direction": "up",
    "trend_percentage": 47.0,
    
    "forecast": {
      "forecast_value": 15.0,
      "forecast_range": {"lower": 12.0, "upper": 18.0},  # ±20% range
      "historical_values": [14.0, 15.0, 13.0, 16.0],
      "weights_applied": [0.1, 0.2, 0.3, 0.4],
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "↗",
      "deviation_percent": 46.7,
      "status_text": "+47% above normal",
      "color_class": "text-warning",  # Warning for WIP too high
      "is_good": false
    }
  },
  
  # ... remaining metrics follow same pattern ...
}
```

**Backward Compatibility**:
- Legacy snapshots without `forecast` field: Valid, UI shows "N/A" or hides forecast section
- Missing `trend_vs_forecast`: UI only shows existing trend indicator
- Partial forecast data: Validation fails, treated as missing

**Storage Location**: `metrics_snapshots.json` (existing file)

**Migration Strategy**:
- No migration needed for old snapshots
- New snapshots automatically include forecast starting from feature deployment
- Gradual accumulation: 4 weeks after deployment = all forecasts at full confidence

---

## Data Relationships

### Calculation Flow

```
Historical Weeks (from JIRA)
         ↓
[Week W-3, Week W-2, Week W-1, Week W-0]
         ↓
calculate_forecast() → ForecastData
         ↓
Current Week Value (from JIRA)
         ↓
calculate_trend_vs_forecast() → TrendIndicator
         ↓
save_metrics_snapshot() → Enhanced MetricSnapshot
         ↓
metrics_snapshots.json (persistent storage)
         ↓
create_metric_card() → UI Display
```

### State Transitions

**Confidence State Machine**:
```
No Data (0-1 weeks)
    ↓
    [Week 2 data arrives]
    ↓
Building (2-3 weeks) → confidence="building", equal weights
    ↓
    [Week 4 data arrives]
    ↓
Established (4+ weeks) → confidence="established", weighted [0.1,0.2,0.3,0.4]
    ↓
    [Stays in Established, rolling window]
```

**Trend State Machine**:
```
Current Value Input
    ↓
    [Compare to Forecast]
    ↓
    ├─ >+10% → direction="↗", evaluate is_good by metric_type
    ├─ ±10%  → direction="→", is_good=True (on track)
    └─ <-10% → direction="↘", evaluate is_good by metric_type
```

---

## Validation Rules

### Forecast Validation

```python
def validate_forecast_data(forecast: ForecastData) -> bool:
    """Validate ForecastData structure and constraints."""
    
    # Basic type checks
    assert isinstance(forecast.forecast_value, (int, float))
    assert forecast.forecast_value >= 0, "Forecast cannot be negative"
    
    # Week constraints
    assert forecast.weeks_available in [2, 3, 4], "Must have 2-4 weeks"
    assert len(forecast.historical_values) == forecast.weeks_available
    assert len(forecast.weights_applied) == forecast.weeks_available
    
    # Weight validation
    assert abs(sum(forecast.weights_applied) - 1.0) < 0.001, "Weights must sum to 1.0"
    assert all(0 <= w <= 1 for w in forecast.weights_applied), "Weights must be 0-1"
    
    # Confidence validation
    assert forecast.confidence in ["building", "established"]
    if forecast.weeks_available == 4:
        assert forecast.confidence == "established"
    if forecast.weeks_available < 4:
        assert forecast.confidence == "building"
    
    # Range validation (Flow Load only)
    if forecast.forecast_range is not None:
        assert "lower" in forecast.forecast_range
        assert "upper" in forecast.forecast_range
        assert forecast.forecast_range["lower"] < forecast.forecast_value
        assert forecast.forecast_value < forecast.forecast_range["upper"]
    
    return True
```

### Trend Validation

```python
def validate_trend_indicator(trend: TrendIndicator) -> bool:
    """Validate TrendIndicator structure and constraints."""
    
    # Arrow validation
    assert trend.direction in ["↗", "→", "↘"], f"Invalid direction: {trend.direction}"
    
    # Percentage can be any float (positive or negative)
    assert isinstance(trend.deviation_percent, (int, float))
    
    # Status text must not be empty
    assert len(trend.status_text) > 0, "Status text cannot be empty"
    
    # Color class validation
    valid_colors = ["text-success", "text-secondary", "text-danger", "text-warning", "text-info"]
    assert trend.color_class in valid_colors, f"Invalid color: {trend.color_class}"
    
    # Boolean check
    assert isinstance(trend.is_good, bool)
    
    return True
```

### Snapshot Validation

```python
def validate_metric_snapshot_enhancement(snapshot: dict) -> bool:
    """Validate that snapshot has correct forecast structure."""
    
    # Check all 9 metrics have forecast fields (if present)
    metric_keys = [
        "deployment_frequency", "lead_time_for_changes", 
        "change_failure_rate", "mean_time_to_recovery",
        "flow_velocity", "flow_time", "flow_efficiency", 
        "flow_load", "flow_distribution"
    ]
    
    for metric_key in metric_keys:
        if metric_key not in snapshot:
            continue  # Metric might not be calculated yet
        
        metric = snapshot[metric_key]
        
        # If forecast exists, validate it
        if "forecast" in metric:
            validate_forecast_data(ForecastData(**metric["forecast"]))
        
        # If trend_vs_forecast exists, validate it
        if "trend_vs_forecast" in metric:
            validate_trend_indicator(TrendIndicator(**metric["trend_vs_forecast"]))
        
        # Both should be present together or both absent
        has_forecast = "forecast" in metric
        has_trend = "trend_vs_forecast" in metric
        assert has_forecast == has_trend, f"{metric_key}: forecast and trend must both be present or absent"
    
    return True
```

---

## Example Data Scenarios

### Scenario 1: Current Week (Monday, No Completions)

```json
{
  "timestamp": "2025-11-10T00:00:00Z",
  "flow_velocity": {
    "value": 0,
    "unit": "items completed this week",
    "trend_direction": "stable",
    "trend_percentage": 0.0,
    
    "forecast": {
      "forecast_value": 13.0,
      "historical_values": [10.0, 12.0, 11.0, 13.0],
      "weights_applied": [0.1, 0.2, 0.3, 0.4],
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "→",
      "deviation_percent": -100.0,
      "status_text": "Week starting...",
      "color_class": "text-secondary",
      "is_good": true
    }
  }
}
```

**UI Display**:
```
Flow Velocity          [Last Week Badge]
0 items completed this week
↘ -100% vs prev avg

Forecast: ~13 items/week
→ Week starting...
```

### Scenario 2: Mid-Week (Wednesday, Behind Forecast)

```json
{
  "timestamp": "2025-11-10T00:00:00Z",
  "flow_velocity": {
    "value": 5.0,
    "unit": "items completed this week",
    "trend_direction": "down",
    "trend_percentage": -62.0,
    
    "forecast": {
      "forecast_value": 13.0,
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "↘",
      "deviation_percent": -61.5,
      "status_text": "-62% vs forecast",
      "color_class": "text-danger",
      "is_good": false
    }
  }
}
```

**UI Display**:
```
Flow Velocity          [Last Week Badge]
5 items completed this week
↘ -62% vs prev avg

Forecast: ~13 items/week
↘ -62% vs forecast
```

### Scenario 3: Completed Week (Above Forecast)

```json
{
  "timestamp": "2025-11-03T00:00:00Z",
  "flow_velocity": {
    "value": 18.0,
    "unit": "items/week",
    "trend_direction": "up",
    "trend_percentage": 38.0,
    
    "forecast": {
      "forecast_value": 13.0,
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "↗",
      "deviation_percent": 38.5,
      "status_text": "+38% above forecast",
      "color_class": "text-success",
      "is_good": true
    }
  }
}
```

**UI Display**:
```
Flow Velocity          [Elite Badge]
18 items/week
↗ +38% vs prev avg

Forecast: ~13 items/week
↗ +38% above forecast
```

### Scenario 4: Building Baseline (Week 2)

```json
{
  "timestamp": "2025-11-10T00:00:00Z",
  "flow_velocity": {
    "value": 12.0,
    "unit": "items/week",
    
    "forecast": {
      "forecast_value": 11.0,
      "historical_values": [10.0, 12.0],
      "weights_applied": [0.5, 0.5],
      "weeks_available": 2,
      "confidence": "building"
    },
    "trend_vs_forecast": {
      "direction": "→",
      "deviation_percent": 9.1,
      "status_text": "On track",
      "color_class": "text-secondary",
      "is_good": true
    }
  }
}
```

**UI Display**:
```
Flow Velocity          [Medium Badge]
12 items/week
(no previous trend - only 2 weeks)

Forecast: ~11 items (based on 2 weeks)
🆕 Building baseline...
→ On track
```

### Scenario 5: Flow Load (WIP Too High)

```json
{
  "timestamp": "2025-11-10T00:00:00Z",
  "flow_load": {
    "value": 24.0,
    "unit": "items work in progress",
    "trend_direction": "up",
    "trend_percentage": 60.0,
    
    "forecast": {
      "forecast_value": 15.0,
      "forecast_range": {"lower": 12.0, "upper": 18.0},
      "weeks_available": 4,
      "confidence": "established"
    },
    "trend_vs_forecast": {
      "direction": "↗",
      "deviation_percent": 60.0,
      "status_text": "+60% above normal",
      "color_class": "text-warning",
      "is_good": false
    }
  }
}
```

**UI Display**:
```
Flow Load (WIP)        [Warning Badge]
24 items work in progress
↗ +60% vs prev avg

Forecast: ~15 items (12-18)
↗ +60% above normal ⚠️
```

---

## Data Model Summary

**Total New Entities**: 2 (ForecastData, TrendIndicator)
**Enhanced Entities**: 1 (MetricSnapshot)
**Storage Impact**: +~4.5KB per snapshot (minimal)
**Validation Functions**: 3 (forecast, trend, snapshot)
**Backward Compatibility**: ✅ Full (legacy snapshots remain valid)

**Next Phase**: API Contracts (`contracts/` directory)
