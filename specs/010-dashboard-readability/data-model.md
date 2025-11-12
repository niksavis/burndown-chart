# Data Model: Dashboard Readability & Test Coverage

**Feature**: 010-dashboard-readability  
**Date**: 2025-11-12  
**Status**: Complete

## Overview

This document defines the data structures used by the Project Dashboard for metrics calculation, UI rendering, and test validation. All structures already exist in the codebase - this documentation formalizes them for test contract development.

## Core Data Structures

### 1. StatisticsDataPoint

**Purpose**: Represents a single data point in the project's historical statistics

**Location**: Input to `data/processing.py::calculate_dashboard_metrics()`

**Schema**:
```python
{
    "date": str,                  # ISO 8601 date (YYYY-MM-DD)
    "completed_items": int,       # Number of items completed on this date
    "completed_points": float,    # Number of story points completed on this date
    "created_items": int,         # Optional: New items added on this date
    "created_points": float       # Optional: New points added on this date
}
```

**Example**:
```python
{
    "date": "2025-01-15",
    "completed_items": 7,
    "completed_points": 35.0,
    "created_items": 2,
    "created_points": 10.0
}
```

**Validation Rules**:
- `date` MUST be valid ISO 8601 format
- `completed_items` MUST be non-negative integer
- `completed_points` MUST be non-negative float
- `created_items` and `created_points` are OPTIONAL (default to 0)

**Relationships**:
- Multiple StatisticsDataPoint instances form a time series
- Typically sorted chronologically for calculations
- Used as input array to all dashboard calculation functions

---

### 2. DashboardSettings

**Purpose**: Configuration parameters for dashboard calculations

**Location**: Loaded from `app_settings.json`, passed to calculation functions

**Schema**:
```python
{
    "pert_factor": float,              # PERT confidence window (default: 1.5)
    "deadline": str | None,            # ISO 8601 date or None
    "estimated_total_items": int,      # Total scope in items
    "estimated_total_points": float,   # Total scope in points
    "data_points_count": int,          # Number of recent weeks to analyze (default: 10)
    "forecast_max_days": int,          # Maximum forecast horizon (default: 730)
    "pessimistic_multiplier_cap": int  # Cap for pessimistic forecast (default: 5)
}
```

**Example**:
```python
{
    "pert_factor": 1.5,
    "deadline": "2025-12-31",
    "estimated_total_items": 100,
    "estimated_total_points": 500.0,
    "data_points_count": 10,
    "forecast_max_days": 730,
    "pessimistic_multiplier_cap": 5
}
```

**Validation Rules**:
- `pert_factor` MUST be positive (typically 1.0 - 3.0)
- `deadline` MUST be valid ISO 8601 or None
- `estimated_total_items` MUST be non-negative
- `estimated_total_points` MUST be non-negative
- `data_points_count` MUST be positive integer (default: 10)
- `forecast_max_days` MUST be positive integer ≤ 3653 (10 years)
- `pessimistic_multiplier_cap` MUST be positive integer (default: 5)

---

### 3. DashboardMetrics

**Purpose**: Aggregated project health metrics calculated from statistics and settings

**Location**: Output of `data/processing.py::calculate_dashboard_metrics()`

**Schema**:
```python
{
    "completion_forecast_date": str | None,  # ISO 8601 date or None
    "completion_confidence": float | None,   # Percentage (0-100) or None
    "days_to_completion": int | None,        # Days or None
    "days_to_deadline": int | None,          # Days or None (can be negative)
    "completion_percentage": float,          # Percentage (0-100+)
    "remaining_items": int,                  # Non-negative integer
    "remaining_points": float,               # Non-negative float
    "current_velocity_items": float,         # Items per week
    "current_velocity_points": float,        # Points per week
    "velocity_trend": str,                   # "increasing" | "stable" | "decreasing" | "unknown"
    "last_updated": str                      # ISO 8601 timestamp
}
```

**Example**:
```python
{
    "completion_forecast_date": "2025-06-15",
    "completion_confidence": 82.5,
    "days_to_completion": 120,
    "days_to_deadline": 200,
    "completion_percentage": 68.5,
    "remaining_items": 32,
    "remaining_points": 160.0,
    "current_velocity_items": 6.5,
    "current_velocity_points": 32.5,
    "velocity_trend": "stable",
    "last_updated": "2025-11-12T10:30:00Z"
}
```

