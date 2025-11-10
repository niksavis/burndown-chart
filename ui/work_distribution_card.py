"""Work Distribution metric card component.

Displays work distribution breakdown across 4 Flow item types (Feature, Defect, Tech Debt, Risk)
with stacked bar chart showing historical trends. Matches the style of other DORA/Flow metric cards.

This card is 2x wider than regular metric cards (width=12 instead of 6).
"""

from typing import Dict, Any, Optional, List
import dash_bootstrap_components as dbc
from dash import html, dcc
from ui.tooltip_utils import create_info_tooltip
from visualization.flow_distribution_chart import create_work_distribution_chart


def create_work_distribution_card(
    distribution_data: Dict[str, int],
    week_label: str,
    distribution_history: List[Dict[str, Any]],
    card_id: Optional[str] = None,
) -> dbc.Card:
    """Create Work Distribution metric card matching DORA/Flow card style.

    Args:
        distribution_data: Current week distribution counts
            {"feature": 3, "defect": 2, "tech_debt": 11, "risk": 0, "total": 16}
        week_label: Current week label (e.g., "2025-W45")
        distribution_history: List of weekly distribution data
            [{"week": "2025-W34", "feature": 5, "defect": 3, ...}, ...]
        card_id: Optional HTML ID for the card

    Returns:
        dbc.Card component with 2x width (for width=12 column)
    """
    # Extract counts
    feature_count = distribution_data.get("feature", 0)
    defect_count = distribution_data.get("defect", 0)
    tech_debt_count = distribution_data.get("tech_debt", 0)
    risk_count = distribution_data.get("risk", 0)
    total = distribution_data.get("total", 0)

    # Calculate percentages
    feature_pct = (feature_count / total * 100) if total > 0 else 0
    defect_pct = (defect_count / total * 100) if total > 0 else 0
    tech_debt_pct = (tech_debt_count / total * 100) if total > 0 else 0
    risk_pct = (risk_count / total * 100) if total > 0 else 0

    # Determine health status for each type
    # Feature: HIGH is good (opposite of others - we WANT high feature work)
    if feature_pct < 40:
        feature_status = "critical"  # Below 40% is critical - not enough feature work
    elif feature_pct <= 60:
        feature_status = "warning"  # 40-60% needs attention
    else:
        feature_status = "healthy"  # Above 60% is healthy - lots of feature work!

    # Defect: LOW is good, HIGH is warning, CRITICAL is danger
    if defect_pct < 20:
        defect_status = "healthy"  # Below range is GOOD
    elif defect_pct <= 40:
        defect_status = "warning"  # In range 20-40% needs attention
    else:
        defect_status = "critical"  # Above 40% is critical

    # Tech Debt: LOW is good, HIGH is warning, CRITICAL is danger
    if tech_debt_pct < 10:
        tech_debt_status = "healthy"  # Below range is GOOD
    elif tech_debt_pct <= 20:
        tech_debt_status = "warning"  # In range 10-20% needs attention
    else:
        tech_debt_status = "critical"  # Above 20% is critical

    # Risk: LOW is good, HIGH is warning, CRITICAL is danger
    if risk_pct <= 10:
        risk_status = (
            "warning" if risk_pct > 0 else "healthy"
        )  # 0-10% is warning (acceptable), 0 is healthy
    else:
        risk_status = "critical"  # Above 10% is critical

    # Determine overall badge status based on worst status
    statuses = [feature_status, defect_status, tech_debt_status, risk_status]
    critical_count = statuses.count("critical")
    warning_count = statuses.count("warning")

    if critical_count > 0:
        badge_text = "Critical"
        badge_color = "danger"
        badge_tooltip = f"{critical_count} work type(s) at critical levels - immediate action needed"
    elif warning_count > 0:
        badge_text = "Needs Attention"
        badge_color = "warning"
        badge_tooltip = f"{warning_count} work type(s) need attention"
    else:
        badge_text = "Healthy"
        badge_color = "success"
        badge_tooltip = "All work types are at healthy levels"

    # For range indicators (show green check if healthy, warning otherwise)
    feature_in_range = feature_status == "healthy"
    defect_in_range = defect_status == "healthy"
    tech_debt_in_range = tech_debt_status == "healthy"
    risk_in_range = risk_status in ["healthy", "warning"]  # 0-10% is acceptable

    # Build card header with title and badge with tooltip
    badge_id = f"{card_id}-badge" if card_id else "work-distribution-badge"

    card_header = dbc.CardHeader(
        html.Div(
            [
                html.Span(
                    [
                        "Work Distribution",
                        " ",
                        create_info_tooltip(
                            help_text="Distribution of completed work across Flow item types. Healthy balance: Feature >60% (higher is better), Defect <20% (lower is better), Tech Debt <10% (lower is better), Risk 0-10% (acceptable).",
                            id_suffix="work-distribution",
                            placement="top",
                            variant="dark",
                        ),
                    ],
                    className="metric-card-title",
                ),
                html.Div(
                    [
                        dbc.Badge(
                            badge_text,
                            color=badge_color,
                            className="ms-auto",
                            style={"fontSize": "0.75rem", "fontWeight": "600"},
                            id=badge_id,
                        ),
                        dbc.Tooltip(
                            badge_tooltip,
                            target=badge_id,
                            placement="top",
                        ),
                    ],
                    className="d-inline-block",
                ),
            ],
            className="d-flex align-items-center justify-content-between w-100",
        ),
    )

    # Build metric row (4 columns) with week label - reduced spacing
    metric_row = dbc.Row(
        [
            # Week label (above metrics)
            dbc.Col(
                [
                    html.Small(
                        f"Week {week_label}",
                        className="text-muted text-center d-block mb-1",  # Reduced from mb-2
                        style={"fontWeight": "600"},
                    ),
                ],
                width=12,
            ),
            # Feature
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span("Feature", className="small text-muted d-block"),
                            html.Span(
                                f"{feature_count} ",
                                className="h4 mb-0",
                                style={"color": "#198754"},
                            ),
                            html.Span(
                                f"({feature_pct:.0f}%)",
                                className="h6 mb-0",
                                style={"color": "#198754"},
                            ),
                        ]
                    ),
                    html.Small(
                        [
                            html.I(
                                className=f"fas fa-{'check-circle text-success' if feature_in_range else 'exclamation-triangle text-warning'} me-1",
                                id=f"{card_id}-feature-range"
                                if card_id
                                else "work-dist-feature-range",
                            ),
                            "40-60%",
                            dbc.Tooltip(
                                "Target: >60% (higher is better). Warning if 40-60%, Critical if <40%",
                                target=f"{card_id}-feature-range"
                                if card_id
                                else "work-dist-feature-range",
                                placement="top",
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                width=3,
                className="text-center mb-2",  # Reduced from mb-3
            ),
            # Defect
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span("Defect", className="small text-muted d-block"),
                            html.Span(
                                f"{defect_count} ",
                                className="h4 mb-0",
                                style={"color": "#dc3545"},
                            ),
                            html.Span(
                                f"({defect_pct:.0f}%)",
                                className="h6 mb-0",
                                style={"color": "#dc3545"},
                            ),
                        ]
                    ),
                    html.Small(
                        [
                            html.I(
                                className=f"fas fa-{'check-circle text-success' if defect_in_range else 'exclamation-triangle text-warning'} me-1",
                                id=f"{card_id}-defect-range"
                                if card_id
                                else "work-dist-defect-range",
                            ),
                            "20-40%",
                            dbc.Tooltip(
                                "Target: <20% (lower is better). Warning if 20-40%, Critical if >40%",
                                target=f"{card_id}-defect-range"
                                if card_id
                                else "work-dist-defect-range",
                                placement="top",
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                width=3,
                className="text-center mb-2",
            ),
            # Tech Debt
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span(
                                "Tech Debt", className="small text-muted d-block"
                            ),
                            html.Span(
                                f"{tech_debt_count} ",
                                className="h4 mb-0",
                                style={"color": "#fd7e14"},
                            ),
                            html.Span(
                                f"({tech_debt_pct:.0f}%)",
                                className="h6 mb-0",
                                style={"color": "#fd7e14"},
                            ),
                        ]
                    ),
                    html.Small(
                        [
                            html.I(
                                className=f"fas fa-{'check-circle text-success' if tech_debt_in_range else 'exclamation-triangle text-warning'} me-1",
                                id=f"{card_id}-techdebt-range"
                                if card_id
                                else "work-dist-techdebt-range",
                            ),
                            "10-20%",
                            dbc.Tooltip(
                                "Target: <10% (lower is better). Warning if 10-20%, Critical if >20%",
                                target=f"{card_id}-techdebt-range"
                                if card_id
                                else "work-dist-techdebt-range",
                                placement="top",
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                width=3,
                className="text-center mb-2",
            ),
            # Risk
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span("Risk", className="small text-muted d-block"),
                            html.Span(
                                f"{risk_count} ",
                                className="h4 mb-0",
                                style={"color": "#ffc107"},
                            ),
                            html.Span(
                                f"({risk_pct:.0f}%)",
                                className="h6 mb-0",
                                style={"color": "#ffc107"},
                            ),
                        ]
                    ),
                    html.Small(
                        [
                            html.I(
                                className=f"fas fa-{'check-circle text-success' if risk_in_range else 'exclamation-triangle text-warning'} me-1",
                                id=f"{card_id}-risk-range"
                                if card_id
                                else "work-dist-risk-range",
                            ),
                            "0-10%",
                            dbc.Tooltip(
                                "Target: 0-10% acceptable. Warning if >0%, Critical if >10%",
                                target=f"{card_id}-risk-range"
                                if card_id
                                else "work-dist-risk-range",
                                placement="top",
                            ),
                        ],
                        className="text-muted",
                    ),
                ],
                width=3,
                className="text-center mb-2",
            ),
        ],
        className="mb-2",  # Reduced from mb-3
    )

    # Create stacked bar chart using visualization module (same pattern as other charts)
    fig = create_work_distribution_chart(distribution_history)

    # Chart component with optimized height for readability
    chart = html.Div(
        [
            html.Hr(className="my-1"),  # Minimal separator margin
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False, "responsive": True},
                style={"height": "400px"},  # Increased 15% from 350px
            ),
        ],
    )

    # Card body with metrics and chart
    card_body = dbc.CardBody(
        [
            metric_row,
            chart,
        ]
    )

    # Build footer with warnings if any out of range (matching metric_cards.py pattern)
    footer_warnings = []
    if not feature_in_range:
        footer_warnings.append("Feature")
    if not defect_in_range:
        footer_warnings.append("Defect")
    if not tech_debt_in_range:
        footer_warnings.append("Tech Debt")
    if not risk_in_range:
        footer_warnings.append("Risk")

    if footer_warnings:
        warning_text = ", ".join(footer_warnings) + " outside recommended range"
        card_footer = dbc.CardFooter(
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Span(warning_text),
                ],
                color="warning",
                className="mb-0 py-2 px-3",
                style={"fontSize": "0.85rem", "lineHeight": "1.4"},
            ),
            className="bg-light border-top",
        )
    else:
        # Empty footer (same gray background for visual symmetry)
        card_footer = dbc.CardFooter(
            html.Div(
                "\u00a0",  # Non-breaking space to maintain minimal height
                className="text-center text-muted",
                style={"fontSize": "0.75rem", "opacity": "0"},
            ),
            className="bg-light border-top py-2",  # Same padding and styling
        )

    # Build complete card
    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]


