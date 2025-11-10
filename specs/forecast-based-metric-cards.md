# Forecast-Based Metric Cards Design Specification

**Date:** November 10, 2025  
**Purpose:** Add 4-week weighted forecast benchmarks to all Flow and DORA metric cards with trend indicators

---

## Overview

Currently, metric cards show misleading values at the start of the week (zeros trigger wrong performance badges). This design adds **4-week weighted forecast** as a benchmark to provide meaningful context for current week metrics, showing whether the team is on track or not.

---

## Core Principles

### 1. **Consistent 4-Week Forecast Window**
- **Matches existing app patterns**: Velocity charts, bug trends, PERT forecasting all use 4 weeks
- **Weighted average**: Same weights used throughout app
  - Most recent week: **40%**
  - 2 weeks ago: **30%**
  - 3 weeks ago: **20%**
  - 4 weeks ago: **10%**
- **Formula**: `Forecast = (W-3 × 0.1) + (W-2 × 0.2) + (W-1 × 0.3) + (W-0 × 0.4)`

### 2. **Trend Direction Indicators**
- All cards show trend direction relative to forecast
- Visual indicators:
  - **↗** Rising / Above forecast
  - **→** Stable / At forecast
  - **↘** Falling / Below forecast

### 3. **Apply to All Metrics (Flow + DORA)**
- **Flow Metrics**: Velocity, Time, Efficiency, Load, Distribution
- **DORA Metrics**: Deployment Frequency, Lead Time, Change Failure Rate, MTTR

---

## Forecast Calculation by Metric Type

### Accumulation Metrics (Most Metrics)

**Metrics:** Flow Velocity, Flow Time, Flow Efficiency, Deployment Frequency, Lead Time, CFR, MTTR

**Calculation:**
```python
last_4_weeks = [week_n-3, week_n-2, week_n-1, week_n]  # Historical completed weeks
weights = [0.1, 0.2, 0.3, 0.4]
forecast = sum(value * weight for value, weight in zip(last_4_weeks, weights))
```

**Display:** Point estimate
```
Forecast: ~12 items/week
```

---

### Snapshot Metric (Flow Load Only)

**Metric:** Flow Load (WIP)

**Unique Characteristics:**
- Measured at a point in time (not accumulated over week)
- Can be too high OR too low (bidirectional concern)
- Represents current state, not completion rate

**Calculation:**
```python
# Same weighted average as other metrics
last_4_weeks_wip = [14, 15, 13, 16]
weights = [0.1, 0.2, 0.3, 0.4]
forecast_wip = sum(value * weight for value, weight in zip(last_4_weeks_wip, weights))
# = 14.8 ≈ 15 items

# Calculate acceptable deviation range (±20%)
lower_bound = forecast_wip * 0.8  # 12 items
upper_bound = forecast_wip * 1.2  # 18 items
```

**Display:** Range with deviation
```
Forecast: ~15 items (±20%: 12-18)
```

---

## Trend Direction Logic

### For Accumulation Metrics

**Compare current value to forecast:**

```python
if current_value >= forecast * 1.1:
    trend = "↗"  # Above forecast (+10%)
    status = "Above forecast"
elif current_value <= forecast * 0.9:
    trend = "↘"  # Below forecast (-10%)
    status = "Below forecast"
else:
    trend = "→"  # At forecast (±10%)
    status = "On track"
```

**Interpretation:**
- **Flow Velocity**: Higher is better → ↗ is good
- **Flow Time**: Lower is better → ↘ is good
- **Flow Efficiency**: Higher is better → ↗ is good
- **Deployment Frequency**: Higher is better → ↗ is good
- **Lead Time**: Lower is better → ↘ is good
- **CFR**: Lower is better → ↘ is good
- **MTTR**: Lower is better → ↘ is good

---

### For Flow Load (WIP)

**Compare to forecast range:**

```python
if current_wip > upper_bound:
    trend = "↗"  # Above normal range
    status = f"+{percent}% above normal"
    severity = "warning"  # Too much WIP
elif current_wip < lower_bound:
    trend = "↘"  # Below normal range
    status = f"-{percent}% below normal"
    severity = "info"  # Possible underutilization
else:
    trend = "→"  # Within normal range
    status = "Within normal range ✓"
    severity = "good"
```

**Interpretation:**
- **↗ Above range**: Potential bottleneck, too much WIP
- **→ In range**: Healthy WIP level
- **↘ Below range**: May run out of work, possible underutilization

---

## Current Card Structure (DO NOT CHANGE)

