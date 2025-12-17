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
from typing import Dict

#######################################################################
# LOGGING CONFIGURATION
#######################################################################
# Initialize comprehensive file-based logging with rotation and redaction
from configuration.logging_config import setup_logging, cleanup_old_logs

# Setup logging on module import (runs once at application startup)
setup_logging(
    log_dir="logs", max_bytes=10 * 1024 * 1024, backup_count=5, log_level="INFO"
)

# Clean up old log files (30-day retention)
cleanup_old_logs(log_dir="logs", max_age_days=30)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info("Application configuration loaded - logging initialized")

#######################################################################
# APPLICATION CONSTANTS
#######################################################################
# Default values
# Confidence Window (formerly called PERT Factor) - controls sample size for best/worst case
# Higher values = more conservative, Lower values = reflects recent volatility
# Recommended: 6 weeks (20-30% of typical history)
DEFAULT_PERT_FACTOR = 6
DEFAULT_TOTAL_ITEMS = 100
DEFAULT_TOTAL_POINTS = 1000
DEFAULT_DEADLINE = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
DEFAULT_ESTIMATED_ITEMS = 20  # Default value for estimated items (20% of total items)
DEFAULT_ESTIMATED_POINTS = (
    200  # Default value for estimated points (based on default averages)
)
DEFAULT_DATA_POINTS_COUNT = 12  # Minimum 12 weeks for reliable forecasting

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

