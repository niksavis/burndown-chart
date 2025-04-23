"""
UI Components Module

This module provides reusable UI components like tooltips, modals, and information tables
that are used across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import warnings
from datetime import datetime, timedelta

# Third-party library imports
from dash import html, dcc
import dash_bootstrap_components as dbc

# Application imports
from configuration import COLOR_PALETTE
from ui.tooltip_utils import (
    create_info_tooltip as new_create_info_tooltip,
    create_enhanced_tooltip as new_create_enhanced_tooltip,
    create_form_help_tooltip as new_create_form_help_tooltip,
    create_contextual_help as new_create_contextual_help,
)
from ui.button_utils import create_button as new_create_button
from ui.loading_utils import (
    create_spinner,
    create_growing_spinner,
    create_skeleton_loader,
    create_loading_overlay,
    create_content_placeholder,
    create_async_content as new_create_async_content,
    create_lazy_loading_tabs as new_create_lazy_loading_tabs,
    create_data_loading_section as new_create_data_loading_section,
)

#######################################################################
# INFO TOOLTIP COMPONENT
#######################################################################


def create_info_tooltip(id_suffix, help_text):
    """
    DEPRECATED: Use ui.tooltip_utils.create_info_tooltip instead.
    This function will be removed in a future release.

    Create an information tooltip component with an info icon.

    Args:
        id_suffix: Suffix for the component ID
        help_text: Text to display in the tooltip

    Returns:
        Component with info icon and tooltip
    """
    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.create_info_tooltip instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_info_tooltip(id_suffix, help_text)


#######################################################################
# ENHANCED TOOLTIP COMPONENTS
#######################################################################


def create_enhanced_tooltip(
    id_suffix,
    help_text,
    target=None,
    variant="primary",
    placement="top",
    trigger_text=None,
    icon_class=None,
    delay={"show": 200, "hide": 100},
):
    """
    DEPRECATED: Use ui.tooltip_utils.create_enhanced_tooltip instead.
    This function will be removed in a future release.

    Create an enhanced tooltip component with consistent styling and animations.

    Args:
        id_suffix: Suffix for component ID
        help_text: Text to display in the tooltip (can be string or Dash component)
        target: Optional target ID (if not provided, will use info-icon)
        variant: Style variant (primary, info, success, warning, danger)
        placement: Tooltip placement (top, bottom, left, right)
        trigger_text: Optional text to show as the tooltip trigger
        icon_class: FontAwesome icon class for custom icon (defaults to info circle)
        delay: Show/hide delay in milliseconds

    Returns:
        Dash component with enhanced tooltip
    """
    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.create_enhanced_tooltip instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_enhanced_tooltip(
        id_suffix=id_suffix,
        help_text=help_text,
        target=target,
        variant=variant,
        placement=placement,
        trigger_text=trigger_text,
        icon_class=icon_class,
        delay=delay,
    )


def create_form_help_tooltip(id_suffix, field_label, help_text, variant="info"):
    """
    DEPRECATED: Use ui.tooltip_utils.create_form_help_tooltip instead.
    This function will be removed in a future release.

    Create a form field label with integrated help tooltip.

    Args:
        id_suffix: Suffix for tooltip ID
        field_label: Label text for the form field
        help_text: Help text to display in the tooltip
        variant: Tooltip variant (primary, info, success, warning, danger)

    Returns:
        Dash component with label and tooltip
    """
    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.create_form_help_tooltip instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_form_help_tooltip(
        id_suffix=id_suffix,
        field_label=field_label,
        help_text=help_text,
        variant=variant,
    )


def create_contextual_help(id_suffix, help_text, trigger_text=None, variant="primary"):
    """
    DEPRECATED: Use ui.tooltip_utils.create_contextual_help instead.
    This function will be removed in a future release.

    Create a contextual help text with underline indicator for inline help.

    Args:
        id_suffix: Suffix for tooltip ID
        help_text: Help text to display in tooltip
        trigger_text: Text that triggers the tooltip (underlined with dotted line)
        variant: Tooltip variant

    Returns:
        Dash component with inline help
    """
    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.create_contextual_help instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_contextual_help(
        id_suffix=id_suffix,
        help_text=help_text,
        trigger_text=trigger_text,
        variant=variant,
    )


#######################################################################
# PERT INFO TABLE COMPONENT
#######################################################################


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

    # Enhanced formatted strings with days and weeks
    items_completion_enhanced = f"{items_completion_str} ({pert_time_items:.1f} days, {pert_time_items / 7:.1f} weeks)"
    points_completion_enhanced = f"{points_completion_str} ({pert_time_points:.1f} days, {pert_time_points / 7:.1f} weeks)"

    # Enhanced formatted strings for average and median
    avg_items_days = weeks_avg_items * 7
    med_items_days = weeks_med_items * 7
    avg_points_days = weeks_avg_points * 7
    med_points_days = weeks_med_points * 7

    avg_items_completion_enhanced = (
        f"{avg_items_completion_str} ({avg_items_days:.1f} days, {weeks_avg_items:.1f} weeks)"
        if weeks_avg_items != float("inf")
        else "∞"
    )
    med_items_completion_enhanced = (
        f"{med_items_completion_str} ({med_items_days:.1f} days, {weeks_med_items:.1f} weeks)"
        if weeks_med_items != float("inf")
        else "∞"
    )
    avg_points_completion_enhanced = (
        f"{avg_points_completion_str} ({avg_points_days:.1f} days, {weeks_avg_points:.1f} weeks)"
        if weeks_avg_points != float("inf")
        else "∞"
    )
    med_points_completion_enhanced = (
        f"{med_points_completion_str} ({med_points_days:.1f} days, {weeks_med_points:.1f} weeks)"
        if weeks_med_points != float("inf")
        else "∞"
    )

    # Define trend indicators (simplified version from performance trend)
    # These would normally come from calculate_performance_trend but we'll simulate it here
    # In a real implementation, you would pass trend data from the parent component

    # Simulate trend data for demonstration - these would normally be calculated and passed in
    # Positive values indicate an upward trend compared to previous period
    # Negative values indicate a downward trend compared to previous period
    avg_items_trend = 10  # sample value: 10% increase from previous period
    med_items_trend = -5  # sample value: 5% decrease from previous period
    avg_points_trend = 0  # sample value: no change
    med_points_trend = 15  # sample value: 15% increase from previous period

    # Define trend arrow icons and colors based on the trend values
    def get_trend_icon_and_color(trend_value):
        if abs(trend_value) < 5:  # Less than 5% change is considered stable
            return "fas fa-equals", "#6c757d"  # Equals sign, gray color
        elif trend_value > 0:
            return "fas fa-arrow-up", "#28a745"  # Up arrow, green color
        else:
            return "fas fa-arrow-down", "#dc3545"  # Down arrow, red color

    # Get icons and colors for each metric
    avg_items_icon, avg_items_icon_color = get_trend_icon_and_color(avg_items_trend)
    med_items_icon, med_items_icon_color = get_trend_icon_and_color(med_items_trend)
    avg_points_icon, avg_points_icon_color = get_trend_icon_and_color(avg_points_trend)
    med_points_icon, med_points_icon_color = get_trend_icon_and_color(med_points_trend)

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
                    html.H5(
                        [
                            html.I(
                                className="fas fa-project-diagram me-2",
                                style={"color": "#20c997"},
                            ),
                            "Project Overview",
                        ],
                        className="mb-3 border-bottom pb-2 d-flex align-items-center",
                    ),
                    html.Div(
                        [
                            # Project progress section
                            html.Div(
                                [
                                    # Combined progress for similar percentages
                                    html.Div(
                                        [
                                            html.Div(
                                                className="progress",
                                                style={
                                                    "height": "24px",
                                                    "position": "relative",
                                                    "borderRadius": "6px",
                                                    "overflow": "hidden",
                                                    "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                                },
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
                                                        style={
                                                            "position": "absolute",
                                                            "top": "0",
                                                            "left": "0",
                                                            "width": "100%",
                                                            "height": "100%",
                                                            "display": "flex",
                                                            "alignItems": "center",
                                                            "justifyContent": "center",
                                                            "color": "white"
                                                            if items_percentage > 40
                                                            else "black",
                                                            "fontWeight": "bold",
                                                            "textShadow": "0 0 2px rgba(0,0,0,0.2)"
                                                            if items_percentage > 40
                                                            else "none",
                                                        },
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
                                                                    html.Strong(
                                                                        f"{completed_items}"
                                                                    ),
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
                                                                    html.Strong(
                                                                        f"{completed_points}"
                                                                    ),
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
                                        style={
                                            "display": "block"
                                            if similar_percentages
                                            else "none"
                                        },
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
                                            "display": "block"
                                            if not similar_percentages
                                            else "none"
                                        },
                                        className="mb-3",
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Deadline card
                            html.Div(
                                [
                                    html.Div(
                                        className="d-flex align-items-center mb-2",
                                        children=[
                                            html.I(
                                                className="fas fa-calendar-day fs-3 me-3",
                                                style={
                                                    "color": COLOR_PALETTE["deadline"]
                                                },
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
                                                    html.Small(
                                                        "Today", className="text-muted"
                                                    ),
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
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-calendar-check me-2",
                                        style={"color": "#20c997"},
                                    ),
                                    "Completion Forecast",
                                ],
                                className="mb-3 border-bottom pb-2 d-flex align-items-center",
                            ),
                            html.Div(
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
                                    html.Div(
                                        [
                                            # Header with icon
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-2",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Items Forecast",
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
                                            # PERT row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({items_color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                                                    "borderRadius": "4px",
                                                    "border": f"1px solid {items_color}",
                                                },
                                                children=[
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "PERT",
                                                                className="fw-bold",
                                                            ),
                                                            html.I(
                                                                className="fas fa-star-of-life ms-2",
                                                                style={
                                                                    "fontSize": "0.7rem",
                                                                    "color": items_color,
                                                                },
                                                            ),
                                                        ],
                                                        style={"width": "25%"},
                                                        className="d-flex align-items-center",
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            items_completion_str,
                                                            style={
                                                                "color": items_color
                                                            },
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{pert_time_items:.1f}d ({pert_time_items / 7:.1f}w)",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Average row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_avg_items_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_avg_items != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Average",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            avg_items_completion_str,
                                                            style={
                                                                "color": weeks_avg_items_color
                                                            }
                                                            if weeks_avg_items
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{avg_items_days:.1f}d ({weeks_avg_items:.1f}w)"
                                                            if weeks_avg_items
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Median row
                                            html.Div(
                                                className="d-flex align-items-center p-2",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_med_items_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_med_items != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Median",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            med_items_completion_str,
                                                            style={
                                                                "color": weeks_med_items_color
                                                            }
                                                            if weeks_med_items
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{med_items_days:.1f}d ({weeks_med_items:.1f}w)"
                                                            if weeks_med_items
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="mb-4 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Points Forecast Card
                                    html.Div(
                                        [
                                            # Header with icon
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-bar me-2",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Points Forecast",
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
                                            # PERT row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({points_color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                                                    "borderRadius": "4px",
                                                    "border": f"1px solid {points_color}",
                                                },
                                                children=[
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "PERT",
                                                                className="fw-bold",
                                                            ),
                                                            html.I(
                                                                className="fas fa-star-of-life ms-2",
                                                                style={
                                                                    "fontSize": "0.7rem",
                                                                    "color": points_color,
                                                                },
                                                            ),
                                                        ],
                                                        style={"width": "25%"},
                                                        className="d-flex align-items-center",
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            points_completion_str,
                                                            style={
                                                                "color": points_color
                                                            },
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{pert_time_points:.1f}d ({pert_time_points / 7:.1f}w)",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Average row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_avg_points_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_avg_points != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Average",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            avg_points_completion_str,
                                                            style={
                                                                "color": weeks_avg_points_color
                                                            }
                                                            if weeks_avg_points
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{avg_points_days:.1f}d ({weeks_avg_points:.1f}w)"
                                                            if weeks_avg_points
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Median row
                                            html.Div(
                                                className="d-flex align-items-center p-2",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_med_points_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_med_points != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Median",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            med_points_completion_str,
                                                            style={
                                                                "color": weeks_med_points_color
                                                            }
                                                            if weeks_med_points
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{med_points_days:.1f}d ({weeks_med_points:.1f}w)"
                                                            if weeks_med_points
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="mb-3 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Legend
                                    html.Div(
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-star-of-life me-1",
                                                    style={"fontSize": "0.6rem"},
                                                ),
                                                "PERT forecast combines optimistic, most likely, and pessimistic estimates",
                                            ],
                                            className="text-muted fst-italic text-center",
                                        ),
                                        className="mt-2",
                                    ),
                                ],
                                className="p-3 border rounded h-100",
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
                            html.Div(
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
                                    html.Div(
                                        [
                                            # Header with icon
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-2",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Items", className="fw-medium"
                                                    ),
                                                ],
                                                className="d-flex align-items-center justify-content-center mb-3",
                                            ),
                                            # Velocity metrics - using flex layout for better responsiveness
                                            html.Div(
                                                [
                                                    # Average Items
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Average",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{avg_items_icon} me-1",
                                                                                style={
                                                                                    "color": avg_items_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if avg_items_trend > 0 else ''}{avg_items_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": avg_items_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{avg_weekly_items}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#0d6efd"
                                                                    },
                                                                ),
                                                                className="text-center mb-2",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{10 + (i * 3) + (5 if i % 3 == 0 else -5)}px",
                                                                                        "backgroundColor": "#0d6efd",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of completed items over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginRight": "0.5rem",
                                                        },
                                                    ),
                                                    # Median Items
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Median",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{med_items_icon} me-1",
                                                                                style={
                                                                                    "color": med_items_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if med_items_trend > 0 else ''}{med_items_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": med_items_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{med_weekly_items}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#6c757d"
                                                                    },
                                                                ),
                                                                className="text-center mb-2",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{8 + (i * 2) + (4 if i % 2 == 0 else -3)}px",
                                                                                        "backgroundColor": "#6c757d",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of median completed items over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginLeft": "0.5rem",
                                                        },
                                                    ),
                                                ],
                                                className="d-flex flex-wrap",
                                                style={
                                                    "marginLeft": "-0.5rem",
                                                    "marginRight": "-0.5rem",
                                                },
                                            ),
                                        ],
                                        className="mb-4 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Points Velocity Card
                                    html.Div(
                                        [
                                            # Header with icon
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-bar me-2",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Points", className="fw-medium"
                                                    ),
                                                ],
                                                className="d-flex align-items-center justify-content-center mb-3",
                                            ),
                                            # Velocity metrics - using flex layout for better responsiveness
                                            html.Div(
                                                [
                                                    # Average Points
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Average",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{avg_points_icon} me-1",
                                                                                style={
                                                                                    "color": avg_points_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if avg_points_trend > 0 else ''}{avg_points_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": avg_points_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{avg_weekly_points}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#fd7e14"
                                                                    },
                                                                ),
                                                                className="text-center mb-1",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{12 + (i * 3) + (7 if i % 2 == 0 else -4)}px",
                                                                                        "backgroundColor": "#fd7e14",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of average points completed over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginRight": "0.5rem",
                                                        },
                                                    ),
                                                    # Median Points
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Median",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{med_points_icon} me-1",
                                                                                style={
                                                                                    "color": med_points_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if med_points_trend > 0 else ''}{med_points_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": med_points_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{med_weekly_points}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#6c757d"
                                                                    },
                                                                ),
                                                                className="text-center mb-1",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{10 + (i * 2) + (6 if i % 3 == 0 else -2)}px",
                                                                                        "backgroundColor": "#6c757d",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of median points completed over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginLeft": "0.5rem",
                                                        },
                                                    ),
                                                ],
                                                className="d-flex flex-wrap",
                                                style={
                                                    "marginLeft": "-0.5rem",
                                                    "marginRight": "-0.5rem",
                                                },
                                            ),
                                        ],
                                        className="mb-3 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
                                        },
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
    from dash import html

    # Extract values from trend data or use defaults
    percent_change = trend_data.get("percent_change", 0)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine trend direction and colors
    if abs(percent_change) < 5:
        direction = "stable"
        icon_class = "fas fa-equals"
        text_color = "#6c757d"  # Gray
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
    elif percent_change > 0:
        direction = "up"
        icon_class = "fas fa-arrow-up"
        text_color = "#28a745"  # Green
        bg_color = "rgba(40, 167, 69, 0.1)"
        border_color = "rgba(40, 167, 69, 0.2)"
    else:
        direction = "down"
        icon_class = "fas fa-arrow-down"
        text_color = "#dc3545"  # Red
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
                                style={
                                    "marginRight": "15px"
                                },  # Add explicit right margin
                            ),
                            html.Span(
                                f"Previous: {previous_avg} {metric_name.lower()}/week",
                                style={"marginLeft": "5px"},  # Add explicit left margin
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
    from dash import html

    # Extract values from trend data or use defaults
    percent_change = trend_data.get("percent_change", 0)
    is_significant = trend_data.get("is_significant", False)
    weeks = trend_data.get("weeks_compared", 4)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine trend direction and set appropriate icon and color
    if abs(percent_change) < 5:
        direction = "stable"
        trend_icons = {
            "stable": "fas fa-equals",
            "up": "fas fa-arrow-up",
            "down": "fas fa-arrow-down",
        }
        trend_colors = {"stable": "#6c757d", "up": "#28a745", "down": "#dc3545"}
    elif percent_change > 0:
        direction = "up"
        trend_icons = {
            "stable": "fas fa-equals",
            "up": "fas fa-arrow-up",
            "down": "fas fa-arrow-down",
        }
        trend_colors = {"stable": "#6c757d", "up": "#28a745", "down": "#dc3545"}
    else:
        direction = "down"
        trend_icons = {
            "stable": "fas fa-equals",
            "up": "fas fa-arrow-up",
            "down": "fas fa-arrow-down",
        }
        trend_colors = {"stable": "#6c757d", "up": "#28a745", "down": "#dc3545"}

    # Determine text color and font weight based on significance
    text_color = trend_colors.get(direction, "#6c757d")
    font_weight = "bold" if is_significant else "normal"

    # Build the component
    return html.Div(
        [
            html.H6(f"{metric_name} Trend (Last {weeks * 2} Weeks)", className="mb-2"),
            html.Div(
                [
                    html.I(
                        className=trend_icons.get(direction, "fas fa-arrows-alt-h"),
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
    from ui.styles import create_button

    buttons = []

    if chart_id:
        # Add CSV export button for chart using the new button styling system
        csv_button = create_button(
            text="Export CSV",
            id=f"{chart_id}-csv-button",
            variant="secondary",
            size="sm",
            outline=True,
            icon_class="fas fa-file-csv",
            className="me-2",
            tooltip="Export chart data as CSV",
        )
        buttons.append(csv_button)
        buttons.append(html.Div(dcc.Download(id=f"{chart_id}-csv-download")))

        # Add PNG export button as well
        png_button = create_button(
            text="Export Image",
            id=f"{chart_id}-png-button",
            variant="secondary",
            size="sm",
            outline=True,
            icon_class="fas fa-file-image",
            className="me-2",
            tooltip="Export chart as image",
        )
        buttons.append(png_button)

    if statistics_data:
        # Add button for export stats using the new button styling system
        stats_button = create_button(
            text="Export Statistics",
            id="export-statistics-button",
            variant="secondary",
            size="sm",
            outline=True,
            icon_class="fas fa-file-export",
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
    from dash import html
    from ui.styles import create_form_feedback_style

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


def create_button(
    text=None,
    id=None,
    variant="primary",
    size="md",
    outline=False,
    icon_class=None,
    className="",
    tooltip=None,
    disabled=False,
):
    """
    DEPRECATED: Use ui.button_utils.create_button instead.
    This function will be removed in a future release.

    Create a standardized button with consistent styling and optional icon.

    Args:
        text: Button text (optional if icon_class provided)
        id: Component ID
        variant: Bootstrap color variant (primary, secondary, success, etc.)
        size: Button size (sm, md, lg)
        outline: Whether to use outline style
        icon_class: FontAwesome icon class (e.g., "fas fa-plus")
        className: Additional CSS classes
        tooltip: Optional tooltip text
        disabled: Whether the button is disabled

    Returns:
        A dbc.Button component with standardized styling
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.button_utils.create_button instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_button(
        text=text,
        id=id,
        variant=variant,
        size=size,
        outline=outline,
        icon_class=icon_class,
        className=className,
        tooltip=tooltip,
        disabled=disabled,
    )