All metric cards currently follow this exact structure:

```
┌─────────────────────────────────────────────────────┐
│ CARD HEADER (dbc.CardHeader)                        │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Icon] Metric Name [?]          [Badge]         │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ CARD BODY (dbc.CardBody)                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │ <H2> 45.2 </H2>        ← Metric value (large)  │ │
│ │ <P> deployments/month  ← Unit (muted)          │ │
│ │ [Icon] 15.3% vs prev avg ← Trend indicator     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ COLLAPSE SECTION (expandable)                       │
│ └─ Trend chart with historical data                │
└─────────────────────────────────────────────────────┘
```

**Key Layout Elements:**
- **Header**: Title (left) + Badge (right) using `d-flex justify-content-between`
- **Body**: Centered value + unit + trend indicator
- **Collapse**: Expandable section with charts (NOT visible by default)

## Card Display Formats - WITH FORECAST ADDITIONS

### **CONSTRAINT: Maintain Existing Structure**
- ✅ All cards must keep current header/body/collapse layout
- ✅ No new major sections (header, body, footer)
- ✅ Forecast info must fit within existing CardBody
- ✅ Mobile responsiveness must be preserved

### Current Week Cards (Running Totals)

**Format for Accumulation Metrics:**
```
┌─────────────────────────────────────────────────────┐
│ HEADER: [Icon] Metric Name [?]          [Badge]    │ ← UNCHANGED
├─────────────────────────────────────────────────────┤
│ BODY:                                               │
│   45.2                           ← Value (H2)       │
│   deployments/month              ← Unit (P)         │
│   ↗ 15.3% vs prev avg           ← EXISTING trend   │
│                                                     │
│   Forecast: ~13 items/week       ← NEW: Forecast   │ 
│   ↗ +23% above forecast          ← NEW: vs Forecast│
└─────────────────────────────────────────────────────┘
```

**NEW Elements to Add (in CardBody, after existing trend):**
1. **Forecast line**: Shows 4-week weighted average
2. **Forecast comparison**: Shows current vs forecast with trend arrow

**Example - Flow Velocity (Tuesday, Current Week):**
```
┌─────────────────────────────────────────────────────┐
│ [Rocket] Flow Velocity [?]         [High Perf]     │
├─────────────────────────────────────────────────────┤
│                   5 items                           │ ← H2 value
│               completed this week                   │ ← P unit
│            ↘ -62% vs prev avg                       │ ← Existing trend (vs previous weeks)
│                                                     │
│          Forecast: ~13 items/week                   │ ← NEW: 4-week weighted forecast
│             ↘ -62% vs forecast                      │ ← NEW: Comparison to forecast
└─────────────────────────────────────────────────────┘
```

**Example - Flow Load (Tuesday, Current Week):**
```
┌─────────────────────────────────────────────────────┐
│ [Layer] Flow Load (WIP) [?]         [Warning]      │
├─────────────────────────────────────────────────────┤
│                  22 items                           │ ← H2 value
│                work in progress                     │ ← P unit
│            ↗ +47% vs prev avg                       │ ← Existing trend
│                                                     │
│       Forecast: ~15 items (12-18)                   │ ← NEW: Range forecast
│           ↗ +47% above normal                       │ ← NEW: vs Forecast range
└─────────────────────────────────────────────────────┘
```

---

### Historical Week Cards (Completed Weeks)

**Format:**
```
┌─────────────────────────────────────────────────────┐
│ HEADER: [Icon] Metric Name [?]          [Badge]    │ ← Performance badge
├─────────────────────────────────────────────────────┤
│ BODY:                                               │
│   18 items                           ← Value (H2)   │
│   completed/week                     ← Unit (P)     │
│   ↗ 38% vs prev avg                 ← EXISTING     │
│                                                     │
│   Forecast: ~13 items/week           ← NEW         │
│   ↗ +38% above forecast              ← NEW         │
└─────────────────────────────────────────────────────┘
```

**Example - Flow Velocity (Week 2025-W45, Completed):**
```
┌─────────────────────────────────────────────────────┐
│ [Rocket] Flow Velocity [?]            [Elite]      │
├─────────────────────────────────────────────────────┤
│                  18 items                           │
│               completed/week                        │
│             ↗ 38% vs prev avg                       │
│                                                     │
│          Forecast: ~13 items/week                   │
│             ↗ +38% above forecast                   │
└─────────────────────────────────────────────────────┘
```

---

## Badge Logic

### Current Week
- Use **last completed week's performance badge**
- Prevents misleading badges from zeros at week start
- Shows recent performance trend

