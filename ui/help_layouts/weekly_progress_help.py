"""Weekly progress help layout components."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component


def _create_quick_reference_table() -> dbc.Table:
    rows = [
        ("Week Start (Monday)", "Reference date for the work week"),
        ("Items Done", "Completed items this week"),
        ("Points Done", "Completed effort this week (preferred for forecasting)"),
        ("New Items", "Items added to the backlog this week"),
        ("New Points", "Effort added to the backlog this week"),
    ]

    return dbc.Table(
        [
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Th(label, className="text-nowrap pe-3"),
                            html.Td(description, className="text-muted"),
                        ]
                    )
                    for label, description in rows
                ]
            )
        ],
        bordered=True,
        striped=True,
        size="sm",
        className="mb-0",
    )


def _create_card(
    title: str,
    icon_class: str,
    body: Component,
    class_name: str = "",
) -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader(
                [html.I(className=f"{icon_class} me-2 text-primary"), title],
                className="py-2",
            ),
            dbc.CardBody(body, className="py-2"),
        ],
        className=class_name,
    )


def _create_list(items: list[str]) -> html.Ul:
    return html.Ul(
        [html.Li(item, className="mb-1") for item in items],
        className="mb-0",
    )


def create_weekly_progress_help_layout() -> list[Component]:
    """Create structured layout for weekly progress help content."""
    summary = html.P(
        "Weekly Progress Data tracks delivery and scope changes week by week.",
        className="text-muted",
    )

    quick_reference_card = _create_card(
        "Quick Reference",
        "fas fa-table",
        _create_quick_reference_table(),
        class_name="h-100",
    )

    patterns_card = _create_card(
        "How to Read Patterns",
        "fas fa-chart-line",
        _create_list(
            [
                "Items/Points Done rising = improving delivery",
                "New Items/Points rising = scope growth",
                "Done consistently > New = backlog shrinking",
            ]
        ),
    )

    quality_card = _create_card(
        "Data Quality",
        "fas fa-check-circle",
        _create_list(
            [
                "Use a consistent done definition",
                "Enter every week (avoid gaps)",
                "Do not enter cumulative totals",
            ]
        ),
    )

    scope_card = _create_card(
        "Scope Signals",
        "fas fa-compass",
        _create_list(
            [
                "New > Done for several weeks = expanding scope",
                "New < Done = backlog shrinking",
                "Volatility suggests planning or estimation drift",
            ]
        ),
    )

    forecast_card = _create_card(
        "Forecast Impact",
        "fas fa-bullseye",
        _create_list(
            [
                "Points Done drives most forecasts",
                "Missing weeks reduce confidence",
                "Large spikes widen forecast ranges",
            ]
        ),
    )

    return [
        summary,
        dbc.Row(
            [
                dbc.Col(quick_reference_card, md=6, className="mb-3"),
                dbc.Col(
                    html.Div(
                        [
                            patterns_card,
                            quality_card,
                            scope_card,
                            forecast_card,
                        ],
                        className="d-grid gap-3 h-100",
                    ),
                    md=6,
                    className="mb-3",
                ),
            ],
            className="g-3 align-items-stretch",
        ),
    ]
