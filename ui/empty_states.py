"""Empty State UI Components.

Provides unified "no data" and "no metrics" states for Flow and DORA dashboards.
Ensures consistent messaging and visual design across the application.
"""

from typing import List, Dict, Any
from dash import html
import dash_bootstrap_components as dbc


def _create_info_card_row(cards: List[Dict[str, Any]]) -> dbc.Row:
    """Create a centered row with info cards (DRY helper).

    Args:
        cards: List of dicts with keys:
            - icon: Font Awesome icon name (e.g., "calculator", "bolt")
            - icon_color: Bootstrap color class (e.g., "primary", "success")
            - title: Card heading text
            - description: Card body text

    Returns:
        dbc.Row with centered cards
    """
    cols = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        [
                            html.I(
                                className=f"fas fa-{card['icon']} fa-2x text-{card['icon_color']} mb-3"
                            ),
                            html.H5(card["title"], className="mb-2"),
                            html.P(
                                card["description"],
                                className="text-muted small mb-0",
                            ),
                        ],
                        className="text-center",
                    )
                ),
                className="empty-state-card border-0 shadow-sm h-100",
            ),
            xs=12,
            md=5,
            lg=4,
            className="mb-3 d-flex",
        )
        for card in cards
    ]
    return dbc.Row(cols, justify="center")


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
                        _create_info_card_row(
                            [
                                {
                                    "icon": "download",
                                    "icon_color": "primary",
                                    "title": "Placeholder Card",
                                    "description": "Placeholder text to match card height exactly.",
                                },
                                {
                                    "icon": "cog",
                                    "icon_color": "info",
                                    "title": "Placeholder Card",
                                    "description": "Placeholder text to match card height exactly.",
                                },
                            ]
                        ),
                        xs=12,
                        lg=10,
                        xl=8,
                        className="mx-auto",
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
                                    "Placeholder text to match alert height exactly.",
                                ],
                                color="info",
                                className="mb-0 empty-state-alert",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        className="p-5 empty-state-banner",  # Match padding of actual empty state
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
                                        className="empty-state-title mb-3",
                                    ),
                                    html.P(
                                        [
                                            f"{metric_type} metrics are calculated from your JIRA data and cached for fast display. ",
                                            "Configure Field Mappings (Settings → Field Mappings → Fields tab) ",
                                            "and optionally specify DevOps Projects before calculating."
                                            if metric_type == "DORA"
                                            else "to ensure accurate metric calculation.",
                                        ],
                                        className="empty-state-lead mb-4",
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
                        _create_info_card_row(
                            [
                                {
                                    "icon": "calculator",
                                    "icon_color": "primary",
                                    "title": "Calculate Metrics",
                                    "description": "Click 'Update Data' (delta fetch) or 'Force Refresh' (full refresh) in the Settings panel to calculate metrics from your JIRA data.",
                                },
                                {
                                    "icon": "bolt",
                                    "icon_color": "success",
                                    "title": "Fast & Cached",
                                    "description": "Metrics are calculated once and cached. Future page loads are instant.",
                                },
                            ]
                        ),
                        xs=12,
                        lg=10,
                        xl=8,
                        className="mx-auto",
                    ),
                ],
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
                                        className="empty-state-title mb-3",
                                    ),
                                    html.P(
                                        "Load your JIRA project data to start tracking metrics.",
                                        className="empty-state-lead mb-4",
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
                        _create_info_card_row(
                            [
                                {
                                    "icon": "download",
                                    "icon_color": "primary",
                                    "title": "Load JIRA Data",
                                    "description": "Click the Update Data button in the Settings panel to fetch issues from JIRA.",
                                },
                                {
                                    "icon": "cog",
                                    "icon_color": "info",
                                    "title": "Configure JIRA",
                                    "description": "Ensure JIRA connection is configured in Settings → JIRA Configuration tab.",
                                },
                            ]
                        ),
                        xs=12,
                        lg=10,
                        xl=8,
                        className="mx-auto",
                    ),
                ],
            ),
        ],
        className="p-5 empty-state-banner",  # Standard padding + animation class
    )


