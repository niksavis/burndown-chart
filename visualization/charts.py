"""
Visualization Charts Module

This module contains functions to create and customize various chart types
including capacity charts, burnup charts, and other visualization components.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Application imports
from configuration import COLOR_PALETTE
from ui.tooltip_utils import create_hoverlabel_config, format_hover_template

# Mobile optimization removed for simplicity - will implement via CSS and responsive config

#######################################################################
# CHART CREATION FUNCTIONS
#######################################################################


def create_capacity_chart(capacity_data, forecast_data, settings):
    """
    Create a chart visualizing team capacity against forecasted work.

    Args:
        capacity_data (dict): Dictionary with capacity metrics
        forecast_data (dict): Dictionary with forecasted work
        settings (dict): Application settings

    Returns:
        plotly.graph_objects.Figure: Capacity chart
    """
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Extract dates and convert to datetime objects
    dates = [
        pd.to_datetime(date, format="mixed", errors="coerce")
        for date in forecast_data.get("dates", [])
    ]

    if not dates:
        # If no forecast data, return empty chart with message
        fig.add_annotation(
            text="No forecast data available.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # Calculate weekly capacity line (constant)
    team_capacity = capacity_data.get("weekly_capacity", 0)
    capacity_line = [team_capacity] * len(dates)

    # Extract forecasted work requirements
    forecasted_items = forecast_data.get("forecasted_items", [])
    forecasted_points = forecast_data.get("forecasted_points", [])

    # Calculate required hours based on hours per item/point
    hours_per_item = capacity_data.get("avg_hours_per_item", 0)
    hours_per_point = capacity_data.get("avg_hours_per_point", 0)

    items_hours = [items * hours_per_item for items in forecasted_items]
    points_hours = [points * hours_per_point for points in forecasted_points]

    # Create capacity line (constant team capacity)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=capacity_line,
            mode="lines",
            name="Team Capacity",
            line=dict(color="rgba(0, 200, 0, 0.8)", width=2, dash="dash"),
            hovertemplate=format_hover_template(
                title="Team Capacity",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("success"),
        ),
        secondary_y=False,
    )

    # Create items-based required capacity
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=items_hours,
            mode="lines",
            name="Required (Items)",
            line=dict(color=COLOR_PALETTE["items"], width=2),
            fill="tozeroy",
            hovertemplate=format_hover_template(
                title="Items Work Hours",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=False,
    )

    # Create points-based required capacity
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=points_hours,
            mode="lines",
            name="Required (Points)",
            line=dict(color=COLOR_PALETTE["points"], width=2),
            fill="tozeroy",
            hovertemplate=format_hover_template(
                title="Points Work Hours",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=False,
    )

    # Add utilization percentage on secondary y-axis
    max_utilization = (
        max(
            max(items_hours + [0.1]) / team_capacity if team_capacity else 1,
            max(points_hours + [0.1]) / team_capacity if team_capacity else 1,
            1,
        )
        * 100
    )

    # Utilization threshold lines
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[100] * len(dates),
            mode="lines",
            name="100% Utilization",
            line=dict(color="rgba(255, 165, 0, 0.8)", width=1.5, dash="dot"),
            hovertemplate=format_hover_template(
                title="Utilization Threshold",
                fields={
                    "Threshold": "100%",
                },
            ),
            hoverlabel=create_hoverlabel_config("warning"),
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[85] * len(dates),
            mode="lines",
            name="85% Target Utilization",
            line=dict(color="rgba(0, 128, 0, 0.6)", width=1.5, dash="dot"),
            hovertemplate=format_hover_template(
                title="Utilization Target",
                fields={
                    "Target": "85%",
                },
            ),
            hoverlabel=create_hoverlabel_config("success"),
        ),
        secondary_y=True,
    )

    # Calculate utilization percentages
    items_utilization = [
        (hours / team_capacity * 100) if team_capacity else 0 for hours in items_hours
    ]
    points_utilization = [
        (hours / team_capacity * 100) if team_capacity else 0 for hours in points_hours
    ]

    # Add utilization percentages traces
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=items_utilization,
            mode="lines",
            name="Items Utilization %",
            line=dict(color=COLOR_PALETTE["items"], width=1.5),
            visible=True,
            hovertemplate=format_hover_template(
                title="Items Utilization",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Utilization": "%{y:.1f}%",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=points_utilization,
            mode="lines",
            name="Points Utilization %",
            line=dict(color=COLOR_PALETTE["points"], width=1.5),
            visible=True,
            hovertemplate=format_hover_template(
                title="Points Utilization",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Utilization": "%{y:.1f}%",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=True,
    )

    # Customize axis labels
    fig.update_layout(
        title="Team Capacity vs. Forecasted Work",
        xaxis_title="Date",
        yaxis_title="Hours per Week",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified",
        margin=dict(l=60, r=60, t=50, b=50),
        hoverlabel=dict(font_size=14),
    )

    fig.update_yaxes(title_text="Hours per Week", secondary_y=False)

    fig.update_yaxes(
        title_text="Utilization (%)",
        secondary_y=True,
        range=[
            0,
            max(max_utilization * 1.1, 110),
        ],  # Set scale to maximum utilization + 10%
    )

    return fig


def create_chart_with_loading(
    id, figure=None, loading_state=None, type="default", height=None
):
    """
    Create a chart component with built-in loading states.

    Args:
        id (str): Component ID for the chart
        figure (dict, optional): Initial Plotly figure
        loading_state (dict, optional): Loading state information
        type (str): Chart type (default, bar, line, scatter)
        height (str, optional): Chart height

    Returns:
        html.Div: Chart component with loading states
    """
    from dash import dcc
    from ui.loading_utils import create_loading_overlay

    # Determine if we're in a loading state
    is_loading = loading_state is not None and loading_state.get("is_loading", False)

    # Create appropriate loading message based on chart type
    loading_messages = {
        "default": "Loading chart...",
        "bar": "Generating bar chart...",
        "line": "Preparing line chart...",
        "scatter": "Creating scatter plot...",
        "pie": "Building pie chart...",
        "area": "Creating area chart...",
    }
    message = loading_messages.get(type, "Loading chart...")

    # Create the chart component
    chart = dcc.Graph(
        id=id,
        figure=figure or {},
        config={
            "displayModeBar": True,
            "responsive": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"{id.replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "scale": 2,
            },
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
        },
        style={"height": height or "100%", "width": "100%"},
    )

    # Wrap the chart with a loading state
    return create_loading_overlay(
        children=chart,
        style_key="primary",
        size_key="lg",
        text=message,
        is_loading=is_loading,
        opacity=0.7,
        className=f"{id}-loading-wrapper",
    )


def format_hover_template_fix(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):
    """
    Create a consistent hover template string for Plotly charts.
    This version properly escapes format specifiers for Plotly.

    Args:
        title (str, optional): Title to display at the top of the tooltip
        fields (dict, optional): Dictionary of {label: value_template} pairs
        extra_info (str, optional): Additional information for the <extra> tag
        include_extra_tag (bool, optional): Whether to include the <extra> tag

    Returns:
        str: Formatted hover template string for Plotly
    """
    template = []

    # Add title if provided
    if title:
        template.append(f"<b>{title}</b><br>")

    # Add fields if provided
    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    # Join all template parts
    hover_text = "".join(template)

    # Add extra tag if requested
    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


# create_burnup_chart function removed - burnup functionality deprecated


def identify_significant_scope_growth(df, threshold_pct=10):
    """
    Identify periods with significant scope growth.

    Args:
        df: DataFrame with statistics data including cum_scope_items and cum_scope_points
        threshold_pct: Percentage threshold for significant growth (default: 10%)

    Returns:
        List of dictionaries with start_date and end_date for periods of significant growth
    """
    if df.empty:
        return []

    significant_periods = []
    current_period = None

    # Calculate percentage changes
    df = df.copy().sort_values("date")
    df["items_pct_change"] = df["cum_scope_items"].pct_change() * 100
    df["points_pct_change"] = df["cum_scope_points"].pct_change() * 100

    # Find periods with significant growth
    for i, row in df.iterrows():
        if (
            row["items_pct_change"] > threshold_pct
            or row["points_pct_change"] > threshold_pct
        ):
            if current_period is None:
                # Start a new significant period
                current_period = {
                    "start_date": row["date"],
                    "end_date": row["date"],
                    "max_items_pct": row["items_pct_change"]
                    if not pd.isna(row["items_pct_change"])
                    else 0,
                    "max_points_pct": row["points_pct_change"]
                    if not pd.isna(row["points_pct_change"])
                    else 0,
                }
            else:
                # Extend the current period
                current_period["end_date"] = row["date"]
                if (
                    not pd.isna(row["items_pct_change"])
                    and row["items_pct_change"] > current_period["max_items_pct"]
                ):
                    current_period["max_items_pct"] = row["items_pct_change"]
                if (
                    not pd.isna(row["points_pct_change"])
                    and row["points_pct_change"] > current_period["max_points_pct"]
                ):
                    current_period["max_points_pct"] = row["points_pct_change"]
        else:
            # End the current period if it exists
            if current_period is not None:
                # Only include periods that span at least one day
                if (
                    current_period["end_date"] - current_period["start_date"]
                ).days >= 0:
                    significant_periods.append(current_period)
                current_period = None

    # Handle case where last row is part of a significant period
    if current_period is not None:
        current_period["end_date"] = current_period["end_date"] + pd.Timedelta(days=1)
        significant_periods.append(current_period)

    return significant_periods


def prepare_visualization_data(
    df,
    total_items,
    total_points,
    pert_factor,
    data_points_count=None,
    is_burnup=False,
    scope_items=None,
    scope_points=None,
    show_points=True,
):
    """
    Prepare all necessary data for the forecast visualization.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        data_points_count: Number of most recent data points to use (defaults to all)
        is_burnup: Whether this is for a burnup chart (True) or burndown chart (False)
        scope_items: Total scope of items (required for burnup charts)
        scope_points: Total scope of points (required for burnup charts)
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        Dictionary containing all data needed for visualization
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # Import needed functions from data module
    from data.processing import (
        daily_forecast_burnup,
        compute_weekly_throughput,
        calculate_rates,
    )
    from utils.dataframe_utils import ensure_dataframe

    # Handle empty dataframe case
    if (
        df is None
        or (isinstance(df, pd.DataFrame) and df.empty)
        or (isinstance(df, list) and len(df) == 0)
    ):
        return {
            "df_calc": pd.DataFrame() if not isinstance(df, pd.DataFrame) else df,
            "pert_time_items": 0,
            "pert_time_points": 0,
            "items_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "points_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "max_items": total_items,
            "max_points": total_points,
            "start_date": datetime.now(),
            "last_items": total_items,
            "last_points": total_points,
        }

    # Convert to DataFrame if input is a list of dictionaries
    df_calc = ensure_dataframe(df)

    # Convert string dates to datetime for calculations
    df_calc["date"] = pd.to_datetime(df_calc["date"], format="mixed", errors="coerce")

    # Ensure data is sorted by date in ascending order
    df_calc = df_calc.sort_values("date", ascending=True)

    # Initialize scope variables
    total_scope_items = total_items
    total_scope_points = total_points

    # Calculate total scope by adding completed work and remaining work
    if not is_burnup:
        # For burndown charts, calculate completed work
        completed_items = (
            df_calc["completed_items"].sum()
            if "completed_items" in df_calc.columns
            else 0
        )
        completed_points = (
            df_calc["completed_points"].sum()
            if "completed_points" in df_calc.columns
            else 0
        )

        # Calculate total scope
        total_scope_items = completed_items + total_items
        total_scope_points = completed_points + total_points

        # PERFORMANCE OPTIMIZATION: Use vectorized operations instead of slow loop
        # Calculate remaining work by reverse cumsum (much faster than iterative approach)
        if (
            "completed_items" in df_calc.columns
            and "completed_points" in df_calc.columns
        ):
            # Ensure numeric types
            df_calc["completed_items"] = pd.to_numeric(
                df_calc["completed_items"], errors="coerce"
            ).fillna(0)
            df_calc["completed_points"] = pd.to_numeric(
                df_calc["completed_points"], errors="coerce"
            ).fillna(0)

            # Vectorized calculation: reverse cumsum to get remaining work at each point
            reversed_items = df_calc["completed_items"][::-1].cumsum()[::-1]
            reversed_points = df_calc["completed_points"][::-1].cumsum()[::-1]

            df_calc["cum_items"] = reversed_items + total_items
            df_calc["cum_points"] = reversed_points + total_points
        else:
            # Fallback if columns don't exist
            df_calc["cum_items"] = total_scope_items
            df_calc["cum_points"] = total_scope_points

    # Filter to use only the specified number of most recent data points
    # CRITICAL FIX: Use date-based filtering instead of row count (.iloc)
    # data_points_count represents WEEKS, not rows. With sparse data,
    # row-based filtering gives incorrect results.

    # Initialize logger early for debug logging
    import logging

    logger = logging.getLogger(__name__)

    if (
        data_points_count is not None
        and data_points_count > 0
        and not df_calc.empty
        and "date" in df_calc.columns
    ):
        # Apply date-based filtering
        latest_date = df_calc["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        rows_before = len(df_calc)
        df_calc = df_calc[df_calc["date"] >= cutoff_date]
        rows_after = len(df_calc)

        logger.info(
            f"[FORECAST FILTER] data_points_count={data_points_count} weeks, "
            f"latest_date={latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else latest_date}, "
            f"cutoff_date={cutoff_date.strftime('%Y-%m-%d') if hasattr(cutoff_date, 'strftime') else cutoff_date}, "
            f"rows: {rows_before} -> {rows_after}"
        )

    # Compute weekly throughput with the filtered data
    grouped = compute_weekly_throughput(df_calc)

    # Ensure grouped is a DataFrame
    if not isinstance(grouped, pd.DataFrame):
        grouped = pd.DataFrame(grouped)
    logger.info(
        f"[CHART DATA] df_calc rows={len(df_calc)}, grouped weeks={len(grouped)}, "
        f"data_points_count={data_points_count}, "
        f"grouped non-zero items={len(grouped[grouped['completed_items'] > 0])}, "
        f"grouped non-zero points={len(grouped[grouped['completed_points'] > 0])}"
    )

    # Filter out zero-value weeks before calculating rates
    # Filter separately for items and points to support projects with only one tracking type
    # Zero weeks (often from fill_missing_weeks) shouldn't influence rate calculations
    grouped_items_non_zero = grouped[grouped["completed_items"] > 0].copy()
    grouped_points_non_zero = grouped[grouped["completed_points"] > 0].copy()

    # Determine which filtering to use based on available data
    has_items_data = len(grouped_items_non_zero) > 0
    has_points_data = len(grouped_points_non_zero) > 0

    # If no valid weeks exist for either metric, return early with safe defaults
    # (prevents pessimistic forecasts from extending years into the future)
    if not has_items_data and not has_points_data:
        # Return empty forecast data to indicate insufficient data
        return {
            "df_calc": df_calc,
            "pert_time_items": 0,
            "pert_time_points": 0,
            "items_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "points_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "max_items": df_calc["cum_items"].max()
            if not df_calc.empty
            else total_items,
            "max_points": df_calc["cum_points"].max()
            if not df_calc.empty
            else total_points,
            "start_date": df_calc["date"].iloc[-1]
            if not df_calc.empty
            else datetime.now(),
            "last_items": df_calc["cum_items"].iloc[-1]
            if not df_calc.empty
            else total_items,
            "last_points": df_calc["cum_points"].iloc[-1]
            if not df_calc.empty
            else total_points,
        }

    # Use items data for calculation if available, otherwise use points data
    # This ensures we can calculate forecasts even when only one type has data
    grouped_non_zero = (
        grouped_items_non_zero if has_items_data else grouped_points_non_zero
    )

    rates = calculate_rates(
        grouped_non_zero, total_items, total_points, pert_factor, show_points
    )

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

    # Debug logging for forecast calculation
    logger.info(
        f"[CHART FORECAST] start_date={start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date}, "
        f"pert_time_items={pert_time_items:.2f}, total_items={total_items}, "
        f"items_daily_rate={items_daily_rate:.4f}"
    )

    # For burndown charts, we need to get the correct last values
    # (these represent remaining work, not completed work)
    if not is_burnup:
        last_items = (
            df_calc["cum_items"].iloc[-1] if not df_calc.empty else total_scope_items
        )
        last_points = (
            df_calc["cum_points"].iloc[-1] if not df_calc.empty else total_scope_points
        )
    else:
        # For burnup charts, use the completed work values
        last_completed_items = df_calc["cum_items"].iloc[-1] if not df_calc.empty else 0
        last_completed_points = (
            df_calc["cum_points"].iloc[-1] if not df_calc.empty else 0
        )
        last_items = last_completed_items  # This is completed items for burnup
        last_points = last_completed_points  # This is completed points for burnup

    # Use completed items/points values for burnup chart
    # PERFORMANCE: Limit forecast to 2 years (730 days) and max 100 points per line
    if is_burnup:
        # For burnup charts, start from completed values and forecast toward scope
        items_forecasts = {
            "avg": daily_forecast_burnup(
                last_items,
                items_daily_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            ),
            "opt": daily_forecast_burnup(
                last_items,
                optimistic_items_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            ),
            "pes": daily_forecast_burnup(
                last_items,
                pessimistic_items_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            ),
        }

        points_forecasts = {
            "avg": daily_forecast_burnup(
                last_points,
                points_daily_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            ),
            "opt": daily_forecast_burnup(
                last_points,
                optimistic_points_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            ),
            "pes": daily_forecast_burnup(
                last_points,
                pessimistic_points_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            ),
        }
    else:
        # For burndown charts, we need to ensure consistent end dates with burnup charts
        # First, calculate burnup forecasts to get end dates
        # PERFORMANCE: Limit forecast to 2 years (730 days) and max 100 points per line
        burnup_items_avg = daily_forecast_burnup(
            0, items_daily_rate, start_date, total_items, max_days=730, max_points=100
        )
        burnup_points_avg = daily_forecast_burnup(
            0, points_daily_rate, start_date, total_points, max_days=730, max_points=100
        )

        # Get the end dates from burnup forecasts
        items_end_date = burnup_items_avg[0][-1] if burnup_items_avg[0] else start_date
        points_end_date = (
            burnup_points_avg[0][-1] if burnup_points_avg[0] else start_date
        )

        logger.info(
            f"[CHART FORECAST] Burndown end dates: items_end_date={items_end_date.strftime('%Y-%m-%d') if hasattr(items_end_date, 'strftime') else items_end_date}, "
            f"days_to_items_end={(items_end_date - start_date).days if hasattr(items_end_date, 'strftime') else 0}"
        )

        # Now calculate burndown forecasts with fixed end dates
        items_forecasts = generate_burndown_forecast(
            last_items,
            items_daily_rate,
            optimistic_items_rate,
            pessimistic_items_rate,
            start_date,
            items_end_date,
        )

        points_forecasts = generate_burndown_forecast(
            last_points,
            points_daily_rate,
            optimistic_points_rate,
            pessimistic_points_rate,
            start_date,
            points_end_date,
        )

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

    # Y-axis now dynamically scales to actual data shown on chart
    # (removed fixed scope ceiling that was pushing graphs down)

    # Return results with scope information for burndown charts
    result = {
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

    # Add total scope information for burndown charts
    if not is_burnup:
        result["total_scope_items"] = total_scope_items
        result["total_scope_points"] = total_scope_points

    return result


def generate_burndown_forecast(
    last_value, avg_rate, opt_rate, pes_rate, start_date, end_date
):
    """
    Generate burndown forecast with a fixed end date to ensure consistency with burnup charts.
    Includes strict performance optimizations: 2-year max horizon, 100 points per line max.

    Args:
        last_value: Current remaining value (items or points)
        avg_rate: Average daily completion rate
        opt_rate: Optimistic daily completion rate
        pes_rate: Pessimistic daily completion rate
        start_date: Start date for forecast
        end_date: End date the forecast should reach (for alignment with burnup chart)

    Returns:
        Dictionary containing forecasts for average, optimistic, and pessimistic scenarios
    """
    # PERFORMANCE: Limit forecast to 2 years and max 100 points per line
    # This prevents chart freezing with thousands of data points
    MAX_FORECAST_DAYS = 730  # 2 years maximum
    MAX_POINTS_PER_LINE = 100  # Maximum data points per forecast line

    # Calculate days between start and end
    days_span = (end_date - start_date).days
    if days_span <= 0:
        # If end date is same as or before start date, use 1 day
        days_span = 1

    # Calculate days needed for each rate to reach zero, but cap at max
    days_to_zero_avg = min(
        MAX_FORECAST_DAYS,
        int(last_value / avg_rate) if avg_rate > 0.001 else days_span * 2,
    )
    days_to_zero_opt = min(
        MAX_FORECAST_DAYS,
        int(last_value / opt_rate) if opt_rate > 0.001 else days_span * 2,
    )
    days_to_zero_pes = min(
        MAX_FORECAST_DAYS,
        int(last_value / pes_rate) if pes_rate > 0.001 else days_span * 2,
    )

    # PERFORMANCE: Calculate sampling interval to limit data points
    def generate_sampled_forecast(days_to_zero, rate):
        """Generate forecast with even sampling throughout the entire forecast period."""
        # Calculate interval to distribute points evenly across entire forecast
        # This ensures consistent spacing from start to finish (no condensed-then-sparse appearance)
        sample_interval = max(1, int(days_to_zero / MAX_POINTS_PER_LINE))

        dates = []
        values = []
        day = 0

        # Sample evenly across the entire forecast period
        while day <= days_to_zero:
            forecast_date = start_date + timedelta(days=day)
            remaining = max(0, last_value - (rate * day))
            dates.append(forecast_date)
            values.append(remaining)

            # Stop if we reached zero
            if remaining <= 0:
                break

            day += sample_interval

        # Always ensure we have a final point at zero for visual closure
        if values and values[-1] > 0:
            final_date = start_date + timedelta(days=days_to_zero)
            dates.append(final_date)
            values.append(0)

        return dates, values

    # Generate forecasts with sampling
    dates_avg, avg_values = generate_sampled_forecast(days_to_zero_avg, avg_rate)
    dates_opt, opt_values = generate_sampled_forecast(days_to_zero_opt, opt_rate)
    dates_pes, pes_values = generate_sampled_forecast(days_to_zero_pes, pes_rate)

    # Debug logging
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"[BURNDOWN FORECAST] Generated forecasts: avg={len(dates_avg)} points, "
        f"opt={len(dates_opt)} points, pes={len(dates_pes)} points"
    )

    return {
        "avg": (dates_avg, avg_values),
        "opt": (dates_opt, opt_values),
        "pes": (dates_pes, pes_values),
    }


def _create_forecast_axes_titles(fig, forecast_data):
    """
    Configure the axis titles for the forecast plot.

    Args:
        fig: Plotly figure object
        forecast_data: Dictionary with forecast data

    Returns:
        Updated figure with configured axis titles
    """
    # Configure x-axis title
    fig.update_xaxes(
        title={"text": "Date", "font": {"size": 16}},
    )

    # Configure primary y-axis (items) title
    fig.update_yaxes(
        title={"text": "Remaining Items", "font": {"size": 16}},
        secondary_y=False,
    )

    # Configure secondary y-axis (points) title
    fig.update_yaxes(
        title={"text": "Remaining Points", "font": {"size": 16}},
        secondary_y=True,
    )

    return fig


def _calculate_forecast_completion_dates(pert_time_items, pert_time_points):
    """
    Calculate formatted completion dates based on PERT estimates.

    Args:
        pert_time_items: PERT time estimate for items in days
        pert_time_points: PERT time estimate for points in days

    Returns:
        Tuple of (items_completion_enhanced, points_completion_enhanced) strings
    """
    import math

    # Handle NaN, None, or invalid values
    if pert_time_items is None or (
        isinstance(pert_time_items, float) and math.isnan(pert_time_items)
    ):
        items_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        items_completion_date = current_date + timedelta(days=pert_time_items)
        items_completion_str = items_completion_date.strftime("%Y-%m-%d")
        items_completion_enhanced = f"{items_completion_str} ({pert_time_items:.1f} days, {pert_time_items / 7:.1f} weeks)"

    if pert_time_points is None or (
        isinstance(pert_time_points, float) and math.isnan(pert_time_points)
    ):
        points_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        points_completion_date = current_date + timedelta(days=pert_time_points)
        points_completion_str = points_completion_date.strftime("%Y-%m-%d")
        points_completion_enhanced = f"{points_completion_str} ({pert_time_points:.1f} days, {pert_time_points / 7:.1f} weeks)"

    return items_completion_enhanced, points_completion_enhanced


def _prepare_metrics_data(
    total_items,
    total_points,
    deadline,
    pert_time_items,
    pert_time_points,
    data_points_count,
    df,
    items_completion_enhanced,
    points_completion_enhanced,
    avg_weekly_items=0.0,
    avg_weekly_points=0.0,
    med_weekly_items=0.0,
    med_weekly_points=0.0,
):
    """
    Prepare metrics data for display in the forecast plot.

    Args:
        total_items: Total number of remaining items to complete
        total_points: Total number of remaining points to complete
        deadline: Deadline date
        pert_time_items: PERT time estimate for items in days
        pert_time_points: PERT time estimate for points in days
        data_points_count: Number of data points used in the forecast
        df: DataFrame with historical data
        items_completion_enhanced: Enhanced completion date string for items
        points_completion_enhanced: Enhanced completion date string for points
        avg_weekly_items: Average weekly completed items
        avg_weekly_points: Average weekly completed points
        med_weekly_items: Median weekly completed items
        med_weekly_points: Median weekly completed points

    Returns:
        Dictionary with metrics data
    """
    # Calculate days to deadline
    current_date = datetime.now()

    # Handle NaT deadline safely
    if pd.isna(deadline):
        days_to_deadline = 0
        deadline_str = "No deadline set"
    else:
        days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)
        deadline_str = deadline.strftime("%Y-%m-%d")

    # Calculate completed work from the dataframe
    completed_items = 0
    completed_points = 0

    if (
        not df.empty
        and "completed_items" in df.columns
        and "completed_points" in df.columns
    ):
        completed_items = (
            df["completed_items"].sum() if "completed_items" in df.columns else 0
        )
        completed_points = (
            df["completed_points"].sum() if "completed_points" in df.columns else 0
        )

    # Calculate total scope (completed + remaining)
    total_scope_items = completed_items + total_items
    total_scope_points = completed_points + total_points

    # Calculate completion percentage
    items_percent_complete = 0
    points_percent_complete = 0

    if total_scope_items > 0:
        items_percent_complete = (completed_items / total_scope_items) * 100

    if total_scope_points > 0:
        points_percent_complete = (completed_points / total_scope_points) * 100

    # Create metrics data dictionary with explicit float conversions for weekly metrics
    return {
        "total_items": total_items,
        "total_points": total_points,
        "total_scope_items": total_scope_items,
        "total_scope_points": total_scope_points,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "items_percent_complete": items_percent_complete,
        "points_percent_complete": points_percent_complete,
        "deadline": deadline_str,
        "days_to_deadline": days_to_deadline,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "avg_weekly_items": round(float(avg_weekly_items), 2),
        "avg_weekly_points": round(float(avg_weekly_points), 2),
        "med_weekly_items": round(float(med_weekly_items), 2),
        "med_weekly_points": round(float(med_weekly_points), 2),
        # Ensure string representations use 2 decimal places and never get converted to integers
        "avg_weekly_items_str": f"{float(avg_weekly_items):.2f}",
        "avg_weekly_points_str": f"{float(avg_weekly_points):.2f}",
        "med_weekly_items_str": f"{float(med_weekly_items):.2f}",
        "med_weekly_points_str": f"{float(med_weekly_points):.2f}",
        "data_points_used": int(data_points_count)
        if data_points_count is not None and isinstance(data_points_count, (int, float))
        else (len(df) if hasattr(df, "__len__") else 0),
        "data_points_available": len(df) if hasattr(df, "__len__") else 0,
        "items_completion_enhanced": items_completion_enhanced,
        "points_completion_enhanced": points_completion_enhanced,
    }


