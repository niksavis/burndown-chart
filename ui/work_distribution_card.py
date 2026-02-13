"""Work Distribution metric card component.

Displays work distribution breakdown across 4 Flow item types (Feature, Defect, Tech Debt, Risk)
with stacked bar chart showing historical trends. Matches the style of other DORA/Flow metric cards.

This card is 2x wider than regular metric cards (width=12 instead of 6).
"""

from typing import Any, Dict, List, Optional, cast
import dash_bootstrap_components as dbc
from dash import html, dcc
from ui.styles import create_metric_card_header
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
    elif warning_count > 0:
        badge_text = "Needs Attention"
        badge_color = "warning"
    else:
        badge_text = "Healthy"
        badge_color = "success"

    # For range indicators (show green check if healthy, warning otherwise)
    feature_in_range = feature_status == "healthy"
    defect_in_range = defect_status == "healthy"
    tech_debt_in_range = tech_debt_status == "healthy"
    risk_in_range = risk_status in ["healthy", "warning"]  # 0-10% is acceptable

    # Build card header with title and badge with tooltip
    badge_id = f"{card_id}-badge" if card_id else "work-distribution-badge"

    card_header = create_metric_card_header(
        title="Work Distribution",
        tooltip_text="Distribution of completed work across Flow item types. Healthy balance: Feature >60% (higher is better), Defect <20% (lower is better), Tech Debt <10% (lower is better), Risk 0-10% (acceptable).",
        tooltip_id="work-distribution",
        badge=dbc.Badge(
            badge_text,
            color=badge_color,
            className="ms-auto metric-badge",
            id=badge_id,
        ),
    )

    # Build metric row (4 columns) with week label - mobile-first responsive design
    metric_row = dbc.Row(
        [
            # Week label (above metrics) - full width on all screens
            dbc.Col(
                html.Small(
                    week_label,
                    className="text-muted text-center d-block mb-2 metric-week-label",
                ),
                width=12,
            ),
            # Feature - responsive: 6 cols mobile, 6 tablet, 3 desktop
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Feature", className="small text-muted d-block mb-1"
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"{feature_count}",
                                            className="h3 mb-0 me-2 text-success",
                                        ),
                                        html.Span(
                                            f"{feature_pct:.0f}%",
                                            className="h5 mb-0 text-success",
                                        ),
                                    ],
                                    className="d-flex align-items-baseline justify-content-center",
                                ),
                            ],
                            className="text-center",
                        ),
                        dbc.Badge(
                            "Healthy" if feature_in_range else "Low",
                            color="success" if feature_in_range else "warning",
                            className="mt-1 metric-badge-sm",
                            id=f"{card_id}-feature-badge"
                            if card_id
                            else "work-dist-feature-badge",
                        ),
                        dbc.Tooltip(
                            "Target: 40-60% of work should be features",
                            target=f"{card_id}-feature-badge"
                            if card_id
                            else "work-dist-feature-badge",
                            placement="top",
                            trigger="click",
                            autohide=True,
                        ),
                    ],
                    className="text-center",
                ),
                xs=6,
                sm=6,
                md=3,
                className="mb-3",
            ),
            # Defect - responsive layout
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Defect", className="small text-muted d-block mb-1"
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"{defect_count}",
                                            className="h3 mb-0 me-2 text-danger",
                                        ),
                                        html.Span(
                                            f"{defect_pct:.0f}%",
                                            className="h5 mb-0 text-danger",
                                        ),
                                    ],
                                    className="d-flex align-items-baseline justify-content-center",
                                ),
                            ],
                            className="text-center",
                        ),
                        dbc.Badge(
                            "Healthy" if defect_in_range else "High",
                            color="success" if defect_in_range else "warning",
                            className="mt-1 metric-badge-sm",
                            id=f"{card_id}-defect-badge"
                            if card_id
                            else "work-dist-defect-badge",
                        ),
                        dbc.Tooltip(
                            "Target: <20% of work should be defects",
                            target=f"{card_id}-defect-badge"
                            if card_id
                            else "work-dist-defect-badge",
                            placement="top",
                            trigger="click",
                            autohide=True,
                        ),
                    ],
                    className="text-center",
                ),
                xs=6,
                sm=6,
                md=3,
                className="mb-3",
            ),
            # Tech Debt - responsive layout
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Tech Debt",
                                    className="small text-muted d-block mb-1",
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"{tech_debt_count}",
                                            className="h3 mb-0 me-2 text-points",
                                        ),
                                        html.Span(
                                            f"{tech_debt_pct:.0f}%",
                                            className="h5 mb-0 text-points",
                                        ),
                                    ],
                                    className="d-flex align-items-baseline justify-content-center",
                                ),
                            ],
                            className="text-center",
                        ),
                        dbc.Badge(
                            "Healthy" if tech_debt_in_range else "High",
                            color="success" if tech_debt_in_range else "warning",
                            className="mt-1 metric-badge-sm",
                            id=f"{card_id}-techdebt-badge"
                            if card_id
                            else "work-dist-techdebt-badge",
                        ),
                        dbc.Tooltip(
                            "Target: 10-20% of work for tech debt",
                            target=f"{card_id}-techdebt-badge"
                            if card_id
                            else "work-dist-techdebt-badge",
                            placement="top",
                            trigger="click",
                            autohide=True,
                        ),
                    ],
                    className="text-center",
                ),
                xs=6,
                sm=6,
                md=3,
                className="mb-3",
            ),
            # Risk - responsive layout
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Risk", className="small text-muted d-block mb-1"
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"{risk_count}",
                                            className="h3 mb-0 me-2 text-warning",
                                        ),
                                        html.Span(
                                            f"{risk_pct:.0f}%",
                                            className="h5 mb-0 text-warning",
                                        ),
                                    ],
                                    className="d-flex align-items-baseline justify-content-center",
                                ),
                            ],
                            className="text-center",
                        ),
                        dbc.Badge(
                            "Healthy" if risk_in_range else "High",
                            color="success" if risk_in_range else "warning",
                            className="mt-1 metric-badge-sm",
                            id=f"{card_id}-risk-badge"
                            if card_id
                            else "work-dist-risk-badge",
                        ),
                        dbc.Tooltip(
                            "Target: 0-10% of work for risk reduction",
                            target=f"{card_id}-risk-badge"
                            if card_id
                            else "work-dist-risk-badge",
                            placement="top",
                            trigger="click",
                            autohide=True,
                        ),
                    ],
                    className="text-center",
                ),
                xs=6,
                sm=6,
                md=3,
                className="mb-3",
            ),
        ],
        className="mb-2",
    )

    # Create stacked bar chart using visualization module (same pattern as other charts)
    fig = create_work_distribution_chart(distribution_history)

    # Add relationship hint for work distribution patterns (before chart, matching metric_cards.py)
    relationship_hint = None
    if defect_pct > 30 or tech_debt_pct > 15:
        relationship_hint = html.P(
            [
                html.I(className="fas fa-lightbulb me-1"),
                "High defect/debt work reduces capacity for features and may signal quality issues",
            ],
            className="text-muted text-center small mb-2 metric-hint",
        )

    chart_height = cast(int, getattr(fig.layout, "height", None) or 400)

    # Chart component with optimized height for readability
    chart = html.Div(
        [
            html.Hr(className="my-1"),  # Minimal separator margin
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False, "responsive": True},
                style={"height": f"{chart_height}px"},
            ),
        ],
    )

    # Card body with metrics, hint (if present), and chart
    card_body = dbc.CardBody(
        [
            metric_row,
            relationship_hint if relationship_hint else html.Div(),
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
                className="mb-0 py-2 px-3 metric-alert-text",
            ),
            className="bg-light border-top",
        )
    else:
        # Empty footer (same gray background for visual symmetry)
        card_footer = dbc.CardFooter(
            html.Div(
                "\u00a0",  # Non-breaking space to maintain minimal height
                className="text-center text-muted metric-footer-placeholder",
            ),
            className="bg-light border-top py-2",  # Same padding and styling
        )

    # Build complete card
    card_props = {
        "className": "metric-card metric-card-large metric-card-chart mb-3 h-100"
    }
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
    card_props = {"className": "metric-card metric-card-large mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Card header
    card_header = create_metric_card_header(
        title="Work Distribution",
        badge=dbc.Badge("No Data", color="secondary", className="ms-2"),
    )

    # Card body - empty state message
    card_body = dbc.CardBody(
        html.Div(
            [
                html.I(
                    className="fas fa-database fa-3x text-muted mb-3 opacity-30",
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
            className="text-center text-muted metric-footer-placeholder",
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
                    className="fas fa-chart-line fa-3x text-muted mb-3 opacity-30",
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
                        html.Strong("Update Data / Force Refresh"),
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
            className="text-center text-muted metric-footer-placeholder",
        ),
        className="bg-light border-top py-2",
    )

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]
