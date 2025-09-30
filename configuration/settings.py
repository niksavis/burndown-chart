"""
Configuration Module

This module centralizes all constants, paths, color definitions,
help texts and logging configuration for the application.
"""

#######################################################################
# IMPORTS
#######################################################################
import logging
import pandas as pd
from datetime import datetime, timedelta

#######################################################################
# LOGGING CONFIGURATION
#######################################################################
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

#######################################################################
# APPLICATION CONSTANTS
#######################################################################
# Default values
DEFAULT_PERT_FACTOR = 3
DEFAULT_TOTAL_ITEMS = 100
DEFAULT_TOTAL_POINTS = 1000
DEFAULT_DEADLINE = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
DEFAULT_ESTIMATED_ITEMS = 20  # Default value for estimated items (20% of total items)
DEFAULT_ESTIMATED_POINTS = (
    200  # Default value for estimated points (based on default averages)
)
DEFAULT_DATA_POINTS_COUNT = 2 * DEFAULT_PERT_FACTOR  # Default to minimum valid value

# File paths for data persistence
SETTINGS_FILE = (
    "forecast_settings.json"  # Legacy settings file for backward compatibility
)
APP_SETTINGS_FILE = (
    "app_settings.json"  # New app-level settings (PERT, deadline, toggles)
)
PROJECT_DATA_FILE = (
    "project_data.json"  # New project data (statistics, scope, metadata)
)

# Sample data for initialization
SAMPLE_DATA = pd.DataFrame(
    {
        "date": [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(10, 0, -1)
        ],
        "completed_items": [5, 7, 3, 6, 4, 8, 5, 6, 7, 4],
        "completed_points": [50, 70, 30, 60, 40, 80, 50, 60, 70, 40],
    }
)

# Colors used consistently across the application
COLOR_PALETTE = {
    "items": "rgb(0, 99, 178)",  # Blue for items
    "points": "rgb(255, 127, 14)",  # Orange for points
    "optimistic": "rgb(20, 168, 150)",  # Teal for optimistic forecast (changed from green)
    "pessimistic": "rgb(128, 0, 128)",  # Purple for pessimistic forecast
    "deadline": "rgb(220, 20, 60)",  # Crimson for deadline
    "items_grid": "rgba(0, 99, 178, 0.1)",  # Light blue grid
    "points_grid": "rgba(255, 127, 14, 0.1)",  # Light orange grid
}

# Help text definitions
HELP_TEXTS = {
    "app_intro": """
        This application helps you forecast project completion based on historical progress. 
        It uses the PERT methodology to estimate when your project will be completed based on 
        optimistic, pessimistic, and most likely scenarios.
    """,
    "pert_factor": """
        The PERT factor determines how many data points to use for optimistic and pessimistic estimates.
        A higher value considers more historical data points for calculating scenarios.
        Range: 1-15, dynamically constrained by available data (minimum: 1 for small datasets, 3 for larger datasets)
    """,
    "data_points_count": """
        Select how many historical data points to include in your forecast calculation.
        The minimum is 2× your PERT Factor to ensure statistically valid results.
        Using fewer points makes your forecast more responsive to recent trends.
    """,
    "deadline": """
        Set your project deadline here. The app will show if you're on track to meet it.
        Format: YYYY-MM-DD
    """,
    "total_items": """
        The total number of remaining items (tasks, stories, etc.) yet to be completed in your project.
        This represents the remaining work quantity needed to complete the project.
    """,
    "total_points": """
        The total number of remaining points (effort, complexity) yet to be completed.
        This represents the remaining work effort/complexity needed to complete the project.
    """,
    "estimated_items": """
        The number of remaining items that have already been estimated with points.
        This should be less than or equal to Remaining Total Items.
    """,
    "estimated_points": """
        The sum of points for the remaining items that have been estimated.
        Used to calculate the average points per item for the remaining work.
    """,
    "csv_format": """
        Your CSV file should contain the following columns:
        - date: Date of work completed (YYYY-MM-DD format)
        - completed_items: Number of items completed on that date
        - completed_points: Number of points completed on that date
        
        The file can use semicolon (;) or comma (,) as separators.
        Example:
        date;completed_items;completed_points
        2025-03-01;5;50
        2025-03-02;7;70
    """,
    "statistics_table": """
        This table shows your historical data. You can:
        - Edit any cell by clicking on it
        - Delete rows with the 'x' button
        - Add new rows with the 'Add Row' button
        - Sort by clicking column headers
        
        Changes to this data will update the forecast immediately.
    """,
    "forecast_explanation": """
        The graph shows your burndown forecast based on historical data:
        - Solid lines: Historical progress
        - Dashed lines: Most likely forecast
        - Dotted lines: Optimistic and pessimistic forecasts
        - Blue/Green lines: Items tracking
        - Orange/Yellow lines: Points tracking
        - Red vertical line: Your deadline
        
        Where the forecast lines cross the zero line indicates estimated completion dates.
    """,
}