### Historical Weeks
- Use **standard performance tier badges**
- Based on absolute thresholds (Elite/High/Medium/Low)
- Shows achieved performance level

---

## Edge Cases

### 1. First 4 Weeks of Tracking (Insufficient History)

**Handling:**
```python
if len(historical_weeks) < 4:
    # Use available weeks with equal weighting
    forecast = mean(available_weeks)
    display = f"Forecast: ~{forecast} (based on {len(available_weeks)} weeks)"
    note = "Building forecast baseline..."
```

**Display:**
```
┌────────────────────────────────────┐
│ Flow Velocity          [New]       │
│ 12 items → (Week 2)                │
│ Forecast: ~10 items (2 weeks)      │
│ 🆕 Building baseline...            │
└────────────────────────────────────┘
```

### 2. Start of Week (Monday, No Completions Yet)

**Handling:**
```python
if current_week_value == 0 and day_of_week == "Mon":
    trend = "→"  # Neutral, just starting
    status = "Week starting..."
```

**Display:**
```
┌────────────────────────────────────┐
│ Flow Velocity          [Last Week] │
│ 0 items → (Mon)                    │
│ Forecast: ~13 items/week           │
│ Week starting...                   │
└────────────────────────────────────┘
```

### 3. Outlier Weeks in History

**Handling:**
```python
# Weighted average naturally dampens outliers
# Most recent week (40% weight) has highest influence
# Very old outliers (10% weight) have minimal impact

# Optional: Cap extreme values before averaging
if abs(week_value - median) > 3 * std_dev:
    # Use median instead for this week
    week_value = median
```

### 4. Zero or Missing Data in History

**Handling:**
```python
# Filter out weeks with no data before calculating forecast
valid_weeks = [w for w in last_4_weeks if w is not None and w > 0]

if len(valid_weeks) < 2:
    # Not enough data for reliable forecast
    show_message = "Insufficient data for forecast"
    hide_forecast = True
```

---

## Metric-Specific Considerations

### Flow Velocity
- **Unit:** items/week
- **Forecast interpretation:** Expected completions
- **Trend:** ↗ = Good (delivering more)

### Flow Time
- **Unit:** days
- **Forecast interpretation:** Expected cycle time
- **Trend:** ↘ = Good (faster delivery)

### Flow Efficiency
- **Unit:** percentage
- **Forecast interpretation:** Expected efficiency
- **Trend:** ↗ = Good (more efficient)

### Flow Load (WIP)
- **Unit:** items (current count)
- **Forecast interpretation:** Normal/healthy WIP level
- **Trend:** → = Good (stable WIP), ↗ = Warning (growing WIP), ↘ = Info (low WIP)
- **Special:** Show range instead of point estimate

### Flow Distribution
- **Unit:** percentages by category
- **Forecast interpretation:** Expected mix of work types
- **Trend:** Show for each category separately
- **Example:** "Feature: 60% ↗ (forecast: 50%)"

### Deployment Frequency
- **Unit:** deploys/week
- **Forecast interpretation:** Expected deployment cadence
- **Trend:** ↗ = Good (deploying more frequently)

### Lead Time for Changes
- **Unit:** hours
- **Forecast interpretation:** Expected time from commit to deploy
- **Trend:** ↘ = Good (faster to production)

### Change Failure Rate
- **Unit:** percentage
- **Forecast interpretation:** Expected failure rate
- **Trend:** ↘ = Good (fewer failures)

### MTTR (Mean Time to Recovery)
- **Unit:** hours
- **Forecast interpretation:** Expected recovery time
- **Trend:** ↘ = Good (faster recovery)

---

## Implementation Phases

### Phase 1: Core Forecast Calculation
- [ ] Create `calculate_weighted_forecast()` utility function in `data/forecast_utils.py`
- [ ] Support weighted 4-week average (40%, 30%, 20%, 10%)
- [ ] Handle insufficient history (< 4 weeks)
- [ ] Add range calculation for Flow Load (±20%)
- [ ] Add unit tests for forecast calculations

### Phase 2: Trend Detection  
- [ ] Create `calculate_forecast_trend()` in `data/forecast_utils.py`
- [ ] Compare current value to forecast
- [ ] Determine trend direction (↗ → ↘)
- [ ] Calculate deviation percentage
- [ ] Generate status text
- [ ] Add unit tests for trend detection