#######################################################################
# DASHBOARD VISUALIZATIONS (User Story 2)
#######################################################################


def create_pert_timeline_chart(pert_data: dict) -> go.Figure:
    """
    Create horizontal timeline visualization for PERT forecasts.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It creates an interactive timeline showing optimistic, most likely, and
    pessimistic completion dates with visual indicators for confidence range.

    Args:
        pert_data: PERTTimelineData dictionary from calculate_pert_timeline()

    Returns:
        go.Figure: Plotly figure with horizontal timeline

    Example:
        >>> pert_data = calculate_pert_timeline(stats, settings)
        >>> fig = create_pert_timeline_chart(pert_data)

    Chart Features:
        - Horizontal bar showing date range
        - Markers for optimistic, most likely, pessimistic dates
        - PERT weighted average highlighted
        - Confidence range shading
    """
    from datetime import datetime

    # Parse dates
    try:
        optimistic = (
            datetime.strptime(pert_data["optimistic_date"], "%Y-%m-%d")
            if pert_data.get("optimistic_date")
            else None
        )
        most_likely = (
            datetime.strptime(pert_data["most_likely_date"], "%Y-%m-%d")
            if pert_data.get("most_likely_date")
            else None
        )
        pessimistic = (
            datetime.strptime(pert_data["pessimistic_date"], "%Y-%m-%d")
            if pert_data.get("pessimistic_date")
            else None
        )
        pert_estimate = (
            datetime.strptime(pert_data["pert_estimate_date"], "%Y-%m-%d")
            if pert_data.get("pert_estimate_date")
            else None
        )
    except (ValueError, TypeError):
        # Return empty chart if dates are invalid
        fig = go.Figure()
        fig.add_annotation(
            text="No forecast data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        return fig

    if not all([optimistic, most_likely, pessimistic, pert_estimate]):
        # Return empty chart if dates are missing
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for timeline forecast",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        return fig

    # Create figure
    fig = go.Figure()

    # Add confidence range bar (optimistic to pessimistic)
    fig.add_trace(
        go.Scatter(
            x=[optimistic, pessimistic],
            y=[0, 0],
            mode="lines",
            line=dict(color="rgba(13, 110, 253, 0.2)", width=20),
            name="Confidence Range",
            showlegend=True,
            hovertemplate="Range: %{x}<extra></extra>",
        )
    )

    # Add markers for key dates
    scenarios = [
        (optimistic, "Optimistic", "green", "circle"),
        (most_likely, "Most Likely", "blue", "diamond"),
        (pert_estimate, "PERT Estimate", "purple", "star"),
        (pessimistic, "Pessimistic", "orange", "circle"),
    ]

    for date, label, color, symbol in scenarios:
        fig.add_trace(
            go.Scatter(
                x=[date],
                y=[0],
                mode="markers+text",
                marker=dict(
                    size=15,
                    color=color,
                    symbol=symbol,
                    line=dict(width=2, color="white"),
                ),
                text=[label],
                textposition="top center",
                name=label,
                showlegend=True,
                hovertemplate=f"<b>{label}</b><br>Date: %{{x|%Y-%m-%d}}<br>Days: {pert_data.get(label.lower().replace(' ', '_') + '_days', 'N/A')}<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title="PERT Timeline Forecast",
        xaxis=dict(
            title="Completion Date",
            type="date",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.5, 0.5],
        ),
        height=300,
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


#######################################################################
# MOBILE OPTIMIZATION HELPERS (Phase 7: User Story 5)
#######################################################################


def get_mobile_chart_config(is_mobile=False, is_tablet=False):
    """
    Get mobile-optimized chart configuration for Plotly graphs.

    This function provides responsive chart configurations that optimize
    chart display for different viewport sizes by adjusting margins,
    legends, and interactive features.

    Args:
        is_mobile: Whether the viewport is mobile (<768px)
        is_tablet: Whether the viewport is tablet (768-992px)

    Returns:
        dict: Plotly graph config object optimized for viewport

    Example:
        >>> config = get_mobile_chart_config(is_mobile=True)
        >>> dcc.Graph(figure=fig, config=config)
    """
    if is_mobile:
        # Mobile configuration: show toolbar with standard buttons
        return {
            "displayModeBar": True,
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "showTips": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
        }
    elif is_tablet:
        # Tablet configuration: show standard toolbar
        return {
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "displaylogo": False,
        }
    else:
        # Desktop configuration: standard toolbar
        return {
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "displaylogo": False,
        }


def get_mobile_chart_layout(
    is_mobile=False, is_tablet=False, show_legend=True, title=None
):
    """
    Get mobile-optimized layout configuration for Plotly charts.

    Adjusts margins, font sizes, legend placement, and other layout
    properties based on viewport size for optimal mobile experience.

    Args:
        is_mobile: Whether the viewport is mobile (<768px)
        is_tablet: Whether the viewport is tablet (768-992px)
        show_legend: Whether to show legend (automatically hidden on mobile)
        title: Chart title (optional, hidden on mobile to save space)

    Returns:
        dict: Plotly layout updates to merge with existing layout

    Example:
        >>> mobile_layout = get_mobile_chart_layout(is_mobile=True)
        >>> fig.update_layout(**mobile_layout)
    """
    if is_mobile:
        # Mobile layout: minimal margins, no legend, compact
        return {
            "margin": dict(l=40, r=10, t=30 if title else 10, b=40),
            "showlegend": False,  # Hide legend on mobile to maximize chart space
            "font": dict(size=10),  # Smaller font for mobile
            "title": dict(
                text=title if title else None,
                font=dict(size=14),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "height": 300,  # Fixed height for mobile
            "hovermode": "closest",  # Closest point for touch precision
        }
    elif is_tablet:
        # Tablet layout: moderate margins, bottom legend
        return {
            "margin": dict(
                l=50, r=20, t=50 if title else 20, b=80 if show_legend else 50
            ),
            "showlegend": show_legend,
            "font": dict(size=12),
            "title": dict(
                text=title if title else None,
                font=dict(size=16),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "legend": dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
            )
            if show_legend
            else None,
            "height": 400,
            "hovermode": "x unified",
        }
    else:
        # Desktop layout: standard margins and configuration
        return {
            "margin": dict(
                l=60, r=30, t=80 if title else 30, b=100 if show_legend else 60
            ),
            "showlegend": show_legend,
            "font": dict(size=13),
            "title": dict(
                text=title if title else None,
                font=dict(size=18),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "legend": dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="right",
                x=1.15,
            )
            if show_legend
            else None,
            "height": 500,
            "hovermode": "x unified",
        }


def apply_mobile_optimization(fig, is_mobile=False, is_tablet=False, title=None):
    """
    Apply mobile optimization to an existing Plotly figure.

    This is a convenience function that applies both config and layout
    optimizations to a figure in one call.

    Args:
        fig: Plotly figure object to optimize
        is_mobile: Whether the viewport is mobile (<768px)
        is_tablet: Whether the viewport is tablet (768-992px)
        title: Optional chart title

    Returns:
        tuple: (optimized_figure, config_dict) ready for dcc.Graph

    Example:
        >>> fig = create_forecast_plot(...)
        >>> optimized_fig, config = apply_mobile_optimization(fig, is_mobile=True)
        >>> dcc.Graph(figure=optimized_fig, config=config)
    """
    # Get mobile-optimized layout
    layout_updates = get_mobile_chart_layout(
        is_mobile=is_mobile, is_tablet=is_tablet, show_legend=not is_mobile, title=title
    )

    # Apply layout updates
    fig.update_layout(**layout_updates)

    # Get config
    config = get_mobile_chart_config(is_mobile=is_mobile, is_tablet=is_tablet)

    return fig, config