# PERT and Forecasting Help Texts
FORECAST_HELP_TEXTS = {
    "pert_methodology": """
        PERT (Program Evaluation and Review Technique) uses three-point estimation:
        
        - Optimistic: Best-case scenario using highest velocity periods
        - Most Likely: Current average velocity based on recent data
        - Pessimistic: Worst-case scenario using lowest velocity periods
        - Expected: Weighted average using formula (O + 4×ML + P) ÷ 6
        
        This provides a range of completion estimates with statistical confidence.
    """,
    "optimistic_forecast": """
        Best-case completion estimate based on your highest velocity periods.
        
        Calculated using the top performing periods from your historical data.
        This represents what's possible if everything goes well and velocity improves.
    """,
    "most_likely_forecast": """
        Most probable completion estimate based on current average velocity.
        
        Uses the mathematical average of your recent velocity data points.
        This is typically the most reliable single-point estimate.
    """,
    "pessimistic_forecast": """
        Worst-case completion estimate based on your lowest velocity periods.
        
        Calculated using the poorest performing periods from your historical data.
        This helps identify risks and plan for potential delays.
    """,
    "expected_forecast": """
        PERT Expected estimate using weighted average of all three scenarios.
        
        Formula: (Optimistic + 4×Most Likely + Pessimistic) ÷ 6
        This balances optimism with realism and provides the most statistically sound estimate.
    """,
    "three_point_estimation": """
        Three-point estimation technique provides forecast ranges instead of single points.
        
        Benefits:
        - Accounts for uncertainty and variability
        - Provides confidence ranges for planning
        - Helps identify best/worst case scenarios
        - More accurate than single-point estimates
    """,
    "forecast-info": """
        Comprehensive guide to interpreting the forecast graph and its components.
        
        Visual Elements:
        • Solid lines: Historical actual data from your project
        • Dashed lines: PERT forecast projections (optimistic/most likely/pessimistic)
        • Confidence bands: Uncertainty ranges around forecasts
        • Deadline marker: Target completion date (red vertical line)
        • Milestone indicators: Interim project goals and checkpoints
        
        Reading the Chart:
        • Y-axis: Work remaining (burndown) or completed (burnup)
        • X-axis: Time progression from start to deadline
        • Forecast accuracy improves with more historical data points
        • Color coding matches PERT methodology (blue/orange/teal/indigo)
    """,
}

# Weekly Velocity and Trend Help Texts
VELOCITY_HELP_TEXTS = {
    "weekly_velocity": """
        Weekly velocity measures your team's completion rate over time.
        
        Calculated using a rolling window of recent data points to show:
        - Current team performance trends
        - Consistency of delivery
        - Seasonal or cyclical patterns
    """,
    "velocity_average": """
        Average weekly completion rate over the selected time period.
        
        Calculation: Sum of completed items/points ÷ Number of weeks
        This smooths out weekly variations to show overall team capacity.
    """,
    "velocity_median": """
        Middle value of weekly completion rates when sorted from lowest to highest.
        
        Less affected by outliers than average, representing typical weekly performance.
        Useful when your velocity has high variability or occasional exceptional weeks.
    """,
    "velocity_trend": """
        Direction and magnitude of velocity change over recent periods.
        
        - UP Green: Velocity increasing (positive trend)
        - DOWN Red: Velocity decreasing (negative trend)  
        - = Gray: Velocity stable (minimal change)
        
        Percentage shows the rate of change compared to previous period.
    """,
    "ten_week_calculation": """
        Velocity calculations use the most recent 10 weeks of data by default.
        
        This provides:
        - Sufficient sample size for statistical reliability
        - Recent enough to reflect current team capacity
        - Balance between stability and responsiveness to changes
    """,
    "trend_significance": """
        Trend changes are marked as statistically significant when they exceed normal variation.
        
        Significant trends (marked in bold) indicate real changes in team performance,
        while non-significant trends may be due to normal weekly fluctuations.
    """,
}