### Phase 3: Metric Calculation Integration
- [ ] Modify `calculate_and_save_weekly_metrics()` in `data/metrics_calculator.py`
- [ ] Calculate forecast when saving weekly metrics
- [ ] Store forecast data in snapshots (forecast value, historical values, trend)
- [ ] Update snapshot schema to include forecast fields
- [ ] Ensure backward compatibility with existing snapshots

### Phase 4: Card UI Updates (CRITICAL - Maintain Structure)
- [ ] Update `create_metric_card()` in `ui/metric_cards.py`
- [ ] Add forecast display lines WITHIN existing CardBody
- [ ] Add forecast trend indicator AFTER existing trend
- [ ] Use existing styling classes and structure
- [ ] **NO changes to CardHeader or overall card layout**
- [ ] Ensure consistent spacing/alignment with existing elements
- [ ] Test mobile responsiveness (cards must not break on small screens)

### Phase 5: Data Loading Updates
- [ ] Modify Flow metrics data preparation to include forecast
- [ ] Modify DORA metrics data preparation to include forecast
- [ ] Update `get_metric_snapshot()` to return forecast data
- [ ] Ensure callbacks receive forecast in metric_data dict

### Phase 6: Testing & Refinement
- [ ] Test with real data across all metrics
- [ ] Verify mobile responsiveness (320px - 1440px)
- [ ] Test edge cases (first weeks, zeros, outliers)
- [ ] Visual regression testing (cards look correct)
- [ ] Performance testing (forecast calculation overhead)
- [ ] Gather user feedback
- [ ] Adjust thresholds if needed

---

## CSS Requirements (Reuse Existing Styles)

### Existing Classes to Use (DO NOT CREATE NEW STYLES)
- `.text-center` - Center alignment
- `.text-muted` - Gray text for secondary info
- `.small` - Smaller text size
- `.mb-1`, `.mb-2` - Margin bottom spacing
- `.text-success`, `.text-danger`, `.text-secondary` - Trend colors

### Forecast Display Styling
```python
# Forecast line - matches existing unit styling
html.P(
    "Forecast: ~13 items/week",
    className="text-muted text-center small mb-1",  # Reuse existing classes
    style={"fontSize": "0.85rem"}  # Slightly smaller than unit
)

# Forecast trend - matches existing trend indicator
html.Div(
    [
        html.I(className="fas fa-arrow-up me-1"),
        html.Span("+23% vs forecast"),
    ],
    className="text-center text-success small mb-2",  # Same as existing trend
    style={"fontWeight": "500"}  # Same as existing trend
)
```

**NO NEW CSS FILES OR CLASSES** - Reuse all existing Bootstrap and custom classes.

---

## Data Requirements

### Snapshot Data Structure Enhancement

**Current:**
```json
{
  "2025-W46": {
    "flow_velocity": {
      "completed_count": 12,
      "timestamp": "2025-11-10T14:00:00Z"
    }
  }
}
```

**Enhanced with Forecast:**
```json
{
  "2025-W46": {
    "flow_velocity": {
      "completed_count": 12,
      "forecast": {
        "value": 13.2,
        "based_on_weeks": 4,
        "historical_values": [10, 12, 15, 14],
        "weights": [0.1, 0.2, 0.3, 0.4]
      },
      "trend": {
        "direction": "↘",
        "deviation_pct": -9.1,
        "status": "Below forecast"
      },
      "timestamp": "2025-11-10T14:00:00Z"
    }
  }
}
```

---

## Success Criteria

1. ✅ All Flow and DORA metric cards show 4-week weighted forecast
2. ✅ Trend indicators (↗ → ↘) visible on all cards
3. ✅ Flow Load shows range (±20%) instead of point estimate
4. ✅ Current week cards don't show misleading performance badges
5. ✅ Forecast calculation matches existing app patterns (40/30/20/10 weights)
6. ✅ Cards remain mobile-responsive and readable
7. ✅ Edge cases handled gracefully (< 4 weeks history, zeros, outliers)
8. ✅ User can quickly see if current week is on track

---

## Open Questions

1. **Day-of-week pro-rating:** Should we show "expected by Tuesday" or just weekly forecast?
   - Recommendation: Start with weekly forecast only (simpler)
   - Can add day-of-week refinement in Phase 6 if needed

2. **Flow Load deviation threshold:** Is ±20% the right range?
   - Could make configurable in app settings
   - Or calculate dynamically based on historical variance

3. **Trend threshold:** Is ±10% the right threshold for trend arrows?
   - 10% seems reasonable for most metrics
   - Could vary by metric (WIP might need ±15%)

