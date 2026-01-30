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