# Project Dashboard and Progress Help Texts
PROJECT_HELP_TEXTS = {
    "project_overview": """
        High-level view of project completion status and progress metrics.
        
        Shows:
        - Overall completion percentages for items and points
        - Relationship between different work measurement methods
        - Visual progress indicators with milestone markers
    """,
    "completion_percentage": """
        Percentage of total work completed based on historical progress data.
        
        Items: (Completed Items ÷ Total Items) × 100%
        Points: (Completed Points ÷ Total Points) × 100%
        
        Different percentages indicate varying complexity or estimation accuracy.
    """,
    "items_vs_points": """
        Comparison between item-based and point-based progress tracking.
        
        - Similar percentages: Consistent estimation accuracy
        - Different percentages: Items may vary in complexity
        - Points typically reflect effort/complexity better than item count
    """,
    "weekly_averages": """
        Average completion rates over recent weeks, showing sustainable team velocity.
        
        These metrics help predict future performance and identify capacity changes.
        Consistent averages indicate stable team performance.
    """,
    "velocity_stability": """
        Measure of how consistent your team's weekly completion rates are.
        
        - Stable: Low variation in weekly velocity (predictable)
        - Moderate: Some variation but generally consistent
        - Variable: High week-to-week changes (less predictable)
    """,
    "completion_timeline": """
        Projected dates when different completion scenarios will be reached.
        
        Based on PERT calculations using historical velocity data to provide
        realistic timeline expectations with confidence ranges.
    """,
}

# Scope Change and Stability Help Texts
SCOPE_HELP_TEXTS = {
    "scope_change_rate": """
        Percentage of new work discovered and added compared to the original project baseline.
        
        Calculation: (New Items Created ÷ Original Baseline) × 100%
        
        🎯 Agile Context:
        - <20%: Normal discovery and refinement
        - 20-40%: Active learning and adaptation  
        - >40%: Significant discovery, consider timeline adjustments
        
        In agile projects, scope changes reflect learning and adaptation to user needs.
    """,
    "throughput_ratio": """
        Ratio comparing new work discovery versus work completion velocity.
        
        Calculation: Created Items ÷ Completed Items
        
        📊 Interpretation:
        - <1.0: Completing faster than discovering (catching up)
        - =1.0: Balanced discovery and completion velocity
        - >1.0: Discovering faster than completing (exploring ahead)
        
        This helps understand the balance between exploration and execution.
    """,
    "threshold_color_coding": """
        Visual indicators based on velocity impact rather than absolute scope changes.
        
        🟢 Green: Changes within team's absorption capacity
        🟡 Yellow: Changes may impact delivery timeline, monitor velocity
        🔴 Red: Changes significantly outpacing completion, consider prioritization
        
        Focuses on sustainable pace rather than preventing necessary changes.
    """,
    "adaptability_index": """
        Measures how well the team adapts to new requirements while maintaining velocity.
        
        📈 Scale: 0.0 (highly adaptive) to 1.0 (more predictable scope)
        
        Agile Perspective:
        - Lower values (0.2-0.5): High adaptability, actively responding to feedback
        - Mid values (0.5-0.7): Balanced adaptation and predictability
        - Higher values (0.7-1.0): More stable scope, fewer discoveries
        
        Note: In agile projects, adaptability (lower values) is often more valuable than stability.
    """,
    "weekly_scope_patterns": """
        Week-by-week tracking of requirement discovery patterns and velocity impact.
        
        🔍 Helps identify:
        - Sprint boundaries and planning cycles
        - User feedback integration patterns  
        - Market response and adaptation cycles
        - Sustainable discovery and delivery balance
        
        Shows the health of your discovery-to-delivery pipeline.
    """,
    "agile_scope_philosophy": """
        In agile methodologies, scope changes are expected and valuable, not problems to avoid.
        
        💡 Healthy Agile Projects Show:
        - Regular requirement discovery and refinement
        - Balanced creation and completion velocity
        - Adaptation based on user feedback and market changes
        - Sustainable pace of change absorption
        
        These metrics help optimize the balance between exploration and execution.
    """,
    "scope_metrics_explanation": """
        Comprehensive tracking of how project scope evolves over time with agile-friendly interpretation.
        
        📊 Key Metrics:
        - Scope Change Rate: Percentage of new work discovered vs original baseline
        - Throughput Ratio: Balance between new discoveries and completion velocity
        - Adaptability Index: Team's responsiveness to changing requirements
        - Growth Patterns: Week-by-week evolution of scope and priorities
        
        🎯 Purpose: Understand scope evolution patterns to optimize discovery-delivery balance.
    """,
    "cumulative_chart": """
        Shows the cumulative impact of scope changes over time compared to the original baseline.
        
        📈 Chart Features:
        - Baseline (gray line): Original project scope
        - Items line (teal): Running total of items added to scope
        - Points line (orange): Running total of story points added to scope
        - Growth areas: Visual representation of scope expansion
        
        💡 Agile Insight: Steady upward slopes indicate continuous discovery and adaptation.
    """,
    "weekly_growth": """
        Week-by-week breakdown of scope additions and reductions showing discovery patterns.
        
        📊 Bar Chart Interpretation:
        - Positive bars: New requirements, features, or scope additions discovered
        - Negative bars: Scope reduction, backlog refinement, or completed items
        - Variable heights: Natural agile rhythm of discovery and delivery
        
        🔍 Look for patterns in sprint cycles, user feedback integration, and market responses.
    """,
}

