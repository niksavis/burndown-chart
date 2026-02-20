"""DORA/Flow metric detail callback handlers.

Contains collapse toggles, lazy detail chart rendering, and progress state restore.
"""

from __future__ import annotations

import logging
from typing import Any

from dash import Input, Output, State, callback, html, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("flow_velocity-details-collapse", "is_open"),
    Input("flow_velocity-details-btn", "n_clicks"),
    State("flow_velocity-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_velocity_details(n_clicks, is_open):
    """Toggle Flow Velocity detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("flow_time-details-collapse", "is_open"),
    Input("flow_time-details-btn", "n_clicks"),
    State("flow_time-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_time_details(n_clicks, is_open):
    """Toggle Flow Time detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("flow_efficiency-details-collapse", "is_open"),
    Input("flow_efficiency-details-btn", "n_clicks"),
    State("flow_efficiency-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_efficiency_details(n_clicks, is_open):
    """Toggle Flow Efficiency detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("flow_load-details-collapse", "is_open"),
    Input("flow_load-details-btn", "n_clicks"),
    State("flow_load-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_load_details(n_clicks, is_open):
    """Toggle Flow Load detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("lead_time_for_changes-details-collapse", "is_open"),
    Input("lead_time_for_changes-details-btn", "n_clicks"),
    State("lead_time_for_changes-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_lead_time_details(n_clicks, is_open):
    """Toggle Lead Time for Changes detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("deployment_frequency-details-collapse", "is_open"),
    Input("deployment_frequency-details-btn", "n_clicks"),
    State("deployment_frequency-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_deployment_frequency_details(n_clicks, is_open):
    """Toggle Deployment Frequency detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("change_failure_rate-details-collapse", "is_open"),
    Input("change_failure_rate-details-btn", "n_clicks"),
    State("change_failure_rate-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_change_failure_rate_details(n_clicks, is_open):
    """Toggle Change Failure Rate detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("mean_time_to_recovery-details-collapse", "is_open"),
    Input("mean_time_to_recovery-details-btn", "n_clicks"),
    State("mean_time_to_recovery-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_mean_time_to_recovery_details(n_clicks, is_open):
    """Toggle Mean Time to Recovery detailed chart collapse."""
    return not is_open if n_clicks else is_open


def _get_metric_display_name(metric_name: str, metric_data: dict[str, Any]) -> str:
    """Resolve display name for a metric chart."""
    alternative_name = metric_data.get("alternative_name")
    if alternative_name:
        return str(alternative_name)
    return metric_name.replace("_", " ").title()


def _get_dora_tier_hex_color(tier_color: str) -> str:
    """Map DORA tier colors to hex values for trend lines."""
    return {
        "green": "#198754",
        "blue": "#0dcaf0",
        "yellow": "#ffc107",
        "orange": "#fd7e14",
    }.get(tier_color, "#6c757d")


def _build_metric_details_chart(metric_name: str, metric_data: dict[str, Any]) -> Any:
    """Create a detail chart for the expanded metric card."""
    from ui.metric_cards import (
        _create_detailed_chart,
        _get_flow_performance_tier_color_hex,
    )

    weekly_labels = metric_data.get("weekly_labels", [])
    weekly_values = metric_data.get("weekly_values", [])
    weekly_values_adjusted = metric_data.get("weekly_values_adjusted")
    if not weekly_labels or not weekly_values:
        return html.Div()

    display_name = _get_metric_display_name(metric_name, metric_data)
    latest_value = weekly_values[-1] if weekly_values else 0

    if metric_name.startswith("flow_"):
        sparkline_color = _get_flow_performance_tier_color_hex(
            metric_name, latest_value
        )
    else:
        sparkline_color = _get_dora_tier_hex_color(
            metric_data.get("performance_tier_color", "")
        )

    return _create_detailed_chart(
        metric_name=metric_name,
        display_name=display_name,
        weekly_labels=weekly_labels,
        weekly_values=weekly_values,
        weekly_values_adjusted=weekly_values_adjusted,
        metric_data=metric_data,
        sparkline_color=sparkline_color,
    )


def _render_metric_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    metric_name: str,
    current_children: Any,
) -> Any:
    """Render the metric details chart only when the collapse is open."""
    if not is_open:
        return no_update
    if current_children:
        return no_update
    if not metrics_store:
        return html.Div()

    metric_data = metrics_store.get(metric_name)
    if not isinstance(metric_data, dict):
        return html.Div()
    return _build_metric_details_chart(metric_name, metric_data)


@callback(
    Output("flow_velocity-details-chart", "children"),
    Input("flow_velocity-details-collapse", "is_open"),
    State("flow-metrics-store", "data"),
    State("flow_velocity-details-chart", "children"),
    prevent_initial_call=True,
)
def render_flow_velocity_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Flow Velocity detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "flow_velocity", current_children
    )


@callback(
    Output("flow_time-details-chart", "children"),
    Input("flow_time-details-collapse", "is_open"),
    State("flow-metrics-store", "data"),
    State("flow_time-details-chart", "children"),
    prevent_initial_call=True,
)
def render_flow_time_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Flow Time detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "flow_time", current_children
    )


@callback(
    Output("flow_efficiency-details-chart", "children"),
    Input("flow_efficiency-details-collapse", "is_open"),
    State("flow-metrics-store", "data"),
    State("flow_efficiency-details-chart", "children"),
    prevent_initial_call=True,
)
def render_flow_efficiency_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Flow Efficiency detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "flow_efficiency", current_children
    )


@callback(
    Output("flow_load-details-chart", "children"),
    Input("flow_load-details-collapse", "is_open"),
    State("flow-metrics-store", "data"),
    State("flow_load-details-chart", "children"),
    prevent_initial_call=True,
)
def render_flow_load_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Flow Load detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "flow_load", current_children
    )


@callback(
    Output("deployment_frequency-details-chart", "children"),
    Input("deployment_frequency-details-collapse", "is_open"),
    State("dora-metrics-store", "data"),
    State("deployment_frequency-details-chart", "children"),
    prevent_initial_call=True,
)
def render_deployment_frequency_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Deployment Frequency detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "deployment_frequency", current_children
    )


@callback(
    Output("lead_time_for_changes-details-chart", "children"),
    Input("lead_time_for_changes-details-collapse", "is_open"),
    State("dora-metrics-store", "data"),
    State("lead_time_for_changes-details-chart", "children"),
    prevent_initial_call=True,
)
def render_lead_time_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Lead Time for Changes detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "lead_time_for_changes", current_children
    )


@callback(
    Output("change_failure_rate-details-chart", "children"),
    Input("change_failure_rate-details-collapse", "is_open"),
    State("dora-metrics-store", "data"),
    State("change_failure_rate-details-chart", "children"),
    prevent_initial_call=True,
)
def render_change_failure_rate_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Change Failure Rate detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "change_failure_rate", current_children
    )


@callback(
    Output("mean_time_to_recovery-details-chart", "children"),
    Input("mean_time_to_recovery-details-collapse", "is_open"),
    State("dora-metrics-store", "data"),
    State("mean_time_to_recovery-details-chart", "children"),
    prevent_initial_call=True,
)
def render_mean_time_to_recovery_details_chart(
    is_open: bool,
    metrics_store: dict[str, Any] | None,
    current_children: Any,
) -> Any:
    """Render Mean Time to Recovery detail chart lazily."""
    return _render_metric_details_chart(
        is_open, metrics_store, "mean_time_to_recovery", current_children
    )


@callback(
    [
        Output("calculate-metrics-button", "disabled", allow_duplicate=True),
        Output("calculate-metrics-button", "children", allow_duplicate=True),
        Output("calculate-metrics-status", "children", allow_duplicate=True),
    ],
    Input("url", "pathname"),
    prevent_initial_call="initial_duplicate",
)
def restore_calculate_metrics_progress(pathname):
    """Restore metrics calculation button state if task is in progress."""
    from data.task_progress import TaskProgress

    active_task = TaskProgress.get_active_task()
    if active_task and active_task.get("task_id") == "calculate_metrics":
        logger.info("Restoring metrics calculation progress state on page load")
        button_loading = [
            html.I(className="fas fa-spinner fa-spin", style={"marginRight": "0.5rem"}),
            "Calculating...",
        ]
        status_message = html.Div(
            [
                html.I(className="fas fa-spinner fa-spin me-2 text-primary"),
                html.Span(
                    TaskProgress.get_task_status_message("calculate_metrics")
                    or "Calculating metrics...",
                    className="fw-medium",
                ),
            ],
            className="text-primary small text-center mt-2",
        )
        return True, button_loading, status_message

    button_normal = [
        html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
        "Calculate Metrics",
    ]
    return False, button_normal, ""
