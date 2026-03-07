"""Error and loading state cards for metric display."""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def _create_error_card(metric_data: dict, card_id: str | None) -> dbc.Card:
    """Create card for error state with actionable guidance.

    Matches h-100 layout of success cards for consistent card heights.
    """
    error_state = metric_data.get("error_state", "unknown_error")
    error_message = metric_data.get("error_message", "An error occurred")

    metric_name = metric_data.get("metric_name", "Unknown Metric")
    alternative_name = metric_data.get("alternative_name")
    display_name = (
        alternative_name if alternative_name else metric_name.replace("_", " ").title()
    )

    error_config: dict[str, Any] = {
        "missing_mapping": {
            "icon": "fas fa-cog",
            "title": "Field Mapping Required",
            "color": "warning",
            "action_text": "Configure Mappings",
            "action_id": {"type": "open-field-mapping", "index": metric_name},
            "message_override": (
                "Configure JIRA field mappings in Settings to enable this metric."
            ),
        },
        "field_not_configured": {
            "icon": "fas fa-toggle-off",
            "title": "Metric Disabled",
            "color": "secondary",
            "action_text": "Configure Field Mapping",
            "action_id": {"type": "open-field-mapping", "index": metric_name},
            "message_override": (
                "This metric is disabled because the required JIRA field "
                "mapping is not configured for your JIRA setup."
            ),
        },
        "points_tracking_disabled": {
            "icon": "fas fa-toggle-off",
            "title": "Points Tracking Disabled",
            "color": "secondary",
            "action_text": "Enable in Parameters",
            "action_id": "open-parameters-panel",
            "message_override": (
                "Points tracking is disabled. Enable Points Tracking in "
                "Parameters panel to view story points metrics."
            ),
        },
        "no_data": {
            "icon": "fas fa-database",
            "title": "No Data Available",
            "color": "secondary",
            "action_text": "Recalculate Metrics",
            "action_id": "open-time-period-selector",
            "message_override": (
                "No data available for the selected time period. "
                "Adjust the Data Points slider or refresh metrics."
            ),
        },
        "calculation_error": {
            "icon": "fas fa-exclamation-triangle",
            "title": "Calculation Error",
            "color": "danger",
            "action_text": "Retry Calculation",
            "action_id": "retry-metric-calculation",
        },
    }

    config = error_config.get(
        error_state,
        {
            "icon": "fas fa-exclamation-circle",
            "title": "Error",
            "color": "warning",
            "action_text": "View Details",
            "action_id": "view-error-details",
        },
    )

    card_props: dict[str, Any] = {
        "className": "metric-card metric-card-error mb-3 h-100"
    }
    if card_id:
        card_props["id"] = card_id

    badge_text_map = {
        "no_data": "No Data",
        "missing_mapping": "Setup Required",
        "field_not_configured": "Disabled",
        "points_tracking_disabled": "Disabled",
        "calculation_error": "Error",
    }
    badge_text = badge_text_map.get(error_state, "Error")

    card_header = dbc.CardHeader(
        [
            html.Span(display_name, className="metric-card-title"),
            dbc.Badge(
                children=badge_text,
                color=config["color"],
                className="float-end",
            ),
        ]
    )

    card_body = dbc.CardBody(
        [
            html.Div(
                [
                    html.I(
                        className=(
                            f"{config['icon']} fa-2x text-{config['color']} mb-2"
                        )
                    ),
                    html.H2(
                        "\u2014", className="text-center metric-value mb-1 text-muted"
                    ),
                    html.P(
                        config["title"],
                        className="text-muted text-center metric-unit mb-2",
                    ),
                ],
                className="text-center",
            ),
            html.Hr(className="my-2"),
            html.Small(
                config.get("message_override", error_message),
                className="text-muted d-block text-center",
            ),
        ],
        className="d-flex flex-column",
    )

    card_footer = dbc.CardFooter(
        html.Div(
            "\u00a0",  # Non-breaking space to maintain minimal height
            className="text-center text-muted",
            style={"fontSize": "0.75rem", "opacity": "0"},
        ),
        className="bg-light border-top py-2",
    )

    return dbc.Card([card_header, card_body, card_footer], **card_props)  # type: ignore[call-arg]


def create_loading_card(metric_name: str) -> dbc.Card:
    """Create a loading placeholder card.

    Args:
        metric_name: Name of the metric being calculated

    Returns:
        Card with loading spinner
    """
    display_name = metric_name.replace("_", " ").title()

    return dbc.Card(
        [
            dbc.CardHeader(display_name),
            dbc.CardBody(
                [
                    dbc.Spinner(size="lg", color="primary"),
                    html.P("Calculating...", className="text-muted text-center mt-3"),
                ],
                className="text-center",
            ),
        ],
        className="metric-card metric-card-loading mb-3",
    )
