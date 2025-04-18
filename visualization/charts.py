"""
Visualization Charts Module

This module contains functions to create and customize the forecast chart
with all its components like traces, markers, and metrics annotations.
"""

#######################################################################
# IMPORTS
#######################################################################
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# Import from other modules
from configuration import COLOR_PALETTE
from data import (
    prepare_forecast_data,
    calculate_weekly_averages,
    generate_weekly_forecast,
)

# Import add_deadline_marker from elements module to avoid duplication
from visualization.elements import add_deadline_marker

#######################################################################
# CHART CREATION FUNCTIONS
#######################################################################


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
    base_y_position = -0.28  # Changed from -0.2 to -0.28 to move metrics box lower
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
                if "Items" in metric["label"]:
                    if (
                        metrics_data["pert_time_items"]
                        > metrics_data["days_to_deadline"]
                    ):
                        text_color = "red"
                    else:
                        text_color = "green"
                elif "Points" in metric["label"]:
                    if (
                        metrics_data["pert_time_points"]
                        > metrics_data["days_to_deadline"]
                    ):
                        text_color = "red"
                    else:
                        text_color = "green"

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


def create_forecast_plot(
    df, total_items, total_points, pert_factor, deadline_str, data_points_count=None
):
    """
    Create the complete forecast plot with all components.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        deadline_str: Deadline date as string (YYYY-MM-DD)
        data_points_count: Number of most recent data points to use (defaults to all)

    Returns:
        Tuple of (figure, pert_time_items, pert_time_points)
    """
    # Ensure proper date format for deadline
    deadline = pd.to_datetime(deadline_str)

    # Prepare all data needed for the visualization
    forecast_data = prepare_forecast_data(
        df, total_items, total_points, pert_factor, data_points_count
    )

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
    avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
        0,
        0,
        0,
        0,
    )
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
        "data_points_used": data_points_count
        if data_points_count is not None
        else len(df),
        "data_points_available": len(df),
    }

    fig = add_metrics_annotations(fig, metrics_data)

    return fig, forecast_data["pert_time_items"], forecast_data["pert_time_points"]


