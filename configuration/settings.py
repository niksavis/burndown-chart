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
        Percentage of new work added compared to the original project baseline.
        
        Calculation: (New Items Created ÷ Original Baseline) × 100%
        
        - <20%: Normal scope evolution
        - 20-40%: Moderate scope growth, monitor closely  
        - >40%: Significant scope increase, timeline impact likely
    """,
    "throughput_ratio": """
        Ratio of new work created versus work completed in the same period.
        
        Calculation: Created Items ÷ Completed Items
        
        - <1.0: Completing more than creating (scope decreasing)
        - =1.0: Balanced creation and completion
        - >1.0: Creating more than completing (scope increasing)
    """,
    "threshold_color_coding": """
        Visual indicators based on configurable thresholds for scope metrics.
        
        - Green: Within acceptable limits
        - Yellow/Orange: Approaching threshold, attention needed
        - Red: Exceeded threshold, intervention required
        
        Thresholds can be adjusted based on project tolerance for scope changes.
    """,
    "stability_index": """
        Composite metric measuring overall project scope stability (0-1 scale).
        
        Factors:
        - Rate of scope changes over time
        - Consistency of velocity
        - Variability in creation vs completion patterns
        
        Higher values indicate more predictable, stable project execution.
    """,
    "weekly_growth_data": """
        Week-by-week tracking of scope additions and their impact on project timeline.
        
        Shows patterns in scope changes to help identify:
        - Seasonal trends in requirement changes
        - Impact of external factors on scope
        - Effectiveness of scope management practices
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
