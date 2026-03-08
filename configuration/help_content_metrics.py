"""Metrics, charts, and flow help content.

Tooltips and help text for scope, statistics, charts, bug analysis,
dashboard metrics, parameter inputs, and flow metrics.
"""

STATISTICS_HELP_DETAILED = {
    "data_collection_methodology": """
        Data collection methodology for accurate project tracking and forecasting.
        
        [Date] **Weekly Data Collection:**
        • Collection Point: End of each work week (typically Friday)
        • Scope: Monday-Sunday work period for consistency
        • Frequency: Weekly snapshots for trend analysis
        
        [Calc] **Data Fields Explained:**
        
        **Week Start (Monday)**: 
        - Date marking the beginning of the work week
        - Used as the reference point for all weekly measurements
        - Should be actual Monday date even if work starts Tuesday
        
        **Items Done This Week**:
        - Count of work items completed during the weekly period
        - Must be truly "done" items that deliver value to users
        - Incremental value (not cumulative) for proper trend analysis
        
        **Points Done This Week**:
        - Story points or effort units completed during the weekly period
        - Should match the point values of items marked as done
        - Incremental value for accurate velocity calculations
        
        **New Items Added**:
        - Count of new work items discovered or added to backlog
        - Includes user stories, bugs, technical tasks, scope additions
        - Tracks scope growth and requirement discovery patterns
        
        **New Points Added**:
        - Point estimate for newly added work items
        - Represents effort impact of scope changes
        - Used for scope change rate and throughput ratio calculations
    """,
    "data_quality_guidelines": """
        Guidelines for maintaining high-quality project data for accurate forecasting.
        
        [OK] **Data Quality Checklist:**
        
        **Completeness:**
        • No missing weeks in the data series
        • All required fields populated for each week
        • Consistent data collection schedule
        
        **Accuracy:**
        • Items marked "done" are truly complete and deliverable
        • Point estimates reflect actual effort, not initial estimates
        • Scope additions captured when decisions are made, not retroactively
        
        **Consistency:**
        • Same definition of "done" applied throughout project
        • Consistent point estimation approach across the team
        • Regular weekly collection schedule maintained
        
        **Context:**
        • Document significant events (holidays, team changes, major scope shifts)
        • Note any data collection irregularities or exceptions
        • Track external factors that might affect velocity patterns
        
        [Stats] **Impact on Forecasting:**
        High-quality data leads to:
        • More accurate PERT forecasts
        • Narrower confidence intervals
        • Better trend detection
        • More reliable completion predictions
        
        Poor data quality results in:
        • Wide uncertainty ranges
        • Unreliable forecasts
        • Missed trend signals
        • Reduced stakeholder confidence
    """,
    "weekly_progress_data_explanation": """
        Weekly Progress Data tracks delivery and scope changes week by week.
    """,
}

