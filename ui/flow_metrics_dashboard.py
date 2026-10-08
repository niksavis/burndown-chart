from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html

from configuration.help_content_metrics import FLOW_METRICS_TOOLTIPS
from data.cache_manager import has_jira_data_for_query
from data.metrics_snapshots import get_available_weeks
from data.query_manager import get_active_profile_id, get_active_query_id
from ui.empty_states import (
    create_metrics_skeleton,
    create_no_data_state,
    create_no_metrics_state,
)
from ui.metric_cards import create_metric_card
from ui.tooltip_utils import create_info_tooltip


def create_flow_dashboard() -> dbc.Container:

    has_jira_data = False
    has_metrics = False

    try:
        active_profile_id = get_active_profile_id()
        active_query_id = get_active_query_id()

        if active_profile_id and active_query_id:
            has_jira_data = has_jira_data_for_query(active_profile_id, active_query_id)

            if has_jira_data:
                available_weeks = get_available_weeks()
                has_metrics = len(available_weeks) > 0
    except Exception:
        pass

    if not has_jira_data:
        initial_content = [create_no_data_state()]
    elif not has_metrics:
        initial_content = [create_no_metrics_state(metric_type="Flow")]
    else:
        initial_content = [create_metrics_skeleton(num_cards=5)]

    return dbc.Container(
        [
            dcc.Store(id="flow-welcome-dismissed", storage_type="local", data=False),
            html.Div(
                id="flow-welcome-banner",
                children=[],
            ),
            html.Div(
                id="flow-overview-wrapper",
                children=[
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    id="flow-metrics-overview",
                                    children=[],
                                ),
                            ],
                            className="pt-3 px-3 pb-0",
                        ),
                        className="mb-3 overview-section",
                        style={
                            "backgroundColor": "#f8f9fa",
                            "border": "none",
                            "borderRadius": "8px",
                        },
                    ),
                    html.P(
                        [
                            html.I(className="fas fa-info-circle me-2 text-info"),
                            "Flow metrics calculated per ISO week. Use ",
                            html.Strong("Update Data / Force Refresh"),
                            " button to refresh. ",
                            html.Strong("Data Points slider"),
                            " controls weeks displayed.",
                        ],
                        className="text-muted small mb-3 mt-3",
                    ),
                ],
                style={"display": "none"},
            ),
            html.Div(
                children=initial_content,
                id="flow-metrics-cards-container",
                className="mb-4",
            ),
            dcc.Store(id="flow-metrics-store", data={}),
        ],
        fluid=True,
        className="py-4",
    )


def create_flow_metric_card(
    metric_data: dict[str, Any],
    metric_name: str,
) -> dbc.Card:

    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        return _create_flow_error_card(metric_data, metric_name)

    value = metric_data.get("value")
    unit = metric_data.get("unit", "")

    if isinstance(value, float):
        value_display = f"{value:.2f}"
    else:
        value_display = str(value)

    status_color = _get_flow_metric_color(metric_data["metric_name"], value or 0.0)

    metric_key = metric_data["metric_name"]
    tooltip_text = FLOW_METRICS_TOOLTIPS.get(metric_key, "")

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
                    _create_type_breakdown(metric_data.get("details", {})),
                    _create_trend_indicator(metric_data.get("details", {})),
                ]
            ),
        ],
        className="h-100 shadow-sm",
    )

    return card


def _create_flow_error_card(metric_data: dict[str, Any], metric_name: str) -> dbc.Card:

    error_message = metric_data.get("error_message", "Unknown error")

    return dbc.Card(
        [
            dbc.CardBody(
                children=[
                    html.H6(metric_name, className="text-muted mb-2"),
                    html.Div(
                        children=[
                            html.I(
                                className=(
                                    "fas fa-exclamation-triangle text-warning me-2"
                                )
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


def _create_type_breakdown(details: dict[str, Any]) -> html.Div:

    by_type = details.get("by_type", {})

    if not by_type or all(v == 0 for v in by_type.values()):
        return html.Div()

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


def _create_trend_indicator(details: dict[str, Any]) -> html.Div:

    trend_direction = details.get("trend_direction", "unknown")
    trend_percentage = details.get("trend_percentage", 0)

    if trend_direction == "unknown" or trend_percentage == 0:
        return html.Div()

    if trend_direction == "up":
        icon = "fa-arrow-up"
        color = "success"
    elif trend_direction == "down":
        icon = "fa-arrow-down"
        color = "danger"
    else:
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

    if metric_name == "flow_load":
        if value < 10:
            return "Healthy"
        elif value < 20:
            return "Warning"
        elif value < 30:
            return "High"
        else:
            return "Critical"
    elif metric_name == "flow_velocity":
        if value >= 20:
            return "Excellent"
        elif value >= 10:
            return "Good"
        elif value >= 5:
            return "Fair"
        else:
            return "Low"
    elif metric_name == "flow_time":
        if value <= 3:
            return "Excellent"
        elif value <= 7:
            return "Good"
        elif value <= 14:
            return "Fair"
        else:
            return "Slow"
    elif metric_name == "flow_efficiency":
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

    tier = _get_flow_performance_tier(metric_name, value)

    tier_color_map = {
        "Excellent": "green",
        "Good": "blue",
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

    if metric_name == "flow_efficiency":
        if 25 <= value <= 40:
            return "success"
        elif value < 15:
            return "danger"
        else:
            return "warning"

    if metric_name == "flow_load":
        if value < 10:
            return "success"
        elif value < 20:
            return "info"
        else:
            return "warning"

    return "primary"


def create_flow_metrics_cards_grid(metrics_data: dict):

    if not metrics_data:
        return html.Div(
            children="No Flow metrics available. Please ensure data is loaded.",
            className="text-muted p-3",
        )

    cards = []
    for metric_name, metric_info in metrics_data.items():
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

        card_id = f"{metric_name}-card"
        card = create_metric_card(metric_info, card_id)

        cards.append(dbc.Col(card, width=12, className="mb-3"))

    return dbc.Row(cards, className="metric-cards-grid")
