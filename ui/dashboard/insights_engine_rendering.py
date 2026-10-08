from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from ui.dashboard.insights_engine_scoring import _build_insights_list


def _get_severity_config(severity: str) -> dict[str, str]:

    severity_configs: dict[str, dict[str, str]] = {
        "danger": {
            "icon": "fa-exclamation-triangle",
            "color": "danger",
            "badge_text": "Critical",
        },
        "warning": {
            "icon": "fa-exclamation-circle",
            "color": "warning",
            "badge_text": "High",
        },
        "info": {
            "icon": "fa-info-circle",
            "color": "info",
            "badge_text": "Medium",
        },
        "success": {
            "icon": "fa-check-circle",
            "color": "success",
            "badge_text": "Low",
        },
    }
    return severity_configs.get(severity, severity_configs["info"])


def create_insights_section(
    statistics_df: pd.DataFrame,
    settings: dict[str, Any],
    budget_data: dict[str, Any] | None,
    pert_data: dict[str, Any] | None,
    deadline: str | None,
    bug_metrics: dict[str, Any] | None = None,
    flow_metrics: dict[str, Any] | None = None,
    dora_metrics: dict[str, Any] | None = None,
) -> html.Div:

    insights = _build_insights_list(
        statistics_df=statistics_df,
        settings=settings,
        budget_data=budget_data,
        pert_data=pert_data,
        deadline=deadline,
        bug_metrics=bug_metrics,
        flow_metrics=flow_metrics,
        dora_metrics=dora_metrics,
    )

    insight_items = []
    for idx, insight in enumerate(insights):
        severity_config = _get_severity_config(insight["severity"])
        collapse_id = f"actionable-insight-collapse-{idx}"

        insight_item = dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {severity_config['icon']} me-2"
                                    ),
                                    html.Span(
                                        insight["message"],
                                        className="insight-header-text",
                                    ),
                                ],
                                className="insight-header-main",
                            ),
                            html.Div(
                                [
                                    dbc.Badge(
                                        severity_config["badge_text"],
                                        color=severity_config["color"],
                                        className="insight-severity-badge",
                                    ),
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"actionable-insight-toggle-{idx}",
                                        color="link",
                                        size="sm",
                                        className="p-0 insight-toggle-btn",
                                    ),
                                ],
                                className="insight-header-actions",
                            ),
                        ],
                        className="insight-header-row",
                    ),
                    className=(
                        f"bg-{severity_config['color']} bg-opacity-10 "
                        f"border-{severity_config['color']}"
                    ),
                    style={"cursor": "pointer"},
                    id=f"actionable-insight-header-{idx}",
                ),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.H6("Recommendation:", className="fw-bold mb-2"),
                            html.P(
                                insight["recommendation"],
                                className="mb-0",
                            ),
                        ],
                        className="insight-body",
                    ),
                    id=collapse_id,
                    is_open=False,
                ),
            ],
            className="mb-2",
        )
        insight_items.append(insight_item)

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-lightbulb me-2", style={"color": "#ffc107"}
                    ),
                    "Actionable Insights",
                ],
                className="mb-3 mt-4",
            ),
            html.Div(insight_items, className="mb-4"),
        ],
    )