def create_no_bugs_state() -> html.Div:
    """Create empty state when data is loaded but no bugs are found.

    This is a positive state - data loaded successfully, just no bugs to show.

    Returns:
        html.Div with celebratory empty state UI
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
                                        className="fas fa-check-circle fa-4x text-success mb-4",
                                        style={"opacity": "0.7"},
                                    ),
                                    html.H4(
                                        "No Bugs Found",
                                        className="empty-state-title mb-3",
                                    ),
                                    html.P(
                                        "Great news! No bugs were found in the current dataset.",
                                        className="empty-state-lead mb-2",
                                    ),
                                    html.P(
                                        "This could mean your project has excellent quality, or bug tracking uses different issue types.",
                                        className="empty-state-subtle",
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
                        _create_info_card_row(
                            [
                                {
                                    "icon": "cog",
                                    "icon_color": "info",
                                    "title": "Check Bug Types",
                                    "description": "Verify bug issue types are configured in Settings → Field Mappings → Types tab.",
                                },
                                {
                                    "icon": "filter",
                                    "icon_color": "secondary",
                                    "title": "Check Query Scope",
                                    "description": "Ensure your JQL query includes projects that contain bug issues.",
                                },
                            ]
                        ),
                        xs=12,
                        lg=10,
                        xl=8,
                        className="mx-auto",
                    ),
                ],
            ),
        ],
        className="p-5 empty-state-banner",
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
                # Header with title and badge placeholder
                html.Div(
                    [
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-title",
                        ),
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-badge",
                        ),
                    ],
                    className="d-flex align-items-center justify-content-between w-100",
                ),
            ),
            dbc.CardBody(
                [
                    # H2 metric value placeholder (text-center metric-value mb-2)
                    html.H2(
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-value",
                        ),
                        className="text-center metric-value mb-2",
                    ),
                    # P unit text placeholder (text-muted text-center metric-unit mb-1)
                    html.P(
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-unit",
                        ),
                        className="text-muted text-center metric-unit mb-1",
                    ),
                    # P relationship hint placeholder (optional, small mb-2)
                    html.P(
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-relationship",
                        ),
                        className="text-muted text-center small mb-2 skeleton-text-sm",
                    ),
                    # Div deployment count placeholder (text-center text-muted small mb-2)
                    html.Div(
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-deployments",
                        ),
                        className="text-center text-muted small mb-2 skeleton-text-sm",
                    ),
                    # Forecast section placeholder (mt-2 mb-2 with border-top)
                    html.Div(
                        [
                            # Forecast value line
                            html.Div(
                                html.Div(
                                    className="skeleton-shimmer skeleton-bar-forecast",
                                ),
                                className="text-center mb-1",
                            ),
                            # Trend vs forecast line
                            html.Div(
                                html.Div(
                                    className="skeleton-shimmer skeleton-bar-trend",
                                ),
                                className="text-center small skeleton-text-sm",
                            ),
                        ],
                        className="mt-2 mb-2 skeleton-divider",
                    ),
                    # Div metric-trend-section
                    html.Div(
                        [
                            # HR (my-2)
                            html.Hr(className="my-2"),
                            # Trend label
                            html.Div(
                                html.Small(
                                    html.Div(
                                        className="skeleton-shimmer skeleton-bar-label",
                                    ),
                                    className="text-muted d-block mb-1",
                                ),
                                className="text-center",
                            ),
                            # Sparkline bars placeholder (d-flex align-items-end justify-content-center, height: 40px)
                            html.Div(
                                html.Div(
                                    className="skeleton-shimmer skeleton-bar-sparkline",
                                ),
                                className="d-flex align-items-end justify-content-center skeleton-sparkline",
                            ),
                            # "Show Details" button placeholder (mt-2 p-0)
                            html.Div(
                                html.Div(
                                    className="skeleton-shimmer skeleton-bar-button",
                                ),
                                className="text-center mt-2",
                            ),
                        ],
                        className="metric-trend-section",
                    ),
                    # HR (my-2)
                    html.Hr(className="my-2"),
                    # Bottom info placeholder (text-muted d-block text-center)
                    html.Small(
                        html.Div(
                            className="skeleton-shimmer skeleton-bar-footer",
                        ),
                        className="text-muted d-block text-center skeleton-text-sm",
                    ),
                ],
            ),
            # Card footer (matches real card footer structure)
            dbc.CardFooter(
                html.Div(
                    "\u00a0",  # Non-breaking space to maintain minimal height
                    className="text-center text-muted skeleton-text-xs",
                    style={"opacity": "0"},
                ),
                className="bg-light border-top py-2",  # Same padding and styling as real cards
            ),
        ],
        className="metric-card mb-3 h-100",  # Added h-100 for consistent height
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