**Validation Rules**:
- `completion_forecast_date` can be None if no forecast possible
- `completion_confidence` MUST be 0-100 if not None
- `days_to_completion` can be None if no forecast possible
- `days_to_deadline` can be negative (past deadline)
- `completion_percentage` can exceed 100% (scope decreased)
- `remaining_items` MUST be ≥ 0
- `remaining_points` MUST be ≥ 0
- `current_velocity_items` MUST be ≥ 0
- `current_velocity_points` MUST be ≥ 0
- `velocity_trend` MUST be one of 4 enum values
- `last_updated` MUST be valid ISO 8601 timestamp

**Calculation Dependencies**:
- Requires StatisticsDataPoint array with at least 1 entry for meaningful results
- Requires DashboardSettings for totals and deadline
- Empty statistics returns safe defaults (zeros, None for dates)

---

### 4. PERTTimelineData

**Purpose**: PERT-based forecast data with optimistic/pessimistic/likely scenarios

**Location**: Output of `data/processing.py::calculate_pert_timeline()`

**Schema**:
```python
{
    "optimistic_date": str | None,       # ISO 8601 date (best case)
    "pessimistic_date": str | None,      # ISO 8601 date (worst case)
    "most_likely_date": str | None,      # ISO 8601 date (expected)
    "pert_estimate_date": str | None,    # ISO 8601 date (weighted average)
    "optimistic_days": int,              # Days to optimistic completion
    "pessimistic_days": int,             # Days to pessimistic completion
    "most_likely_days": int,             # Days to likely completion
    "confidence_range_days": int         # Difference (pessimistic - optimistic)
}
```

**Example**:
```python
{
    "optimistic_date": "2025-05-01",
    "pessimistic_date": "2025-07-15",
    "most_likely_date": "2025-06-01",
    "pert_estimate_date": "2025-06-05",
    "optimistic_days": 90,
    "pessimistic_days": 165,
    "most_likely_days": 120,
    "confidence_range_days": 75
}
```

**Validation Rules**:
- All dates can be None if no forecast possible (zero velocity)
- `optimistic_days` < `most_likely_days` < `pessimistic_days` (if all valid)
- `confidence_range_days` = `pessimistic_days` - `optimistic_days`
- PERT estimate uses formula: `(optimistic + 4*most_likely + pessimistic) / 6`

**Calculation Dependencies**:
- Requires DashboardMetrics with valid velocity data
- Requires remaining work > 0
- Returns all None/zeros if velocity is zero

---

### 5. HealthScore

**Purpose**: Composite project health score with component breakdown

**Location**: Calculated by `ui/dashboard_cards.py::_calculate_health_score()`

**Schema**:
```python
{
    "total_score": int,           # 0-100 (sum of components, capped)
    "color_code": str,            # Hex color (#198754, #0dcaf0, #ffc107, #fd7e14)
    "label_text": str,            # "Excellent" | "Good" | "Fair" | "Needs Attention"
    "progress_score": float,      # 0-25 points
    "schedule_score": float,      # 0-30 points
    "velocity_score": float,      # 0-25 points
    "confidence_score": float     # 0-20 points
}
```

**Example**:
```python
{
    "total_score": 82,
    "color_code": "#198754",
    "label_text": "Excellent",
    "progress_score": 21.5,
    "schedule_score": 28.0,
    "velocity_score": 20.0,
    "confidence_score": 16.5
}
```

**Validation Rules**:
- `total_score` MUST be 0-100 (capped)
- `color_code` MUST match label_text:
  - ≥80: "#198754" (green), "Excellent"
  - ≥60: "#0dcaf0" (cyan), "Good"
  - ≥40: "#ffc107" (yellow), "Fair"
  - <40: "#fd7e14" (orange), "Needs Attention"
- Component scores MUST not exceed their maximums
- Component scores MUST be non-negative