4. **Badge for current week:** Last week's badge or forecast-based?
   - Recommendation: Last week's badge (simpler, less confusing)

---

## Future Enhancements (Not in Scope)

- **Cross-metric insights:** "High WIP correlates with longer Flow Time"
- **Confidence intervals:** Show forecast uncertainty range
- **Seasonal adjustments:** Account for holidays, vacations
- **Team size normalization:** Adjust forecast when team size changes
- **Smart alerts:** Notify when metric significantly deviates from forecast
- **Historical forecast accuracy:** Track how accurate forecasts have been

---

## Visual Design Examples

### Complete Card Examples (Showing EXACT Layout)

**Monday Morning (Start of Week):**
```
┌─────────────────────────────────────────────────────┐
│ [Rocket] Flow Velocity [?]            [Good]       │ ← Header: UNCHANGED
├─────────────────────────────────────────────────────┤
│                   0 items                           │ ← Body: Value (H2)
│               completed this week                   │ ← Unit (P)
│             → 0% vs prev avg                        │ ← EXISTING trend
│                                                     │
│          Forecast: ~13 items/week                   │ ← NEW: Forecast (P small)
│             → Week starting...                      │ ← NEW: Neutral status
└─────────────────────────────────────────────────────┘
```

**Tuesday Afternoon (Behind Forecast):**
```
┌─────────────────────────────────────────────────────┐
│ [Rocket] Flow Velocity [?]         [High Perf]     │
├─────────────────────────────────────────────────────┤
│                   3 items                           │
│               completed this week                   │
│            ↘ -75% vs prev avg                       │ ← Down from recent weeks
│                                                     │
│          Forecast: ~13 items/week                   │
│             ↘ -77% vs forecast                      │ ← Behind forecast (red)
└─────────────────────────────────────────────────────┘
```

**Friday (Above Forecast):**
```
┌─────────────────────────────────────────────────────┐
│ [Rocket] Flow Velocity [?]            [Elite]      │
├─────────────────────────────────────────────────────┤
│                  16 items                           │
│               completed this week                   │
│             ↗ 33% vs prev avg                       │ ← Up from recent weeks
│                                                     │
│          Forecast: ~13 items/week                   │
│             ↗ +23% above forecast                   │ ← Above forecast (green)
└─────────────────────────────────────────────────────┘
```

**Flow Load (High WIP - Warning State):**
```
┌─────────────────────────────────────────────────────┐
│ [Layer] Flow Load (WIP) [?]         [Warning]      │
├─────────────────────────────────────────────────────┤
│                  24 items                           │
│               work in progress                      │
│             ↗ 60% vs prev avg                       │ ← Rising WIP
│                                                     │
│       Forecast: ~15 items (12-18)                   │ ← Range, not point
│           ↗ +60% above normal                       │ ← Above range (red)
└─────────────────────────────────────────────────────┘
```

**Flow Load (Normal - Good State):**
```
┌─────────────────────────────────────────────────────┐
│ [Layer] Flow Load (WIP) [?]            [Good]      │
├─────────────────────────────────────────────────────┤
│                  14 items                           │
│               work in progress                      │
│             → -7% vs prev avg                       │ ← Stable
│                                                     │
│       Forecast: ~15 items (12-18)                   │
│           → Within normal range ✓                   │ ← In range (green)
└─────────────────────────────────────────────────────┘
```

**DORA Metric Example - Deployment Frequency:**
```
┌─────────────────────────────────────────────────────┐
│ [Rocket] Deployment Freq [?]       [High Perf]     │
├─────────────────────────────────────────────────────┤
│                    8                                │
│               deployments/week                      │
│             ↗ 14% vs prev avg                       │
│                                                     │
│          Forecast: ~7 deploys/week                  │
│             ↗ +14% above forecast                   │
└─────────────────────────────────────────────────────┘
```

**DORA Metric Example - Lead Time (Lower is Better):**
```
┌─────────────────────────────────────────────────────┐
│ [Clock] Lead Time [?]               [Elite]        │
├─────────────────────────────────────────────────────┤
│                  18.5                               │
│                  hours                              │
│             ↘ -23% vs prev avg                      │ ← Down is good
│                                                     │
│          Forecast: ~24 hours                        │
│             ↘ -23% below forecast                   │ ← Below is good (green)
└─────────────────────────────────────────────────────┘
```

---

## Layout Specifications (CRITICAL)

