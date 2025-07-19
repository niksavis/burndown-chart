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
STATISTICS_FILE = "forecast_statistics.csv"

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
        Range: 3-15 (default: 3)
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