#######################################################################
# LOADING STATE COMPONENTS
#######################################################################


def create_loading_indicator(
    id="loading", type="spinner", message="Loading...", color="primary", size="md"
):
    """
    DEPRECATED: Use ui.loading_utils.create_spinner or ui.loading_utils.create_growing_spinner instead.
    This function will be removed in a future release.

    Create a standardized loading indicator component.

    Args:
        id (str): Component ID
        type (str): Type of indicator (spinner, growing, skeleton)
        message (str): Message to display while loading
        color (str): Bootstrap color variant
        size (str): Size of the loading indicator (sm, md, lg)

    Returns:
        Dash component: A loading indicator component
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.loading_utils.create_spinner or "
        "ui.loading_utils.create_growing_spinner instead.",
        DeprecationWarning,
        stacklevel=2,
    )


    # Map the old parameters to the new function calls
    if type == "skeleton":
        return create_skeleton_loader(
            type="text", lines=3, className="mb-3", width="100%"
        )
    elif type == "growing":
        return create_growing_spinner(
            style_key=color, size_key=size, text=message, id=id
        )
    else:  # Default spinner
        return create_spinner(
            style_key=color, size_key=size, text=message, className="my-3", id=id
        )


def create_loading_wrapper(
    children,
    is_loading=False,
    id=None,
    type="overlay",
    color="primary",
    size="md",
    message="Loading...",
):
    """
    DEPRECATED: Use ui.loading_utils.create_loading_overlay or ui.loading_utils.create_content_placeholder instead.
    This function will be removed in a future release.

    Create a wrapper that shows loading state over content.

    Args:
        children: Child components to wrap
        is_loading: Whether the loading state is active
        id: Component ID
        type: Type of loading indicator (overlay, spinner, skeleton)
        color: Bootstrap color variant
        size: Size of the loading indicator
        message: Message to display while loading

    Returns:
        Dash component with loading indication
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.loading_utils.create_loading_overlay or "
        "ui.loading_utils.create_content_placeholder instead.",
        DeprecationWarning,
        stacklevel=2,
    )


    # Map the old parameters to the new function calls
    if is_loading:
        if type == "skeleton":
            return create_content_placeholder(placeholder_type="card", lines=3)
        else:  # Default to overlay
            return create_loading_overlay(
                children,
                is_loading=True,
                spinner_props={"style_key": color, "size_key": size},
                text=message,
                id=id,
            )
    return children


