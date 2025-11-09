"""DORA Metrics Dashboard UI Components.

Provides the user interface for viewing DORA (DevOps Research and Assessment) metrics.
Displays all four DORA metrics with performance tier indicators and error states.

Uses Data Points slider from settings panel to control historical data display.
Metrics calculated per ISO week (Monday-Sunday), showing current week + N-1 historical weeks.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html, dcc

from ui.metric_cards import create_loading_card
from ui.empty_states import (
    create_metrics_skeleton,
    create_no_data_state,
)  # Visible skeleton with shimmer


def create_dora_dashboard() -> dbc.Container:
    """Create the complete DORA metrics dashboard layout.

    Returns:
        dbc.Container with DORA metrics dashboard components
    """
    # Check if JIRA data exists AND if metrics are calculated
    from data.jira_simple import load_jira_cache, get_jira_config
    from data.persistence import load_app_settings
    from data.dora_metrics_calculator import load_dora_metrics_from_cache

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
                            "Metrics calculated per ISO week. Use ",
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
            # Metrics cards grid with loading wrapper
            dcc.Loading(
                id="dora-metrics-loading-wrapper",
                type="dot",
                color="#0d6efd",
                delay_show=100,  # Only show spinner if loading takes >100ms
                children=html.Div(
                    id="dora-metrics-cards-container",
                    children=initial_content,  # Show banner or skeleton based on data availability
                ),
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
                                                        "DORA (DevOps Research and Assessment) metrics measure software "
                                                        "delivery and operational performance:",
                                                        className="mb-3",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-rocket text-primary me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Deployment Frequency"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "How often you deploy to production",
                                                                        className="text-muted small mb-0",
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
                                                                                className="fas fa-clock text-success me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Lead Time for Changes"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "Time from commit to production",
                                                                        className="text-muted small mb-0",
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
                                                                                className="fas fa-exclamation-triangle text-warning me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Change Failure Rate"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "% of deployments causing incidents",
                                                                        className="text-muted small mb-0",
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
                                                                                className="fas fa-wrench text-danger me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Mean Time to Recovery"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "Time to restore service after incident",
                                                                        className="text-muted small mb-0",
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
                                                                className="fas fa-chart-bar me-2"
                                                            ),
                                                            "Metrics show performance tiers (Elite, High, Medium, Low) based on ",
                                                            html.A(
                                                                "DORA research",
                                                                href="https://dora.dev/",
                                                                target="_blank",
                                                                className="text-decoration-none",
                                                            ),
                                                            ". Data is mapped from your JIRA projects using configurable field mappings.",
                                                        ],
                                                        className="mb-0 text-muted small",
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
    raw_metrics: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
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
