"""Bug analysis UI components.

Provides UI components for bug metrics display, charts, and analysis tab layout.
"""

from dash import html
import dash_bootstrap_components as dbc
from typing import Dict


def create_bug_metrics_card(bug_metrics: Dict) -> dbc.Card:
    """Create bug metrics summary card.

    Args:
        bug_metrics: Bug metrics summary dictionary with:
            - total_bugs: Total bug count
            - open_bugs: Open bug count
            - closed_bugs: Closed bug count
            - resolution_rate: Resolution rate (0.0-1.0)

    Returns:
        Dash Bootstrap Components Card with bug metrics
    """
    # Handle zero bugs case (T027)
    if not bug_metrics or bug_metrics.get("total_bugs", 0) == 0:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Bug Metrics", className="card-title"),
                    html.Div(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            html.Span("No bugs found in the current dataset."),
                        ],
                        className="alert alert-info",
                    ),
                ]
            ),
            className="mb-3",
        )

    # Extract metrics
    total_bugs = bug_metrics.get("total_bugs", 0)
    open_bugs = bug_metrics.get("open_bugs", 0)
    closed_bugs = bug_metrics.get("closed_bugs", 0)
    resolution_rate = bug_metrics.get("resolution_rate", 0.0)

    # Determine resolution rate color
    if resolution_rate >= 0.80:
        rate_color = "success"
    elif resolution_rate >= 0.70:
        rate_color = "warning"
    else:
        rate_color = "danger"

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Bug Metrics Overview", className="card-title mb-3"),
                # Metrics row
                dbc.Row(
                    [
                        # Total bugs
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-bug fa-2x text-primary mb-2"
                                        ),
                                        html.H3(total_bugs, className="mb-0"),
                                        html.P(
                                            "Total Bugs", className="text-muted small"
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=12,
                            md=3,
                        ),
                        # Open bugs
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-folder-open fa-2x text-warning mb-2"
                                        ),
                                        html.H3(open_bugs, className="mb-0"),
                                        html.P("Open", className="text-muted small"),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=12,
                            md=3,
                        ),
                        # Closed bugs
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-check-circle fa-2x text-success mb-2"
                                        ),
                                        html.H3(closed_bugs, className="mb-0"),
                                        html.P("Closed", className="text-muted small"),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=12,
                            md=3,
                        ),
                        # Resolution rate
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className=f"fas fa-chart-line fa-2x text-{rate_color} mb-2"
                                        ),
                                        html.H3(
                                            f"{resolution_rate * 100:.1f}%",
                                            className="mb-0",
                                        ),
                                        html.P(
                                            "Resolution Rate",
                                            className="text-muted small",
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=12,
                            md=3,
                        ),
                    ],
                    className="g-3",
                ),
                # Additional details
                html.Hr(className="my-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Small(
                                    [
                                        html.I(className="fas fa-info-circle me-1"),
                                        f"Average resolution time: {bug_metrics.get('avg_resolution_time_days', 0):.1f} days",
                                    ],
                                    className="text-muted",
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
            ]
        ),
        className="mb-3",
    )


def create_bug_analysis_tab() -> html.Div:
    """Create bug analysis tab layout.

    Returns:
        Dash HTML Div containing the bug analysis tab layout
    """
    return html.Div(
        [
            # Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                [
                                    html.I(className="fas fa-bug me-2"),
                                    "Bug Analysis Dashboard",
                                ],
                                className="mb-3",
                            ),
                            html.P(
                                "Track bug creation, resolution trends, and quality metrics to maintain project health.",
                                className="text-muted",
                            ),
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Bug metrics card (will be populated by callback)
            dbc.Row(
                [dbc.Col([html.Div(id="bug-metrics-card")], width=12)], className="mb-4"
            ),
            # Bug trends chart (will be populated by callback)
            dbc.Row(
                [dbc.Col([html.Div(id="bug-trends-chart")], width=12)], className="mb-4"
            ),
            # Placeholder for future insights
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-lightbulb fa-3x text-muted mb-3"
                                    ),
                                    html.H5(
                                        "Quality Insights Coming Soon",
                                        className="text-muted",
                                    ),
                                    html.P(
                                        "Actionable recommendations will be displayed here.",
                                        className="text-muted small",
                                    ),
                                ],
                                className="text-center p-5 border rounded bg-light",
                            )
                        ],
                        width=12,
                    )
                ]
            ),
        ],
        id="bug-analysis-tab-content",
    )