# CHART HELP CONTENT - Comprehensive explanations for help pages
CHART_HELP_DETAILED = {
    "burndown_chart": """
        Comprehensive guide to interpreting burndown charts for project tracking.
        
        📉 **Burndown Charts:**
        • Show remaining work decreasing over time
        • Start high (total scope) and trend toward zero
        • Ideal for tracking progress against fixed deadlines
        • Emphasize completion progress and deadline tracking
        
        [Tip] **Best Practices:**
        • Monitor actual progress against forecasted timelines
        • Track "how much work is left" to completion
        • Identify trends and potential delays early
        • Communicate project status to stakeholders
        
        [Stats] **Visual Elements:**
        • Solid lines: Historical actual data
        • Dashed lines: PERT forecast projections  
        • Dotted lines: Confidence intervals and uncertainty ranges
        • Vertical line: Current date marker
        • Scope change indicators: Show requirement additions/removals
    """,
    "pert_forecast_methodology": """
        PERT (Program Evaluation Review Technique) creates realistic forecasts
        using three-point estimation.
        
        [Calc] **Three-Point Estimation Process:**
        1. **Optimistic Scenario**: Best-case timeline from peak velocity periods
        2. **Most Likely Scenario**: Realistic estimate from current average velocity
        3. **Pessimistic Scenario**: Worst-case timeline from lowest velocity periods
        4. **Expected Value**: Weighted calculation = (O + 4×ML + P) ÷ 6
        
        [Stats] **Mathematical Foundation:**
        • Follows beta distribution for project estimation
        • Weights most likely scenario 4x more than extremes
        • Provides statistically sound forecasts with confidence intervals
        • Accounts for both optimism bias and risk factors
        
        [Trend] **Confidence Intervals:**
        • Calculated using coefficient of variation applied to PERT forecast
        • 50th percentile: The PERT forecast itself (median estimate)
        • 80th percentile: PERT + 0.84 standard deviations
        • 95th percentile: PERT + 1.65 standard deviations
        • Wider intervals indicate higher velocity uncertainty
        • Narrower intervals suggest more predictable delivery patterns
        • Use for risk planning and stakeholder communication
        
        [Tip] **Practical Application:**
        • Expected value: Primary planning target
        • Optimistic: Best-case scenario for resource planning
        • Pessimistic: Risk mitigation and buffer planning
        • Confidence bands: Communication of forecast uncertainty
        
        [Note] **Accuracy Factors:**
        Forecast accuracy improves with:
        • More historical data points (8+ weeks recommended)
        • Consistent team composition and working arrangements
        • Stable definition of "done" and point estimation
        • Regular, complete data collection practices
    """,
    "weekly_chart_methodology": """
        Weekly velocity charts with predictive forecasting using weighted
        moving averages.
        
        [Stats] **Chart Components:**
        • Historical bars: Actual weekly completion rates
        • Forecast bars: Predicted next week performance using PERT methodology  
        • Trend lines: Moving average patterns for visual trend identification
        • Confidence intervals: Error bars showing forecast uncertainty ranges
        
        [Calc] **Forecasting Methodology:**
        **Weighted Moving Average:**
        • Most recent week: 40% weight
        • Second recent: 30% weight  
        • Third recent: 20% weight
        • Fourth recent: 10% weight
        • Formula: 0.4×W1 + 0.3×W2 + 0.2×W3 + 0.1×W4
        
        **PERT Integration:**
        • Optimistic: Top 25% of historical weekly performance
        • Most Likely: Weighted moving average calculation
        • Pessimistic: Bottom 25% of historical weekly performance
        • Expected: (O + 4×ML + P) ÷ 6 for next week prediction
        
        [Trend] **Visual Interpretation:**
        • Solid bars: Confirmed historical performance
        • Patterned bars: Forecasted performance with uncertainty
        • Error bars: Confidence intervals using coefficient of variation method
        • Trend direction: Overall velocity acceleration or deceleration patterns
        
        [Tip] **Usage Guidelines:**
        • Use for short-term capacity planning (1-2 weeks ahead)
        • Compare forecast vs actual for methodology refinement
        • Monitor confidence interval width for prediction reliability
        • Adjust team capacity based on consistent trend patterns
    """,
}

# BUG ANALYSIS HELP CONTENT - Tooltips for bug metrics
BUG_ANALYSIS_TOOLTIPS = {
    "resolution_rate": (
        "Percentage of closed bugs. ≥80% excellent, 70-79% good, <70% needs attention."
    ),
    "open_bugs": "Current unresolved bug count. Green: 0, Teal: 1-5, Orange: >5 bugs.",
    "expected_resolution": (
        "Forecast weeks to clear bug backlog using last 8 weeks of data. Green: "
        "≤2 weeks, Teal: 3-4 weeks, Yellow: >4 weeks."
    ),
}

# DASHBOARD METRICS HELP CONTENT - Tooltips for main dashboard cards
DASHBOARD_METRICS_TOOLTIPS = {
    "completion_forecast": (
        "Estimated project completion date using PERT three-point estimation. Based "
        "on optimistic, most likely, and pessimistic velocity scenarios from your "
        "historical data."
    ),
    "completion_forecast_detail": (
        "This forecast uses your team's actual velocity data to predict when all "
        "remaining work will be completed. The calculation accounts for best-case, "
        "average, and worst-case scenarios to provide a realistic estimate with "
        "confidence ranges."
    ),
    "remaining_work": (
        "Current backlog of incomplete work items and story points. Tracks both the "
        "number of items and their estimated effort to give you a complete picture of "
        "what's left to deliver."
    ),
    "remaining_items": (
        "Number of work items (tasks, stories, bugs) not yet completed. This count "
        "helps track progress independently of estimation complexity."
    ),
    "remaining_points": (
        "Total story points for all incomplete work. Represents the estimated effort "
        "remaining, which may differ from item count due to varying complexity."
    ),
    "velocity_trend": (
        "Team's delivery rate over time, measured in items and points completed per "
        "week. Shows whether your team is accelerating, maintaining pace, or slowing "
        "down."
    ),
    "current_velocity": (
        "Average items and points completed per week based on recent historical data. "
        "This is your team's current sustainable delivery pace used for forecasting."
    ),
    "pert_expected": (
        "Weighted average of optimistic, most likely, and pessimistic forecasts using "
        "the formula: (O + 4×ML + P) ÷ 6. Provides the most statistically reliable "
        "single-point estimate."
    ),
    "confidence_range": (
        "Uncertainty band around the forecast showing the range of possible completion "
        "dates. Wider ranges indicate higher unpredictability; narrower ranges show "
        "consistent velocity."
    ),
    "scope_growth": (
        "New work added vs baseline or completed work. Tracks requirement evolution "
        "and impact on forecasts. Two views: growth from baseline and creation vs "
        "completion rate."
    ),
    "health_score": (
        "Health score (0-100 points). Automatically adapts to available data sources: "
        "Dashboard (Delivery Performance 25%, Predictability 20%), Process Quality "
        "(DORA metrics 20%), Delivery Efficiency (Flow metrics 15%), Risk Indicators "
        "(Bug Analysis, Scope, Budget 25%). Weights dynamically adjust based on data "
        "availability, gracefully handling missing metrics. Note: scope change rate "
        "for health uses created divided by (remaining + completed) within the "
        "selected window, which differs from baseline-based scope tracking."
    ),
}

