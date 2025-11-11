"""Empty State UI Components.

Provides unified "no data" and "no metrics" states for Flow and DORA dashboards.
Ensures consistent messaging and visual design across the application.
"""

from dash import html
import dash_bootstrap_components as dbc


def create_loading_placeholder() -> html.Div:
    """Create an invisible placeholder that exactly matches empty state banner structure.

    This prevents layout shift (CLS) by reserving exact space before the actual banner loads.
    Uses the same DOM structure as create_no_data_state() but with opacity: 0.

    Returns:
        html.Div with invisible banner matching exact dimensions
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
                                        style={"opacity": "0"},
                                    ),
                                    html.H4(
                                        "Loading...",
                                        className="text-dark mb-3",
                                    ),
                                    html.P(
                                        "Placeholder text for spacing.",
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
                                                        "Placeholder Card",
                                                        className="mb-2",
                                                    ),
                                                    html.P(
                                                        "Placeholder text to match card height exactly.",
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
                                                        "Placeholder Card",
                                                        className="mb-2",
                                                    ),
                                                    html.P(
                                                        "Placeholder text to match card height exactly.",
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
                                    "Placeholder text to match alert height exactly.",
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
        className="p-5",  # Match padding of actual empty state
        style={"opacity": "0"},  # Completely invisible but takes up space
    )


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
                                        [
                                            f"{metric_type} metrics are calculated from your JIRA data and cached for fast display. ",
                                            "Configure Field Mappings (Settings → Field Mappings → Fields tab) ",
                                            "and optionally specify DevOps Projects before calculating."
                                            if metric_type == "DORA"
                                            else "to ensure accurate metric calculation.",
                                        ],
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
        className="p-5 empty-state-banner",  # Standard padding + animation class
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
        className="p-5 empty-state-banner",  # Standard padding + animation class
    )


def create_metrics_skeleton(num_cards: int = 4) -> dbc.Row:
    """Create a visible skeleton grid with shimmer effect.

    Shows a loading placeholder that matches the metric cards layout to prevent
    layout shift (CLS) while content loads.

    Args:
        num_cards: Number of metric cards to create (default 4 for DORA, use 5 for Flow)

    Returns:
        dbc.Row with visible skeleton cards with shimmer animation
    """
    skeleton_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    style={"height": "24px", "backgroundColor": "#e9ecef"},
                    className="skeleton-shimmer",
                ),
            ),
            dbc.CardBody(
                [
                    # Large metric value placeholder
                    html.Div(
                        style={
                            "height": "48px",
                            "backgroundColor": "#e9ecef",
                            "marginBottom": "16px",
                        },
                        className="skeleton-shimmer",
                    ),
                    # Performance tier badge placeholder
                    html.Div(
                        style={
                            "height": "24px",
                            "width": "120px",
                            "margin": "0 auto 16px",
                            "backgroundColor": "#e9ecef",
                        },
                        className="skeleton-shimmer",
                    ),
                    # Chart placeholder
                    html.Div(
                        style={"height": "200px", "backgroundColor": "#e9ecef"},
                        className="skeleton-shimmer",
                    ),
                ],
                className="text-center",
            ),
        ],
        className="metric-card mb-3",
        # Removed opacity: 0 - skeleton should be visible
    )

    # Create 2-column grid with specified number of cards
    # For Flow metrics (num_cards=5), the last card (Work Distribution) spans full width
    cols = []
    for i in range(num_cards):
        # Last card in 5-card layout spans full width (Work Distribution)
        if num_cards == 5 and i == num_cards - 1:
            cols.append(dbc.Col(skeleton_card, xs=12, lg=12, className="mb-3"))
        else:
            cols.append(dbc.Col(skeleton_card, xs=12, lg=6, className="mb-3"))

    return dbc.Row(
        cols,
        className="metric-cards-skeleton",  # Different class to avoid animation conflict
        # Removed opacity: 0 - skeleton should be visible with shimmer
    )
