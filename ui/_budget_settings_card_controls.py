"""
Budget Settings Card - Control Helpers

Private helper functions for budget settings control components.
Used by budget_settings_card.py main builder.

Functions:
- _create_budget_total_display(): Calculated budget total display (Time x Cost)
- _create_revision_history_card(): Revision history card with pagination
- _create_advanced_options_collapse(): Danger zone collapsible section
"""

import dash_bootstrap_components as dbc
from dash import html


def _create_budget_total_display(
    time_allocated: int | None = None,
    team_cost: float | None = None,
    currency_symbol: str = "€",
) -> html.Div:
    """
    Create calculated budget total display (Time × Cost).

    Args:
        time_allocated: Current time allocated in weeks
        team_cost: Current team cost per week
        currency_symbol: Currency symbol for display

    Returns:
        html.Div: Budget total calculation display with reactive update

    Component IDs:
        - budget-total-display-value: Span for calculated total (updated by callback)
    """
    # Calculate total budget
    total_budget = 0
    if time_allocated and team_cost:
        total_budget = time_allocated * team_cost

    return html.Div(
        [
            dbc.Label(
                "Total Budget (Time × Cost)",
                className="mb-1",
                style={"fontSize": "0.875rem", "fontWeight": "600"},
            ),
            html.Div(
                [
                    html.Span(
                        [
                            html.I(
                                className="fas fa-calculator text-primary me-2",
                                style={"fontSize": "0.875rem"},
                            ),
                            html.Span(
                                f"{currency_symbol}{total_budget:,.2f}",
                                id="budget-total-display-value",
                                className="fw-bold",
                                style={"fontSize": "0.875rem"},
                            ),
                        ],
                        style={"fontSize": "0.875rem"},
                    ),
                ],
                className="mb-2",
            ),
        ],
        className="mb-2",
    )


def _create_revision_history_card() -> dbc.Card:
    """
    Create revision history card with pagination (same height as Current Budget card).

    Returns:
        dbc.Card: Revision history card with table and pagination

    Component IDs:
        - budget-revision-history: Content div for revision table
        - budget-revision-history-page: Current page number store
        - budget-revision-history-prev: Previous page button
        - budget-revision-history-next: Next page button
        - budget-revision-history-page-info: Page info text
    """
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    # Title
                    html.Div(
                        [
                            html.I(className="fas fa-history text-primary me-2"),
                            "Revision History",
                        ],
                        className="fw-bold mb-2",
                        style={"fontSize": "0.9rem"},
                    ),
                    # Revision history table container
                    html.Div(
                        id="budget-revision-history",
                        children=[
                            html.P(
                                "No revisions yet. Budget changes will appear here.",
                                className="text-muted small text-center",
                                style={"padding": "1rem 0"},
                            )
                        ],
                        style={
                            "overflowY": "auto",
                            "flex": "1",
                            "marginBottom": "0.5rem",
                        },
                    ),
                    # Pagination controls
                    html.Div(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                html.I(className="fas fa-chevron-left"),
                                                id="budget-revision-history-prev",
                                                size="sm",
                                                color="secondary",
                                                outline=True,
                                                disabled=True,
                                            ),
                                            dbc.Button(
                                                html.I(
                                                    className="fas fa-chevron-right"
                                                ),
                                                id="budget-revision-history-next",
                                                size="sm",
                                                color="secondary",
                                                outline=True,
                                                disabled=True,
                                            ),
                                        ],
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    html.Small(
                                        "Page 1 of 1",
                                        id="budget-revision-history-page-info",
                                        className="text-muted",
                                    ),
                                    className="d-flex align-items-center",
                                ),
                            ],
                            className="g-2 align-items-center",
                        ),
                        className="border-top pt-2",
                        style={"borderColor": "#dee2e6 !important"},
                    ),
                ],
                style={
                    "padding": "0.75rem 1rem",
                    "minHeight": "200px",
                    "maxHeight": "200px",
                    "display": "flex",
                    "flexDirection": "column",
                },
            ),
            dbc.CardFooter(
                dbc.Button(
                    [
                        html.I(className="fas fa-eraser me-2 d-none d-sm-inline"),
                        html.I(className="fas fa-eraser d-inline d-sm-none"),
                        html.Span("Clear History", className="d-none d-sm-inline"),
                    ],
                    id="budget-delete-history-button",
                    color="danger",
                    outline=True,
                    size="sm",
                    className="w-100",
                ),
                className="bg-light border-top py-2",
                style={"padding": "0.5rem"},
            ),
        ],
        id="budget-revision-history-card",
        className="mb-2 border-secondary shadow-sm h-100",
        style={"backgroundColor": "var(--bs-light)"},
    )


def _create_advanced_options_collapse() -> html.Div:
    """
    Create collapsible section for danger zone actions only.

    Returns:
        html.Div: Collapsible danger zone section

    Component IDs:
        - budget-danger-zone-toggle: Toggle button
        - budget-danger-zone-collapse: Collapse container
    """
    return html.Div(
        [
            dbc.Button(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Danger Zone",
                    html.I(
                        className="fas fa-chevron-down ms-auto",
                        id="budget-danger-zone-chevron",
                    ),
                ],
                id="budget-danger-zone-toggle",
                color="link",
                className=(
                    "d-flex align-items-center w-100 text-start p-0 "
                    "text-decoration-none text-danger mb-2"
                ),
                style={"border": "none"},
            ),
            dbc.Collapse(
                html.Div(
                    [
                        # Danger Zone buttons in 2 columns
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.P(
                                            "Delete all budget revision "
                                            "history and reset baseline.",
                                            className="text-muted small mb-2",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(className="fas fa-trash me-2"),
                                                "Reset Baseline...",
                                            ],
                                            id="budget-delete-history-button",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            className="w-100",
                                        ),
                                    ],
                                    xs=12,
                                    md=6,
                                    className="mb-2",
                                ),
                                dbc.Col(
                                    [
                                        html.P(
                                            "Completely remove budget "
                                            "configuration and all data.",
                                            className="text-muted small mb-2",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(
                                                    className="fas fa-times-circle me-2"
                                                ),
                                                "Delete Completely...",
                                            ],
                                            id="budget-delete-complete-button",
                                            color="danger",
                                            size="sm",
                                            className="w-100",
                                        ),
                                    ],
                                    xs=12,
                                    md=6,
                                    className="mb-2",
                                ),
                            ],
                        ),
                    ],
                    className="p-3 border border-danger rounded mt-2",
                ),
                id="budget-danger-zone-collapse",
                is_open=False,
            ),
        ],
        className="mb-3",
    )