# PARAMETER INPUTS HELP CONTENT - Tooltips for parameter panel controls
PARAMETER_INPUTS_TOOLTIPS = {
    "pert_factor": (
        "Forecast Range: Controls how many weeks to sample for best/worst case "
        "forecasts. Higher values (8-12) provide conservative estimates using "
        "sustained performance patterns. Lower values (3-6) reflect recent "
        "variability. Minimum 6 weeks of data recommended for reliability."
    ),
    "pert_factor_detail": (
        "This parameter determines how many of your best and worst performing weeks "
        "are averaged to calculate optimistic and pessimistic scenarios. For "
        "example, with a value of 6, your forecast uses the average of your 6 best "
        "weeks as the optimistic case and your 6 worst weeks as the pessimistic "
        "case. The most likely scenario always uses the average of all available "
        "data. This approach provides data-driven forecasts based on your team's "
        "actual historical performance, which is more reliable than simple averages "
        "or gut feelings. Recommended: 20-30% of your total history (e.g., 6 weeks "
        "if you have 30 weeks of data)."
    ),
    "deadline": (
        "Target completion date for your project. Used to calculate timeline pressure "
        "and whether current velocity will meet the deadline. Shown as a vertical "
        "line on forecast charts."
    ),
    "deadline_detail": (
        "Set your desired or committed project deadline. The forecast will compare "
        "this date against velocity-based predictions to show if you're on track, "
        "ahead, or behind schedule."
    ),
    "milestone": (
        "Optional visual marker for any significant project date. Appears as a green "
        "vertical line on charts. Useful for sprint boundaries, phase gates, or "
        "external dependencies. Can be set to any future date."
    ),
    "estimated_items": (
        "Number of work items that have effort estimates (story points, hours, "
        "etc.). Used to calculate average effort per item. If 0, the system will "
        "use historical averages. Manual changes will be overwritten by JIRA "
        "updates."
    ),
    "remaining_items": (
        "Total number of currently open/unresolved work items. This is your current "
        "remaining scope. Used to calculate total remaining effort when combined with "
        "estimated points. Manual changes will be overwritten by JIRA updates."
    ),
    "estimated_points": (
        "Total story points for items that have been estimated. Used with Estimated "
        "Items to calculate average points per item. Leave at 0 if story points are "
        "unavailable. Manual changes will be overwritten by JIRA updates."
    ),
    "remaining_points": (
        "Auto-calculated total remaining effort. Formula: Estimated Points + "
        "(avg_points_per_item × unestimated_items), where avg = Estimated Points ÷ "
        "Estimated Items, and unestimated = Remaining Items - Estimated Items. "
        "Updates automatically when any input changes."
    ),
    "total_items": (
        "Baseline Items (at window start): Total work items that needed to be "
        "completed at the start of your selected time window. This baseline is used "
        "for tracking progress and calculating completion percentage within the "
        "window. Currently Open = Baseline - Completed."
    ),
    "completed_items": (
        "Number of work items finished within the selected time window. Used to "
        "calculate completion percentage and determine currently open work: Baseline "
        "Items - Completed Items."
    ),
    "total_points": (
        "Baseline Points (at window start): Total story points that needed to be "
        "completed at the start of your selected time window. This baseline includes "
        "both estimated and extrapolated points for items without estimates. "
        "Currently Open = Baseline - Completed."
    ),
    "completed_points": (
        "Story points for work items finished within the selected time window. Used "
        "to calculate effort-based completion percentage: Completed Points ÷ Baseline "
        "Points × 100%."
    ),
    "scope_buffer": (
        "Optional reserve capacity for scope changes and unknowns. Adding a buffer "
        "(e.g., 10-20% of total scope) provides contingency for new requirements."
    ),
    "data_points": (
        "Time Period: Number of historical weeks to include for baseline and velocity "
        "calculations. Minimum 4-6 weeks recommended; 8-12 weeks optimal for stable "
        "forecasts. This defines your analysis window."
    ),
    "data_points_detail": (
        "More data points provide stability but may miss recent trends. Fewer points "
        "are more responsive to changes but can be volatile. Balance based on your "
        "project's stability."
    ),
}