### Vertical Spacing in CardBody
```python
card_body_children = [
    # 1. VALUE (H2) - UNCHANGED
    html.H2(
        formatted_value,
        className="text-center metric-value mb-2"  # margin-bottom: 0.5rem
    ),
    
    # 2. UNIT (P) - UNCHANGED  
    html.P(
        unit_text,
        className="text-muted text-center metric-unit mb-1"  # margin-bottom: 0.25rem
    ),
    
    # 3. EXISTING TREND vs Previous Average - UNCHANGED
    html.Div(
        [html.I(className="fas fa-arrow-up me-1"), "15.3% vs prev avg"],
        className="text-center text-success small mb-2"  # margin-bottom: 0.5rem
    ),
    
    # --- NEW FORECAST SECTION STARTS HERE ---
    
    # 4. FORECAST LINE - NEW (same styling as unit)
    html.P(
        "Forecast: ~13 items/week",
        className="text-muted text-center small mb-1",  # margin-bottom: 0.25rem
        style={"fontSize": "0.85rem", "marginTop": "0.5rem"}  # Top spacing separator
    ),
    
    # 5. FORECAST TREND - NEW (same styling as existing trend)
    html.Div(
        [html.I(className="fas fa-arrow-up me-1"), "+23% above forecast"],
        className="text-center text-success small mb-2",  # margin-bottom: 0.5rem
        style={"fontWeight": "500"}
    ),
]
```

### Mobile Responsiveness Constraints
- **Minimum width**: 320px (iPhone SE)
- **Maximum lines in CardBody**: 6-7 lines total
- **Font sizes**: 
  - Value (H2): ~2rem (default)
  - Unit: ~0.875rem
  - Trends: ~0.85rem
  - Forecast: ~0.85rem
- **Text wrapping**: Allowed for long unit names
- **Horizontal padding**: Existing Bootstrap card padding (1rem)

### Color Coding for Trends (Reuse Existing)
```python
# EXISTING trend indicator colors (keep as-is)
if is_higher_better:
    trend_color = "success" if change > 0 else "danger"
else:
    trend_color = "success" if change < 0 else "danger"

# NEW forecast trend indicator (use SAME logic)
if is_higher_better:
    forecast_trend_color = "success" if current > forecast else "danger"
else:
    forecast_trend_color = "success" if current < forecast else "danger"

# Neutral for small changes (±10%)
if abs(deviation_pct) < 10:
    forecast_trend_color = "secondary"
```

---

## Technical Implementation Notes

### Forecast Calculation Function

```python
def calculate_weighted_forecast(
    historical_values: List[float],
    weights: List[float] = [0.1, 0.2, 0.3, 0.4]
) -> Dict[str, Any]:
    """
    Calculate 4-week weighted forecast.
    
    Args:
        historical_values: Last 4 weeks of data (oldest to newest)
        weights: Weight for each week (must sum to 1.0)
    
    Returns:
        {
            "forecast": 13.2,
            "based_on_weeks": 4,
            "historical_values": [10, 12, 15, 14],
            "weights": [0.1, 0.2, 0.3, 0.4]
        }
    """
    # Filter out None/invalid values
    valid_data = [(v, w) for v, w in zip(historical_values, weights) if v is not None]
    
    if len(valid_data) < 2:
        return None  # Insufficient data
    
    # Calculate weighted average
    total_weight = sum(w for _, w in valid_data)
    forecast = sum(v * w for v, w in valid_data) / total_weight
    
    return {
        "forecast": round(forecast, 1),
        "based_on_weeks": len(valid_data),
        "historical_values": [v for v, _ in valid_data],
        "weights": [w for _, w in valid_data]
    }
```

### Trend Detection Function

```python
def calculate_trend(
    current_value: float,
    forecast: float,
    metric_type: str,  # "higher_better" or "lower_better" or "range"
    range_tolerance: float = 0.2  # For WIP only
) -> Dict[str, Any]:
    """
    Determine trend direction and status.
    
    Returns:
        {
            "direction": "↗" | "→" | "↘",
            "deviation_pct": 15.0,  # Percentage difference
            "status": "Above forecast" | "On track" | "Below forecast"
        }
    """
    deviation_pct = ((current_value - forecast) / forecast) * 100
    
    if metric_type == "range":  # Flow Load
        upper = forecast * (1 + range_tolerance)
        lower = forecast * (1 - range_tolerance)
        
        if current_value > upper:
            return {
                "direction": "↗",
                "deviation_pct": round(deviation_pct, 1),
                "status": f"+{abs(round(deviation_pct))}% above normal"
            }
        elif current_value < lower:
            return {
                "direction": "↘",
                "deviation_pct": round(deviation_pct, 1),
                "status": f"-{abs(round(deviation_pct))}% below normal"
            }
        else:
            return {
                "direction": "→",
                "deviation_pct": round(deviation_pct, 1),
                "status": "Within normal range ✓"
            }
    
    else:  # Other metrics
        threshold = 0.10  # ±10%
        
        if deviation_pct > threshold * 100:
            direction = "↗"
            status = f"+{round(abs(deviation_pct))}% above forecast"
        elif deviation_pct < -threshold * 100:
            direction = "↘"
            status = f"{round(deviation_pct)}% below forecast"
        else:
            direction = "→"
            status = "On track"
        
        return {
            "direction": direction,
            "deviation_pct": round(deviation_pct, 1),
            "status": status
        }
```

