from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards._card_builders import (
    _build_blend_section,
    _build_card_badge,
    _build_sparkline_section,
    _build_title_element,
)
from ui.metric_cards._forecast import create_forecast_section
from ui.metric_cards._helpers import (
    _format_additional_info,
    _get_action_prompt,
    _get_metric_relationship_hint,
)

_TIER_COLOR_MAP = {
    "green": "success",
    "blue": "tier-high",
    "yellow": "tier-medium",
    "orange": "tier-orange",
    "red": "danger",
}

_CUSTOM_CLASS_COLORS = {"tier-high", "tier-medium", "tier-orange"}


def _resolve_flow_load_tier_color(value: float, wip_thresholds: dict[str, Any]) -> str:
    if wip_thresholds and "healthy" in wip_thresholds:
        if value < wip_thresholds["healthy"]:
            return "green"
        if value < wip_thresholds["warning"]:
            return "yellow"
        if value < wip_thresholds["high"]:
            return "orange"
        return "red"
    if value < 10:
        return "green"
    if value < 20:
        return "yellow"
    if value < 30:
        return "orange"
    return "red"


def _format_metric_value(metric_name: str, value: float) -> str:
    if metric_name == "items_completed":
        return f"{int(round(value))}"
    if "items_per_week" in metric_name or "items/week" in metric_name:
        return f"{value:.1f}"
    if "points" in metric_name:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _create_success_card(
    metric_data: dict,
    card_id: str | None,
    forecast_data: dict[str, Any] | None = None,
    trend_vs_forecast: dict[str, Any] | None = None,
    show_details_button: bool = True,
    text_details: list[Any] | None = None,
) -> dbc.Card:

    metric_name = metric_data.get("metric_name", "Unknown Metric")
    value = metric_data.get("value")

    tier_color = metric_data.get("performance_tier_color", "secondary")
    if metric_name == "flow_load" and value is not None:
        tier_color = _resolve_flow_load_tier_color(
            value, metric_data.get("wip_thresholds", {})
        )

    bootstrap_color = _TIER_COLOR_MAP.get(tier_color, "secondary")
    use_custom_class = bootstrap_color in _CUSTOM_CLASS_COLORS

    alternative_name = metric_data.get("alternative_name")
    metric_tooltip = metric_data.get("tooltip")
    display_name = alternative_name or metric_name.replace("_", " ").title()

    formatted_value = (
        _format_metric_value(metric_name, value) if value is not None else "N/A"
    )

    task_value = metric_data.get("task_value")
    formatted_task_value = f"{task_value:.2f}" if task_value is not None else None

    card_props: dict[str, Any] = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    title_element = _build_title_element(
        metric_name, display_name, alternative_name, metric_tooltip
    )
    badge = _build_card_badge(
        metric_name, value, bootstrap_color, use_custom_class, card_id, metric_data
    )
    card_header = dbc.CardHeader(
        [
            html.Div(
                [title_element, badge],
                className="d-flex align-items-center justify-content-between w-100",
            )
        ]
    )

    card_body_children: list[Any] = [
        html.H2(formatted_value, className="text-center metric-value mb-2"),
        html.P(
            metric_data.get("unit", ""),
            className="text-muted text-center metric-unit mb-1",
        ),
    ]

    relationship_hint = _get_metric_relationship_hint(metric_name, value, metric_data)
    if relationship_hint:
        card_body_children.append(
            html.P(
                [html.I(className="fas fa-lightbulb me-1"), relationship_hint],
                className="text-muted text-center small mb-2",
                style={"fontSize": "0.8rem", "fontStyle": "italic"},
            )
        )

    weekly_labels: list[str] = metric_data.get("weekly_labels", [])
    weekly_values: list[float] = metric_data.get("weekly_values", [])
    if metric_name == "deployment_frequency":
        sparkline_values = metric_data.get("weekly_release_values") or weekly_values
    else:
        sparkline_values = weekly_values

    if metric_name == "deployment_frequency" and formatted_task_value is not None:
        card_body_children.append(
            html.Div(
                [
                    html.I(className="fas fa-rocket me-1"),
                    html.Span(f"{formatted_task_value} deployments/week"),
                ],
                className="text-center text-muted small mb-2",
            )
        )

    if metric_name == "change_failure_rate":
        release_cfr = metric_data.get("release_value")
        if release_cfr is not None:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className="fas fa-tag me-1"),
                        html.Span(f"{release_cfr:.1f}% by release"),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    if metric_name == "lead_time_for_changes":
        value_hours = metric_data.get("value_hours")
        if value_hours is not None:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className="fas fa-clock me-1"),
                        html.Span(f"{value_hours:.2f} hours"),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )
    elif metric_name == "mean_time_to_recovery":
        value_days = metric_data.get("value_days")
        if value_days is not None:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className="fas fa-calendar-day me-1"),
                        html.Span(f"{value_days:.2f} days"),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    if forecast_data or trend_vs_forecast:
        forecast_section = create_forecast_section(
            forecast_data=forecast_data,
            trend_vs_forecast=trend_vs_forecast,
            metric_name=metric_name,
            unit=metric_data.get("unit", ""),
        )
        if forecast_section.children:
            card_body_children.append(forecast_section)

    blend_section = _build_blend_section(
        metric_data.get("blend_metadata"), weekly_values, forecast_data
    )
    if blend_section is not None:
        card_body_children.append(blend_section)

    if text_details:
        card_body_children.append(html.Hr(className="my-2"))
        card_body_children.extend(text_details)

    sparkline_section = _build_sparkline_section(
        metric_name, weekly_labels, sparkline_values, tier_color, show_details_button
    )
    if sparkline_section is not None:
        card_body_children.append(sparkline_section)

    card_body_children.extend(
        [
            html.Hr(className="my-2"),
            html.Small(
                _format_additional_info(metric_data),
                className="text-muted d-block text-center",
            ),
        ]
    )

    card_body = dbc.CardBody(card_body_children)

    action_prompt = _get_action_prompt(metric_name, value, metric_data)
    if action_prompt:
        card_footer = dbc.CardFooter(
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Span(action_prompt),
                ],
                color="warning",
                className="mb-0 py-2 px-3",
                style={"fontSize": "0.85rem", "lineHeight": "1.4"},
            ),
            className="bg-light border-top",
        )
    else:
        card_footer = dbc.CardFooter(
            html.Div(
                "\u00a0",
                className="text-center text-muted",
                style={"fontSize": "0.75rem", "opacity": "0"},
            ),
            className="bg-light border-top py-2",
        )

    return dbc.Card([card_header, card_body, card_footer], **card_props)  # type: ignore[call-arg]
