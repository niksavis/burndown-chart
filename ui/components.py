"""
UI Components Module

This module provides reusable UI components like tooltips, modals, and information tables
that are used across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
from dash import html, dcc
import dash_bootstrap_components as dbc

# Application imports
from configuration import COLOR_PALETTE
from ui.icon_utils import create_icon_text
from ui.styles import create_form_feedback_style
from ui.button_utils import create_button

# Define common trend icons and colors
TREND_ICONS = {
    "stable": "fas fa-equals",
    "up": "fas fa-arrow-up",
    "down": "fas fa-arrow-down",
}

TREND_COLORS = {
    "stable": "#6c757d",  # Gray
    "up": "#28a745",  # Green
    "down": "#dc3545",  # Red
}

#######################################################################
# PERT INFO TABLE COMPONENT
#######################################################################


# Add these utility functions to help with PERT table components without breaking existing functionality
def _create_header_with_icon(icon_class, title, color="#20c997"):
    """Create a header with an icon for PERT info sections."""
    return html.H5(
        [
            html.I(
                className=f"{icon_class} me-2",
                style={"color": color},
            ),
            title,
        ],
        className="mb-3 border-bottom pb-2 d-flex align-items-center",
    )


def _create_forecast_row(
    label, completion_date, timeframe, bg_color, is_highlighted=False, icon=None
):
    """Create a standardized forecast row for PERT tables."""
    # Create appropriate class names based on highlight status and bg_color
    row_classes = ["forecast-row"]
    label_classes = ["label-text"]
    icon_classes = ["forecast-row-icon"]

    if is_highlighted:
        row_classes.append("highlighted")
        label_classes.append("highlighted")
        # Determine if this is a success or danger highlighted row
        if "40,167,69" in bg_color:  # Check if it's green
            row_classes.append("success")
            icon_classes.append("success")
        else:
            row_classes.append("danger")
            icon_classes.append("danger")

    # Style attribute for the background color only
    row_style = {"backgroundColor": bg_color}

    label_content = [html.Span(label, className=" ".join(label_classes))]

    if icon and is_highlighted:
        label_content.append(html.I(className=f"{icon} ms-2 {' '.join(icon_classes)}"))

    return html.Div(
        className=" ".join(row_classes),
        style=row_style,
        children=[
            html.Div(label_content, className="forecast-row-label"),
            html.Div(
                html.Span(
                    completion_date,
                    className="fw-medium",
                ),
                className="forecast-row-date",
            ),
            html.Div(html.Small(timeframe), className="forecast-row-timeframe"),
        ],
    )


def _get_trend_icon_and_color(trend_value):
    """
    Determine appropriate icon and color based on trend value.

    Args:
        trend_value (float): Percentage change in trend

    Returns:
        tuple: (icon_class, color_hex)
    """
    if abs(trend_value) < 5:  # Less than 5% change is considered stable
        return TREND_ICONS["stable"], TREND_COLORS["stable"]  # Equals sign, gray color
    elif trend_value > 0:
        return TREND_ICONS["up"], TREND_COLORS["up"]  # Up arrow, green color
    else:
        return TREND_ICONS["down"], TREND_COLORS["down"]  # Down arrow, red color


def _create_project_overview_section(
    items_percentage,
    points_percentage,
    completed_items,
    completed_points,
    actual_total_items,
    actual_total_points,
    total_items,
    remaining_points,
    similar_percentages=False,
):
    """
    Create the project overview section with progress bars.

    Args:
        items_percentage: Percentage of items completed
        points_percentage: Percentage of points completed
        completed_items: Number of completed items
        completed_points: Number of completed points
        actual_total_items: Total items (completed + remaining)
        actual_total_points: Total points (completed + remaining)
        total_items: Number of remaining items
        remaining_points: Number of remaining points
        similar_percentages: Whether items and points percentages are similar

    Returns:
        dash.html.Div: Project overview section
    """
    return html.Div(
        [
            # Project progress section
            html.Div(
                [
                    # Combined progress for similar percentages
                    html.Div(
                        [
                            html.Div(
                                className="progress-container",
                                children=[
                                    html.Div(
                                        className="progress-bar bg-primary",
                                        style={
                                            "width": f"{items_percentage}%",
                                            "height": "100%",
                                            "transition": "width 1s ease",
                                        },
                                    ),
                                    html.Span(
                                        f"{items_percentage}% Complete",
                                        className=f"progress-label {'dark-text' if items_percentage > 40 else 'light-text'}",
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Small(
                                        [
                                            html.Span(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.Strong(f"{completed_items}"),
                                                    f" of {actual_total_items} items",
                                                ],
                                                className="me-3",
                                            ),
                                            html.Span(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-line me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.Strong(f"{completed_points}"),
                                                    f" of {actual_total_points} points",
                                                ]
                                            ),
                                        ],
                                        className="text-muted mt-2 d-block",
                                    ),
                                ],
                                className="d-flex justify-content-center",
                            ),
                        ],
                        style={"display": "block" if similar_percentages else "none"},
                        className="mb-3",
                    ),
                    # Separate progress bars for different percentages
                    html.Div(
                        [
                            # Items progress
                            html.Div(
                                [
                                    html.Div(
                                        className="d-flex justify-content-between align-items-center mb-1",
                                        children=[
                                            html.Small(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    "Items Progress",
                                                ],
                                                className="fw-medium",
                                            ),
                                            html.Small(
                                                f"{items_percentage}% Complete",
                                                className="text-muted",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="progress",
                                        style={
                                            "height": "16px",
                                            "borderRadius": "4px",
                                            "overflow": "hidden",
                                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                        },
                                        children=[
                                            html.Div(
                                                className="progress-bar bg-info",
                                                style={
                                                    "width": f"{items_percentage}%",
                                                    "height": "100%",
                                                    "transition": "width 1s ease",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Small(
                                        f"{completed_items} of {actual_total_items} items ({total_items} remaining)",
                                        className="text-muted mt-1 d-block",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Points progress
                            html.Div(
                                [
                                    html.Div(
                                        className="d-flex justify-content-between align-items-center mb-1",
                                        children=[
                                            html.Small(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-line me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    "Points Progress",
                                                ],
                                                className="fw-medium",
                                            ),
                                            html.Small(
                                                f"{points_percentage}% Complete",
                                                className="text-muted",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="progress",
                                        style={
                                            "height": "16px",
                                            "borderRadius": "4px",
                                            "overflow": "hidden",
                                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                        },
                                        children=[
                                            html.Div(
                                                className="progress-bar bg-warning",
                                                style={
                                                    "width": f"{points_percentage}%",
                                                    "height": "100%",
                                                    "transition": "width 1s ease",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Small(
                                        f"{completed_points} of {actual_total_points} points ({remaining_points} remaining)",
                                        className="text-muted mt-1 d-block",
                                    ),
                                ],
                            ),
                        ],
                        style={
                            "display": "block" if not similar_percentages else "none"
                        },
                        className="mb-3",
                    ),
                ],
                className="mb-4",
            )
        ]
    )


def _create_deadline_section(deadline_date_str, days_to_deadline):
    """
    Create the project deadline visualization section.

    Args:
        deadline_date_str: Formatted deadline date
        days_to_deadline: Days remaining until deadline

    Returns:
        dash.html.Div: Deadline visualization section
    """
    return html.Div(
        [
            html.Div(
                className="d-flex align-items-center mb-2",
                children=[
                    html.I(
                        className="fas fa-calendar-day fs-3 me-3",
                        style={"color": COLOR_PALETTE["deadline"]},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Project Deadline",
                                className="text-muted small",
                            ),
                            html.Div(
                                deadline_date_str,
                                className="fs-5 fw-bold",
                            ),
                        ]
                    ),
                ],
            ),
            # Days remaining visualization
            html.Div(
                [
                    html.Div(
                        className="d-flex justify-content-between align-items-center",
                        children=[
                            html.Small("Today", className="text-muted"),
                            html.Small(
                                "Deadline",
                                className="text-muted",
                            ),
                        ],
                    ),
                    html.Div(
                        className="progress mt-1 mb-1",
                        style={
                            "height": "8px",
                            "borderRadius": "4px",
                        },
                        children=[
                            html.Div(
                                className="progress-bar bg-danger",
                                style={
                                    "width": f"{max(5, min(100, (100 - (days_to_deadline / (days_to_deadline + 30) * 100))))}%",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        html.Strong(
                            f"{days_to_deadline} days remaining",
                            style={
                                "color": "green"
                                if days_to_deadline > 30
                                else "orange"
                                if days_to_deadline > 14
                                else "red"
                            },
                        ),
                        className="text-center mt-1",
                    ),
                ],
                className="mt-2",
            ),
        ],
        className="p-3 border rounded",
        style={
            "background": "linear-gradient(to bottom, rgba(220, 53, 69, 0.05), rgba(255, 255, 255, 1))",
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
        },
    )


def _create_forecast_card(
    title,
    metric_type,
    completion_str,
    pert_time,
    color,
    avg_completion_str,
    med_completion_str,
    weeks_avg,
    avg_days,
    weeks_med,
    med_days,
    weeks_avg_color,
    weeks_med_color,
):
    """
    Create a forecast card for either items or points.

    Args:
        title: Title of the forecast card (e.g., "Items Forecast")
        metric_type: Type of metric, either "items" or "points"
        completion_str: Formatted completion date string
        pert_time: PERT estimate for completion (days)
        color: Color indicator (green/red) based on meeting deadline
        avg_completion_str: Average completion date string
        med_completion_str: Median completion date string
        weeks_avg: Number of weeks to completion based on average
        avg_days: Number of days to completion based on average
        weeks_med: Number of weeks to completion based on median
        med_days: Number of days to completion based on median
        weeks_avg_color: Color for average forecast (green/red)
        weeks_med_color: Color for median forecast (green/red)

    Returns:
        dash.html.Div: A forecast card component
    """
    return html.Div(
        [
            # Header with icon
            html.Div(
                [
                    html.I(
                        className=f"{'fas fa-tasks' if metric_type == 'items' else 'fas fa-chart-bar'} me-2",
                        style={"color": COLOR_PALETTE[metric_type]},
                    ),
                    html.Span(
                        title,
                        className="fw-medium",
                    ),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Table header
            html.Div(
                className="d-flex mb-2 px-3 py-2 bg-light rounded-top border-bottom",
                style={"fontSize": "0.8rem"},
                children=[
                    html.Div(
                        "Method",
                        className="text-muted",
                        style={"width": "25%"},
                    ),
                    html.Div(
                        "Completion Date",
                        className="text-muted text-center",
                        style={"width": "45%"},
                    ),
                    html.Div(
                        "Timeframe",
                        className="text-muted text-end",
                        style={"width": "30%"},
                    ),
                ],
            ),
            _create_forecast_row(
                "PERT",
                completion_str,
                f"{pert_time:.1f}d ({pert_time / 7:.1f}w)",
                f"rgba({color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                is_highlighted=True,
                icon="fas fa-star-of-life",
            ),
            # Average row
            _create_forecast_row(
                "Average",
                avg_completion_str,
                (
                    f"{avg_days:.1f}d ({weeks_avg:.1f}w)"
                    if weeks_avg != float("inf")
                    else "∞"
                ),
                f"rgba({weeks_avg_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
            ),
            # Median row
            _create_forecast_row(
                "Median",
                med_completion_str,
                (
                    f"{med_days:.1f}d ({weeks_med:.1f}w)"
                    if weeks_med != float("inf")
                    else "∞"
                ),
                f"rgba({weeks_med_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
            ),
        ],
        className=f"{'mb-4' if metric_type == 'items' else 'mb-3'} p-3 border rounded",
        style={
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))"
            if metric_type == "items"
            else "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
        },
    )


def _create_completion_forecast_section(
    items_completion_str,
    points_completion_str,
    pert_time_items,
    pert_time_points,
    items_color,
    points_color,
    avg_items_completion_str,
    med_items_completion_str,
    avg_points_completion_str,
    med_points_completion_str,
    weeks_avg_items,
    weeks_med_items,
    weeks_avg_points,
    weeks_med_points,
    avg_items_days,
    med_items_days,
    avg_points_days,
    med_points_days,
    weeks_avg_items_color,
    weeks_med_items_color,
    weeks_avg_points_color,
    weeks_med_points_color,
):
    """
    Create the completion forecast section.

    Args:
        Multiple parameters for both items and points forecasts

    Returns:
        dash.html.Div: Completion forecast section
    """
    return html.Div(
        [
            # Subtitle with methodology information
            html.Div(
                html.Small(
                    "Based on PERT methodology (optimistic, most likely, and pessimistic estimates)",
                    className="text-muted mb-3 d-block text-center",
                ),
                className="mb-3",
            ),
            # Items Forecast Card
            _create_forecast_card(
                "Items Forecast",
                "items",
                items_completion_str,
                pert_time_items,
                items_color,
                avg_items_completion_str,
                med_items_completion_str,
                weeks_avg_items,
                avg_items_days,
                weeks_med_items,
                med_items_days,
                weeks_avg_items_color,
                weeks_med_items_color,
            ),
            # Points Forecast Card
            _create_forecast_card(
                "Points Forecast",
                "points",
                points_completion_str,
                pert_time_points,
                points_color,
                avg_points_completion_str,
                med_points_completion_str,
                weeks_avg_points,
                avg_points_days,
                weeks_med_points,
                med_points_days,
                weeks_avg_points_color,
                weeks_med_points_color,
            ),
            # Legend
            html.Div(
                html.Small(
                    create_icon_text(
                        "fas fa-star-of-life",
                        "PERT forecast combines optimistic, most likely, and pessimistic estimates",
                        size="xs",
                    ),
                    className="text-muted fst-italic text-center",
                ),
                className="mt-2",
            ),
        ],
        className="p-3 border rounded h-100",
    )


def _create_velocity_metric_card(
    title, value, trend, trend_icon, trend_color, color, is_mini=False
):
    """
    Create a velocity metric card (average or median).

    Args:
        title: Title of the card (Average or Median)
        value: Value to display
        trend: Trend percentage
        trend_icon: Icon for trend direction
        trend_color: Color for trend indicator
        color: Color for the value
        is_mini: Whether this is the mini version for the sparklines

    Returns:
        dash.html.Div: A velocity metric card
    """
    # Generate some demo data for the sparklines
    sparkline_bars = []
    for i in range(10):
        if title == "Average" and not is_mini:
            height = f"{10 + (i * 3) + (5 if i % 3 == 0 else -5)}px"
            bg_color = "#0d6efd" if not is_mini else "#fd7e14"
        else:
            height = f"{8 + (i * 2) + (4 if i % 2 == 0 else -3)}px"
            bg_color = "#6c757d"
            if is_mini:
                height = f"{10 + (i * 2) + (6 if i % 3 == 0 else -2)}px"

        sparkline_bars.append(
            html.Div(
                className="mx-1",
                style={
                    "width": "5px",
                    "height": height,
                    "backgroundColor": bg_color,
                    "opacity": f"{0.4 + (i * 0.06)}",
                    "borderRadius": "1px",
                },
            )
        )

    # Create the card with proper styles
    style_dict = {
        "flex": "1",
        "minWidth": "150px",
    }

    # Add the appropriate margin based on card type
    if title == "Average":
        style_dict["marginRight"] = "0.5rem"
    else:
        style_dict["marginLeft"] = "0.5rem"

    return html.Div(
        [
            # Header row with label and trend
            html.Div(
                [
                    html.Span(
                        title,
                        className="fw-medium",
                    ),
                    html.Span(
                        [
                            html.I(
                                className=f"{trend_icon} me-1",
                                style={
                                    "color": trend_color,
                                    "fontSize": "0.75rem",
                                },
                            ),
                            f"{'+' if trend > 0 else ''}{trend}%",
                        ],
                        style={"color": trend_color},
                        title="Change compared to previous period",
                    ),
                ],
                className="d-flex justify-content-between align-items-center mb-2",
            ),
            # Value
            html.Div(
                html.Span(
                    f"{value}",
                    className="fs-3 fw-bold",
                    style={"color": color},
                ),
                className="text-center mb-2" if not is_mini else "text-center mb-1",
            ),
            # Mini sparkline trend
            html.Div(
                [
                    html.Div(
                        className="d-flex align-items-end justify-content-center",
                        style={"height": "30px"},
                        children=sparkline_bars,
                    ),
                    html.Div(
                        html.Small(
                            "10-week trend",
                            className="text-muted",
                        ),
                        className="text-center mt-1",
                    ),
                ],
                title=f"Visual representation of {title.lower()} {'items' if not is_mini else 'points'} completed over the last 10 weeks",
            ),
        ],
        className="p-3 border rounded mb-3",
        style=style_dict,
    )


def _create_velocity_metric_section(
    metric_type,
    avg_weekly_value,
    med_weekly_value,
    avg_trend,
    med_trend,
    avg_trend_icon,
    avg_trend_color,
    med_trend_icon,
    med_trend_color,
):
    """
    Create a velocity metric section (items or points).

    Args:
        metric_type: Type of metric, either "items" or "points"
        avg_weekly_value: Average weekly value
        med_weekly_value: Median weekly value
        avg_trend: Average trend percentage
        med_trend: Median trend percentage
        avg_trend_icon: Icon for average trend
        avg_trend_color: Color for average trend
        med_trend_icon: Icon for median trend
        med_trend_color: Color for median trend

    Returns:
        dash.html.Div: Velocity metric section
    """
    # Set colors based on metric type
    is_items = metric_type == "items"
    avg_color = "#0d6efd" if is_items else "#fd7e14"
    med_color = "#6c757d"
    is_mini = not is_items

    return html.Div(
        [
            # Header with icon
            html.Div(
                [
                    html.I(
                        className=f"{'fas fa-tasks' if is_items else 'fas fa-chart-bar'} me-2",
                        style={"color": COLOR_PALETTE[metric_type]},
                    ),
                    html.Span("Items" if is_items else "Points", className="fw-medium"),
                ],
                className="d-flex align-items-center justify-content-center mb-3",
            ),
            # Velocity metrics - using flex layout for better responsiveness
            html.Div(
                [
                    # Average Items/Points
                    _create_velocity_metric_card(
                        "Average",
                        avg_weekly_value,
                        avg_trend,
                        avg_trend_icon,
                        avg_trend_color,
                        avg_color,
                        is_mini,
                    ),
                    # Median Items/Points
                    _create_velocity_metric_card(
                        "Median",
                        med_weekly_value,
                        med_trend,
                        med_trend_icon,
                        med_trend_color,
                        med_color,
                        is_mini,
                    ),
                ],
                className="d-flex flex-wrap",
                style={
                    "marginLeft": "-0.5rem",
                    "marginRight": "-0.5rem",
                },
            ),
        ],
        className=f"{'mb-4' if is_items else 'mb-3'} p-3 border rounded",
        style={
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))"
            if is_items
            else "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
        },
    )


def _create_weekly_velocity_section(
    avg_weekly_items,
    med_weekly_items,
    avg_weekly_points,
    med_weekly_points,
    avg_items_trend,
    med_items_trend,
    avg_points_trend,
    med_points_trend,
    avg_items_icon,
    avg_items_icon_color,
    med_items_icon,
    med_items_icon_color,
    avg_points_icon,
    avg_points_icon_color,
    med_points_icon,
    med_points_icon_color,
):
    """
    Create the weekly velocity section.

    Args:
        Multiple parameters for velocity metrics

    Returns:
        dash.html.Div: Weekly velocity section
    """
    return html.Div(
        [
            # Subtitle with period information
            html.Div(
                html.Small(
                    "Based on last 10 weeks of data",
                    className="text-muted mb-3 d-block text-center",
                ),
                className="mb-3",
            ),
            # Items Velocity Card
            _create_velocity_metric_section(
                "items",
                avg_weekly_items,
                med_weekly_items,
                avg_items_trend,
                med_items_trend,
                avg_items_icon,
                avg_items_icon_color,
                med_items_icon,
                med_items_icon_color,
            ),
            # Points Velocity Card
            _create_velocity_metric_section(
                "points",
                avg_weekly_points,
                med_weekly_points,
                avg_points_trend,
                med_points_trend,
                avg_points_icon,
                avg_points_icon_color,
                med_points_icon,
                med_points_icon_color,
            ),
            # Info text at the bottom
            html.Div(
                html.Div(
                    [
                        html.I(
                            className="fas fa-info-circle me-1",
                            style={"color": "#6c757d"},
                        ),
                        "10-week velocity data used for project forecasting.",
                    ],
                    className="text-muted fst-italic small text-center",
                ),
                className="mt-2",
            ),
        ],
        className="p-3 border rounded h-100",
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
    total_items=0,  # New parameter for total items
    total_points=0,  # New parameter for total points
    deadline_str=None,  # Add parameter for direct deadline string
    statistics_df=None,  # New parameter for statistics data
):
    """
    Create the PERT information table with improved organization and visual grouping.

    Args:
        pert_time_items: PERT estimate for items (days)
        pert_time_points: PERT estimate for points (days)
        days_to_deadline: Days remaining until deadline
        avg_weekly_items: Average weekly items completed (last 10 weeks)
        avg_weekly_points: Average weekly points completed (last 10 weeks)
        med_weekly_items: Median weekly items completed (last 10 weeks)
        med_weekly_points: Median weekly points completed (last 10 weeks)
        pert_factor: Number of data points used for optimistic/pessimistic scenarios
        total_items: Total remaining items to complete
        total_points: Total remaining points to complete
        deadline_str: The deadline date string from settings
        statistics_df: DataFrame containing the statistics data

    Returns:
        Dash component with improved PERT information display
    """
    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    # Calculate weeks to complete based on average and median rates
    weeks_avg_items = (
        total_items / avg_weekly_items if avg_weekly_items > 0 else float("inf")
    )
    weeks_med_items = (
        total_items / med_weekly_items if med_weekly_items > 0 else float("inf")
    )
    weeks_avg_points = (
        total_points / avg_weekly_points if avg_weekly_points > 0 else float("inf")
    )
    weeks_med_points = (
        total_points / med_weekly_points if med_weekly_points > 0 else float("inf")
    )

    # Determine colors for weeks estimates
    weeks_avg_items_color = (
        "green" if weeks_avg_items * 7 <= days_to_deadline else "red"
    )
    weeks_med_items_color = (
        "green" if weeks_med_items * 7 <= days_to_deadline else "red"
    )
    weeks_avg_points_color = (
        "green" if weeks_avg_points * 7 <= days_to_deadline else "red"
    )
    weeks_med_points_color = (
        "green" if weeks_med_points * 7 <= days_to_deadline else "red"
    )

    # Calculate projected completion dates
    current_date = datetime.now()
    items_completion_date = current_date + timedelta(days=pert_time_items)
    points_completion_date = current_date + timedelta(days=pert_time_points)

    # Calculate dates for average and median completion
    avg_items_completion_date = current_date + timedelta(days=weeks_avg_items * 7)
    med_items_completion_date = current_date + timedelta(days=weeks_med_items * 7)
    avg_points_completion_date = current_date + timedelta(days=weeks_avg_points * 7)
    med_points_completion_date = current_date + timedelta(days=weeks_med_points * 7)

    # Format dates and values for display with enhanced format
    items_completion_str = items_completion_date.strftime("%Y-%m-%d")
    points_completion_str = points_completion_date.strftime("%Y-%m-%d")

    # Format dates for average and median completion
    avg_items_completion_str = avg_items_completion_date.strftime("%Y-%m-%d")
    med_items_completion_str = med_items_completion_date.strftime("%Y-%m-%d")
    avg_points_completion_str = avg_points_completion_date.strftime("%Y-%m-%d")
    med_points_completion_str = med_points_completion_date.strftime("%Y-%m-%d")

    # Enhanced formatted strings for average and median
    avg_items_days = weeks_avg_items * 7
    med_items_days = weeks_med_items * 7
    avg_points_days = weeks_avg_points * 7
    med_points_days = weeks_med_points * 7

    # Sample trend values for demonstration
    # In a production system, these would ideally be calculated from real data
    avg_items_trend = 10  # sample value: 10% increase from previous period
    med_items_trend = -5  # sample value: 5% decrease from previous period
    avg_points_trend = 0  # sample value: no change
    med_points_trend = 15  # sample value: 15% increase from previous period

    # Get icons and colors for each metric
    avg_items_icon, avg_items_icon_color = _get_trend_icon_and_color(avg_items_trend)
    med_items_icon, med_items_icon_color = _get_trend_icon_and_color(med_items_trend)
    avg_points_icon, avg_points_icon_color = _get_trend_icon_and_color(avg_points_trend)
    med_points_icon, med_points_icon_color = _get_trend_icon_and_color(med_points_trend)

    # Use the provided deadline string instead of recalculating
    if deadline_str:
        deadline_date_str = deadline_str
    else:
        # Fallback to calculation if not provided
        deadline_date = current_date + timedelta(days=days_to_deadline)
        deadline_date_str = deadline_date.strftime("%Y-%m-%d")

    # Calculate completed items and points from statistics data
    completed_items = 0
    completed_points = 0
    if statistics_df is not None and not statistics_df.empty:
        completed_items = int(statistics_df["no_items"].sum())
        completed_points = int(statistics_df["no_points"].sum())

    # Calculate actual total project items and points
    actual_total_items = completed_items + total_items
    actual_total_points = round(completed_points + total_points)

    # Round the remaining points to natural number for display
    remaining_points = round(total_points)

    # Calculate percentages based on actual project totals
    items_percentage = (
        int((completed_items / actual_total_items) * 100)
        if actual_total_items > 0
        else 0
    )
    points_percentage = (
        int((completed_points / actual_total_points) * 100)
        if actual_total_points > 0
        else 0
    )

    # Check if percentages are similar (within 2% of each other)
    similar_percentages = abs(items_percentage - points_percentage) <= 2

    return html.Div(
        [
            # Project Overview section at the top - full width (100%)
            html.Div(
                [
                    # Replace direct icon definition with utility function
                    _create_header_with_icon(
                        "fas fa-project-diagram", "Project Overview", "#20c997"
                    ),
                    html.Div(
                        [
                            # Project progress section
                            _create_project_overview_section(
                                items_percentage,
                                points_percentage,
                                completed_items,
                                completed_points,
                                actual_total_items,
                                actual_total_points,
                                total_items,
                                remaining_points,
                                similar_percentages,
                            ),
                            # Deadline card
                            _create_deadline_section(
                                deadline_date_str, days_to_deadline
                            ),
                        ],
                        className="p-3 border rounded h-100",
                    ),
                ],
                className="mb-4",
            ),
            # Reorganized layout: Completion Forecast and Weekly Velocity side by side
            dbc.Row(
                [
                    # Left column - Completion Forecast
                    dbc.Col(
                        [
                            # Replace direct icon definition with utility function
                            _create_header_with_icon(
                                "fas fa-calendar-check",
                                "Completion Forecast",
                                "#20c997",
                            ),
                            _create_completion_forecast_section(
                                items_completion_str,
                                points_completion_str,
                                pert_time_items,
                                pert_time_points,
                                items_color,
                                points_color,
                                avg_items_completion_str,
                                med_items_completion_str,
                                avg_points_completion_str,
                                med_points_completion_str,
                                weeks_avg_items,
                                weeks_med_items,
                                weeks_avg_points,
                                weeks_med_points,
                                avg_items_days,
                                med_items_days,
                                avg_points_days,
                                med_points_days,
                                weeks_avg_items_color,
                                weeks_med_items_color,
                                weeks_avg_points_color,
                                weeks_med_points_color,
                            ),
                        ],
                        width=12,
                        lg=6,
                        className="mb-3 mb-lg-0",
                    ),
                    # Right column - Weekly Velocity with improved mobile responsiveness
                    dbc.Col(
                        [
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-tachometer-alt me-2",
                                        style={"color": "#6610f2"},
                                    ),
                                    "Weekly Velocity",
                                ],
                                className="mb-3 border-bottom pb-2 d-flex align-items-center",
                            ),
                            _create_weekly_velocity_section(
                                avg_weekly_items,
                                med_weekly_items,
                                avg_weekly_points,
                                med_weekly_points,
                                avg_items_trend,
                                med_items_trend,
                                avg_points_trend,
                                med_points_trend,
                                avg_items_icon,
                                avg_items_icon_color,
                                med_items_icon,
                                med_items_icon_color,
                                avg_points_icon,
                                avg_points_icon_color,
                                med_points_icon,
                                med_points_icon_color,
                            ),
                        ],
                        width=12,
                        lg=6,
                    ),
                ],
                className="mb-4",
            ),
        ],
    )


#######################################################################
# TREND INDICATOR COMPONENT
#######################################################################


def create_compact_trend_indicator(trend_data, metric_name="Items"):
    """
    Create a compact trend indicator component that shows performance trends in a space-efficient way.

    Args:
        trend_data: Dictionary containing trend information
        metric_name: Name of the metric being shown (Items or Points)

    Returns:
        Dash component for displaying trend information in a compact format
    """
    # Extract values from trend data or use defaults
    percent_change = trend_data.get("percent_change", 0)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine trend direction and colors
    if abs(percent_change) < 5:
        direction = "stable"
        icon_class = TREND_ICONS["stable"]
        text_color = TREND_COLORS["stable"]
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
    elif percent_change > 0:
        direction = "up"
        icon_class = TREND_ICONS["up"]
        text_color = TREND_COLORS["up"]
        bg_color = "rgba(40, 167, 69, 0.1)"
        border_color = "rgba(40, 167, 69, 0.2)"
    else:
        direction = "down"
        icon_class = TREND_ICONS["down"]
        text_color = TREND_COLORS["down"]
        bg_color = "rgba(220, 53, 69, 0.1)"
        border_color = "rgba(220, 53, 69, 0.2)"

    # Create the compact trend indicator
    return html.Div(
        className="compact-trend-indicator d-flex align-items-center p-2 rounded mb-3",
        style={
            "backgroundColor": bg_color,
            "border": f"1px solid {border_color}",
            "maxWidth": "100%",
        },
        children=[
            # Trend icon with circle background
            html.Div(
                className="trend-icon me-3 d-flex align-items-center justify-content-center rounded-circle",
                style={
                    "width": "36px",
                    "height": "36px",
                    "backgroundColor": "white",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "flexShrink": 0,
                },
                children=html.I(
                    className=f"{icon_class}",
                    style={"color": text_color, "fontSize": "1rem"},
                ),
            ),
            # Trend information
            html.Div(
                className="trend-info",
                style={"flexGrow": 1, "minWidth": 0},
                children=[
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline",
                        children=[
                            html.Span(
                                f"Weekly {metric_name} Trend",
                                className="fw-medium",
                                style={"fontSize": "0.9rem"},
                            ),
                            html.Span(
                                f"{abs(percent_change)}% {direction.capitalize()}",
                                style={
                                    "color": text_color,
                                    "fontWeight": "500",
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline mt-1",
                        style={"fontSize": "0.8rem", "color": "#6c757d"},
                        children=[
                            html.Span(
                                f"4-week avg: {current_avg} {metric_name.lower()}/week",
                                style={"marginRight": "15px"},
                            ),
                            html.Span(
                                f"Previous: {previous_avg} {metric_name.lower()}/week",
                                style={"marginLeft": "5px"},
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def create_trend_indicator(trend_data, metric_name="Items"):
    """
    Create a trend indicator component that shows performance trends.

    Args:
        trend_data: Dictionary containing trend information
        metric_name: Name of the metric being shown (Items or Points)

    Returns:
        Dash component for displaying trend information
    """
    # Extract values from trend data or use defaults
    percent_change = trend_data.get("percent_change", 0)
    is_significant = trend_data.get("is_significant", False)
    weeks = trend_data.get("weeks_compared", 4)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine trend direction based on percent change
    if abs(percent_change) < 5:
        direction = "stable"
    elif percent_change > 0:
        direction = "up"
    else:
        direction = "down"

    # Use global constants for icons and colors
    text_color = TREND_COLORS[direction]
    icon_class = TREND_ICONS[direction]

    # Determine font weight based on significance
    font_weight = "bold" if is_significant else "normal"

    # Build the component
    return html.Div(
        [
            html.H6(f"{metric_name} Trend (Last {weeks * 2} Weeks)", className="mb-2"),
            html.Div(
                [
                    html.I(
                        className=icon_class,
                        style={
                            "color": text_color,
                            "fontSize": "1.5rem",
                            "marginRight": "10px",
                        },
                    ),
                    html.Span(
                        f"{abs(percent_change)}% {'Increase' if direction == 'up' else 'Decrease' if direction == 'down' else 'Change'}",
                        style={
                            "color": text_color,
                            "fontWeight": font_weight,
                            "fontSize": "1.2rem",
                        },
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Recent Average: ", className="font-weight-bold"),
                            html.Span(f"{current_avg} {metric_name.lower()}/week"),
                        ],
                        className="mr-3",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Previous Average: ", className="font-weight-bold"
                            ),
                            html.Span(f"{previous_avg} {metric_name.lower()}/week"),
                        ],
                    ),
                ],
                className="d-flex flex-wrap small text-muted",
            ),
            # Add warning/celebration message for significant changes
            html.Div(
                html.Span(
                    f"This {'increase' if direction == 'up' else 'decrease' if direction == 'down' else 'trend'} is {'statistically significant' if is_significant else 'not statistically significant'}.",
                    className=f"{'text-success' if direction == 'up' and is_significant else 'text-danger' if direction == 'down' and is_significant else 'text-muted'}",
                ),
                className="mt-2 small",
                style={"display": "block" if is_significant else "none"},
            ),
        ],
        className="trend-indicator mb-4 p-3 border rounded",
        style={
            "backgroundColor": f"rgba({text_color.replace('#', '')}, 0.05)"
            if text_color.startswith("#")
            else "rgba(108, 117, 125, 0.05)",
        },
    )


#######################################################################
# EXPORT BUTTONS COMPONENT
#######################################################################


def create_export_buttons(chart_id=None, statistics_data=None):
    """
    Create a row of export buttons for charts or statistics data.

    Args:
        chart_id: ID of the chart for export filename
        statistics_data: Statistics data to export (if provided, shows statistics export button)

    Returns:
        Dash Div component with export buttons
    """
    buttons = []

    if chart_id:
        # Add CSV export button for chart using the new button styling system
        csv_button = create_button(
            children=[html.I(className="fas fa-file-csv me-2"), "Export CSV"],
            id=f"{chart_id}-csv-button",
            variant="secondary",
            size="sm",
            outline=True,
            tooltip="Export chart data as CSV",
            className="me-2",
        )
        buttons.append(csv_button)
        buttons.append(html.Div(dcc.Download(id=f"{chart_id}-csv-download")))

        # Add PNG export button as well
        png_button = create_button(
            children=[html.I(className="fas fa-file-image me-2"), "Export Image"],
            id=f"{chart_id}-png-button",
            variant="secondary",
            size="sm",
            outline=True,
            tooltip="Export chart as image",
            className="me-2",
        )
        buttons.append(png_button)

    if statistics_data:
        # Add button for export stats using the new button styling system
        stats_button = create_button(
            children=[html.I(className="fas fa-file-export me-2"), "Export Statistics"],
            id="export-statistics-button",
            variant="secondary",
            size="sm",
            outline=True,
            tooltip="Export statistics data",
        )
        buttons.append(stats_button)
        buttons.append(html.Div(dcc.Download(id="export-statistics-download")))

    return html.Div(
        buttons,
        className="d-flex justify-content-end mb-3",
    )


#######################################################################
# FORM VALIDATION COMPONENT
#######################################################################


def create_validation_message(message, show=False, type="invalid"):
    """
    Create a validation message for form inputs with consistent styling.

    Args:
        message (str): The validation message to display
        show (bool): Whether to show the message (default: False)
        type (str): The type of validation (valid, invalid, warning)

    Returns:
        html.Div: A validation message component
    """
    # Determine the appropriate style class based on validation type
    class_name = "d-none"
    if show:
        if type == "valid":
            class_name = "valid-feedback d-block"
        elif type == "warning":
            class_name = "text-warning d-block"
        else:
            class_name = "invalid-feedback d-block"

    # Get the base style from the styling function
    base_style = create_form_feedback_style(type)

    # Add icon based on the type
    icon_class = ""
    if type == "valid":
        icon_class = "fas fa-check-circle me-1"
    elif type == "warning":
        icon_class = "fas fa-exclamation-triangle me-1"
    elif type == "invalid":
        icon_class = "fas fa-times-circle me-1"

    # Return the validation message component
    return html.Div(
        [html.I(className=icon_class) if icon_class else "", message],
        className=class_name,
        style=base_style,
    )


#######################################################################
# ERROR ALERT COMPONENT
#######################################################################


def create_error_alert(
    message="An unexpected error occurred. Please try again later.",
    title="Error",
    error_details=None,
):
    """
    Creates a standardized Bootstrap Alert component for displaying errors.

    Args:
        message (str): The main user-friendly error message.
        title (str): The title for the alert.
        error_details (str, optional): Additional technical details to display,
                                       potentially hidden by default.

    Returns:
        dbc.Alert: A Dash Bootstrap Components Alert.
    """
    children = [
        html.H4(
            create_icon_text("error", title, size="md"),
            className="alert-heading d-flex align-items-center",
        ),
        html.P(message),
    ]
    if error_details:
        children.extend(
            [
                html.Hr(),
                html.P(f"Details: {error_details}", className="mb-0 small text-muted"),
            ]
        )

    return dbc.Alert(
        children,
        color="danger",
        dismissable=True,
        className="error-alert",
    )
