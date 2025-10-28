"""DORA Metrics Dashboard UI Components.

Provides the user interface for viewing DORA (DevOps Research and Assessment) metrics.
Displays all four DORA metrics with performance tier indicators and error states.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html, dcc

from ui.metric_cards import create_metric_cards_grid, create_loading_card


def create_dora_dashboard() -> dbc.Container:
    """Create the complete DORA metrics dashboard layout.
    
    Returns:
        dbc.Container with DORA metrics dashboard components
    """
    return dbc.Container(
        [
            # Header section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                "DORA Metrics Dashboard",
                                className="mb-2",
                            ),
                            html.P(
                                "DevOps Research and Assessment metrics for measuring "
                                "software delivery and operational performance.",
                                className="text-muted mb-4",
                            ),
                        ],
                        width=12,
                        md=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-cog me-2"),
                                    "Configure Field Mappings",
                                ],
                                id="open-field-mapping-modal",
                                color="secondary",
                                className="float-end",
                            ),
                        ],
                        width=12,
                        md=4,
                        className="d-flex align-items-center justify-content-end",
                    ),
                ],
                className="mb-4",
            ),
            
            # Time period selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Time Period:", className="fw-bold mb-2"),
                            dbc.Select(
                                id="dora-time-period-select",
                                options=[
                                    {"label": "Last 7 Days", "value": "7"},
                                    {"label": "Last 30 Days", "value": "30"},
                                    {"label": "Last 90 Days", "value": "90"},
                                    {"label": "Custom Range", "value": "custom"},
                                ],
                                value="30",
                                className="mb-3",
                            ),
                        ],
                        width=12,
                        md=6,
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Label("Custom Date Range:", className="fw-bold mb-2"),
                                    dcc.DatePickerRange(
                                        id="dora-date-range-picker",
                                        display_format="YYYY-MM-DD",
                                        className="d-block",
                                        style={"display": "none"},  # Hidden by default
                                    ),
                                ],
                                id="dora-custom-date-range-container",
                            ),
                        ],
                        width=12,
                        md=6,
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-sync-alt me-2"),
                                    "Refresh Metrics",
                                ],
                                id="dora-refresh-button",
                                color="primary",
                                className="mt-4",
                            ),
                        ],
                        width=12,
                        md=12,
                        lg=4,
                        className="d-flex align-items-end justify-content-lg-end",
                    ),
                ],
                className="mb-4",
            ),
            
            # Loading/Error state placeholder
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                id="dora-loading-state",
                                children=[]  # Will be populated by callback
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            
            # Metrics cards grid
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                id="dora-metrics-cards-container",
                                children=[
                                    # Initial loading state
                                    create_metric_cards_grid({
                                        "deployment_frequency": {
                                            "metric_name": "deployment_frequency",
                                            "value": None,
                                            "error_state": "loading",
                                        },
                                        "lead_time_for_changes": {
                                            "metric_name": "lead_time_for_changes",
                                            "value": None,
                                            "error_state": "loading",
                                        },
                                        "change_failure_rate": {
                                            "metric_name": "change_failure_rate",
                                            "value": None,
                                            "error_state": "loading",
                                        },
                                        "mean_time_to_recovery": {
                                            "metric_name": "mean_time_to_recovery",
                                            "value": None,
                                            "error_state": "loading",
                                        },
                                    }),
                                ],
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            
            # Information and help section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-info-circle me-2"),
                                            "About DORA Metrics",
                                        ],
                                        className="fw-bold",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                "DORA metrics measure software delivery performance through "
                                                "four key indicators:",
                                                className="mb-2",
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        [
                                                            html.Strong("Deployment Frequency: "),
                                                            "How often code is deployed to production",
                                                        ]
                                                    ),
                                                    html.Li(
                                                        [
                                                            html.Strong("Lead Time for Changes: "),
                                                            "Time from code commit to production deployment",
                                                        ]
                                                    ),
                                                    html.Li(
                                                        [
                                                            html.Strong("Change Failure Rate: "),
                                                            "Percentage of deployments causing incidents",
                                                        ]
                                                    ),
                                                    html.Li(
                                                        [
                                                            html.Strong("Mean Time to Recovery: "),
                                                            "Average time to restore service after an incident",
                                                        ]
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            html.P(
                                                [
                                                    "Performance tiers (Elite, High, Medium, Low) are based on ",
                                                    html.A(
                                                        "DORA research benchmarks",
                                                        href="https://dora.dev/",
                                                        target="_blank",
                                                        className="text-decoration-none",
                                                    ),
                                                    ".",
                                                ],
                                                className="mb-0 text-muted",
                                            ),
                                        ]
                                    ),
                                ],
                                className="border-start border-primary border-4",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
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
    raw_metrics: Dict[str, Dict[str, Any]]
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