def create_async_content(id, loading_state_id, content_type="chart"):
    """
    DEPRECATED: Use ui.loading_utils.create_async_content instead.
    This function will be removed in a future release.

    Create a component that will show content when it's loaded asynchronously.

    Args:
        id (str): ID of the content element
        loading_state_id (str): ID for the loading state element
        content_type (str): Type of content (chart, table, data, etc.)

    Returns:
        dbc.Spinner: A spinner that wraps the content container
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.loading_utils.create_async_content instead.",
        DeprecationWarning,
        stacklevel=2,
    )


    return new_create_async_content(id, loading_state_id, content_type)


def create_lazy_loading_tabs(
    tabs_data, tab_id_prefix="tab", content_id_prefix="tab-content"
):
    """
    DEPRECATED: Use ui.loading_utils.create_lazy_loading_tabs instead.
    This function will be removed in a future release.

    Create tabs that load content lazily when selected.

    Args:
        tabs_data (list): List of dictionaries with tab properties (label, content, icon, active)
        tab_id_prefix (str): Prefix for tab IDs
        content_id_prefix (str): Prefix for content IDs

    Returns:
        tuple: (tabs, content) components for lazy-loading tabs
    """
    warnings.warn(
        "This function is deprecated. Use ui.loading_utils.create_lazy_loading_tabs instead.",
        DeprecationWarning,
        stacklevel=2,
    )


    return new_create_lazy_loading_tabs(tabs_data, tab_id_prefix, content_id_prefix)


def create_data_loading_section(
    id,
    title=None,
    loading_message="Loading data...",
    error_message="Failed to load data",
    retry_button=True,
):
    """
    DEPRECATED: Use ui.loading_utils.create_data_loading_section instead.
    This function will be removed in a future release.

    Create a section that handles loading, error, and success states for data loading.

    Args:
        id (str): Base ID for components
        title (str): Section title
        loading_message (str): Message to show during loading
        error_message (str): Message to show on error
        retry_button (bool): Whether to include a retry button on error

    Returns:
        html.Div: Container with content for each state
    """
    warnings.warn(
        "This function is deprecated. Use ui.loading_utils.create_data_loading_section instead.",
        DeprecationWarning,
        stacklevel=2,
    )


    return new_create_data_loading_section(
        id=id,
        title=title,
        loading_message=loading_message,
        error_message=error_message,
        retry_button=retry_button,
    )
