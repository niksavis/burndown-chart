"""
Budget Settings Card - Display Helpers

Private helper functions for the current budget display card.
Used by budget_settings_card.py and callbacks that update card content.

Functions:
- _create_current_budget_card_content(): Card body content (used by callbacks)
- _create_current_budget_card(): Full card with header and footer
"""

from datetime import datetime
from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def _create_current_budget_card_content(
    budget_data: dict[str, Any] | None = None,
    live_metrics: dict[str, Any] | None = None,
    show_placeholder: bool = True,
) -> list:
    """
    Create content for current budget card (without the Card wrapper).

    This is used by callbacks to update the card's children.

    Args:
        budget_data: Current budget settings
        live_metrics: Live metrics from dashboard (optional)
        show_placeholder: Whether to show placeholder when no data exists

    Returns:
        list: Content elements for CardBody
    """
    if not budget_data or show_placeholder:
        # Placeholder state - no budget configured
        return [
            html.H6(
                [
                    html.I(className="fas fa-info-circle text-info me-2"),
                    "Current Budget (Not Configured)",
                ],
                className="mb-3",
            ),
            html.P(
                "No budget configured yet. Configure your budget below "
                "to start tracking costs.",
                className="text-muted small mb-0",
            ),
        ]

    # Active budget state
    currency = budget_data.get("currency_symbol", "€")
    total = budget_data.get("budget_total_eur", 0)
    time_allocated = budget_data.get("time_allocated_weeks", 0)
    team_cost = budget_data.get("team_cost_per_week_eur", 0)
    updated_at = budget_data.get("updated_at", "")
    created_at = budget_data.get("created_at", "")
    week_label = budget_data.get("week_label", "")

    # Format timestamps
    updated_str = "Not set"
    created_str = "Not set"

    if updated_at:
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            updated_str = dt.strftime("%Y-%m-%d")
        except Exception:
            updated_str = updated_at[:10] if len(updated_at) >= 10 else updated_at

    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_str = dt.strftime("%Y-%m-%d")
        except Exception:
            created_str = created_at[:10] if len(created_at) >= 10 else created_at

    content: list[Any] = [
        html.Div(
            [
                html.I(className="fas fa-chart-line text-success me-2"),
                "Current Budget (Active)",
            ],
            className="fw-semibold mb-2",
            style={
                "fontSize": "0.875rem",
                "paddingTop": "0.5rem",
                "paddingLeft": "0.25rem",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Strong(
                            "Total Budget: ",
                            style={"minWidth": "130px", "display": "inline-block"},
                        ),
                        html.Span(
                            f"{currency}{total:,.2f}",
                            className="text-primary fw-bold",
                        ),
                    ],
                    className="mb-2 d-flex align-items-center small",
                ),
                html.Div(
                    [
                        html.Strong(
                            "Time Allocated: ",
                            style={"minWidth": "130px", "display": "inline-block"},
                        ),
                        html.Span(f"{time_allocated} weeks"),
                    ],
                    className="mb-2 d-flex align-items-center small",
                ),
                html.Div(
                    [
                        html.Strong(
                            "Team Cost: ",
                            style={"minWidth": "130px", "display": "inline-block"},
                        ),
                        html.Span(f"{currency}{team_cost:,.2f}/week"),
                    ],
                    className="mb-2 d-flex align-items-center small",
                ),
                html.Div(
                    [
                        html.Strong(
                            "Effective From: ",
                            style={"minWidth": "130px", "display": "inline-block"},
                        ),
                        html.Span(
                            f"{week_label} ({created_str})"
                            if week_label
                            else created_str,
                            className="text-muted",
                        ),
                    ],
                    className="mb-2 d-flex align-items-center small",
                ),
                html.Div(
                    [
                        html.Strong(
                            "Last Modified: ",
                            style={"minWidth": "130px", "display": "inline-block"},
                        ),
                        html.Span(updated_str, className="text-muted"),
                    ],
                    className="mb-0 d-flex align-items-center small",
                ),
            ],
            style={
                "padding": "0.75rem",
                "backgroundColor": "rgba(25, 135, 84, 0.05)",
                "borderRadius": "0.375rem",
            },
        ),
    ]

    # Add live metrics if available
    if live_metrics:
        consumed_pct = live_metrics.get("consumed_pct", 0)
        consumed_eur = live_metrics.get("consumed_eur", 0)
        burn_rate = live_metrics.get("burn_rate", 0)
        runway_weeks = live_metrics.get("runway_weeks", 0)

        content.append(html.Hr(className="my-3"))
        content.append(
            html.H6(
                [
                    html.I(className="fas fa-tachometer-alt text-primary me-2"),
                    "Live Metrics",
                ],
                className="mb-2",
            )
        )
        content.append(
            html.Ul(
                [
                    html.Li(
                        [
                            html.Strong("Consumed: "),
                            html.Span(
                                f"{consumed_pct:.1f}% ({currency}{consumed_eur:,.2f})"
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Strong("Burn Rate: "),
                            html.Span(f"{currency}{burn_rate:,.2f}/week"),
                        ]
                    ),
                    html.Li(
                        [
                            html.Strong("Runway: "),
                            html.Span(
                                f"{runway_weeks:.1f} weeks"
                                if runway_weeks > 0
                                else "N/A"
                            ),
                        ]
                    ),
                ],
                className="small mb-0",
                style={"listStyleType": "disc", "paddingLeft": "1.5rem"},
            )
        )

    return content


def _create_current_budget_card(
    budget_data: dict[str, Any] | None = None,
    live_metrics: dict[str, Any] | None = None,
    show_placeholder: bool = True,
) -> dbc.Card:
    """
    Create always-visible card showing active budget state with live metrics.

    Args:
        budget_data: Current budget settings (time_allocated_weeks, budget_total_eur,
                     team_cost_per_week_eur, currency_symbol, updated_at)
        live_metrics: Live metrics from dashboard (consumed_pct, consumed_eur,
                      burn_rate, runway_weeks) - Optional
        show_placeholder: Whether to show placeholder when no data exists

    Returns:
        dbc.Card: Always-visible current budget card with metrics

    Example budget_data:
        {
            "time_allocated_weeks": 12,
            "budget_total_eur": 50000,
            "team_cost_per_week_eur": 4000,
            "currency_symbol": "€",
            "updated_at": "2026-01-05T10:00:00Z",
            "week_label": "2026-W01"
        }
    """
    content = _create_current_budget_card_content(
        budget_data, live_metrics, show_placeholder
    )

    # Determine card styling based on content
    if not budget_data or show_placeholder:
        card_color = "light"
    else:
        card_color = "success-subtle"

    return dbc.Card(
        [
            dbc.CardBody(
                content,
                id="budget-current-card-body",
                style={
                    "padding": "0.75rem 1rem",
                    "minHeight": "200px",
                    "maxHeight": "200px",
                    "overflowY": "auto",
                },
            ),
            dbc.CardFooter(
                dbc.Button(
                    [
                        html.I(className="fas fa-trash me-2 d-none d-sm-inline"),
                        html.I(className="fas fa-trash d-inline d-sm-none"),
                        html.Span("Delete Budget", className="d-none d-sm-inline"),
                    ],
                    id="budget-delete-complete-button",
                    color="danger",
                    outline=True,
                    size="sm",
                    className="w-100",
                ),
                className="bg-light border-top py-2",
                style={"padding": "0.5rem"},
            ),
        ],
        id="budget-current-card",
        className=f"mb-2 border-{card_color.split('-')[0]} shadow-sm h-100",
        style={"backgroundColor": f"var(--bs-{card_color})"},
    )
