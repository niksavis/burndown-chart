from typing import Any, cast

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.styles import create_metric_card_header
from visualization.flow_distribution_chart import create_work_distribution_chart


def create_work_distribution_card(
    distribution_data: dict[str, int],
    week_label: str,
    distribution_history: list[dict[str, Any]],
    card_id: str | None = None,
) -> dbc.Card:

    feature_count = distribution_data.get("feature", 0)
    defect_count = distribution_data.get("defect", 0)
    tech_debt_count = distribution_data.get("tech_debt", 0)
    risk_count = distribution_data.get("risk", 0)
    total = distribution_data.get("total", 0)

    feature_pct = (feature_count / total * 100) if total > 0 else 0
    defect_pct = (defect_count / total * 100) if total > 0 else 0
    tech_debt_pct = (tech_debt_count / total * 100) if total > 0 else 0
    risk_pct = (risk_count / total * 100) if total > 0 else 0

    if feature_pct < 40:
        feature_status = "critical"
    elif feature_pct <= 60:
        feature_status = "warning"
    else:
        feature_status = "healthy"

    if defect_pct < 20:
        defect_status = "healthy"
    elif defect_pct <= 40:
        defect_status = "warning"
    else:
        defect_status = "critical"

    if tech_debt_pct < 10:
        tech_debt_status = "healthy"
    elif tech_debt_pct <= 20:
        tech_debt_status = "warning"
    else:
        tech_debt_status = "critical"

    if risk_pct <= 10:
        risk_status = "warning" if risk_pct > 0 else "healthy"
    else:
        risk_status = "critical"

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

    feature_in_range = feature_status == "healthy"
    defect_in_range = defect_status == "healthy"
    tech_debt_in_range = tech_debt_status == "healthy"
    risk_in_range = risk_status in ["healthy", "warning"]

    badge_id = f"{card_id}-badge" if card_id else "work-distribution-badge"
    distribution_tooltip = (
        "Distribution of completed work across Flow item types. "
        "Healthy balance: Feature >60% (higher is better), "
        "Defect <20% (lower is better), Tech Debt <10% "
        "(lower is better), Risk 0-10% (acceptable)."
    )

    card_header = create_metric_card_header(
        title="Work Distribution",
        tooltip_text=distribution_tooltip,
        tooltip_id="work-distribution",
        badge=dbc.Badge(
            badge_text,
            color=badge_color,
            className="ms-auto metric-badge",
            id=badge_id,
        ),
    )

    metric_row = dbc.Row(
        [
            dbc.Col(
                html.Small(
                    week_label,
                    className="text-muted text-center d-block mb-2 metric-week-label",
                ),
                width=12,
            ),
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
                                    className=(
                                        "d-flex align-items-baseline "
                                        "justify-content-center"
                                    ),
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
                                    className=(
                                        "d-flex align-items-baseline "
                                        "justify-content-center"
                                    ),
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
                                    className=(
                                        "d-flex align-items-baseline "
                                        "justify-content-center"
                                    ),
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
                                    className=(
                                        "d-flex align-items-baseline "
                                        "justify-content-center"
                                    ),
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

    fig = create_work_distribution_chart(distribution_history)

    relationship_hint = None
    if defect_pct > 30 or tech_debt_pct > 15:
        relationship_hint = html.P(
            [
                html.I(className="fas fa-lightbulb me-1"),
                (
                    "High defect/debt work reduces capacity for features "
                    "and may signal quality issues"
                ),
            ],
            className="text-muted text-center small mb-2 metric-hint",
        )

    chart_height = cast(int, getattr(fig.layout, "height", None) or 400)

    chart = html.Div(
        [
            html.Hr(className="my-1"),
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False, "responsive": True},
                style={"height": f"{chart_height}px"},
            ),
        ],
    )

    card_body = dbc.CardBody(
        [
            metric_row,
            relationship_hint if relationship_hint else html.Div(),
            chart,
        ]
    )

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
        card_footer = dbc.CardFooter(
            html.Div(
                "\u00a0",
                className="text-center text-muted metric-footer-placeholder",
            ),
            className="bg-light border-top py-2",
        )

    card_props = {
        "className": "metric-card metric-card-large metric-card-chart mb-3 h-100"
    }
    if card_id:
        card_props["id"] = card_id

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]


def create_work_distribution_no_data_card(card_id: str | None = None) -> dbc.Card:

    card_props = {"className": "metric-card metric-card-large mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    card_header = create_metric_card_header(
        title="Work Distribution",
        badge=dbc.Badge("No Data", color="secondary", className="ms-2"),
    )

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
                        html.I(className="fas fa-info-circle me-2 text-info"),
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

    card_footer = dbc.CardFooter(
        html.Div(
            "\u00a0",
            className="text-center text-muted metric-footer-placeholder",
        ),
        className="bg-light border-top py-2",
    )

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]


def create_work_distribution_no_metrics_card(
    card_id: str | None = None,
) -> dbc.Card:

    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

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

    card_body = dbc.CardBody(
        html.Div(
            [
                html.I(
                    className="fas fa-chart-line fa-3x text-muted mb-3 opacity-30",
                ),
                html.H5("Metrics Not Yet Calculated", className="text-dark mb-2"),
                html.P(
                    (
                        "Flow metrics are calculated from your JIRA data "
                        "and cached for fast display."
                    ),
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

    card_footer = dbc.CardFooter(
        html.Div(
            "\u00a0",
            className="text-center text-muted metric-footer-placeholder",
        ),
        className="bg-light border-top py-2",
    )

    card_children = [card_header, card_body, card_footer]

    return dbc.Card(card_children, **card_props)  # type: ignore[call-arg]