**Calculation Formula**:
```python
# Progress (0-25 points): Based on completion percentage
progress_score = (completion_percentage / 100) * 25

# Schedule (0-30 points): Based on timeline vs deadline ratio
schedule_ratio = days_to_completion / days_to_deadline
if schedule_ratio <= 0.8:  schedule_score = 30  # Ahead
elif schedule_ratio <= 1.0: schedule_score = 25  # On track
elif schedule_ratio <= 1.2: schedule_score = 15  # At risk
else:                        schedule_score = 5   # Behind

# Velocity (0-25 points): Based on trend stability
if velocity_trend == "increasing": velocity_score = 25
elif velocity_trend == "stable":   velocity_score = 20
elif velocity_trend == "decreasing": velocity_score = 10
else:                               velocity_score = 15  # Unknown

# Confidence (0-20 points): Based on forecast confidence
confidence_score = (completion_confidence / 100) * 20

# Total (capped at 100)
total_score = min(100, progress_score + schedule_score + velocity_score + confidence_score)
```

---

### 6. KeyInsight

**Purpose**: Actionable intelligence item for dashboard insights section

**Location**: Generated by `ui/dashboard_cards.py::_create_key_insights()`

**Schema**:
```python
{
    "icon": str,       # FontAwesome class (e.g., "fas fa-check-circle")
    "color": str,      # Bootstrap color name (success, warning, primary, etc.)
    "text": str        # User-facing message
}
```

**Example**:
```python
{
    "icon": "fas fa-check-circle",
    "color": "success",
    "text": "Trending 15 days ahead of deadline"
}
```

**Validation Rules**:
- `icon` MUST be valid FontAwesome class
- `color` MUST be valid Bootstrap color name
- `text` MUST be non-empty human-readable string

**Generation Rules**:
```python
# Schedule Insights
if days_to_deadline and days_to_completion:
    days_diff = days_to_deadline - days_to_completion
    if days_diff > 0:
        insight = {"icon": "fas fa-check-circle", "color": "success", "text": f"Trending {days_diff} days ahead of deadline"}
    elif days_diff < 0:
        insight = {"icon": "fas fa-exclamation-triangle", "color": "warning", "text": f"Trending {abs(days_diff)} days behind deadline"}
    else:
        insight = {"icon": "fas fa-bullseye", "color": "primary", "text": "On track to meet deadline"}

# Velocity Insights
if velocity_trend == "increasing":
    insight = {"icon": "fas fa-arrow-up", "color": "success", "text": "Team velocity is accelerating"}
elif velocity_trend == "decreasing":
    insight = {"icon": "fas fa-arrow-down", "color": "warning", "text": "Team velocity is declining - consider addressing blockers"}

# Progress Insights
if completion_percentage >= 75:
    insight = {"icon": "fas fa-star", "color": "success", "text": "Project is in final stretch - great progress!"}
```

---

### 7. MetricCardData

**Purpose**: Standardized data structure for metric card rendering

**Location**: Input to `ui/metric_cards.py::create_metric_card()`

**Schema**:
```python
{
    "metric_name": str,              # Internal identifier
    "alternative_name": str,         # Display name
    "value": float | int,            # Metric value
    "unit": str,                     # Unit label (e.g., "days", "items/week")
    "performance_tier": str,         # Tier label
    "performance_tier_color": str,   # Tier color (green, blue, yellow, orange)
    "error_state": str,              # "success" | "error" | other
    "total_issue_count": int,        # For DORA/Flow compatibility (0 for dashboard)
    "excluded_issue_count": int,     # For DORA/Flow compatibility (0 for dashboard)
    "details": dict,                 # Additional metric-specific data
    "tooltip": str                   # Help text
}
```

**Example**:
```python
{
    "metric_name": "completion_forecast",
    "alternative_name": "Completion Forecast",
    "value": 120,
    "unit": "days remaining",
    "performance_tier": "On Track",
    "performance_tier_color": "green",
    "error_state": "success",
    "total_issue_count": 0,
    "excluded_issue_count": 0,
    "details": {
        "completion_percentage": 68.5,
        "confidence": 82.5
    },
    "tooltip": "PERT-based estimate of project completion date with confidence level"
}
```