# PERT and Forecasting Help Texts - Phase 9.1 Simplified
# Note: Comprehensive content moved to configuration/help_content.py for Phase 9.2 help system
FORECAST_HELP_TEXTS = {
    "pert_methodology": "3-point estimation combining optimistic, likely, and pessimistic scenarios.",
    "optimistic_forecast": "Best-case completion estimate from peak velocity periods.",
    "most_likely_forecast": "Most probable estimate based on current average velocity.",
    "pessimistic_forecast": "Worst-case estimate from lowest velocity periods.",
    "expected_forecast": "Balanced forecast weighing likely scenario most heavily.",
    "three_point_estimation": "Forecast ranges instead of single-point estimates.",
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

# Weekly Velocity and Trend Help Texts - Phase 9.1 Simplified
# Note: Comprehensive content moved to configuration/help_content.py for Phase 9.2 help system
VELOCITY_HELP_TEXTS = {
    "weekly_velocity": "Team's completion rate over recent weeks with trend indicators.",
    "velocity_average": "Simple average of weekly completion rates over selected period.",
    "velocity_median": "Middle value of weekly rates, resistant to outliers.",
    "velocity_trend": "Direction of velocity change - up, down, or stable with percentage.",
    "ten_week_calculation": "Uses 10 weeks of data for statistical reliability.",
    "trend_significance": "Bold trends indicate statistically significant changes.",
    "weighted_moving_average": "Recent weeks weighted more heavily in calculations.",
}

# Project Dashboard and Progress Help Texts
# Project Overview Help Texts - Phase 9.1 Simplified
# Note: Comprehensive content moved to configuration/help_content.py for Phase 9.2 help system
PROJECT_HELP_TEXTS = {
    "project_overview": "High-level project completion status and progress metrics.",
    "completion_percentage": "Percentage of work completed based on items or points.",
    "items_vs_points": "Comparison of item-based vs point-based progress tracking.",
    "weekly_averages": "Average completion rates showing sustainable team velocity.",
    "velocity_stability": "Consistency of weekly completion rates - stable, moderate, or variable.",
    "completion_timeline": "Projected completion dates based on PERT calculations.",
}

# Scope Change and Stability Help Texts
# Scope Change and Stability Help Texts - Phase 9.1 Simplified
# Note: Comprehensive content moved to configuration/help_content.py for Phase 9.2 help system
SCOPE_HELP_TEXTS = {
    "scope_change_rate": "Percentage of new work discovered vs initial backlog. Baseline = remaining items at start of tracking period (current remaining + total completed).",
    "throughput_ratio": "Ratio comparing discovery rate vs completion velocity.",
    "threshold_color_coding": "Visual indicators showing velocity impact of scope changes.",
    "adaptability_index": "Scope Stability Index: Measures how stable the scope is relative to total work. Calculated as 1 - (created / total_scope). Higher values (0.7+) = stable, predictable scope with few additions. Lower values (0.3-0.6) = dynamic, evolving scope with frequent additions (normal for responsive agile teams).",
    "weekly_scope_patterns": "Week-by-week tracking of requirement discovery patterns.",
    "agile_scope_philosophy": "Scope changes are expected and valuable in agile projects.",
    "scope_metrics_explanation": "Comprehensive tracking of project scope evolution over time.",
    "jira_scope_calculation": "Intelligent extrapolation for items without story points.",
    "cumulative_chart": "Shows cumulative net scope change from start of period. Positive values = scope grew (scope creep). Negative values = backlog reduced faster than additions. Starting from zero makes scope trends clearer.",
    "weekly_growth": "Week-by-week scope additions and reductions showing discovery patterns.",
}

# Statistics Data and Collection Help Texts - Phase 9.1 Simplified
# Note: Comprehensive content moved to configuration/help_content.py for Phase 9.2 help system
STATISTICS_HELP_TEXTS = {
    "date_field": "Data collection date - weekly snapshots in YYYY-MM-DD format.",
    "completed_items": "Number of work items finished during this period.",
    "completed_points": "Story points completed during this period.",
    "created_items": "Number of new work items added during this period.",
    "created_points": "Story points for new work items added during this period.",
    "velocity_items": "Weekly completion rate for items based on historical data.",
    "velocity_points": "Weekly completion rate for points based on historical data.",
    "data_frequency": "Weekly snapshots provide optimal balance for forecasting.",
    "cumulative_vs_incremental": "Values represent incremental work per period, not cumulative totals.",
}

# Chart and Visualization Help Texts
# Chart and Visualization Help Texts - Phase 9.1 Simplified
# Note: Comprehensive content moved to configuration/help_content.py for Phase 9.2 help system
CHART_HELP_TEXTS = {
    "weighted_moving_average": "Recent weeks weighted more heavily than older data (40%, 30%, 20%, 10%).",
    "forecast_vs_actual_bars": "Solid bars show historical data, patterned bars show forecasts with error bars.",
    "forecast_confidence_intervals": "Error bars show uncertainty range around forecast predictions.",
    "exponential_weighting": "Recent performance emphasized over older data for better trend capture.",
    "weekly_chart_methodology": "Weekly aggregation with PERT forecasts and confidence intervals.",
    "pert_forecast_methodology": "Three-point estimation using optimistic, likely, and pessimistic scenarios.",
    "historical_data_influence": "More data points improve forecast accuracy - 6+ weeks recommended.",
    "chart_legend_explained": "Visual cues distinguish historical data, forecasts, and confidence bands.",
    "forecast_confidence_bands": "Band width indicates forecast uncertainty based on velocity variability.",
    "scope_change_indicators": "Vertical markers show scope changes with automatic forecast adjustments.",
    "data_points_precision": "8-15 recent data points provide optimal forecast accuracy.",
    "burndown_vs_burnup": "Burndown shows remaining work decreasing; Burnup shows completed work increasing.",
}


#######################################################################
# BUG ANALYSIS CONFIGURATION
#######################################################################
def get_bug_analysis_config() -> Dict:
    """Get bug analysis configuration from app settings.

    Returns:
        Dictionary containing bug analysis configuration with defaults:
        - enabled: Whether bug analysis is enabled
        - issue_type_mappings: Dict mapping JIRA type names to "bug" category
        - default_bug_type: Default bug type name ("Bug")

    Example:
        >>> config = get_bug_analysis_config()
        >>> config["enabled"]
        True
        >>> "Bug" in config["issue_type_mappings"]
        True
    """
    from data.persistence import load_app_settings

    settings = load_app_settings()

    # Default bug analysis configuration
    default_config = {
        "enabled": True,
        "issue_type_mappings": {"Bug": "bug", "Defect": "bug", "Incident": "bug"},
        "default_bug_type": "Bug",
    }

    # Return bug_analysis_config if present, otherwise default
    return settings.get("bug_analysis_config", default_config)