def create_work_distribution_no_data_card(card_id: Optional[str] = None) -> dbc.Card:
    """Create Work Distribution card for 'No Data' state (2x width).

    Displayed when JIRA data is not loaded yet.

    Args:
        card_id: Optional HTML ID for the card

    Returns:
        dbc.Card component with 2x width (for width=12 column)
    """
    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Card header
    card_header = dbc.CardHeader(
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.I(className="fas fa-chart-pie me-2"),
                        html.Span("Work Distribution"),
                    ],
                    width="auto",
                ),
                dbc.Col(
                    dbc.Badge(
                        "No Data",
                        color="secondary",
                        className="ms-2",
                    ),
                    width="auto",
                    className="ms-auto",
                ),
            ],
            className="align-items-center",
        ),
        className="bg-white border-bottom",
    )

    # Card body - empty state message
    card_body = dbc.CardBody(
        html.Div(
            [
                html.I(
                    className="fas fa-database fa-3x text-muted mb-3",
                    style={"opacity": "0.3"},
                ),
                html.H5("No JIRA Data Loaded", className="text-dark mb-2"),
                html.P(
                    "Load your JIRA project data to view work distribution metrics.",
                    className="text-muted mb-3",
                ),
                html.P(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "Click ",
                        html.Strong("Update Data"),
                        " in the Settings panel to fetch issues from JIRA.",
                    ],
                    className="text-muted small",
                ),
            ],
            className="text-center py-5",
        ),
    )

    # Card footer - matches regular card footer structure
    card_footer = dbc.CardFooter(
        html.Div(
            "\u00a0",  # Non-breaking space to maintain minimal height
            className="text-center text-muted",
            style={"fontSize": "0.75rem", "opacity": "0"},
        ),
        className="bg-light border-top py-2",
    )

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]


