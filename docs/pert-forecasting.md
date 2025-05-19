# PERT Forecasting in Burndown Chart

This document explains how the Program Evaluation and Review Technique (PERT) is implemented
in the Burndown Chart application for forecasting project completion.

## Introduction

PERT is a statistical tool used in project management for analyzing and representing
tasks required to complete a project. In this implementation, PERT is used to provide
three different forecasts (optimistic, most likely, and pessimistic) for project
completion based on historical performance data.

## PERT Calculation Implementation

### Data Collection

The system collects historical data containing:

- Completed items (tasks, stories) per time period
- Completed points (effort, complexity) per time period
- Dates of completion

### Calculation Process

The PERT calculation is primarily implemented in `calculate_rates()` function in
`data/processing.py`:

1. **Data Aggregation**: Historical data is grouped by week to stabilize calculations
2. **Three-point Estimation**: For both items and points, we calculate three completion **rates**:
   - **Optimistic Rate**: Average rate of best-performing weeks
   - **Most Likely Rate**: Average rate of all weeks
   - **Pessimistic Rate**: Average rate of worst-performing weeks (excluding zeros)
3. **Conversion to Time Estimates**: These rates are converted to completion time estimates:
   - **Optimistic Time** = Remaining Work ÷ Optimistic Rate
   - **Most Likely Time** = Remaining Work ÷ Most Likely Rate
   - **Pessimistic Time** = Remaining Work ÷ Pessimistic Rate
4. **PERT Formula Application**: `(O + 4M + P) / 6` where:
   - O = Optimistic completion time
   - M = Most likely completion time (weighted 4× to emphasize its importance)
   - P = Pessimistic completion time
5. **Adaptations for Small Datasets**:
   - For very small datasets (≤3 data points), the mean is used for all estimates
     with slight adjustments for optimistic/pessimistic values
   - PERT factor is dynamically adjusted to be at most 1/3 of available data points

### Key Implementation Details

- **PERT Factor**: Controls how many data points to use for optimistic and pessimistic
  estimates (configurable in UI)
- **Rate Calculation**: Daily rates are derived by dividing weekly values by 7
- **Zero Protection**: All rates have a minimum value of 0.001 to prevent division by zero
- **Data Points Control**: Users can limit how much historical data to include in calculations

### Handling Data Irregularities

The system implements several measures to handle irregular data patterns:

- **Outlier Handling**: The "pessimistic" calculation ignores zero values to prevent skewed forecasts. Extremely high values are included in optimistic calculations, but their impact is balanced by the PERT formula weighting.
- **Small Dataset Adjustments**: For datasets with ≤3 data points, the system uses the mean for base calculations with specific adjustments:
  - For optimistic values: Mean × 1.2 (20% higher)
  - For pessimistic values: Mean × 0.8 (20% lower, never below 0.1)
- **Missing Data Points**: Missing values in the dataset are filtered out during preprocessing, ensuring calculations use only valid data.
- **Error Handling**: When calculations encounter potential errors (such as division by zero), the system applies fallback mechanisms:
  - Enforces minimum rate values (0.001)
  - Returns safe default values when no data is available
  - Caps forecasts at 10 years maximum to prevent timestamp overflow
  - Applies intelligent rounding to ensure human-readable values

## Values Used in Burndown Chart Forecasts

The burndown chart visualizes the following forecast data:

1. **Three Forecast Lines** for both items and points:
   - **Average (Most Likely)**: Based on PERT-weighted average completion rate
   - **Optimistic**: Based on best performing weeks
   - **Pessimistic**: Based on worst performing weeks

2. **Projection Calculation**:
   - Starting from last known cumulative values (`last_items`, `last_points`)
   - Using calculated daily rates to project future completion
   - Extending until total items/points are expected to be completed

3. **Key Values**:
   - `pert_time_items`: PERT-weighted estimate for items completion (days)
   - `pert_time_points`: PERT-weighted estimate for points completion (days)
   - Daily rates derived from PERT calculations

## Visualization Options

Users can configure several aspects of the PERT forecasting visualization:

1. **PERT Factor** (slider range: 3-15):
   - Controls the number of data points used for optimistic/pessimistic scenarios
   - Lower values (3-5): More responsive to recent performance changes, wider confidence range
   - Medium values (6-10): Balanced approach, moderate confidence range
   - Higher values (11-15): More stable forecasts using more historical data, narrower confidence range

2. **Data Points Count** (slider with dynamic range):
   - Minimum: 2× PERT Factor (ensures statistical validity)
   - Maximum: All available data points
   - Controls how much historical data to include in calculations
   - Fewer points make forecasts more responsive to recent trends

3. **Chart Type Toggle**:
   - Burndown view: Shows remaining work with forecast to zero
   - Burnup view: Shows completed work with forecast to total scope

## Limitations and Considerations

The PERT forecasting approach has some inherent limitations to consider:

1. **Historical Dependency**: Forecasts are only as good as the historical data they're based on. Significant changes in team composition or working conditions may reduce forecast accuracy.

2. **Linearity Assumption**: The model assumes relatively linear progress, making it less accurate for projects with highly variable velocity.

3. **Small Dataset Challenges**: With fewer than 6 data points, the distinction between optimistic, most likely, and pessimistic scenarios becomes less meaningful.

4. **Scope Change Impact**: Frequent scope changes can reduce forecast accuracy unless the "scope tracking" features are used to account for them.

5. **Minimum Data Requirements**: The system requires at least 2× PERT Factor data points to generate valid forecasts. For a default PERT Factor of 3, this means at least 6 data points are recommended.

## Interpreting PERT Forecasts

When interpreting PERT forecasts in the application:

1. **PERT Estimate**: The mathematically weighted average that accounts for uncertainty
   and represents the most reliable prediction

2. **Average vs. Median**:
   - **Average**: More sensitive to occasional high-performance weeks
   - **Median**: More resistant to outliers, may better represent typical velocity

3. **Optimistic/Pessimistic Range**: Shows the possible range of outcomes based on
   historical performance variability

4. **Color Indicators**:
   - **Green**: On track to meet deadline
   - **Red**: At risk of missing deadline

5. **Comparison Between Item & Point Forecasts**:
   - Similar forecasts indicate consistent estimation practices
   - Large differences may suggest estimation issues or scope changes