# Statistics Data and Collection Help Texts
STATISTICS_HELP_TEXTS = {
    "date_field": """
        Data collection date - typically weekly snapshots of project progress.
        
        Format: YYYY-MM-DD
        Represents the end date of the measurement period (e.g., end of sprint, week).
    """,
    "completed_items": """
        Number of work items (stories, tasks, tickets) finished during this period.
        
        Should represent truly "done" items that deliver value.
        This is an incremental value for the specific time period.
    """,
    "completed_points": """
        Story points or effort units completed during this period.
        
        Should match the pointing system used by your team (Fibonacci, T-shirt sizes, etc.).
        This is an incremental value for the specific time period.
    """,
    "created_items": """
        Number of new work items added to the project during this period.
        
        Includes newly discovered requirements, scope additions, and change requests.
        Used to track scope growth and calculate throughput ratios.
    """,
    "created_points": """
        Story points or effort for new work items added during this period.
        
        Helps measure the effort impact of scope changes, not just quantity.
        Used for more accurate scope change impact analysis.
    """,
    "velocity_items": """
        Calculated weekly completion rate for items based on historical data.
        
        Formula: Completed Items ÷ Time Period
        Shows team's capacity for delivering discrete work units.
    """,
    "velocity_points": """
        Calculated weekly completion rate for points based on historical data.
        
        Formula: Completed Points ÷ Time Period  
        Shows team's capacity for delivering effort/complexity.
    """,
    "data_frequency": """
        Statistics are typically collected as weekly snapshots for optimal forecasting.
        
        - Daily: Too granular, high noise
        - Weekly: Optimal balance of freshness and stability
        - Monthly: Too infrequent for agile projects
        
        Consistent collection intervals improve forecast accuracy.
    """,
    "cumulative_vs_incremental": """
        Data values represent incremental work completed in each period, not cumulative totals.
        
        Incremental: Work done in this specific period
        Cumulative: Total work done from project start
        
        Forecasting algorithms expect incremental values for velocity calculations.
    """,
}