---

**End of Specification**

---

## Reference Materials & Validation Sources

### Industry Standards for DORA and Flow Metrics

To ensure correctness of metric definitions, thresholds, and forecasting approaches, refer to these authoritative sources:

#### 1. DORA Metrics - Four Keys Guide
**URL**: https://dora.dev/guides/dora-metrics-four-keys/

**What it covers**:
- Official definitions of the four DORA metrics
- Performance tier thresholds (Elite, High, Medium, Low)
- How to measure each metric correctly
- Common pitfalls and measurement anti-patterns

**Use in this feature**:
- ✅ Verify Deployment Frequency units (deploys/week vs deploys/day)
- ✅ Confirm Lead Time for Changes definition (commit to production)
- ✅ Validate Change Failure Rate calculation (% of deployments causing failure)
- ✅ Ensure MTTR measurement approach (time to restore service)
- ✅ Check that "lower is better" metrics (Lead Time, CFR, MTTR) have correct trend direction

**Key validation points**:
```
Elite Performance Thresholds (from DORA):
- Deployment Frequency: Multiple deploys per day
- Lead Time: Less than one hour
- Change Failure Rate: 0-15%
- MTTR: Less than one hour

Use these to validate forecast "good/bad" trend indicators are correctly inversed for lower-is-better metrics.
```

#### 2. Flow Framework - Discover Phase
**URL**: https://flowframework.org/ffc-discover/

**What it covers**:
- Flow Velocity, Flow Time, Flow Efficiency definitions
- Flow Load (WIP) and why it needs bidirectional monitoring
- Flow Distribution and value stream visibility
- How metrics interrelate (high WIP → longer Flow Time)

**Use in this feature**:
- ✅ Validate Flow Load (WIP) range approach (±20% is reasonable)
- ✅ Confirm Flow Efficiency calculation method
- ✅ Verify Flow Distribution categories (Feature/Defect/Risk/Debt)
- ✅ Check that Flow Velocity units match framework (items/week)
- ✅ Ensure Flow Time is measured correctly (started to completed)

**Key validation points**:
```
Flow Load (WIP) Health:
- Too high → bottlenecks, context switching, long cycle times
- Too low → underutilization, running out of work
- Range-based forecast (±20%) captures bidirectional concern

Flow Time vs Lead Time:
- Flow Time: internal team cycle time (To Do → Done)
- Lead Time (DORA): commit to production deployment
- Different metrics, both use "lower is better"
```

#### 3. State of AI-Assisted Software Development (2025)
**URL**: https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf

**What to read**: **Especially the beginning sections** (before AI-specific content)

**What it covers**:
- Statistical analysis of DORA metrics across thousands of teams
- Week-to-week variability in software delivery performance
- Distribution patterns for each metric
- Correlation between metrics and business outcomes

**Use in this feature**:
- ✅ Validate ±10% threshold for "on track" status (is this realistic?)
- ✅ Confirm 4-week forecast window captures meaningful trends
- ✅ Check that weighted average (40/30/20/10) balances recency vs stability
- ✅ Verify typical metric variance supports our edge case handling
- ✅ Benchmark forecast accuracy expectations (our goal: ±20% accuracy, 70% of time)

**Key validation points**:
```
Metric Stability Insights:
- Elite teams have more stable metrics (less week-to-week variance)
- Lower-performing teams show higher variance (outliers more common)
- 4-week window recommended for balancing trend detection vs noise
- Weighted average preferred over simple average to emphasize recent performance

Use this data to:
- Set realistic forecast accuracy targets
- Justify outlier handling (3 standard deviations cap)
- Explain to users why forecasts may be less accurate during improvement phases
```

---

### How to Use These References During Implementation