# FLOW METRICS HELP CONTENT - Tooltips for Flow Framework metrics
FLOW_METRICS_TOOLTIPS = {
    "flow_velocity": (
        "Completed items per week (average). Forecast uses last 4 weeks weighted "
        "[10%, 20%, 30%, 40%]. Current week uses progressive blending to avoid "
        "Monday drops (0-100% actual by day of week). Higher velocity = faster "
        "delivery."
    ),
    "flow_time": (
        "Start-to-completion time (median of weekly medians). Forecast uses last 4 "
        "weeks weighted [10%, 20%, 30%, 40%]. Lower time = faster cycles."
    ),
    "flow_efficiency": (
        "Active work time ÷ total time (average). Forecast uses last 4 weeks "
        "weighted [10%, 20%, 30%, 40%]. 25-40% is typical for healthy teams."
    ),
    "flow_load": (
        "Current work in progress (WIP snapshot). Forecast uses last 4 weeks "
        "weighted [10%, 20%, 30%, 40%]. Lower WIP = better focus and faster "
        "delivery."
    ),
    "flow_distribution": (
        "Breakdown of completed work by type: Features (new value), Defects "
        "(quality issues), Risk (security/compliance), and Tech Debt (maintenance). "
        "Aggregated totals across the selected period. Balanced distribution "
        "indicates healthy development practices."
    ),
}

# 4-WEEK FORECAST HELP CONTENT - Tooltips and detailed help
# for forecasting feature (Feature 009)
FORECAST_HELP_CONTENT = {
    "forecast_overview": (
        "4-week weighted forecast predicting next week's performance based on "
        "historical trends. Uses exponential weighting (1.0, 0.8, 0.6, 0.4) to "
        "emphasize recent data while considering longer patterns. Helps teams "
        "proactively address performance issues before they impact delivery."
    ),
    "forecast_value": (
        "Predicted metric value for next week calculated using weighted average of "
        "last 4 weeks. Recent weeks contribute more weight than older weeks (Week "
        "0: 100%, Week -1: 80%, Week -2: 60%, Week -3: 40%). Normalized by total "
        "weight for accurate prediction."
    ),
    "forecast_confidence": (
        "Forecast reliability based on available historical data. High: 4 weeks "
        "(full weighting), Medium: 3 weeks (reduced accuracy), Low: 2 weeks "
        "(limited reliability). Forecasts require minimum 2 weeks of data; "
        "insufficient data shows 'Gathering data...'"
    ),
    "trend_vs_forecast": (
        "Compares current week's actual performance against forecast to show if team "
        "is on track. Positive deviation (↗) indicates exceeding forecast; negative "
        "(↘) below forecast; stable (→) on track within ±5%. Color coding: Green "
        "(favorable trend), Yellow (moderate deviation 5-15%), Red (significant "
        "deviation >15%)."
    ),
    "monday_morning": (
        "Special handling for week start when current value is zero. Shows 'Week "
        "starting...' message with neutral indicator instead of '-100% vs forecast'. "
        "Prevents false alarms at beginning of work week when no completions have "
        "occurred yet."
    ),
    "deviation_thresholds": (
        "Performance deviation bands: On track (±5%), Moderate (5-15%), Significant "
        "(>15%). Direction interpretation depends on metric type: higher is better "
        "for velocity/efficiency, lower is better for lead time/MTTR. Bands help "
        "identify when intervention may be needed."
    ),
    "metric_snapshots": (
        "Weekly historical data stored for forecast calculations. Automatically "
        "captured when metrics update. Includes metric value, ISO week number, and "
        "timestamp. Used for weighted average calculation and trend analysis. Stored "
        "in metrics_snapshots.json."
    ),
    "weighting_strategy": (
        "Exponential decay weighting: Most recent week (1.0) → 3 weeks ago (0.4). "
        "Formula: weighted_sum = Σ(value × weight) / Σ(weights). Balances "
        "responsiveness to recent changes with stability from historical patterns. "
        "Configurable via FORECAST_CONFIG in metrics_config.py."
    ),
}
