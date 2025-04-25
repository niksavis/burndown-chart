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
2. **Three-point Estimation**: For both items and points completion rates:
   - **Optimistic**: Average of best-performing weeks
   - **Most Likely**: Average of all weeks
   - **Pessimistic**: Average of worst-performing weeks (excluding zeros)
3. **PERT Formula Application**: `(O + 4M + P) / 6` where:
   - O = Optimistic completion time
   - M = Most likely completion time
   - P = Pessimistic completion time
4. **Adaptations for Small Datasets**:
   - For very small datasets (≤3 data points), the mean is used for all estimates
     with slight adjustments for optimistic/pessimistic values
   - PERT factor is dynamically adjusted to be at most 1/3 of available data points

### Key Implementation Details

- **PERT Factor**: Controls how many data points to use for optimistic and pessimistic
  estimates (configurable in UI)
- **Rate Calculation**: Daily rates are derived by dividing weekly values by 7
- **Zero Protection**: All rates have a minimum value of 0.001 to prevent division by zero
- **Data Points Control**: Users can limit how much historical data to include in calculations

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

## Values Used in Project Dashboard

The project dashboard displays additional metrics derived from PERT calculations:

1. **Completion Forecast Section**:
   - **PERT Completion Dates**: Formatted dates showing when items and points are
     expected to be completed based on PERT estimates
   - **Average & Median Forecasts**: Alternative completion forecasts based on
     simple average and median historical rates
   - **Color-coding**: Green if forecast meets deadline, red if it doesn't

2. **Weekly Velocity Section**:
   - `avg_weekly_items`: Average weekly items completed
   - `med_weekly_items`: Median weekly items completed
   - `avg_weekly_points`: Average weekly points completed
   - `med_weekly_points`: Median weekly points completed
   - Trend indicators showing velocity changes

3. **Weeks & Days Calculations**:
   - `weeks_avg_items`: Weeks to complete remaining items at average rate
   - `weeks_med_items`: Weeks to complete remaining items at median rate
   - `weeks_avg_points`: Weeks to complete remaining points at average rate
   - `weeks_med_points`: Weeks to complete remaining points at median rate
   - Corresponding day values (`avg_items_days`, `med_items_days`, etc.)

4. **Project Overview Metrics**:
   - Completion percentages for items and points
   - Progress visualization

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
