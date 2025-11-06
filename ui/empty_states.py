"""Empty State UI Components.

Provides unified "no data" and "no metrics" states for Flow and DORA dashboards.
Ensures consistent messaging and visual design across the application.
"""

from dash import html
import dash_bootstrap_components as dbc


def create_no_metrics_state(metric_type: str = "Flow") -> html.Div:
    """Create unified empty state when metrics haven't been calculated.

    Args:
        metric_type: "Flow" or "DORA" to customize messaging

    Returns:
        html.Div with empty state UI
    """
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-line fa-4x text-primary mb-4",
                                        style={"opacity": "0.3"},
                                    ),
                                    html.H4(
                                        "Metrics Not Yet Calculated",
                                        className="text-dark mb-3",
                                    ),
                                    html.P(
                                        f"{metric_type} metrics are calculated from your JIRA data and cached for fast display.",
                                        className="text-muted mb-4",
                                    ),
                                ],
                                className="text-center mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-calculator fa-2x text-primary mb-3"
                                                    ),
                                                    html.H5(
                                                        "Calculate Metrics",
                                                        className="mb-2",
                                                    ),
                                                    html.P(
                                                        "Click the Calculate Metrics button in the Settings panel (top right) to process your JIRA data.",
                                                        className="text-muted small mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            ),
                                        ]
                                    ),
                                ],
                                className="border-0 shadow-sm h-100",
                            ),
                        ],
                        md=6,
                        className="mb-3 d-flex",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-bolt fa-2x text-success mb-3"
                                                    ),
                                                    html.H5(
                                                        "Fast & Cached",
                                                        className="mb-2",
                                                    ),
                                                    html.P(
                                                        "Metrics are calculated once and cached. Future page loads are instant.",
                                                        className="text-muted small mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            ),
                                        ]
                                    ),
                                ],
                                className="border-0 shadow-sm h-100",
                            ),
                        ],
                        md=6,
                        className="mb-3 d-flex",
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Alert(
                                [
                                    html.I(className="fas fa-info-circle me-2"),
                                    html.Strong("Quick Start: "),
                                    "1) Ensure JIRA data is loaded (Update Data button) → ",
                                    "2) Configure field mappings if needed → ",
                                    "3) Click Calculate Metrics → ",
                                    "4) View your metrics dashboard",
                                ],
                                color="info",
                                className="mb-0",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        className="p-5",
    )


def create_no_data_state() -> html.Div:
    """Create unified empty state when no JIRA data is loaded.

    Returns:
        html.Div with empty state UI
    """
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-database fa-4x text-warning mb-4",
                                        style={"opacity": "0.3"},
                                    ),
                                    html.H4(
                                        "No JIRA Data Loaded",
                                        className="text-dark mb-3",
                                    ),
                                    html.P(
                                        "Load your JIRA project data to start tracking metrics.",
                                        className="text-muted mb-4",
                                    ),
                                ],
                                className="text-center mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-download fa-2x text-primary mb-3"
                                                    ),
                                                    html.H5(
                                                        "Load JIRA Data",
                                                        className="mb-2",
                                                    ),
                                                    html.P(
                                                        "Click the Update Data button in the Settings panel to fetch issues from JIRA.",
                                                        className="text-muted small mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            ),
                                        ]
                                    ),
                                ],
                                className="border-0 shadow-sm h-100",
                            ),
                        ],
                        md=6,
                        className="mb-3 d-flex",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-cog fa-2x text-info mb-3"
                                                    ),
                                                    html.H5(
                                                        "Configure JIRA",
                                                        className="mb-2",
                                                    ),
                                                    html.P(
                                                        "Ensure JIRA connection is configured in Settings → JIRA Configuration tab.",
                                                        className="text-muted small mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            ),
                                        ]
                                    ),
                                ],
                                className="border-0 shadow-sm h-100",
                            ),
                        ],
                        md=6,
                        className="mb-3 d-flex",
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Alert(
                                [
                                    html.I(className="fas fa-lightbulb me-2"),
                                    html.Strong("Tip: "),
                                    "The first data load may take a few minutes depending on your project size. "
                                    "Subsequent updates are incremental and faster.",
                                ],
                                color="info",
                                className="mb-0",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        className="p-5",
    )
