"""Flow Metrics Dashboard UI Components.

Provides the user interface for viewing Flow metrics including Velocity, Time,
Efficiency, Load, and Distribution with work type breakdown.

Uses Data Points slider from settings panel to control historical data display.
Metrics calculated per ISO week (Monday-Sunday), showing current week + N-1 historical weeks.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html, dcc

from configuration.help_content import FLOW_METRICS_TOOLTIPS
from ui.tooltip_utils import create_info_tooltip
from ui.empty_states import (
    create_metrics_skeleton,
    create_no_data_state,
)  # Visible skeleton with shimmer


def create_flow_dashboard() -> dbc.Container:
    """Create the complete Flow metrics dashboard layout.

    Returns:
        dbc.Container with Flow metrics dashboard components
    """
    # Check if JIRA data exists AND if metrics are calculated
    from data.jira_simple import load_jira_cache, get_jira_config
    from data.persistence import load_app_settings
    from data.metrics_snapshots import has_metric_snapshot
    from data.time_period_calculator import get_iso_week, format_year_week
    from datetime import datetime

    has_jira_data = False
    has_metrics = False

    try:
        settings = load_app_settings()
        jql_query = settings.get("jql_query", "")
        config = get_jira_config(jql_query)
        cache_loaded, cached_issues = load_jira_cache(
            current_jql_query=jql_query, current_fields="", config=config
        )
        has_jira_data = cache_loaded and cached_issues and len(cached_issues) > 0

        # Check if metrics are calculated (check current week)
        if has_jira_data:
            year, week = get_iso_week(datetime.now())
            current_week_label = format_year_week(year, week)
            has_metrics = has_metric_snapshot(current_week_label, "flow_velocity")
    except Exception:
        pass  # No data available

    # Determine initial content based on what's available
    if not has_jira_data:
        initial_content = [create_no_data_state()]
    elif not has_metrics:
        from ui.empty_states import create_no_metrics_state

        initial_content = [create_no_metrics_state(metric_type="Flow")]
    else:
        initial_content = [create_metrics_skeleton(num_cards=5)]

    return dbc.Container(
        [
            # Store for tracking if user has seen welcome banner (uses localStorage)
            dcc.Store(id="flow-welcome-dismissed", storage_type="local", data=False),
            # Welcome banner for first-time users (dismissible)
            html.Div(
                id="flow-welcome-banner",
                children=[],  # Will be populated by callback based on storage
            ),
            # Compact overview section with distinct background
            html.Div(
                id="flow-overview-wrapper",
                children=[
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    id="flow-metrics-overview",
                                    children=[],  # Will be populated by callback
                                ),
                            ],
                            className="pt-3 px-3 pb-0",  # Top and side padding, no bottom padding
                        ),
                        className="mb-3 overview-section",
                        style={
                            "backgroundColor": "#f8f9fa",  # Light gray background
                            "border": "none",
                            "borderRadius": "8px",
                        },
                    ),
                    # Info banner with balanced spacing
                    html.P(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Flow metrics calculated per ISO week. Use ",
                            html.Strong("Calculate Metrics"),
                            " button to refresh. ",
                            html.Strong("Data Points slider"),
                            " controls weeks displayed.",
                        ],
                        className="text-muted small mb-3 mt-3",  # Equal top and bottom margin
                    ),
                ],
                style={
                    "display": "none"
                },  # Hidden by default, shown by callback when metrics exist
            ),
            # Metrics cards grid (includes both Flow metrics + Work Distribution in same container)
            # No loading wrapper - skeleton provides loading state
            html.Div(
                children=initial_content,  # Show banner or skeleton based on data availability
                id="flow-metrics-cards-container",
                className="mb-4",  # Add spacing below cards
            ),
            # Store for metrics data
            dcc.Store(id="flow-metrics-store", data={}),
        ],
        fluid=True,
        className="py-4",
    )


def create_flow_metric_card(
    metric_data: Dict[str, Any],
    metric_name: str,
) -> dbc.Card:
    """Create a metric card for a single Flow metric.

    Args:
        metric_data: Metric calculation result
        metric_name: Display name for the metric

    Returns:
        dbc.Card with metric display
    """
    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        # Error card
        return _create_flow_error_card(metric_data, metric_name)

    value = metric_data.get("value")
    unit = metric_data.get("unit", "")

    # Format value display
    if isinstance(value, float):
        value_display = f"{value:.1f}"
    else:
        value_display = str(value)

    # Get status color based on metric type (default to primary if value is None)
    status_color = _get_flow_metric_color(metric_data["metric_name"], value or 0.0)

    # Get tooltip for this metric
    metric_key = metric_data["metric_name"]
    tooltip_text = FLOW_METRICS_TOOLTIPS.get(metric_key, "")

    # Create metric title with info icon
    if tooltip_text:
        title_element = html.H6(
            [
                metric_name,
                " ",
                create_info_tooltip(
                    help_text=tooltip_text,
                    id_suffix=f"flow-{metric_key}",
                    placement="top",
                    variant="dark",
                ),
            ],
            className="text-muted mb-2",
        )
    else:
        title_element = html.H6(metric_name, className="text-muted mb-2")

    card = dbc.Card(
        [
            dbc.CardBody(
                [
                    title_element,
                    html.H2(
                        [
                            html.Span(value_display, className=f"text-{status_color}"),
                            html.Small(f" {unit}", className="text-muted ms-2"),
                        ],
                        className="mb-3",
                    ),
                    # Type breakdown if available
                    _create_type_breakdown(metric_data.get("details", {})),
                    # Trend indicator if available
                    _create_trend_indicator(metric_data.get("details", {})),
                ]
            ),
        ],
        className="h-100 shadow-sm",
    )

    return card


def _create_flow_error_card(metric_data: Dict[str, Any], metric_name: str) -> dbc.Card:
    """Create an error card for Flow metric.

    Args:
        metric_data: Metric data with error state
        metric_name: Display name

    Returns:
        dbc.Card with error display
    """
    error_message = metric_data.get("error_message", "Unknown error")

    return dbc.Card(
        [
            dbc.CardBody(
                children=[
                    html.H6(metric_name, className="text-muted mb-2"),
                    html.Div(
                        children=[
                            html.I(
                                className="fas fa-exclamation-triangle text-warning me-2"
                            ),
                            html.Span("Error", className="text-warning"),
                        ],
                        className="mb-2",
                    ),
                    html.P(
                        error_message,
                        className="small text-muted mb-0",
                    ),
                ]
            ),
        ],
        className="h-100 shadow-sm border-warning",
    )


def _create_type_breakdown(details: Dict[str, Any]) -> html.Div:
    """Create work type breakdown display.

    Args:
        details: Metric details with by_type breakdown

    Returns:
        html.Div with type breakdown or empty div
    """
    by_type = details.get("by_type", {})

    if not by_type or all(v == 0 for v in by_type.values()):
        return html.Div()

    # Create mini badges for each type
    type_badges = []
    type_colors = {
        "Feature": "primary",
        "Defect": "danger",
        "Risk": "warning",
        "Technical_Debt": "info",
    }

    for work_type, count in by_type.items():
        if count > 0:
            color = type_colors.get(work_type, "secondary")
            label = work_type.replace("_", " ")
            type_badges.append(
                dbc.Badge(
                    children=f"{label}: {count}",
                    color=color,
                    className="me-1 mb-1",
                    pill=True,
                )
            )

    if not type_badges:
        return html.Div()

    return html.Div(
        children=type_badges,
        className="mt-2",
    )


def _create_trend_indicator(details: Dict[str, Any]) -> html.Div:
    """Create trend indicator display.

    Args:
        details: Metric details with trend information

    Returns:
        html.Div with trend display or empty div
    """
    trend_direction = details.get("trend_direction", "unknown")
    trend_percentage = details.get("trend_percentage", 0)

    if trend_direction == "unknown" or trend_percentage == 0:
        return html.Div()

    # Determine icon and color
    if trend_direction == "up":
        icon = "fa-arrow-up"
        color = "success"
    elif trend_direction == "down":
        icon = "fa-arrow-down"
        color = "danger"
    else:  # stable
        icon = "fa-minus"
        color = "secondary"

    return html.Div(
        children=[
            html.I(className=f"fas {icon} text-{color} me-1"),
            html.Span(
                f"{abs(trend_percentage):.1f}%",
                className=f"text-{color} small",
            ),
            html.Span(" vs last period", className="text-muted small ms-1"),
        ],
        className="mt-2",
    )


def _get_flow_performance_tier(metric_name: str, value: float) -> str:
    """Get performance tier label for Flow metrics.

    Args:
        metric_name: Metric identifier (e.g., "flow_velocity", "flow_time")
        value: Metric value

    Returns:
        Performance tier label (e.g., "Healthy", "Good", "Needs Improvement")
    """
    if metric_name == "flow_load":
        # Flow Load (WIP) - health-based tiers
        if value < 10:
            return "Healthy"
        elif value < 20:
            return "Warning"
        elif value < 30:
            return "High"
        else:
            return "Critical"
    elif metric_name == "flow_velocity":
        # Flow Velocity - higher is better
        if value >= 20:
            return "Excellent"
        elif value >= 10:
            return "Good"
        elif value >= 5:
            return "Fair"
        else:
            return "Low"
    elif metric_name == "flow_time":
        # Flow Time - lower is better (days)
        if value <= 3:
            return "Excellent"
        elif value <= 7:
            return "Good"
        elif value <= 14:
            return "Fair"
        else:
            return "Slow"
    elif metric_name == "flow_efficiency":
        # Flow Efficiency - percentage, higher is better (less waiting)
        # Most orgs: 10-25% (lots of waiting), Good: 40-60%, Excellent: 60%+
        if value >= 60:
            return "Excellent"
        elif value >= 40:
            return "Good"
        elif value >= 25:
            return "Fair"
        else:
            return "Low"

    return "Unknown"


def _get_flow_performance_tier_color(metric_name: str, value: float) -> str:
    """Get performance tier color for Flow metrics.

    Args:
        metric_name: Metric identifier
        value: Metric value

    Returns:
        Color name (green/blue/yellow/orange/red)
    """
    tier = _get_flow_performance_tier(metric_name, value)

    # Map tier labels to colors with visual distinction
    # Excellent (best) -> green, Good -> blue, Fair -> yellow, Low/Slow/High -> orange, Critical -> red
    tier_color_map = {
        "Excellent": "green",
        "Good": "blue",  # Use blue to distinguish from Excellent
        "Healthy": "green",
        "Fair": "yellow",
        "Warning": "yellow",
        "Slow": "orange",
        "Low": "orange",
        "High": "orange",
        "Critical": "red",
    }

    return tier_color_map.get(tier, "yellow")


def _get_flow_metric_color(metric_name: str, value: float) -> str:
    """Get color for metric based on value and thresholds.

    Args:
        metric_name: Name of the metric
        value: Metric value

    Returns:
        Bootstrap color class name
    """
    # Flow Efficiency thresholds
    if metric_name == "flow_efficiency":
        if 25 <= value <= 40:
            return "success"  # Healthy range
        elif value < 15:
            return "danger"  # Critical
        else:
            return "warning"  # Outside ideal range

    # Flow Load (WIP) - lower is generally better
    if metric_name == "flow_load":
        if value < 10:
            return "success"
        elif value < 20:
            return "info"
        else:
            return "warning"

    # Default colors
    return "primary"


def create_flow_metrics_cards_grid(metrics_data: dict):
    """Create a grid of Flow metric cards with Phase 1 enhancements.

    Now uses the same create_metric_card() function as DORA metrics to include:
    - Performance tier badges (Healthy/Warning/Critical for WIP, Good/Needs Improvement for others)
    - Trend indicators with percentage change
    - Mini sparklines
    - Collapsible detail charts

    Args:
        metrics_data: Dictionary mapping metric names to metric data
            Example:
            {
                "flow_velocity": {
                    "metric_name": "flow_velocity",
                    "value": 5.2,
                    "unit": "items/week",
                    "weekly_labels": [...],
                    "weekly_values": [...],
                    ...
                },
                "flow_time": {...}
            }

    Returns:
        dbc.Row containing the grid of Flow metric cards
    """
    from ui.metric_cards import create_metric_card

    if not metrics_data:
        return html.Div(
            children="No Flow metrics available. Please ensure data is loaded.",
            className="text-muted p-3",
        )

    # Create cards using the same function as DORA metrics (with Phase 1 enhancements)
    cards = []
    for metric_name, metric_info in metrics_data.items():
        # Add performance tier and tooltip if not already present
        if "performance_tier" not in metric_info:
            metric_info["performance_tier"] = _get_flow_performance_tier(
                metric_name, metric_info.get("value", 0)
            )
        if "performance_tier_color" not in metric_info:
            metric_info["performance_tier_color"] = _get_flow_performance_tier_color(
                metric_name, metric_info.get("value", 0)
            )
        if "tooltip" not in metric_info:
            metric_info["tooltip"] = FLOW_METRICS_TOOLTIPS.get(metric_name, "")

        # Use the card ID that matches the expected format for callbacks
        card_id = f"{metric_name}-card"
        card = create_metric_card(metric_info, card_id)

        # Phase 2: One card per row for better detail chart visibility, with bottom margin
        cards.append(dbc.Col(card, width=12, className="mb-3"))

    return dbc.Row(cards, className="metric-cards-grid")