def create_weekly_items_chart(
    statistics_data, date_range_weeks=None, pert_factor=3, include_forecast=True
):
    """
    Create a bar chart showing weekly completed items with optional forecast for the next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        date_range_weeks: Number of weeks to display (None for all)
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)

    Returns:
        Plotly figure object with the weekly items chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Completed Items (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Items Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"])

    # Filter by date range if specified
    if date_range_weeks:
        latest_date = df["date"].max()
        start_date = latest_date - timedelta(weeks=date_range_weeks)
        df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(items=("no_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

    # Calculate weighted moving average (last 4 weeks)
    # More weight given to recent weeks using exponential weights
    if len(weekly_df) >= 4:
        # Create a copy of items column for calculation
        values = weekly_df["items"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Create the figure
    fig = go.Figure()

    # Add bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["items"],
            marker_color=COLOR_PALETTE["items"],
            name="Completed Items",
            text=weekly_df["items"],
            textposition="outside",
            customdata=weekly_df["week_label"],  # Add custom data for hover template
            hovertemplate="Week of %{customdata}<br>Items: %{y}<extra></extra>",
        )
    )

    # Add weighted moving average line if we have enough data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        # Create a separate trace for the weighted average line
        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#0047AB",  # Cobalt blue - darker shade of blue
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df[
                    "week_label"
                ],  # Add custom data for hover template
                hovertemplate="Week of %{customdata}<br>Weighted Avg: %{y:.1f}<extra></extra>",
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data
        forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

        if forecast_data["items"]["dates"]:
            # Most likely forecast - only display the single bar for the next week
            fig.add_trace(
                go.Bar(
                    x=forecast_data["items"]["dates"],
                    y=forecast_data["items"]["most_likely"],
                    marker_color=COLOR_PALETTE["items"],
                    marker_pattern_shape="x",  # Add pattern to distinguish forecast
                    opacity=0.7,
                    name="Next Week Forecast",
                    text=[
                        round(val, 1) for val in forecast_data["items"]["most_likely"]
                    ],
                    textposition="outside",
                    hovertemplate="Forecast for %{x}<br>Items: %{y:.1f}<extra></extra>",
                )
            )

            # Add vertical line between historical and forecast data
            fig.add_vline(
                x=len(weekly_df["week_label"])
                - 0.5,  # Position between last historical and first forecast
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.5)",
                annotation_text="Forecast starts",
                annotation_position="top",
            )

            # Add methodology annotation
            fig.add_annotation(
                x=0.5,
                y=-0.35,  # Changed from -0.32 to -0.35 to match the Weekly Completed Points chart
                xref="paper",
                yref="paper",
                text=(
                    f"<b>Next Week Forecast:</b> Based on PERT analysis with weighted average of historical data.<br>"
                    f"Most Likely: {forecast_data['items'].get('most_likely_value', 0):.1f} items/week | "
                    f"Optimistic: {forecast_data['items'].get('optimistic_value', 0):.1f} items/week | "
                    f"Pessimistic: {forecast_data['items'].get('pessimistic_value', 0):.1f} items/week"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=6,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )

    # Update layout with grid lines and styling
    fig.update_layout(
        title="Weekly Completed Items with Next Week Forecast",
        xaxis_title="Week",
        yaxis_title="Items Completed",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        margin=dict(
            b=130
        ),  # Significantly increased bottom margin to prevent info box cutoff
        height=650,  # Explicitly set height to ensure enough space for the info box
    )

    return fig


def create_weekly_points_chart(
    statistics_data, date_range_weeks=None, pert_factor=3, include_forecast=True
):
    """
    Create a bar chart showing weekly completed points with a weighted moving average line and optional forecast for next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        date_range_weeks: Number of weeks to display (None for all)
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)

    Returns:
        Plotly figure object with the weekly points chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Completed Points (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Points Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"])

    # Filter by date range if specified
    if date_range_weeks:
        latest_date = df["date"].max()
        start_date = latest_date - timedelta(weeks=date_range_weeks)
        df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(points=("no_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

    # Calculate weighted moving average (last 4 weeks)
    # More weight given to recent weeks using exponential weights
    if len(weekly_df) >= 4:
        # Create a copy of points column for calculation
        values = weekly_df["points"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Create the figure
    fig = go.Figure()

    # Add bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["points"],
            marker_color=COLOR_PALETTE["points"],
            name="Completed Points",
            text=weekly_df["points"],
            textposition="outside",
            customdata=weekly_df["week_label"],  # Add custom data for hover template
            hovertemplate="Week of %{customdata}<br>Points: %{y}<extra></extra>",
        )
    )

    # Add weighted moving average line if we have enough data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        # Create a separate trace for the weighted average line
        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#FF6347",  # Tomato color
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df[
                    "week_label"
                ],  # Add custom data for hover template
                hovertemplate="Week of %{customdata}<br>Weighted Avg: %{y:.1f}<extra></extra>",
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data
        forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

        if forecast_data["points"]["dates"]:
            # Get points forecast for next week
            most_likely = forecast_data["points"]["most_likely"]
            optimistic = forecast_data["points"]["optimistic"]
            pessimistic = forecast_data["points"]["pessimistic"]

            # Calculate confidence interval bounds (25% of difference)
            upper_bound = [
                ml + 0.25 * (opt - ml) for ml, opt in zip(most_likely, optimistic)
            ]
            lower_bound = [
                ml - 0.25 * (ml - pes) for ml, pes in zip(most_likely, pessimistic)
            ]

            # Single next week forecast with confidence interval
            fig.add_trace(
                go.Bar(
                    x=forecast_data["points"]["dates"],
                    y=most_likely,
                    marker_color=COLOR_PALETTE["points"],
                    marker_pattern_shape="x",  # Add pattern to distinguish forecast
                    opacity=0.7,
                    name="Next Week Forecast",
                    text=[round(val, 1) for val in most_likely],
                    textposition="outside",
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[u - ml for u, ml in zip(upper_bound, most_likely)],
                        arrayminus=[ml - l for ml, l in zip(most_likely, lower_bound)],
                        color="rgba(0, 0, 0, 0.3)",
                    ),
                    hovertemplate=(
                        "Forecast for %{x}<br>"
                        "Points: %{y:.1f}<br>"
                        "Confidence Interval: [%{error_y.arrayminus:.1f}, %{error_y.array:.1f}]"
                        "<extra></extra>"
                    ),
                )
            )

            # Add vertical line between historical and forecast data
            fig.add_vline(
                x=len(weekly_df["week_label"])
                - 0.5,  # Position between last historical and first forecast
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.5)",
                annotation_text="Forecast starts",
                annotation_position="top",
            )

            # Add methodology annotation
            fig.add_annotation(
                x=0.5,
                y=-0.35,  # Moved down from -0.25 to prevent covering x-axis label
                xref="paper",
                yref="paper",
                text=(
                    f"<b>Next Week Forecast:</b> Based on PERT analysis with weighted average of historical data.<br>"
                    f"Most Likely: {forecast_data['points'].get('most_likely_value', 0):.1f} points/week | "
                    f"Optimistic: {forecast_data['points'].get('optimistic_value', 0):.1f} points/week | "
                    f"Pessimistic: {forecast_data['points'].get('pessimistic_value', 0):.1f} points/week"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=6,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )

    # Update layout with grid lines and styling
    fig.update_layout(
        title="Weekly Completed Points with Next Week Forecast",
        xaxis_title="Week",
        yaxis_title="Points Completed",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        margin=dict(
            b=130
        ),  # Significantly increased bottom margin to prevent info box cutoff
        height=650,  # Explicitly set height to ensure enough space for the info box
    )

    return fig


def create_weekly_items_forecast_chart(
    statistics_data, pert_factor=3, date_range_weeks=None
):
    """
    Create a chart showing weekly completed items with a 4-week forecast.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        date_range_weeks: Number of weeks of historical data to display (None for all)

    Returns:
        Plotly figure object with the weekly items forecast chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Items Forecast (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Items Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"])

    # Filter by date range if specified
    if date_range_weeks:
        latest_date = df["date"].max()
        start_date = latest_date - timedelta(weeks=date_range_weeks)
        df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(items=("no_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

    # Generate forecast data
    forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

    # Create the figure
    fig = go.Figure()

    # Add historical data as bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["items"],
            marker_color=COLOR_PALETTE["items"],
            name="Completed Items",
            text=weekly_df["items"],
            textposition="outside",
            hovertemplate="Week of %{x}<br>Items: %{y}<extra></extra>",
        )
    )

    # Add forecast data if available
    if forecast_data["items"]["dates"]:
        # Most likely forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["items"]["dates"],
                y=forecast_data["items"]["most_likely"],
                marker_color=COLOR_PALETTE["items"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.7,
                name="Most Likely Forecast",
                text=[round(val, 1) for val in forecast_data["items"]["most_likely"]],
                textposition="outside",
                hovertemplate="Week of %{x}<br>Items (Most Likely): %{y:.1f}<extra></extra>",
            )
        )

        # Optimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["items"]["dates"],
                y=forecast_data["items"]["optimistic"],
                marker_color=COLOR_PALETTE["optimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Optimistic Forecast",
                text=[round(val, 1) for val in forecast_data["items"]["optimistic"]],
                textposition="outside",
                hovertemplate="Week of %{x}<br>Items (Optimistic): %{y:.1f}<extra></extra>",
            )
        )

        # Pessimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["items"]["dates"],
                y=forecast_data["items"]["pessimistic"],
                marker_color=COLOR_PALETTE["pessimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Pessimistic Forecast",
                text=[round(val, 1) for val in forecast_data["items"]["pessimistic"]],
                textposition="outside",
                hovertemplate="Week of %{x}<br>Items (Pessimistic): %{y:.1f}<extra></extra>",
            )
        )

    # Add vertical line between historical and forecast data
    if weekly_df["week_label"].any() and forecast_data["items"]["dates"]:
        fig.add_vline(
            x=len(weekly_df["week_label"])
            - 0.5,  # Position between last historical and first forecast
            line_dash="dash",
            line_color="rgba(0, 0, 0, 0.5)",
            annotation_text="Forecast starts",
            annotation_position="top",
        )

    # Update layout with grid lines, styling, and forecast explanation
    fig.update_layout(
        title="Weekly Items Forecast (Next 4 Weeks)",
        xaxis_title="Week Starting",
        yaxis_title="Items Completed",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        annotations=[
            dict(
                x=0.5,
                y=-0.3,
                xref="paper",
                yref="paper",
                text=(
                    f"<b>Forecast Methodology:</b> Based on PERT analysis using historical data.<br>"
                    f"<b>Most Likely:</b> {forecast_data['items'].get('most_likely_value', 0):.1f} items/week (historical average)<br>"
                    f"<b>Optimistic:</b> {forecast_data['items'].get('optimistic_value', 0):.1f} items/week<br>"
                    f"<b>Pessimistic:</b> {forecast_data['items'].get('pessimistic_value', 0)::.1f} items/week"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=8,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )
        ],
        margin=dict(b=100),  # Add more bottom margin for the forecast explanation
    )

    return fig


def create_weekly_points_forecast_chart(
    statistics_data, pert_factor=3, date_range_weeks=None
):
    """
    Create a chart showing weekly completed points with a 4-week forecast.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        date_range_weeks: Number of weeks of historical data to display (None for all)

    Returns:
        Plotly figure object with the weekly points forecast chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Points Forecast (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Points Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"])

    # Filter by date range if specified
    if date_range_weeks:
        latest_date = df["date"].max()
        start_date = latest_date - timedelta(weeks=date_range_weeks)
        df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(points=("no_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

    # Calculate weighted moving average (last 4 weeks)
    if len(weekly_df) >= 4:
        values = weekly_df["points"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Generate forecast data
    forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

    # Create the figure
    fig = go.Figure()

    # Add historical data as bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["points"],
            marker_color=COLOR_PALETTE["points"],
            name="Completed Points",
            text=weekly_df["points"],
            textposition="outside",
            hovertemplate="Week of %{x}<br>Points: %{y}<extra></extra>",
        )
    )

    # Add weighted moving average line if we have enough historical data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#FF6347",  # Tomato color
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df[
                    "week_label"
                ],  # Add custom data for hover template
                hovertemplate="Week of %{customdata}<br>Weighted Avg: %{y:.1f}<extra></extra>",
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add forecast data if available
    if forecast_data["points"]["dates"]:
        # Create confidence interval for the most likely forecast
        most_likely = forecast_data["points"]["most_likely"]
        optimistic = forecast_data["points"]["optimistic"]
        pessimistic = forecast_data["points"]["pessimistic"]

        # Calculate upper and lower bounds for confidence interval (25% of difference)
        upper_bound = [
            ml + 0.25 * (opt - ml) for ml, opt in zip(most_likely, optimistic)
        ]
        lower_bound = [
            ml - 0.25 * (ml - pes) for ml, pes in zip(most_likely, pessimistic)
        ]

        # Most likely forecast with confidence interval
        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=most_likely,
                marker_color=COLOR_PALETTE["points"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.7,
                name="Most Likely Forecast",
                text=[round(val, 1) for val in most_likely],
                textposition="outside",
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[u - ml for u, ml in zip(upper_bound, most_likely)],
                    arrayminus=[ml - l for ml, l in zip(most_likely, lower_bound)],
                    color="rgba(0, 0, 0, 0.3)",
                ),
                hovertemplate=(
                    "Forecast for %{x}<br>"
                    "Points: %{y:.1f}<br>"
                    "Confidence Interval: [%{error_y.arrayminus:.1f}, %{error_y.array:.1f}]"
                    "<extra></extra>"
                ),
            )
        )

        # Optimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=optimistic,
                marker_color=COLOR_PALETTE["optimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Optimistic Forecast",
                text=[round(val, 1) for val in optimistic],
                textposition="outside",
                hovertemplate="Week of %{x}<br>Points (Optimistic): %{y:.1f}<extra></extra>",
            )
        )

        # Pessimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=pessimistic,
                marker_color=COLOR_PALETTE["pessimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Pessimistic Forecast",
                text=[round(val, 1) for val in pessimistic],
                textposition="outside",
                hovertemplate="Week of %{x}<br>Points (Pessimistic): %{y:.1f}<extra></extra>",
            )
        )

    # Add vertical line between historical and forecast data
    if weekly_df["week_label"].any() and forecast_data["points"]["dates"]:
        fig.add_vline(
            x=len(weekly_df["week_label"])
            - 0.5,  # Position between last historical and first forecast
            line_dash="dash",
            line_color="rgba(0, 0, 0, 0.5)",
            annotation_text="Forecast starts",
            annotation_position="top",
        )

    # Update layout with grid lines, styling, and forecast explanation
    fig.update_layout(
        title="Weekly Points Forecast (Next 4 Weeks)",
        xaxis_title="Week Starting",
        yaxis_title="Points Completed",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        annotations=[
            dict(
                x=0.5,
                y=-0.3,
                xref="paper",
                yref="paper",
                text=(
                    f"<b>Forecast Methodology:</b> Based on PERT analysis using historical data.<br>"
                    f"<b>Most Likely:</b> {forecast_data['points'].get('most_likely_value', 0):.1f} points/week (historical average)<br>"
                    f"<b>Optimistic:</b> {forecast_data['points'].get('optimistic_value', 0):.1f} points/week<br>"
                    f"<b>Pessimistic:</b> {forecast_data['points'].get('pessimistic_value', 0):.1f} points/week<br>"
                    f"<b>Weighted Average:</b> More weight given to recent data (40% for most recent week, 30%, 20%, 10% for earlier weeks)"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=8,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )
        ],
        margin=dict(b=120),  # More bottom margin for the forecast explanation
    )

    return fig


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
    dates = [pd.to_datetime(date) for date in forecast_data.get("dates", [])]

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
            hoverinfo="name+y",
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
            hoverinfo="name+y",
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
            visible="legendonly",  # Hidden by default
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
            visible="legendonly",  # Hidden by default
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
