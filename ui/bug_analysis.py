"""Bug analysis UI components.

Provides UI components for bug metrics display, charts, and analysis tab layout.
"""

from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, List
from data.bug_insights import InsightSeverity


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


def create_quality_insights_panel(insights: List[Dict]) -> dbc.Card:
    """Create quality insights panel with severity icons and expandable details.

    Args:
        insights: List of insight dictionaries with:
            - type: InsightType enum
            - severity: InsightSeverity enum
            - message: Short insight message
            - actionable_recommendation: Detailed recommendation

    Returns:
        Dash Bootstrap Components Card with quality insights
    """
    if not insights:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Quality Insights", className="card-title"),
                    html.Div(
                        [
                            html.I(className="fas fa-lightbulb me-2"),
                            html.Span(
                                "No insights available - continue monitoring bug trends."
                            ),
                        ],
                        className="alert alert-info",
                    ),
                ]
            ),
            className="mb-3",
        )

    def get_severity_config(severity: InsightSeverity) -> Dict:
        """Get icon and color configuration for severity level."""
        severity_configs = {
            InsightSeverity.CRITICAL: {
                "icon": "fa-exclamation-triangle",
                "color": "danger",
                "badge_text": "Critical",
            },
            InsightSeverity.WARNING: {
                "icon": "fa-exclamation-circle",
                "color": "warning",
                "badge_text": "Warning",
            },
            InsightSeverity.INFO: {
                "icon": "fa-info-circle",
                "color": "success",
                "badge_text": "Info",
            },
        }
        return severity_configs.get(severity, severity_configs[InsightSeverity.INFO])

    # Create insight items with expandable details
    insight_items = []
    for idx, insight in enumerate(insights):
        severity_config = get_severity_config(insight["severity"])

        # Create collapse ID for this insight
        collapse_id = f"insight-collapse-{idx}"

        insight_item = dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.I(
                                        className=f"fas {severity_config['icon']} me-2"
                                    ),
                                    html.Span(insight["message"]),
                                ],
                                width=10,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        severity_config["badge_text"],
                                        color=severity_config["color"],
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"insight-toggle-{idx}",
                                        color="link",
                                        size="sm",
                                        className="p-0",
                                    ),
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ],
                        align="center",
                    ),
                    className=f"bg-{severity_config['color']} bg-opacity-10 border-{severity_config['color']}",
                    style={"cursor": "pointer"},
                    id=f"insight-header-{idx}",
                ),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.H6("Recommendation:", className="fw-bold mb-2"),
                            html.P(
                                insight["actionable_recommendation"],
                                className="mb-0",
                            ),
                        ]
                    ),
                    id=collapse_id,
                    is_open=False,
                ),
            ],
            className="mb-2",
        )
        insight_items.append(insight_item)

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(
                    [
                        html.I(className="fas fa-lightbulb me-2"),
                        "Quality Insights",
                    ],
                    className="card-title mb-3",
                ),
                html.Div(insight_items),
            ]
        ),
        className="mb-3",
    )


def create_bug_analysis_tab() -> html.Div:
    """Create bug analysis tab layout placeholder.

    Returns a simple placeholder div that will be populated by the callback.
    This matches the pattern used by other tabs (Items per Week, etc.) where
    the entire tab content is returned by a callback instead of using nested
    placeholder divs.

    Returns:
        Dash HTML Div placeholder for bug analysis tab content
    """
    return html.Div(
        id="bug-analysis-tab-content",
        children=html.Div("Loading bug analysis...", className="text-center p-5"),
    )