def create_work_distribution_no_metrics_card(
    card_id: Optional[str] = None,
) -> dbc.Card:
    """Create Work Distribution card for 'No Metrics' state (2x width).

    Displayed when JIRA data is loaded but Flow metrics haven't been calculated yet.

    Args:
        card_id: Optional HTML ID for the card

    Returns:
        dbc.Card component with 2x width (for width=12 column)
    """
    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Card header
    card_header = dbc.CardHeader(
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.I(className="fas fa-chart-pie me-2"),
                        html.Span("Work Distribution"),
                    ],
                    width="auto",
                ),
                dbc.Col(
                    dbc.Badge(
                        "Disabled",
                        color="secondary",
                        className="ms-2",
                    ),
                    width="auto",
                    className="ms-auto",
                ),
            ],
            className="align-items-center",
        ),
        className="bg-white border-bottom",
    )

    # Card body - metrics not calculated message
    card_body = dbc.CardBody(
        html.Div(
            [
                html.I(
                    className="fas fa-chart-line fa-3x text-muted mb-3",
                    style={"opacity": "0.3"},
                ),
                html.H5("Metrics Not Yet Calculated", className="text-dark mb-2"),
                html.P(
                    "Flow metrics are calculated from your JIRA data and cached for fast display.",
                    className="text-muted mb-3",
                ),
                html.P(
                    [
                        html.I(className="fas fa-calculator me-2"),
                        "Click ",
                        html.Strong("Calculate Metrics"),
                        " in the Settings panel to process your JIRA data.",
                    ],
                    className="text-muted small",
                ),
            ],
            className="text-center py-5",
        ),
    )

    # Card footer - matches regular card footer structure
    card_footer = dbc.CardFooter(
        html.Div(
            "\u00a0",  # Non-breaking space to maintain minimal height
            className="text-center text-muted",
            style={"fontSize": "0.75rem", "opacity": "0"},
        ),
        className="bg-light border-top py-2",
    )

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]