# Chart and Visualization Help Texts
CHART_HELP_TEXTS = {
    "weighted_moving_average": """
        Weighted moving average gives more importance to recent weeks than older ones.
        
        Uses exponential weighting over the last 4 weeks:
        - Week 1 (oldest): 0.1 weight (10%)
        - Week 2: 0.2 weight (20%)
        - Week 3: 0.3 weight (30%)
        - Week 4 (newest): 0.4 weight (40%)
        
        This smooths out weekly variations while emphasizing recent performance trends.
    """,
    "forecast_vs_actual_bars": """
        Chart distinguishes between historical and forecast data using visual cues:
        
        - Solid bars: Historical actual completed work
        - Patterned bars (X pattern): Forecast predictions with confidence intervals
        - Vertical line: Separates historical data from forecast projections
        - Error bars: Show uncertainty range (±25% of PERT variance)
        
        Forecast bars display PERT 3-point estimates with statistical confidence ranges.
    """,
    "forecast_confidence_intervals": """
        Confidence intervals show the uncertainty range around forecast predictions.
        
        Calculation method:
        - Most Likely: PERT expected value (main bar height)
        - Upper bound: Most Likely + 25% of (Optimistic - Most Likely)
        - Lower bound: Most Likely - 25% of (Most Likely - Pessimistic)
        
        Error bars provide visual indication of forecast reliability and risk assessment.
        Wider intervals indicate higher uncertainty; narrower intervals suggest more predictable outcomes.
    """,
    "exponential_weighting": """
        Exponential weighting system emphasizes recent performance over older data.
        
        Weight distribution (0.1, 0.2, 0.3, 0.4):
        - Totals 100% for mathematical accuracy
        - Creates exponential decay pattern
        - Recent weeks have 4x more influence than oldest week
        
        This captures current team velocity trends more accurately than simple averages.
    """,
    "weekly_chart_methodology": """
        Weekly charts aggregate daily data into 7-day periods starting on Mondays.
        
        Features:
        - Bar height shows total work completed that week
        - Weighted trend line shows velocity patterns (exponential weighting)
        - Forecast bars predict next week's performance using PERT methodology
        - Error bars show confidence intervals (±25% of PERT variance)
        - Consistent visualization across both items and points charts
        
        Helps identify velocity trends, capacity planning, and performance patterns with statistical rigor.
    """,
    "burndown_vs_burnup": """
        Two complementary views of project progress with different perspectives:
        
        • Burndown Chart: Shows remaining work declining over time
          - Y-axis: Work remaining (decreasing toward zero)
          - Success: Line reaches zero by deadline
          - Focus: How much work is left to complete
        
        • Burnup Chart: Shows completed work accumulating over time
          - Y-axis: Work completed (increasing toward total)
          - Success: Line reaches total scope by deadline
          - Focus: How much work has been accomplished
        
        Both use identical PERT methodology and historical data for consistency.
    """,
    "pert_forecast_methodology": """
        PERT (Program Evaluation Review Technique) creates realistic forecasts using three-point estimation:
        
        Historical Analysis:
        • Analyzes your team's actual performance data
        • Calculates optimistic, most likely, and pessimistic scenarios
        • Uses weighted formula: (Optimistic + 4×Most Likely + Pessimistic) ÷ 6
        
        Forecast Integration:
        • Projects completion dates based on current velocity trends
        • Accounts for historical performance variability
        • Provides confidence ranges for deadline achievement
        
        Visual indicators show all three scenarios with the expected outcome highlighted.
    """,
    "historical_data_influence": """
        Forecast accuracy improves with more historical data points:
        
        Data Quality Impact:
        • 3-5 weeks: Basic trends, high uncertainty
        • 6-10 weeks: Moderate confidence, seasonal patterns emerge
        • 10+ weeks: High confidence, reliable velocity patterns
        
        Forecast Precision:
        • More data points = narrower confidence bands
        • Recent performance weighted more heavily
        • Automatic handling of scope changes and velocity shifts
        
        Recommendation: Use at least 6 weeks of data for reliable forecasting.
    """,
    "chart_legend_explained": """
        Chart legend uses visual cues to distinguish different types of data:
        
        Line Types:
        • Solid lines: Historical actual data (completed work)
        • Dashed lines: PERT forecast projections
        • Dotted lines: Confidence bands (uncertainty ranges)
        
        Visual Elements:
        • Vertical deadline marker: Target completion date
        • Milestone indicators: Interim project goals
        • Scope change annotations: When requirements changed
        
        Color coding remains consistent across all chart views for easy comparison.
    """,
    "forecast_confidence_bands": """
        Confidence bands show the uncertainty range around forecast predictions:
        
        Band Interpretation:
        • Narrow bands: High confidence in forecast accuracy
        • Wide bands: Greater uncertainty due to variable performance
        • Band width based on historical velocity variability
        
        Calculation Method:
        • Uses standard deviation of historical performance
        • Accounts for recent trend stability
        • Widens for longer-term projections
        
        These bands help with risk assessment and deadline planning decisions.
    """,
    "scope_change_indicators": """
        Main chart annotations highlight when project scope changed:
        
        Scope Change Detection:
        • Vertical markers show dates when scope increased/decreased
        • Color coding: Green (scope reduction), Orange (scope increase)
        • Magnitude indicators show size of scope changes
        
        Forecast Impact:
        • Automatic recalculation of forecasts after scope changes
        • Maintains forecast accuracy despite scope modifications
        • Historical velocity adjusted for new scope reality
        
        Helps understand how scope changes affect completion predictions.
    """,
    "data_points_precision": """
        Number of data points significantly affects forecast precision:
        
        Impact on Accuracy:
        • Fewer points: More volatile forecasts, wider confidence bands
        • More points: Stable forecasts, better trend identification
        • Optimal range: 8-15 recent data points for best accuracy
        
        Dynamic Adjustment:
        • System automatically selects optimal data range
        • Balances recent performance with historical patterns
        • Excludes outliers that might skew forecasts
        
        User can override to focus on specific time periods if needed.
    """,
}
