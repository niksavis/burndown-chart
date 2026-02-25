"""DORA Metrics Dashboard UI Components.

Provides the user interface for viewing DORA (DevOps Research and Assessment) metrics.
Displays all four DORA metrics with performance tier indicators and error states.

Uses Data Points slider from settings panel to control historical data display.
Metrics calculated per ISO week (Monday-Sunday),
showing current week + N-1 historical weeks.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.empty_states import (
    create_metrics_skeleton,
    create_no_data_state,
)  # Visible skeleton with shimmer
from ui.metric_cards import create_loading_card


def create_dora_dashboard() -> dbc.Container:
    """Create the complete DORA metrics dashboard layout.

    Returns:
        dbc.Container with DORA metrics dashboard components
    """
    # Check if JIRA data exists AND if metrics are calculated
    from data.cache_manager import has_jira_data_for_query
    from data.dora_metrics_calculator import load_dora_metrics_from_cache
    from data.query_manager import get_active_profile_id, get_active_query_id

    has_jira_data = False
    has_metrics = False

    try:
        # Check if JIRA data exists in database for active query
        active_profile_id = get_active_profile_id()
        active_query_id = get_active_query_id()

        if active_profile_id and active_query_id:
            has_jira_data = has_jira_data_for_query(active_profile_id, active_query_id)

            # Check if metrics are calculated
            if has_jira_data:
                cached_metrics = load_dora_metrics_from_cache(n_weeks=12)
                has_metrics = bool(cached_metrics)
    except Exception:
        pass  # No data available

    # Determine initial content based on what's available
    if not has_jira_data:
        initial_content = [create_no_data_state()]
    elif not has_metrics:
        from ui.empty_states import create_no_metrics_state

        initial_content = [create_no_metrics_state(metric_type="DORA")]
    else:
        initial_content = [create_metrics_skeleton()]

    overview_body_class = "pt-3 px-3 pb-0"
    overview_info_class = "text-muted small mb-3 mt-3"
    metric_desc_class = "text-muted small mb-0"
    metrics_blurb_class = "mb-0 text-muted small"
    dora_intro_text = (
        "DORA (DevOps Research and Assessment) metrics measure "
        "software delivery and operational performance:"
    )
    deploy_icon_class = "fas fa-rocket text-primary me-2"
    lead_time_icon_class = "fas fa-clock text-success me-2"
    failure_rate_icon_class = "fas fa-exclamation-triangle text-warning me-2"
    mttr_icon_class = "fas fa-wrench text-danger me-2"
    deploy_label = "Deployment Frequency"
    lead_time_label = "Lead Time for Changes"
    failure_rate_label = "Change Failure Rate"
    mttr_label = "Mean Time to Recovery"
    deploy_desc = "How often you deploy to production"
    lead_time_desc = "Time from commit to production"
    failure_rate_desc = "% of deployments causing incidents"
    mttr_desc = "Time to restore service after incident"
    chart_bar_icon_class = "fas fa-chart-bar me-2"
    tiers_text = "Metrics show performance tiers (Elite, High, Medium, Low) based on "
    mapping_text = (
        ". Data is mapped from your JIRA projects using configurable field mappings."
    )

    return dbc.Container(
        [
            # Store for tracking if user has seen welcome banner (uses localStorage)
            dcc.Store(id="dora-welcome-dismissed", storage_type="local", data=False),
            # Welcome banner for first-time users (dismissible)
            html.Div(
                id="dora-welcome-banner",
                children=[],  # Will be populated by callback based on storage
            ),
            # Compact overview section with distinct background
            html.Div(
                id="dora-overview-wrapper",
                children=[
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    id="dora-metrics-overview",
                                    children=[],  # Will be populated by callback
                                ),
                            ],
                            className=overview_body_class,
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
                            html.I(className="fas fa-info-circle me-2 text-info"),
                            "Metrics calculated per ISO week. Use ",
                            html.Strong("Update Data / Force Refresh"),
                            " button to refresh. ",
                            html.Strong("Data Points slider"),
                            " controls weeks displayed.",
                        ],
                        className=overview_info_class,
                    ),
                ],
                style={
                    "display": "none"
                },  # Hidden by default, shown by callback when metrics exist
            ),
            # Metrics cards grid (no loading wrapper - skeleton provides loading state)
            html.Div(
                id="dora-metrics-cards-container",
                children=initial_content,
            ),
            # Information and help section (only shown when metrics are available)
            html.Div(
                id="dora-info-section",
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                [
                                                    html.I(
                                                        className="fas fa-rocket me-2"
                                                    ),
                                                    "About DORA Metrics",
                                                ],
                                                className="fw-bold",
                                            ),
                                            dbc.CardBody(
                                                [
                                                    html.P(
                                                        dora_intro_text,
                                                        className="mb-3",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className=deploy_icon_class
                                                                            ),
                                                                            html.Strong(
                                                                                deploy_label
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        deploy_desc,
                                                                        className=metric_desc_class,
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className=lead_time_icon_class
                                                                            ),
                                                                            html.Strong(
                                                                                lead_time_label
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        lead_time_desc,
                                                                        className=metric_desc_class,
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                        ]
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className=failure_rate_icon_class
                                                                            ),
                                                                            html.Strong(
                                                                                failure_rate_label
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        failure_rate_desc,
                                                                        className=metric_desc_class,
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className=mttr_icon_class
                                                                            ),
                                                                            html.Strong(
                                                                                mttr_label
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        mttr_desc,
                                                                        className=metric_desc_class,
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                        ]
                                                    ),
                                                    html.Hr(className="my-3"),
                                                    html.P(
                                                        [
                                                            html.I(
                                                                className=chart_bar_icon_class
                                                            ),
                                                            tiers_text,
                                                            html.A(
                                                                "DORA research",
                                                                href="https://dora.dev/",
                                                                target="_blank",
                                                                className="text-decoration-none",
                                                            ),
                                                            mapping_text,
                                                        ],
                                                        className=metrics_blurb_class,
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="border-0 shadow-sm",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-4",
                    )
                ],
                style={
                    "display": "none"
                },  # Hidden by default, shown by callback when metrics exist
            ),
            # Store for metrics data
            dcc.Store(id="dora-metrics-store", data={}),
        ],
        fluid=True,
        className="dora-dashboard-container py-4",
    )


def create_dora_loading_cards_grid() -> dbc.Row:
    """Create a grid of loading cards for DORA metrics.

    Returns:
        dbc.Row containing loading state cards
    """
    loading_metrics = [
        "deployment_frequency",
        "lead_time_for_changes",
        "change_failure_rate",
        "mean_time_to_recovery",
    ]

    cards = dbc.Row(
        [
            dbc.Col(
                create_loading_card(metric_name),
                width=12,
                md=6,
                lg=3,
                className="mb-3",
            )
            for metric_name in loading_metrics
        ],
        className="metric-cards-grid",
    )

    return cards


def format_dora_metrics_for_display(
    raw_metrics: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Format raw DORA metrics data for display in metric cards.

    Args:
        raw_metrics: Raw metrics data from calculator

    Returns:
        Formatted metrics ready for metric card rendering
    """
    formatted = {}

    for metric_name, metric_data in raw_metrics.items():
        # Pass through most fields as-is
        formatted[metric_name] = {
            "metric_name": metric_name,
            "value": metric_data.get("value"),
            "unit": metric_data.get("unit"),
            "performance_tier": metric_data.get("performance_tier"),
            "performance_tier_color": metric_data.get("performance_tier_color"),
            "error_state": metric_data.get("error_state", "success"),
            "error_message": metric_data.get("error_message"),
            "total_issue_count": metric_data.get("total_issue_count", 0),
            "excluded_issue_count": metric_data.get("excluded_issue_count", 0),
            "details": metric_data.get("details", {}),
        }

    return formatted