#### Phase 1: Core Forecast Calculation
**Before coding**:
- [ ] Review DORA guide to confirm metric units (hours, days, percentage, count)
- [ ] Check Flow Framework for Flow Load range calculation best practices
- [ ] Review variance data from Google research to validate ±10% threshold

**During testing**:
- [ ] Compare calculated forecasts against historical actual values
- [ ] Verify forecast accuracy falls within ±20% at least 70% of the time
- [ ] Test edge cases (outliers, holidays) using patterns from research data

#### Phase 2-3: Metric Calculation Integration
**Before modifying calculators**:
- [ ] Verify DORA metric definitions match official guide (especially CFR and MTTR)
- [ ] Confirm Flow Time calculation aligns with Flow Framework
- [ ] Check that "higher is better" vs "lower is better" is correctly identified

**During snapshot updates**:
- [ ] Ensure backward compatibility with existing snapshot data
- [ ] Validate forecast data structure supports historical analysis
- [ ] Test with real project data spanning 4+ weeks

#### Phase 4: Card UI Updates
**Before updating cards**:
- [ ] Review DORA performance tiers to ensure badges use correct thresholds
- [ ] Confirm trend arrow direction matches metric interpretation (↗ good for velocity, ↘ good for lead time)
- [ ] Validate color coding (green/red) aligns with "higher/lower is better"

**During UI testing**:
- [ ] Test Monday morning scenario (zeros don't trigger misleading badges)
- [ ] Verify mid-week scenarios show correct "on track" / "above" / "below" status
- [ ] Check Flow Load range display matches bidirectional health concept

#### Phase 5-6: Testing & Refinement
**Acceptance testing**:
- [ ] Compare app's metric definitions against DORA/Flow Framework guides
- [ ] Validate forecast accuracy against Google research benchmarks
- [ ] Test with user scenarios matching industry use cases
- [ ] Verify help documentation links to these official resources

---

### Quick Reference: Metric Characteristics

Based on industry standards, here's how each metric should behave in forecasts:

| Metric                   | Type         | Unit          | Higher = Better?    | Forecast Type      | Reference      |
| ------------------------ | ------------ | ------------- | ------------------- | ------------------ | -------------- |
| **Flow Velocity**        | Accumulation | items/week    | ✅ Yes               | Point estimate     | Flow Framework |
| **Flow Time**            | Accumulation | days          | ❌ No (lower better) | Point estimate     | Flow Framework |
| **Flow Efficiency**      | Snapshot     | percentage    | ✅ Yes               | Point estimate     | Flow Framework |
| **Flow Load (WIP)**      | Snapshot     | items (count) | ⚖️ Range-based       | Range (±20%)       | Flow Framework |
| **Flow Distribution**    | Snapshot     | percentages   | ➖ Category-specific | Point per category | Flow Framework |
| **Deployment Frequency** | Accumulation | deploys/week  | ✅ Yes               | Point estimate     | DORA Guide     |
| **Lead Time**            | Accumulation | hours         | ❌ No (lower better) | Point estimate     | DORA Guide     |
| **Change Failure Rate**  | Accumulation | percentage    | ❌ No (lower better) | Point estimate     | DORA Guide     |
| **MTTR**                 | Accumulation | hours         | ❌ No (lower better) | Point estimate     | DORA Guide     |

**Trend Arrow Logic**:
- **↗ (up)**: Good for "higher is better" (velocity, deployment freq, efficiency)
- **↗ (up)**: Bad for "lower is better" (lead time, CFR, MTTR, flow time)
- **↘ (down)**: Bad for "higher is better"
- **↘ (down)**: Good for "lower is better"
- **→ (stable)**: Neutral for all (within ±10% of forecast)

**Flow Load Exception**:
- **↗ (up)**: Warning if > upper bound (too much WIP)
- **↘ (down)**: Info if < lower bound (possible underutilization)
- **→ (stable)**: Good if within range

---

### Validation Checklist

Use this during code review and testing:

- [ ] All metric units match official definitions (DORA/Flow Framework)
- [ ] "Higher is better" classification correct for all 9 metrics
- [ ] Trend arrow direction inverted correctly for "lower is better" metrics
- [ ] Color coding (green/red) matches metric interpretation
- [ ] Performance tier badges use DORA thresholds (Elite/High/Medium/Low)
- [ ] Flow Load uses range forecast, all others use point estimate
- [ ] Forecast accuracy tested against ±20% target (70% of weeks)
- [ ] Edge cases handled consistently with industry best practices
- [ ] Help documentation links to authoritative sources
- [ ] User-facing terminology matches industry standards

---
