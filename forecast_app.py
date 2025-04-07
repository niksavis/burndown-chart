"""
Project Burndown Forecast Application

A Dash-based web application that forecasts project completion using the PERT methodology
based on historical data. This tool visualizes burndown charts for both items and points.
"""

#######################################################################
# IMPORTS
#######################################################################
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import io
import base64
import logging
import json
import os

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

# File paths for data persistence
SETTINGS_FILE = "forecast_settings.json"
STATISTICS_FILE = "forecast_statistics.csv"

# Sample data for initialization
SAMPLE_DATA = pd.DataFrame(
    {
        "date": [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(10, 0, -1)
        ],
        "no_items": [5, 7, 3, 6, 4, 8, 5, 6, 7, 4],
        "no_points": [50, 70, 30, 60, 40, 80, 50, 60, 70, 40],
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

# Help text definitions (could be moved to a separate file if it grows larger)
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
    "deadline": """
        Set your project deadline here. The app will show if you're on track to meet it.
        Format: YYYY-MM-DD
    """,
    "total_items": """
        The total number of items (tasks, stories, etc.) to be completed in your project.
        This represents work quantity.
    """,
    "total_points": """
        The total number of points (effort, complexity) to be completed.
        This represents work effort/complexity.
    """,
    "estimated_items": """
        The number of items that have already been estimated with points.
        This should be less than or equal to Total Items.
    """,
    "estimated_points": """
        The sum of points for the items that have been estimated.
        Used to calculate the average points per item for the entire project.
    """,
    "csv_format": """
        Your CSV file should contain the following columns:
        - date: Date of work completed (YYYY-MM-DD format)
        - no_items: Number of items completed on that date
        - no_points: Number of points completed on that date
        
        The file can use semicolon (;) or comma (,) as separators.
        Example:
        date;no_items;no_points
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

#######################################################################
# DATA PERSISTENCE FUNCTIONS
#######################################################################


def save_settings(
    pert_factor,
    deadline,
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
):
    """
    Save user settings to JSON file.

    Args:
        pert_factor: PERT factor value
        deadline: Deadline date string
        total_items: Total number of items
        total_points: Total number of points
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
    """
    settings = {
        "pert_factor": pert_factor,
        "deadline": deadline,
        "total_items": total_items,
        "total_points": total_points,
        "estimated_items": estimated_items
        if estimated_items is not None
        else DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": estimated_points
        if estimated_points is not None
        else DEFAULT_ESTIMATED_POINTS,
    }

    try:
        # Write to a temporary file first
        temp_file = f"{SETTINGS_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(settings, f)

        # Rename to final file (atomic operation)
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        os.rename(temp_file, SETTINGS_FILE)

        logger.info(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Error saving settings: {e}")


def load_settings():
    """
    Load user settings from JSON file.

    Returns:
        Dictionary containing settings or default values if file not found
    """
    default_settings = {
        "pert_factor": DEFAULT_PERT_FACTOR,
        "deadline": DEFAULT_DEADLINE,
        "total_items": DEFAULT_TOTAL_ITEMS,
        "total_points": DEFAULT_TOTAL_POINTS,
        "estimated_items": DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": DEFAULT_ESTIMATED_POINTS,
    }

    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            logger.info(f"Settings loaded from {SETTINGS_FILE}")

            # Add default values for new fields if they don't exist
            if "estimated_items" not in settings:
                settings["estimated_items"] = DEFAULT_ESTIMATED_ITEMS
            if "estimated_points" not in settings:
                settings["estimated_points"] = DEFAULT_ESTIMATED_POINTS

            return settings
        else:
            logger.info("Settings file not found, using defaults")
            return default_settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return default_settings


def save_statistics(data):
    """
    Save statistics data to CSV file.

    Args:
        data: List of dictionaries containing statistics data
    """
    try:
        df = pd.DataFrame(data)

        # Write to a temporary file first
        temp_file = f"{STATISTICS_FILE}.tmp"
        df.to_csv(temp_file, index=False)

        # Rename to final file (atomic operation)
        if os.path.exists(STATISTICS_FILE):
            os.remove(STATISTICS_FILE)
        os.rename(temp_file, STATISTICS_FILE)

        logger.info(f"Statistics saved to {STATISTICS_FILE}")
    except Exception as e:
        logger.error(f"Error saving statistics: {e}")


def load_statistics():
    """
    Load statistics data from CSV file.

    Returns:
        List of dictionaries containing statistics data or sample data if file not found
    """
    try:
        if os.path.exists(STATISTICS_FILE):
            df = pd.read_csv(STATISTICS_FILE)
            data = df.to_dict("records")
            logger.info(f"Statistics loaded from {STATISTICS_FILE}")
            return data
        else:
            logger.info("Statistics file not found, using sample data")
            return SAMPLE_DATA.to_dict("records")
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
        return SAMPLE_DATA.to_dict("records")


def calculate_total_points(
    total_items, estimated_items, estimated_points, statistics_data=None
):
    """
    Calculate the total points based on estimated points and items.

    Args:
        total_items: Total number of items in the project
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        statistics_data: Optional historical data to use as fallback

    Returns:
        Tuple of (estimated_total_points, avg_points_per_item)
    """
    # Basic validation to prevent division by zero
    if estimated_items <= 0:
        # If no items are estimated, try to use historical data
        if statistics_data and len(statistics_data) > 0:
            # Calculate average points per item from historical data
            df = pd.DataFrame(statistics_data)
            df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce").fillna(0)
            df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce").fillna(0)

            total_completed_items = df["no_items"].sum()
            total_completed_points = df["no_points"].sum()

            if total_completed_items > 0:
                avg_points_per_item = total_completed_points / total_completed_items
                estimated_total_points = total_items * avg_points_per_item
                return estimated_total_points, avg_points_per_item

        # Default to 10 points per item if no data available
        return total_items * 10, 10

    # Calculate average points per item based on estimates
    avg_points_per_item = estimated_points / estimated_items

    # Calculate total points using the average
    estimated_total_points = total_items * avg_points_per_item

    return estimated_total_points, avg_points_per_item


#######################################################################
# DATA PROCESSING FUNCTIONS
#######################################################################


def read_and_clean_data(df):
    """
    Clean and prepare the input dataframe for analysis.

    Args:
        df: Pandas DataFrame with raw data

    Returns:
        Cleaned DataFrame with proper types and no missing values
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce")
    df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce")
    df.dropna(subset=["no_items", "no_points"], inplace=True)
    return df


def compute_cumulative_values(df, total_items, total_points):
    """
    Compute cumulative values for items and points for burndown tracking.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete

    Returns:
        DataFrame with added cumulative columns
    """
    df = df.copy()
    df["cum_items"] = df["no_items"][::-1].cumsum()[::-1] + total_items
    df["cum_points"] = df["no_points"][::-1].cumsum()[::-1] + total_points
    return df


def compute_weekly_throughput(df):
    """
    Aggregate daily data to weekly throughput for more stable calculations.

    Args:
        df: DataFrame with daily completion data

    Returns:
        DataFrame with weekly aggregated data
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-{r['week']}", axis=1)

    grouped = (
        df.groupby("year_week")
        .agg({"no_items": "sum", "no_points": "sum"})
        .reset_index()
    )
    return grouped


def calculate_rates(grouped, total_items, total_points, pert_factor):
    """
    Calculate burn rates using PERT methodology.

    Args:
        grouped: DataFrame with weekly aggregated data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: Number of data points to use for optimistic/pessimistic estimates

    Returns:
        Tuple of calculated values:
        (pert_time_items, optimistic_items_rate, pessimistic_items_rate,
         pert_time_points, optimistic_points_rate, pessimistic_points_rate)
    """
    days_per_week = 7.0

    # Validate and adjust pert_factor based on available data
    pert_factor = min(pert_factor, len(grouped) // 2) if len(grouped) > 0 else 1
    pert_factor = max(pert_factor, 1)  # Ensure at least 1

    if len(grouped) == 0:
        return 0, 0, 0, 0, 0, 0

    # Calculate daily rates for items
    optimistic_items_rate = (
        grouped["no_items"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_items_rate = (
        grouped["no_items"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_items_rate = grouped["no_items"].mean() / days_per_week

    # Calculate daily rates for points
    optimistic_points_rate = (
        grouped["no_points"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_points_rate = (
        grouped["no_points"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_points_rate = grouped["no_points"].mean() / days_per_week

    # Calculate time estimates for items
    optimistic_time_items = (
        total_items / optimistic_items_rate if optimistic_items_rate else float("inf")
    )
    most_likely_time_items = (
        total_items / most_likely_items_rate if most_likely_items_rate else float("inf")
    )
    pessimistic_time_items = (
        total_items / pessimistic_items_rate if pessimistic_items_rate else float("inf")
    )

    # Calculate time estimates for points
    optimistic_time_points = (
        total_points / optimistic_points_rate
        if optimistic_points_rate
        else float("inf")
    )
    most_likely_time_points = (
        total_points / most_likely_points_rate
        if most_likely_points_rate
        else float("inf")
    )
    pessimistic_time_points = (
        total_points / pessimistic_points_rate
        if pessimistic_points_rate
        else float("inf")
    )

    # Apply PERT formula: (O + 4M + P) / 6
    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    return (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    )


def daily_forecast(start_val, daily_rate, start_date):
    """
    Generate daily forecast values from start to completion.

    Args:
        start_val: Starting value (remaining items/points)
        daily_rate: Daily completion rate
        start_date: Starting date for the forecast

    Returns:
        Tuple of (x_values, y_values) for plotting
    """
    if daily_rate <= 0:
        return [start_date], [start_val]

    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date

    while val > 0:
        x_vals.append(current_date)
        y_vals.append(val)
        val -= daily_rate
        current_date += timedelta(days=1)

    # Add final zero point
    x_vals.append(current_date)
    y_vals.append(0)

    return x_vals, y_vals


def calculate_weekly_averages(statistics_data):
    """
    Calculate average and median weekly items and points for the last 10 weeks.

    Args:
        statistics_data: List of dictionaries containing statistics data

    Returns:
        Tuple of (avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points)
    """
    if not statistics_data or len(statistics_data) == 0:
        return 0, 0, 0, 0

    # Create DataFrame and ensure numeric types
    df = pd.DataFrame(statistics_data)
    df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce").fillna(0)
    df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce").fillna(0)

    # Sort by date to ensure we get the most recent 10 weeks
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    # Get the last 10 entries or all if less than 10
    recent_data = df.tail(10)

    # Calculate averages and medians
    avg_weekly_items = recent_data["no_items"].mean()
    avg_weekly_points = recent_data["no_points"].mean()
    med_weekly_items = recent_data["no_items"].median()
    med_weekly_points = recent_data["no_points"].median()

    return (
        round(avg_weekly_items, 1),
        round(avg_weekly_points, 1),
        round(med_weekly_items, 1),
        round(med_weekly_points, 1),
    )


#######################################################################
# VISUALIZATION FUNCTIONS
#######################################################################


def prepare_forecast_data(df, total_items, total_points, pert_factor):
    """
    Prepare all necessary data for the forecast visualization.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations

    Returns:
        Dictionary containing all data needed for visualization
    """
    # Convert string dates to datetime for calculations
    df_calc = df.copy()
    df_calc["date"] = pd.to_datetime(df_calc["date"])

    # Compute weekly throughput and rates
    grouped = compute_weekly_throughput(df_calc)
    rates = calculate_rates(grouped, total_items, total_points, pert_factor)

    (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    ) = rates

    # Compute daily rates
    items_daily_rate = (
        total_items / pert_time_items
        if pert_time_items > 0 and pert_time_items != float("inf")
        else 0
    )

    points_daily_rate = (
        total_points / pert_time_points
        if pert_time_points > 0 and pert_time_points != float("inf")
        else 0
    )

    # Get starting points for forecast
    start_date = df_calc["date"].iloc[-1] if not df_calc.empty else datetime.now()
    last_items = df_calc["cum_items"].iloc[-1] if not df_calc.empty else total_items
    last_points = df_calc["cum_points"].iloc[-1] if not df_calc.empty else total_points

    # Generate forecast data
    items_forecasts = {
        "avg": daily_forecast(last_items, items_daily_rate, start_date),
        "opt": daily_forecast(last_items, optimistic_items_rate, start_date),
        "pes": daily_forecast(last_items, pessimistic_items_rate, start_date),
    }

    points_forecasts = {
        "avg": daily_forecast(last_points, points_daily_rate, start_date),
        "opt": daily_forecast(last_points, optimistic_points_rate, start_date),
        "pes": daily_forecast(last_points, pessimistic_points_rate, start_date),
    }

    # Calculate max values for axis scaling
    max_items = max(
        df_calc["cum_items"].max() if not df_calc.empty else total_items,
        max(
            max(items_forecasts["avg"][1]) if items_forecasts["avg"][1] else 0,
            max(items_forecasts["opt"][1]) if items_forecasts["opt"][1] else 0,
            max(items_forecasts["pes"][1]) if items_forecasts["pes"][1] else 0,
        ),
    )

    max_points = max(
        df_calc["cum_points"].max() if not df_calc.empty else total_points,
        max(
            max(points_forecasts["avg"][1]) if points_forecasts["avg"][1] else 0,
            max(points_forecasts["opt"][1]) if points_forecasts["opt"][1] else 0,
            max(points_forecasts["pes"][1]) if points_forecasts["pes"][1] else 0,
        ),
    )

    return {
        "df_calc": df_calc,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "items_forecasts": items_forecasts,
        "points_forecasts": points_forecasts,
        "max_items": max_items,
        "max_points": max_points,
        "start_date": start_date,
        "last_items": last_items,
        "last_points": last_points,
    }


def create_plot_traces(forecast_data):
    """
    Create all the traces for the plot.

    Args:
        forecast_data: Dictionary of forecast data from prepare_forecast_data

    Returns:
        List of traces for Plotly figure
    """
    df_calc = forecast_data["df_calc"]
    items_forecasts = forecast_data["items_forecasts"]
    points_forecasts = forecast_data["points_forecasts"]

    traces = []

    # Historical items trace
    traces.append(
        {
            "data": go.Scatter(
                x=df_calc["date"],
                y=df_calc["cum_items"],
                mode="lines+markers",
                name="Items History",
                line=dict(color=COLOR_PALETTE["items"], width=3),
                marker=dict(size=8, color=COLOR_PALETTE["items"]),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    # Items forecast traces
    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["avg"][0],
                y=items_forecasts["avg"][1],
                mode="lines",
                name="Items Forecast (Most Likely)",
                line=dict(color=COLOR_PALETTE["items"], dash="dash", width=2),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["opt"][0],
                y=items_forecasts["opt"][1],
                mode="lines",
                name="Items Forecast (Optimistic)",
                line=dict(color=COLOR_PALETTE["optimistic"], dash="dot", width=2),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["pes"][0],
                y=items_forecasts["pes"][1],
                mode="lines",
                name="Items Forecast (Pessimistic)",
                line=dict(color=COLOR_PALETTE["pessimistic"], dash="dot", width=2),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    # Historical points trace
    traces.append(
        {
            "data": go.Scatter(
                x=df_calc["date"],
                y=df_calc["cum_points"],
                mode="lines+markers",
                name="Points History",
                line=dict(color=COLOR_PALETTE["points"], width=3),
                marker=dict(size=8, color=COLOR_PALETTE["points"]),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    # Points forecast traces
    traces.append(
        {
            "data": go.Scatter(
                x=points_forecasts["avg"][0],
                y=points_forecasts["avg"][1],
                mode="lines",
                name="Points Forecast (Most Likely)",
                line=dict(color=COLOR_PALETTE["points"], dash="dash", width=2),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=points_forecasts["opt"][0],
                y=points_forecasts["opt"][1],
                mode="lines",
                name="Points Forecast (Optimistic)",
                line=dict(color="rgb(184, 134, 11)", dash="dot", width=2),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=points_forecasts["pes"][0],
                y=points_forecasts["pes"][1],
                mode="lines",
                name="Points Forecast (Pessimistic)",
                line=dict(color="rgb(165, 42, 42)", dash="dot", width=2),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    return traces


def add_deadline_marker(fig, deadline):
    """
    Add deadline marker line and annotation to the figure.

    Args:
        fig: Plotly figure object
        deadline: Deadline date (datetime object)

    Returns:
        Updated figure with deadline marker
    """
    # Add vertical line at deadline
    fig.add_shape(
        type="line",
        x0=deadline,
        x1=deadline,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color=COLOR_PALETTE["deadline"], dash="dash", width=3),
    )

    # Add deadline annotation
    fig.add_annotation(
        x=deadline,
        y=1,
        yref="paper",
        text="Deadline",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40,
        font=dict(color=COLOR_PALETTE["deadline"], size=14, family="Arial, sans-serif"),
    )

    return fig


def configure_axes(fig, forecast_data):
    """
    Configure the axis scales and styling for the figure.

    Args:
        fig: Plotly figure object
        forecast_data: Dictionary of forecast data

    Returns:
        Updated figure with configured axes
    """
    max_items = forecast_data["max_items"]
    max_points = forecast_data["max_points"]

    # Calculate scale factor to align visually
    scale_factor = max_points / max_items if max_items > 0 else 1

    # Set y-axis ranges to maintain alignment
    items_range = [0, max_items * 1.1]
    points_range = [0, max_items * scale_factor * 1.1]

    # Configure x-axis
    fig.update_xaxes(
        title={"text": "Date", "font": {"size": 16}},
        tickmode="auto",
        nticks=20,
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
    )

    # Configure primary y-axis (items)
    fig.update_yaxes(
        title={"text": "Remaining Items", "font": {"size": 16}},
        range=items_range,
        gridcolor=COLOR_PALETTE["items_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=False,
    )

    # Configure secondary y-axis (points)
    fig.update_yaxes(
        title={"text": "Remaining Points", "font": {"size": 16}},
        range=points_range,
        gridcolor=COLOR_PALETTE["points_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=True,
    )

    return fig


def apply_layout_settings(fig):
    """
    Apply final layout settings to the figure.

    Args:
        fig: Plotly figure object

    Returns:
        Figure with finalized layout settings
    """
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.0,
            xanchor="center",
            x=0.5,
            font={"size": 12},
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="lightgray",
            borderwidth=1,
        ),
        hovermode="closest",
        margin=dict(r=70, l=70, t=80, b=70),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif"},
    )

    return fig


def add_metrics_annotations(fig, metrics_data):
    """
    Add metrics as annotations below the x-axis of the plot.

    Args:
        fig: Plotly figure object
        metrics_data: Dictionary with metrics to display

    Returns:
        Updated figure with metrics annotations
    """
    # Define styles for metrics display
    base_y_position = -0.2  # Starting position below x-axis
    font_color = "#505050"
    title_font_size = 16
    value_font_size = 14

    # Create background shape for metrics area
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=base_y_position - 0.13,  # Background bottom position
        x1=1,
        y1=base_y_position + 0.03,  # Background top position
        fillcolor="rgba(245, 245, 245, 0.8)",
        line=dict(color="rgba(200, 200, 200, 0.5)", width=1),
    )

    # Create a title for the metrics section
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.02,  # Left aligned
        y=base_y_position + 0.04,  # Position at the top of the metrics area
        text="<b>Project Metrics</b>",
        showarrow=False,
        font=dict(size=title_font_size, color=font_color, family="Arial, sans-serif"),
        align="left",
    )

    # Define the metrics to display in columns
    metrics_columns = [
        [
            {
                "label": "Total Items",
                "value": metrics_data["total_items"],
                "format": "{:,}",
            },
            {
                "label": "Total Points",
                "value": metrics_data["total_points"],
                "format": "{:,.0f}",
            },
        ],
        [
            {"label": "Deadline", "value": metrics_data["deadline"], "format": "{}"},
            {
                "label": "Deadline in",
                "value": metrics_data["days_to_deadline"],
                "format": "{:,} days",
            },
        ],
        [
            {
                "label": "Est. Days (Items)",
                "value": metrics_data["pert_time_items"],
                "format": "{:.1f} days",
            },
            {
                "label": "Est. Days (Points)",
                "value": metrics_data["pert_time_points"],
                "format": "{:.1f} days",
            },
        ],
        [
            {
                "label": "Avg Weekly Items (10W)",
                "value": metrics_data["avg_weekly_items"],
                "format": "{:.1f}",
            },
            {
                "label": "Avg Weekly Points (10W)",
                "value": metrics_data["avg_weekly_points"],
                "format": "{:.1f}",
            },
        ],
        [
            {
                "label": "Med Weekly Items (10W)",
                "value": metrics_data["med_weekly_items"],
                "format": "{:.1f}",
            },
            {
                "label": "Med Weekly Points (10W)",
                "value": metrics_data["med_weekly_points"],
                "format": "{:.1f}",
            },
        ],
    ]

    # Calculate column positions with better spacing
    # Use fixed positions rather than relative calculations to ensure consistent spacing
    column_positions = [0.02, 0.21, 0.40, 0.60, 0.80]  # Left position of each column

    # Add metrics to the figure - ensure all are left-aligned
    for col_idx, column in enumerate(metrics_columns):
        x_pos = column_positions[col_idx]  # Use fixed position for consistent spacing

        for row_idx, metric in enumerate(column):
            # Spacing between rows
            y_offset = -0.05 - 0.05 * row_idx
            y_pos = base_y_position + y_offset

            # Format the label and value
            formatted_value = metric["format"].format(metric["value"])

            # Color for estimated days
            text_color = font_color
            if "Est. Days" in metric["label"]:
                if (
                    "Items" in metric["label"]
                    and metrics_data["pert_time_items"]
                    > metrics_data["days_to_deadline"]
                ):
                    text_color = "red"
                elif (
                    "Points" in metric["label"]
                    and metrics_data["pert_time_points"]
                    > metrics_data["days_to_deadline"]
                ):
                    text_color = "red"

            # Add the metric to the figure with explicit left alignment for all columns
            fig.add_annotation(
                xref="paper",
                yref="paper",
                x=x_pos,
                y=y_pos,
                text=f"<b>{metric['label']}:</b> {formatted_value}",
                showarrow=False,
                font=dict(
                    size=value_font_size, color=text_color, family="Arial, sans-serif"
                ),
                align="left",
                xanchor="left",  # Explicitly set left anchor for text alignment
            )

    # Update the figure margin to accommodate the metrics area
    fig.update_layout(
        margin=dict(b=180)  # Increase bottom margin to make room for added metrics
    )

    return fig


def create_forecast_plot(df, total_items, total_points, pert_factor, deadline_str):
    """
    Create the complete forecast plot with all components.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        deadline_str: Deadline date as string (YYYY-MM-DD)

    Returns:
        Tuple of (figure, pert_time_items, pert_time_points)
    """
    # Ensure proper date format for deadline
    deadline = pd.to_datetime(deadline_str)

    # Prepare all data needed for the visualization
    forecast_data = prepare_forecast_data(df, total_items, total_points, pert_factor)

    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add all traces to the figure
    traces = create_plot_traces(forecast_data)
    for trace in traces:
        fig.add_trace(trace["data"], secondary_y=trace["secondary_y"])

    # Add deadline marker and configure axes
    fig = add_deadline_marker(fig, deadline)
    fig = configure_axes(fig, forecast_data)
    fig = apply_layout_settings(fig)

    # Calculate days to deadline for metrics
    current_date = datetime.now()
    days_to_deadline = max(0, (deadline - current_date).days)

    # Calculate average and median weekly metrics for display
    avg_weekly_items, avg_weekly_points = 0, 0
    med_weekly_items, med_weekly_points = 0, 0
    if not df.empty:
        # Get all four values from calculate_weekly_averages
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(df.to_dict("records"))
        )

    # Add metrics data to the plot
    metrics_data = {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline.strftime("%Y-%m-%d"),
        "days_to_deadline": days_to_deadline,
        "pert_time_items": forecast_data["pert_time_items"],
        "pert_time_points": forecast_data["pert_time_points"],
        "avg_weekly_items": avg_weekly_items,
        "avg_weekly_points": avg_weekly_points,
        "med_weekly_items": med_weekly_items,
        "med_weekly_points": med_weekly_points,
    }

    fig = add_metrics_annotations(fig, metrics_data)

    return fig, forecast_data["pert_time_items"], forecast_data["pert_time_points"]


#######################################################################
# UI COMPONENT FUNCTIONS
#######################################################################


def create_info_tooltip(id_suffix, help_text):
    """
    Create an information tooltip component.

    Args:
        id_suffix: Suffix for the component ID
        help_text: Text to display in the tooltip

    Returns:
        Dash component with tooltip
    """
    return html.Div(
        [
            html.I(
                className="fas fa-info-circle text-info ml-2",
                id=f"info-tooltip-{id_suffix}",
                style={"cursor": "pointer", "marginLeft": "5px"},
            ),
            dbc.Tooltip(
                help_text,
                target=f"info-tooltip-{id_suffix}",
                placement="right",
                style={"maxWidth": "300px"},
            ),
        ],
        style={"display": "inline-block"},
    )


def create_help_modal():
    """
    Create the help modal with all content sections.

    Returns:
        Dash Modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader("How to Use the Project Burndown Forecast App"),
            dbc.ModalBody(
                [
                    # Overview section
                    html.Div(
                        [
                            html.H5("Overview", className="border-bottom pb-2 mb-3"),
                            html.P(
                                [
                                    "This application helps you forecast project completion based on historical progress.",
                                    html.Br(),
                                    "It uses the ",
                                    html.Strong("PERT methodology"),
                                    " to estimate when your project will be completed based on optimistic, pessimistic, and most likely scenarios.",
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Input Parameters section
                    html.Div(
                        [
                            html.H5(
                                "Input Parameters", className="border-bottom pb-2 mb-3"
                            ),
                            html.Div(
                                [
                                    html.H6(
                                        html.Strong("PERT Factor:"), className="mt-3"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "Determines how many data points to use for optimistic and pessimistic estimates"
                                            ),
                                            html.Li(
                                                "Higher value considers more historical data points"
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Range:"),
                                                    " 3-15 (default: 3)",
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(html.Strong("Deadline:"), className="mt-3"),
                                    html.Ul(
                                        [
                                            html.Li("Set your project deadline here"),
                                            html.Li(
                                                "The app will show if you're on track to meet it"
                                            ),
                                            html.Li(
                                                [html.Strong("Format:"), " YYYY-MM-DD"]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Total Items:"), className="mt-3"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The total number of items (tasks, stories, etc.) to be completed"
                                            ),
                                            html.Li(
                                                [
                                                    html.Em(
                                                        "This represents work quantity"
                                                    )
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Total Points:"), className="mt-3"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The total number of points (effort, complexity) to be completed"
                                            ),
                                            html.Li(
                                                [
                                                    html.Em(
                                                        "This represents work effort/complexity"
                                                    )
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Estimated Items:"),
                                        className="mt-3",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The number of items that have been estimated with points"
                                            ),
                                            html.Li(
                                                "Used to calculate average points per item and the total points"
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Estimated Points:"),
                                        className="mt-3",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The sum of points for the items that have been estimated"
                                            ),
                                            html.Li(
                                                "Used along with Estimated Items to calculate the average"
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # CSV Upload section with improved formatting
                    html.Div(
                        [
                            html.H5(
                                "CSV Upload Format", className="border-bottom pb-2 mb-3"
                            ),
                            html.Div(
                                [
                                    html.P(
                                        [
                                            html.Strong(
                                                "Your CSV file should contain the following columns:"
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Strong("date:"),
                                                    " Date of work completed (YYYY-MM-DD format)",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("no_items:"),
                                                    " Number of items completed on that date",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("no_points:"),
                                                    " Number of points completed on that date",
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.P(
                                        [
                                            "The file can use ",
                                            html.Em("semicolon (;)"),
                                            " or ",
                                            html.Em("comma (,)"),
                                            " as separators.",
                                        ],
                                        className="mb-2",
                                    ),
                                    html.P(html.Strong("Example:"), className="mb-1"),
                                    html.Pre(
                                        """date;no_items;no_points
2025-03-01;5;50
2025-03-02;7;70""",
                                        className="bg-light p-3 border rounded",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Statistics Table section
                    html.Div(
                        [
                            html.H5(
                                "Working with the Statistics Table",
                                className="border-bottom pb-2 mb-3",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        html.Strong(
                                            "This table shows your historical data. You can:"
                                        ),
                                        className="mb-2",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Strong("Edit any cell"),
                                                    " by clicking on it",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Delete rows"),
                                                    " with the 'x' button",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Add new rows"),
                                                    " with the 'Add Row' button",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Sort"),
                                                    " by clicking column headers",
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Note:"),
                                            " Changes to this data will update the forecast ",
                                            html.Em("immediately"),
                                            ".",
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.P(
                                                html.Strong("Column definitions:"),
                                                className="mb-1",
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li("Date: YYYY-MM-DD format"),
                                                    html.Li(
                                                        "Items: Number of work items completed"
                                                    ),
                                                    html.Li(
                                                        "Points: Effort points completed"
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="bg-light p-3 border rounded",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Understanding the Forecast Graph
                    html.Div(
                        [
                            html.H5(
                                "Understanding the Forecast Graph",
                                className="border-bottom pb-2 mb-3",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        html.Strong(
                                            "The graph shows your burndown forecast based on historical data:"
                                        ),
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                className="row",
                                                children=[
                                                    html.Div(
                                                        className="col-6",
                                                        children=[
                                                            html.H6(
                                                                "Lines:",
                                                                className="mt-2 mb-2",
                                                            ),
                                                            html.Ul(
                                                                [
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Solid lines:"
                                                                            ),
                                                                            " Historical progress",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Dashed lines:"
                                                                            ),
                                                                            " Most likely forecast",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Dotted lines:"
                                                                            ),
                                                                            " Optimistic and pessimistic forecasts",
                                                                        ]
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        className="col-6",
                                                        children=[
                                                            html.H6(
                                                                "Colors:",
                                                                className="mt-2 mb-2",
                                                            ),
                                                            html.Ul(
                                                                [
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Items: "
                                                                            ),
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "items"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Blue (history/likely), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "optimistic"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Teal (optimistic), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "pessimistic"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Purple (pessimistic)",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Points: "
                                                                            ),
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "points"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Orange (history/likely), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": "rgb(184, 134, 11)"
                                                                                },
                                                                            ),
                                                                            " Gold (optimistic), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": "rgb(165, 42, 42)"
                                                                                },
                                                                            ),
                                                                            " Brown (pessimistic)",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Deadline: "
                                                                            ),
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "deadline"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Red vertical line",
                                                                        ]
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="bg-light p-3 border rounded mb-3",
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Project Metrics:"),
                                            html.Br(),
                                            "The graph displays key metrics below the chart, including:",
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "Total Items and Points (whole numbers)"
                                                    ),
                                                    html.Li(
                                                        "Deadline and days remaining"
                                                    ),
                                                    html.Li(
                                                        "Estimated completion days for Items and Points"
                                                    ),
                                                    html.Li(
                                                        "Average and Median weekly Items/Points (last 10 weeks)"
                                                    ),
                                                ]
                                            ),
                                            html.Strong("Status Indicators:"),
                                            " Estimated days appear in ",
                                            html.Span(
                                                "green",
                                                style={
                                                    "color": "green",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " when on track to meet the deadline, and in ",
                                            html.Span(
                                                "red",
                                                style={
                                                    "color": "red",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " when at risk of missing the deadline.",
                                        ],
                                        className="mt-3 mb-0",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ]
                    ),
                ]
            ),
            dbc.ModalFooter(dbc.Button("Close", id="close-help", className="ml-auto")),
        ],
        id="help-modal",
        size="lg",
    )


def create_forecast_graph_card():
    """
    Create the forecast graph card component with customized download filename.

    Returns:
        Dash Card component with the forecast graph
    """
    # Generate the current date for the filename
    current_date = datetime.now().strftime("%Y%m%d")
    default_filename = f"burndown_forecast_{current_date}"

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Forecast Graph", className="d-inline"),
                    create_info_tooltip(
                        "forecast-graph", HELP_TEXTS["forecast_explanation"]
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="forecast-graph",
                        style={"height": "650px"},
                        config={
                            # Only specify the filename, let Plotly handle the rest of the export settings
                            "toImageButtonOptions": {
                                "filename": default_filename,
                            },
                        },
                    ),
                ]
            ),
        ],
        className="mb-3 shadow-sm",
    )


def create_forecast_info_card():
    """
    Create the forecast methodology information card component with enhanced explanations.

    Returns:
        Dash Card component with detailed forecast methodology explanation
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Forecast Information", className="d-inline"),
                    create_info_tooltip(
                        "forecast-info",
                        "Detailed explanation of how to interpret the forecast graph.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Forecast Methodology: "),
                                    "PERT (Program Evaluation and Review Technique) estimation based on your historical performance data. ",
                                    "The forecast uses three scenarios:",
                                ],
                                className="mb-2",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Optimistic: "),
                                            html.Span(
                                                "Teal",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "optimistic"
                                                    ],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for items, ",
                                            html.Span(
                                                "Gold",
                                                style={
                                                    "color": "rgb(184, 134, 11)",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for points. Based on your best performance periods (20% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Most Likely: "),
                                            html.Span(
                                                "Blue",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for items, ",
                                            html.Span(
                                                "Orange",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for points. Based on your average performance (50% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Pessimistic: "),
                                            html.Span(
                                                "Purple",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "pessimistic"
                                                    ],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for items, ",
                                            html.Span(
                                                "Brown",
                                                style={
                                                    "color": "rgb(165, 42, 42)",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for points. Based on your slowest performance periods (80% confidence level).",
                                        ]
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Reading the Graph: "),
                                    "Solid lines show historical data. Dashed and dotted lines show forecasts. ",
                                    "Where these lines cross zero indicates estimated completion dates.",
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Color Coding for Estimates: "),
                                    "Estimated days appear in ",
                                    html.Span(
                                        "green",
                                        style={"color": "green", "fontWeight": "bold"},
                                    ),
                                    " when on track to meet the deadline, and in ",
                                    html.Span(
                                        "red",
                                        style={"color": "red", "fontWeight": "bold"},
                                    ),
                                    " when at risk of missing the deadline. The red vertical line represents your deadline date.",
                                ],
                                className="mb-0",
                            ),
                        ],
                        style={"textAlign": "left"},
                    )
                ],
                className="py-3",  # Slightly more padding for better readability
            ),
        ],
        className="mb-3 shadow-sm",
    )


def create_pert_analysis_card():
    """
    Create the PERT analysis card component.

    Returns:
        Dash Card component for PERT analysis
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("PERT Analysis", className="d-inline"),
                    create_info_tooltip(
                        "pert-info",
                        "PERT (Program Evaluation and Review Technique) estimates project completion time based on optimistic, pessimistic, and most likely scenarios.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(id="pert-info-container", className="text-center"),
                ]
            ),
        ],
        className="mb-3 h-100 shadow-sm",
    )


def create_pert_info_table(
    pert_time_items,
    pert_time_points,
    days_to_deadline,
    avg_weekly_items=0,
    avg_weekly_points=0,
    med_weekly_items=0,
    med_weekly_points=0,
    pert_factor=3,  # Add default value
):
    """
    Create the PERT information table.

    Args:
        pert_time_items: PERT estimate for items (days)
        pert_time_points: PERT estimate for points (days)
        days_to_deadline: Days remaining until deadline
        avg_weekly_items: Average weekly items completed (last 10 weeks)
        avg_weekly_points: Average weekly points completed (last 10 weeks)
        med_weekly_items: Median weekly items completed (last 10 weeks)
        med_weekly_points: Median weekly points completed (last 10 weeks)
        pert_factor: Number of data points used for optimistic/pessimistic scenarios

    Returns:
        Dash component with PERT information table
    """
    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    return html.Div(
        [
            html.Table(
                [
                    html.Tbody(
                        [
                            # PERT formula as first row in the table
                            html.Tr(
                                [
                                    html.Td(
                                        "PERT Formula:",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            dcc.Markdown(
                                                r"$E = \frac{O + 4M + P}{6}$",
                                                mathjax=True,
                                                style={"display": "inline-block"},
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Estimated Days (Items):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{pert_time_items:.1f}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={
                                            "color": items_color,
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Estimated Days (Points):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{pert_time_points:.1f}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={
                                            "color": points_color,
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Deadline in:",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{days_to_deadline}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add separator between deadline and metrics
                            html.Tr(
                                [
                                    html.Td(
                                        html.Hr(style={"margin": "10px 0"}),
                                        colSpan=2,
                                    )
                                ]
                            ),
                            # Add Average Weekly Items
                            html.Tr(
                                [
                                    html.Td(
                                        "Avg Weekly Items (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{avg_weekly_items}",
                                            html.Span(
                                                " items/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add Median Weekly Items (NEW)
                            html.Tr(
                                [
                                    html.Td(
                                        "Med Weekly Items (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{med_weekly_items}",
                                            html.Span(
                                                " items/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add Average Weekly Points
                            html.Tr(
                                [
                                    html.Td(
                                        "Avg Weekly Points (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{avg_weekly_points}",
                                            html.Span(
                                                " points/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add Median Weekly Points (NEW)
                            html.Tr(
                                [
                                    html.Td(
                                        "Med Weekly Points (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{med_weekly_points}",
                                            html.Span(
                                                " points/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Removed the forecast methodology explanation and "Green means..." text
                            # as they are now in the Forecast Info card
                        ]
                    )
                ],
                className="table table-borderless",
                style={
                    "margin": "0 auto",
                    "width": "auto",
                    "border": "1px solid #eee",
                    "borderRadius": "5px",
                    "padding": "10px",
                },
            )
        ]
    )


#######################################################################
# APPLICATION SETUP
#######################################################################

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",  # Font Awesome for icons
    ],
)


# Layout function that gets fresh data on each load
def serve_layout():
    """
    Serve a fresh layout with the latest data from disk.
    This is crucial for proper browser refresh behavior.
    """
    # Load fresh data from disk each time the layout is served
    current_settings = load_settings()
    current_statistics = load_statistics()

    # Calculate total points based on estimated values (for initial display)
    estimated_total_points, avg_points_per_item = calculate_total_points(
        current_settings["total_items"],
        current_settings["estimated_items"],
        current_settings["estimated_points"],
        current_statistics,
    )

    return dbc.Container(
        [
            # Page initialization complete flag (hidden)
            dcc.Store(id="app-init-complete", data=False),
            # Persistent storage for the current data
            dcc.Store(id="current-settings", data=current_settings),
            dcc.Store(id="current-statistics", data=current_statistics),
            # Store for calculation results
            dcc.Store(
                id="calculation-results",
                data={
                    "total_points": estimated_total_points,
                    "avg_points_per_item": avg_points_per_item,
                },
            ),
            # Sticky Help Button in top-right corner
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="fas fa-question-circle mr-2"),
                            "How to Use This App",
                        ],
                        id="help-button",
                        color="info",
                        size="sm",
                        className="shadow",
                    ),
                ],
                style={
                    "position": "fixed",
                    "top": "20px",
                    "right": "20px",
                    "zIndex": "1000",
                },
            ),
            # App header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                "Project Burndown Forecast",
                                className="text-center my-4",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Help modal
            create_help_modal(),
            # First row: Forecast Graph
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_forecast_graph_card(),
                        ],
                        width=12,
                    ),
                ]
            ),
            # New row: Forecast Info Card
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_forecast_info_card(),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Second row: Input Parameters and PERT Analysis
            dbc.Row(
                [
                    # Left: Input Parameters
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4(
                                                "Input Parameters", className="d-inline"
                                            ),
                                            create_info_tooltip(
                                                "parameters",
                                                "Change these values to adjust your project forecast.",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # PERT factor and Deadline (unchanged)
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "PERT Factor:",
                                                                    create_info_tooltip(
                                                                        "pert-factor",
                                                                        HELP_TEXTS[
                                                                            "pert_factor"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dcc.Slider(
                                                                id="pert-factor-slider",
                                                                min=3,
                                                                max=15,
                                                                value=current_settings[
                                                                    "pert_factor"
                                                                ],
                                                                marks={
                                                                    i: str(i)
                                                                    for i in range(
                                                                        3, 16, 2
                                                                    )
                                                                },
                                                                step=1,
                                                            ),
                                                        ],
                                                        width=12,
                                                        lg=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Deadline:",
                                                                    create_info_tooltip(
                                                                        "deadline",
                                                                        HELP_TEXTS[
                                                                            "deadline"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dcc.DatePickerSingle(
                                                                id="deadline-picker",
                                                                date=current_settings[
                                                                    "deadline"
                                                                ],
                                                                display_format="YYYY-MM-DD",
                                                                className="form-control",
                                                            ),
                                                        ],
                                                        width=12,
                                                        lg=6,
                                                    ),
                                                ]
                                            ),
                                            html.Br(),
                                            # REDESIGNED: Estimated Items and Total Items in one row
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Estimated Items:",
                                                                    create_info_tooltip(
                                                                        "estimated-items",
                                                                        HELP_TEXTS[
                                                                            "estimated_items"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.Input(
                                                                id="estimated-items-input",
                                                                type="number",
                                                                value=current_settings[
                                                                    "estimated_items"
                                                                ],
                                                                min=0,
                                                                step=1,
                                                            ),
                                                        ],
                                                        width=12,
                                                        lg=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Total Items:",
                                                                    create_info_tooltip(
                                                                        "total-items",
                                                                        HELP_TEXTS[
                                                                            "total_items"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.Input(
                                                                id="total-items-input",
                                                                type="number",
                                                                value=current_settings[
                                                                    "total_items"
                                                                ],
                                                                min=0,
                                                                step=1,
                                                            ),
                                                        ],
                                                        width=12,
                                                        lg=6,
                                                    ),
                                                ]
                                            ),
                                            html.Br(),
                                            # REDESIGNED: Estimated Points and Total Points in one row
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Estimated Points:",
                                                                    create_info_tooltip(
                                                                        "estimated-points",
                                                                        HELP_TEXTS[
                                                                            "estimated_points"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.Input(
                                                                id="estimated-points-input",
                                                                type="number",
                                                                value=current_settings[
                                                                    "estimated_points"
                                                                ],
                                                                min=0,
                                                                step=1,
                                                            ),
                                                        ],
                                                        width=12,
                                                        lg=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Total Points (calculated):",
                                                                    create_info_tooltip(
                                                                        "total-points",
                                                                        HELP_TEXTS[
                                                                            "total_points"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.Input(
                                                                        id="total-points-display",
                                                                        value=f"{estimated_total_points:.0f}",
                                                                        disabled=True,
                                                                        style={
                                                                            "backgroundColor": "#f8f9fa"
                                                                        },
                                                                    ),
                                                                    dbc.InputGroupText(
                                                                        html.I(
                                                                            className="fas fa-calculator"
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Small(
                                                                id="points-calculation-info",
                                                                children=[
                                                                    f"Using {avg_points_per_item:.1f} points per item for calculation"
                                                                ],
                                                                className="text-muted mt-1 d-block",
                                                            ),
                                                        ],
                                                        width=12,
                                                        lg=6,
                                                    ),
                                                ]
                                            ),
                                            html.Br(),
                                            # CSV Upload section (unchanged)
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Upload Statistics CSV:",
                                                                    create_info_tooltip(
                                                                        "csv-upload",
                                                                        HELP_TEXTS[
                                                                            "csv_format"
                                                                        ],
                                                                    ),
                                                                ]
                                                            ),
                                                            dcc.Upload(
                                                                id="upload-data",
                                                                children=html.Div(
                                                                    [
                                                                        html.I(
                                                                            className="fas fa-file-upload mr-2"
                                                                        ),
                                                                        "Drag and Drop or ",
                                                                        html.A(
                                                                            "Select CSV File"
                                                                        ),
                                                                    ]
                                                                ),
                                                                style={
                                                                    "width": "100%",
                                                                    "height": "60px",
                                                                    "lineHeight": "60px",
                                                                    "borderWidth": "1px",
                                                                    "borderStyle": "dashed",
                                                                    "borderRadius": "5px",
                                                                    "textAlign": "center",
                                                                    "margin": "10px 0",
                                                                },
                                                                multiple=False,
                                                            ),
                                                        ],
                                                        width=12,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3 h-100 shadow-sm",
                            ),
                        ],
                        width=7,
                    ),
                    # Right: PERT Analysis
                    dbc.Col(
                        [
                            create_pert_analysis_card(),
                        ],
                        width=5,
                    ),
                ]
            ),
            # Spacer
            html.Div(className="mb-3"),
            # Third row: Statistics Data Table
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4(
                                                "Statistics Data", className="d-inline"
                                            ),
                                            create_info_tooltip(
                                                "statistics-data",
                                                HELP_TEXTS["statistics_table"],
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dash_table.DataTable(
                                                id="statistics-table",
                                                columns=[
                                                    {
                                                        "name": "Date (YYYY-MM-DD)",
                                                        "id": "date",
                                                        "type": "text",
                                                    },
                                                    {
                                                        "name": "Items Completed",
                                                        "id": "no_items",
                                                        "type": "numeric",
                                                    },
                                                    {
                                                        "name": "Points Completed",
                                                        "id": "no_points",
                                                        "type": "numeric",
                                                    },
                                                ],
                                                data=current_statistics,
                                                editable=True,
                                                row_deletable=True,
                                                sort_action="native",
                                                # Add default sorting by date, descending order (newest first)
                                                sort_by=[
                                                    {
                                                        "column_id": "date",
                                                        "direction": "desc",
                                                    }
                                                ],
                                                # Add pagination
                                                page_size=10,
                                                page_action="native",
                                                style_table={"overflowX": "auto"},
                                                style_cell={
                                                    "textAlign": "center",
                                                    "minWidth": "100px",
                                                    "padding": "10px",
                                                },
                                                style_header={
                                                    "backgroundColor": "#f8f9fa",
                                                    "fontWeight": "bold",
                                                    "border": "1px solid #ddd",
                                                },
                                                style_data={
                                                    "border": "1px solid #ddd",
                                                },
                                                style_data_conditional=[
                                                    {
                                                        "if": {"row_index": "odd"},
                                                        "backgroundColor": "#f9f9f9",
                                                    }
                                                ],
                                                tooltip_data=[
                                                    {
                                                        column: {
                                                            "value": "Click to edit",
                                                            "type": "text",
                                                        }
                                                        for column in [
                                                            "date",
                                                            "no_items",
                                                            "no_points",
                                                        ]
                                                    }
                                                    for _ in range(
                                                        len(current_statistics)
                                                    )
                                                ],
                                                tooltip_duration=None,
                                            ),
                                            html.Div(
                                                [
                                                    # Just one button for adding rows
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className="fas fa-plus mr-2"
                                                            ),
                                                            "Add Row",
                                                        ],
                                                        id="add-row-button",
                                                        color="primary",
                                                        className="mt-3",
                                                    ),
                                                ],
                                                style={"textAlign": "center"},
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Footer
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Hr(),
                        ],
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
    )


# Set the layout function as the app's layout
app.layout = serve_layout

#######################################################################
# CALLBACKS
#######################################################################


@app.callback(Output("app-init-complete", "data"), [Input("forecast-graph", "figure")])
def mark_initialization_complete(figure):
    """
    Mark the application as fully initialized after the graph is rendered.
    This prevents saving during initial load and avoids triggering callbacks prematurely.
    """
    return True


# Add new callback to update the total points calculation (moved from bottom of file)
@app.callback(
    [
        Output("total-points-display", "value"),
        Output("points-calculation-info", "children"),
        Output("calculation-results", "data"),
    ],
    [
        Input("total-items-input", "value"),
        Input("estimated-items-input", "value"),
        Input("estimated-points-input", "value"),
        Input("current-statistics", "modified_timestamp"),
    ],
    [
        State("current-statistics", "data"),
        State("calculation-results", "data"),
    ],
)
def update_total_points_calculation(
    total_items, estimated_items, estimated_points, stats_ts, statistics, calc_results
):
    """
    Update the total points calculation based on estimated items and points or historical data.

    Args:
        total_items: Total number of items in the project
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        stats_ts: Timestamp for statistics changes (trigger)
        statistics: Current statistics data
        calc_results: Previous calculation results

    Returns:
        Tuple of (formatted total points, calculation info text, updated calculation data)
    """
    # Input validation
    if None in [total_items, estimated_items, estimated_points]:
        # Return previous values if any input is None
        return (
            f"{calc_results.get('total_points', 0):.0f}",
            f"Using {calc_results.get('avg_points_per_item', 0):.1f} points per item for calculation",
            calc_results,
        )

    # Handle invalid inputs by converting to numbers
    try:
        total_items = int(total_items)
        estimated_items = int(estimated_items)
        estimated_points = float(estimated_points)
    except (ValueError, TypeError):
        # Return previous values if conversion fails
        return (
            f"{calc_results.get('total_points', 0)::.0f}",
            f"Using {calc_results.get('avg_points_per_item', 0):.1f} points per item for calculation",
            calc_results,
        )

    # Calculate total points and average
    estimated_total_points, avg_points_per_item = calculate_total_points(
        total_items, estimated_items, estimated_points, statistics
    )

    # Prepare info text with source of calculation and styling
    style = {"color": "inherit"}  # Default styling
    if estimated_items <= 0:
        info_text = f"Using {avg_points_per_item:.1f} points per item (based on historical data)"
    else:
        # If estimated items exceeds total, show a warning
        if estimated_items > total_items:
            info_text = (
                f"Warning: Estimated items ({estimated_items}) exceeds total items ({total_items}). "
                f"Using {avg_points_per_item:.1f} points per item."
            )
            style = {"color": "#dc3545"}  # Bootstrap danger red
        else:
            percent_estimated = (
                (estimated_items / total_items) * 100 if total_items > 0 else 0
            )
            # Add confidence level based on percentage estimated
            confidence = "low"
            if percent_estimated >= 75:
                confidence = "high"
                style = {"color": "#28a745"}  # Bootstrap success green
            elif percent_estimated >= 30:
                confidence = "medium"
                style = {"color": "#ffc107"}  # Bootstrap warning yellow

            info_text = (
                f"Using {avg_points_per_item:.1f} points per item "
                f"({percent_estimated:.0f}% of items estimated, {confidence} confidence)"
            )

    # Update the calculation results store
    updated_calc_results = {
        "total_points": estimated_total_points,
        "avg_points_per_item": avg_points_per_item,
    }

    # Return with styled info text
    return (
        f"{estimated_total_points:.0f}",
        html.Span(info_text, style=style),
        updated_calc_results,
    )


@app.callback(
    [
        Output("current-settings", "data"),
        Output("current-settings", "modified_timestamp"),
    ],
    [
        Input("pert-factor-slider", "value"),
        Input("deadline-picker", "date"),
        Input("total-items-input", "value"),
        Input("calculation-results", "data"),  # Use calculated total points
        Input("estimated-items-input", "value"),
        Input("estimated-points-input", "value"),
    ],
    [State("app-init-complete", "data")],
)
def update_and_save_settings(
    pert_factor,
    deadline,
    total_items,
    calc_results,
    estimated_items,
    estimated_points,
    init_complete,
):
    """
    Update current settings and save to disk when changed.
    """
    ctx = dash.callback_context

    # Skip if not initialized or values are None
    if (
        not init_complete
        or not ctx.triggered
        or None
        in [pert_factor, deadline, total_items, estimated_items, estimated_points]
    ):
        raise PreventUpdate

    # Get total points from calculation results
    total_points = calc_results.get("total_points", DEFAULT_TOTAL_POINTS)

    # Create updated settings
    settings = {
        "pert_factor": pert_factor,
        "deadline": deadline,
        "total_items": total_items,
        "total_points": total_points,
        "estimated_items": estimated_items,
        "estimated_points": estimated_points,
    }

    # Save to disk
    save_settings(
        pert_factor,
        deadline,
        total_items,
        total_points,
        estimated_items,
        estimated_points,
    )

    logger.info(f"Settings updated and saved: {settings}")
    return settings, int(datetime.now().timestamp() * 1000)


@app.callback(
    [
        Output("current-statistics", "data"),
        Output("current-statistics", "modified_timestamp"),
    ],
    [Input("statistics-table", "data")],
    [State("app-init-complete", "data")],
)
def update_and_save_statistics(data, init_complete):
    """
    Update current statistics and save to disk when changed.
    """
    ctx = dash.callback_context

    # Skip if not initialized or no data
    if not init_complete or not ctx.triggered or not data:
        raise PreventUpdate

    # Save to disk
    save_statistics(data)
    logger.info("Statistics updated and saved")
    return data, int(datetime.now().timestamp() * 1000)


@app.callback(
    Output("statistics-table", "data"),
    [Input("add-row-button", "n_clicks"), Input("upload-data", "contents")],
    [State("statistics-table", "data"), State("upload-data", "filename")],
)
def update_table(n_clicks, contents, rows, filename):
    """
    Update the statistics table data when a row is added or data is uploaded.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        # No triggers, return unchanged
        return rows

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    try:
        # Add a new row with a smart date calculation
        if trigger_id == "add-row-button":
            if not rows:
                # If no existing rows, use today's date
                new_date = datetime.now().strftime("%Y-%m-%d")
            else:
                # Find the most recent date
                try:
                    date_objects = [
                        datetime.strptime(row["date"], "%Y-%m-%d")
                        for row in rows
                        if row["date"] and len(row["date"]) == 10
                    ]
                    if date_objects:
                        most_recent_date = max(date_objects)
                        # Set new date to 7 days after the most recent
                        new_date = (most_recent_date + timedelta(days=7)).strftime(
                            "%Y-%m-%d"
                        )
                    else:
                        new_date = datetime.now().strftime("%Y-%m-%d")
                except ValueError:
                    # Handle any date parsing errors
                    new_date = datetime.now().strftime("%Y-%m-%d")

            # Insert at beginning (will be at top with desc sorting)
            rows.insert(
                0,
                {
                    "date": new_date,
                    "no_items": 0,
                    "no_points": 0,
                },
            )
            return rows

        elif trigger_id == "upload-data" and contents:
            # Parse uploaded file
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            if "csv" in filename.lower():
                try:
                    # Try semicolon separator first
                    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep=";")
                    if (
                        "date" not in df.columns
                        or "no_items" not in df.columns
                        or "no_points" not in df.columns
                    ):
                        # Try with comma separator
                        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

                    # Clean data and ensure date is in YYYY-MM-DD format
                    df = read_and_clean_data(df)
                    return df.to_dict("records")
                except Exception as e:
                    logger.error(f"Error loading CSV file: {e}")
                    # Return unchanged data if there's an error
                    return rows
    except Exception as e:
        logger.error(f"Error in update_table callback: {e}")
    return rows


@app.callback(
    [Output("forecast-graph", "figure"), Output("pert-info-container", "children")],
    [
        Input("current-settings", "modified_timestamp"),
        Input("current-statistics", "modified_timestamp"),
        Input("calculation-results", "data"),
    ],
    [State("current-settings", "data"), State("current-statistics", "data")],
)
def update_graph_and_pert_info(
    settings_ts, statistics_ts, calc_results, settings, statistics
):
    """
    Update the forecast graph and PERT analysis when settings or statistics change.
    """
    if not settings or not statistics:
        raise PreventUpdate

    try:
        # Create dataframe from statistics data
        df = pd.DataFrame(statistics)

        # Get values from settings
        pert_factor = settings["pert_factor"]
        total_items = settings["total_items"]
        # Use calculated total points from calc_results if available
        total_points = calc_results.get("total_points", settings["total_points"])
        deadline = settings["deadline"]

        # Process data for calculations
        if not df.empty:
            df = compute_cumulative_values(df, total_items, total_points)

        # Create forecast plot and get PERT values
        fig, pert_time_items, pert_time_points = create_forecast_plot(
            df=df,
            total_items=total_items,
            total_points=total_points,
            pert_factor=pert_factor,
            deadline_str=deadline,
        )

        # Calculate days to deadline
        deadline_date = pd.to_datetime(deadline)
        current_date = datetime.now()
        days_to_deadline = max(0, (deadline_date - current_date).days)

        # Calculate average and median weekly metrics
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(statistics)
        )

        # Create PERT info component
        pert_info = create_pert_info_table(
            pert_time_items,
            pert_time_points,
            days_to_deadline,
            avg_weekly_items,
            avg_weekly_points,
            med_weekly_items,
            med_weekly_points,
            pert_factor,  # Pass pert_factor to the function
        )

        return fig, pert_info
    except Exception as e:
        logger.error(f"Error in update_graph_and_pert_info callback: {e}")
        # Return empty figure and error message on failure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error generating forecast: {str(e)}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="red"),
        )
        error_info = html.Div(
            [html.P("Error calculating PERT values", style={"color": "red"})]
        )
        return fig, error_info


@app.callback(
    Output("help-modal", "is_open"),
    [Input("help-button", "n_clicks"), Input("close-help", "n_clicks")],
    [State("help-modal", "is_open")],
)
def toggle_help_modal(n1, n2, is_open):
    """
    Toggle the help modal visibility.
    """
    if n1 or n2:
        return not is_open
    return is_open


#######################################################################
# MAIN
#######################################################################

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