**Validation Rules**:
- `metric_name` MUST be unique identifier (snake_case)
- `alternative_name` MUST be user-friendly display name
- `value` MUST be non-negative (0 allowed)
- `unit` MUST describe the value (not empty)
- `performance_tier` MUST be descriptive label
- `performance_tier_color` MUST be valid Bootstrap/CSS color
- `error_state` MUST be "success" for normal operation
- `details` can contain any metric-specific additional data
- `tooltip` MUST provide user guidance

---

## Test Data Structures

### 8. TestFixtures

**Purpose**: Shared test data for dashboard test suite

**Location**: `tests/utils/dashboard_test_fixtures.py`

**Fixtures**:

#### `sample_statistics_data()`
```python
# 10 weeks of realistic project data
[
    {"date": "2025-01-01", "completed_items": 5, "completed_points": 25},
    {"date": "2025-01-08", "completed_items": 7, "completed_points": 35},
    # ... 8 more weeks
]
```

#### `sample_settings()`
```python
{
    "pert_factor": 1.5,
    "deadline": "2025-12-31",
    "estimated_total_items": 100,
    "estimated_total_points": 500,
    "data_points_count": 10
}
```

#### `empty_statistics_data()`
```python
[]  # New project with no data
```

#### `minimal_statistics_data()`
```python
[{"date": "2025-01-01", "completed_items": 1, "completed_points": 5}]  # Single data point
```

#### `extreme_velocity_data()`
```python
# Very low velocity causing >10 year forecast
[{"date": "2025-01-01", "completed_items": 0.1, "completed_points": 0.5}]
```

---

## Data Flow Diagrams

### Dashboard Metrics Calculation Flow

```
StatisticsDataPoint[] + DashboardSettings
          ↓
data/processing.py::calculate_dashboard_metrics()
          ↓
DashboardMetrics
          ↓
ui/dashboard_cards.py::_calculate_health_score()
          ↓
HealthScore
          ↓
ui/dashboard_cards.py::create_dashboard_*_card()
          ↓
MetricCardData
          ↓
ui/metric_cards.py::create_metric_card()
          ↓
dbc.Card (Dash Bootstrap Component)
```

### PERT Timeline Calculation Flow

```
StatisticsDataPoint[] + DashboardSettings
          ↓
data/processing.py::calculate_dashboard_metrics()
          ↓
DashboardMetrics (velocity + remaining work)
          ↓
data/processing.py::calculate_pert_timeline()
          ↓
PERTTimelineData
          ↓
visualization/charts.py::create_pert_timeline_chart()
          ↓
dcc.Graph (Plotly chart)
```

### Key Insights Generation Flow

```
DashboardMetrics
          ↓
ui/dashboard_cards.py::_create_key_insights()
          ↓
KeyInsight[] (0-3 insights)
          ↓
html.Div (Insight badges)
```

---

## State Transitions

### Velocity Trend State Machine

```
unknown (initial) ──velocity_change > 10%──> increasing
                  ──velocity_change < -10%─> decreasing
                  ──|velocity_change| ≤ 10%─> stable

increasing ──velocity_change < -10%─> decreasing
          ──|velocity_change| ≤ 10%─> stable

stable ──velocity_change > 10%──> increasing
      ──velocity_change < -10%─> decreasing

decreasing ──velocity_change > 10%──> increasing
          ──|velocity_change| ≤ 10%─> stable
```

### Health Score Tier Transitions

```
Needs Attention (<40) ──score increase─> Fair (40-59)
Fair (40-59) ──score increase─> Good (60-79)
Good (60-79) ──score increase─> Excellent (≥80)

Excellent (≥80) ──score decrease─> Good (60-79)
Good (60-79) ──score decrease─> Fair (40-59)
Fair (40-59) ──score decrease─> Needs Attention (<40)
```

---

## Validation Checklist

For each data structure:
- [ ] All required fields documented
- [ ] Valid value ranges specified
- [ ] Default values identified
- [ ] Edge cases described
- [ ] Relationships mapped
- [ ] Example data provided
- [ ] Calculation formulas documented (where applicable)

---

## Change Log

**Version 1.0** (2025-11-12): Initial documentation for feature 010
- Documented 7 core data structures
- Documented 1 test fixture structure
- Added data flow diagrams
- Added state transition diagrams
- Consolidated knowledge from existing codebase
