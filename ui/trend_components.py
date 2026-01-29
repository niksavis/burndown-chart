"""
Trend Components Module

Components for trend visualization and trend indicators.
Extracted from ui/components.py during refactoring (bd-rnol).
"""

from dash import html

# Define common trend icons and colors
TREND_ICONS = {
    "stable": "fas fa-equals",
    "up": "fas fa-arrow-up",
    "down": "fas fa-arrow-down",
    "baseline": "fas fa-hourglass-half",
}

TREND_COLORS = {
    "stable": "#6c757d",  # Gray
    "up": "#28a745",  # Green
    "down": "#dc3545",  # Red
}


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
    weeks_compared = trend_data.get("weeks_compared", 4)

    # Check if we're in baseline building mode (need 8 weeks: 4 recent + 4 older for comparison)
    # Two conditions indicate insufficient data:
    # 1. weeks_compared < 4 means not enough weeks after aggregation
    # 2. total_weeks_available < 8 means insufficient total data
    total_weeks_needed = 8
    total_weeks_available = weeks_compared * 2  # Default calculation

    is_insufficient_data = (
        weeks_compared < 4 or total_weeks_available < total_weeks_needed
    )

    if is_insufficient_data:
        # Not enough data for trend comparison - show baseline building message
        # Estimate weeks available from the data we have
        if weeks_compared < 4:
            total_weeks_available = weeks_compared * 2
        else:
            # When weeks_compared=4 but averages are 0, we have < 8 weeks of actual data
            # This happens when raw statistics_data length < 8
            total_weeks_available = 0  # Unknown exact count

        direction = "baseline"
        icon_class = TREND_ICONS.get("baseline", "fas fa-hourglass-half")
        text_color = "#6c757d"
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
    # Determine trend direction and colors for established trends
    elif abs(percent_change) < 5:
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
                                (
                                    "Building baseline..."
                                    if direction == "baseline"
                                    and total_weeks_available == 0
                                    else f"Building baseline ({total_weeks_available} of {total_weeks_needed} weeks)"
                                    if direction == "baseline"
                                    else f"{abs(percent_change):.0f}% {direction.capitalize()}"
                                ),
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
                        children=(
                            [
                                html.Span(
                                    "Collecting data to establish performance baseline",
                                    style={"fontStyle": "italic"},
                                ),
                            ]
                            if direction == "baseline"
                            else [
                                html.Span(
                                    f"4-week avg: {current_avg:.1f} {metric_name.lower()}/week",
                                    style={"marginRight": "15px"},
                                ),
                                html.Span(
                                    f"Previous: {previous_avg:.1f} {metric_name.lower()}/week",
                                    style={"marginLeft": "5px"},
                                ),
                            ]
                        ),
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
