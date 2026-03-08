"""
Budget Settings Component - Redesigned

Profile-level budget configuration UI with lean/agile budgeting methodology:
- Always-visible current budget state with live metrics
- Explicit Budget Total calculation modes (auto vs manual)
- Simplified update flow (no reconfigure mode)
- Progressive disclosure for advanced features
- Unified terminology aligned with reports

Created: January 4, 2026
Last Updated: January 5, 2026 - Redesign per budget_analysis_and_proposal.md
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui._budget_settings_card_controls import (  # noqa: F401
    _create_advanced_options_collapse,
    _create_budget_total_display,
    _create_revision_history_card,
)
from ui._budget_settings_card_display import (  # noqa: F401
    _create_current_budget_card,
    _create_current_budget_card_content,
)


def create_budget_settings_card() -> html.Div:
    """
    Create budget settings configuration card with redesigned UX.

    Redesign principles:
    - Always-visible current budget state
    - Explicit Budget Total calculation modes (auto vs manual)
    - Simplified update flow (no separate reconfigure mode)
    - Progressive disclosure for advanced features
    - Unified terminology aligned with reports

    Returns:
        html.Div: Budget settings configuration content
    """
    return html.Div(
        [
            # Hidden stores for budget state
            dcc.Store(id="budget-settings-store", data={}),
            dcc.Store(id="budget-revision-history-page", data=1),  # Pagination state
            # Section header
            html.Div(
                [
                    html.I(className="fas fa-coins me-2 text-primary"),
                    html.Span("Budget Configuration", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            # Current Budget + Revision History Row (side by side)
            dbc.Row(
                [
                    dbc.Col(
                        _create_current_budget_card(
                            budget_data=None, show_placeholder=True
                        ),
                        xs=12,
                        lg=6,
                        className="mb-2",
                    ),
                    dbc.Col(
                        _create_revision_history_card(),
                        xs=12,
                        lg=6,
                        className="mb-2",
                    ),
                ],
                className="mb-2",
            ),
            html.Hr(className="my-3"),
            # Main Budget Configuration Row
            # Time Allocated, Team Cost, Effective Date, Reason
            dbc.Row(
                [
                    # Time Allocated (col 1)
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Time Allocated ",
                                    html.I(
                                        className="fas fa-info-circle text-info ms-1",
                                        id="time-allocated-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                                className="form-label fw-medium",
                                style={"fontSize": "0.875rem"},
                            ),
                            dbc.Tooltip(
                                "Weeks to complete",
                                target="time-allocated-tooltip",
                                placement="top",
                                trigger="click",
                                autohide=True,
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        "±", style={"padding": "0.25rem 0.5rem"}
                                    ),
                                    dbc.Input(
                                        id="budget-time-allocated-input",
                                        type="number",
                                        min=1,
                                        step=1,
                                        placeholder="12",
                                        className="text-end",
                                        size="sm",
                                    ),
                                    dbc.InputGroupText(
                                        "wks", style={"padding": "0.25rem 0.5rem"}
                                    ),
                                ],
                                size="sm",
                            ),
                            html.Small(
                                id="budget-time-current-value",
                                className="text-muted d-block mt-1",
                                children="Current: Not set",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        xs=12,
                        sm=6,
                        md=6,
                        lg=2,
                        className="mb-3",
                    ),
                    # Team Cost (col 2)
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Team Cost ",
                                    html.I(
                                        className="fas fa-info-circle text-info ms-1",
                                        id="team-cost-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                                className="form-label fw-medium",
                                style={"fontSize": "0.875rem"},
                            ),
                            dbc.Tooltip(
                                "Weekly cost",
                                target="team-cost-tooltip",
                                placement="top",
                                trigger="click",
                                autohide=True,
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="budget-currency-symbol-input",
                                        type="text",
                                        maxLength=3,
                                        placeholder="€",
                                        value="€",
                                        style={
                                            "maxWidth": "45px",
                                            "fontWeight": "bold",
                                            "padding": "0.25rem 0.25rem",
                                        },
                                        className="text-center",
                                        size="sm",
                                    ),
                                    dbc.InputGroupText(
                                        "±", style={"padding": "0.25rem 0.5rem"}
                                    ),
                                    dbc.Input(
                                        id="budget-team-cost-input",
                                        type="number",
                                        min=0,
                                        step="any",
                                        placeholder="4000",
                                        className="text-end",
                                        size="sm",
                                    ),
                                    dbc.InputGroupText(
                                        "/wk", style={"padding": "0.25rem 0.5rem"}
                                    ),
                                ],
                                size="sm",
                            ),
                            html.Small(
                                id="budget-cost-current-value",
                                className="text-muted d-block mt-1",
                                children="Current: Not set",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        xs=12,
                        sm=6,
                        md=6,
                        lg=3,
                        className="mb-3",
                    ),
                    # Effective Date (col 3)
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Effective Date ",
                                    html.I(
                                        className="fas fa-info-circle text-info ms-1",
                                        id="budget-effective-date-info-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                                className="form-label fw-medium",
                                style={"fontSize": "0.875rem"},
                            ),
                            dbc.Tooltip(
                                "Budget start date",
                                target="budget-effective-date-info-tooltip",
                                placement="top",
                                trigger="click",
                                autohide=True,
                            ),
                            dcc.DatePickerSingle(
                                id="budget-effective-date-picker",
                                date=None,
                                display_format="YYYY-MM-DD",
                                placeholder="Today",
                                clearable=True,
                                className="w-100",
                                style={"fontSize": "0.875rem"},
                            ),
                            html.Small(
                                "Leave empty for today",
                                className="text-muted d-block mt-1",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        xs=12,
                        sm=6,
                        md=6,
                        lg=2,
                        className="mb-3",
                    ),
                    # Reason (col 4)
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Reason (optional) ",
                                    html.I(
                                        className="fas fa-info-circle text-info ms-1",
                                        id="revision-reason-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                                className="form-label fw-medium",
                                style={"fontSize": "0.875rem"},
                            ),
                            dbc.Tooltip(
                                "Why budget changed",
                                target="revision-reason-tooltip",
                                placement="top",
                                trigger="click",
                                autohide=True,
                            ),
                            dbc.Textarea(
                                id="budget-revision-reason-input",
                                placeholder="e.g., Additional funding for Phase 2",
                                rows=1,
                                maxLength=500,
                                style={"resize": "vertical", "fontSize": "0.875rem"},
                                size="sm",
                            ),
                        ],
                        xs=12,
                        sm=6,
                        md=6,
                        lg=5,
                        className="mb-3",
                    ),
                ],
            ),
            # Combined Budget Summary: Total Budget + Baseline Velocity (compact layout)
            html.Div(
                [
                    # Total Budget
                    html.Div(
                        [
                            html.I(
                                className="fas fa-coins text-success me-2",
                                style={"fontSize": "1rem"},
                            ),
                            html.Span(
                                "Total Budget: ",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                "€0.00",
                                id="budget-total-display-value",
                                className="fw-bold text-success",
                                style={"fontSize": "0.90rem"},
                            ),
                            html.Span(
                                " (Time × Cost)",
                                className="text-muted",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        className="mb-2",
                    ),
                    # Baseline Velocity
                    html.Div(
                        [
                            html.I(
                                className="fas fa-tachometer-alt text-info me-2",
                                style={"fontSize": "1rem"},
                            ),
                            html.Span(
                                "Baseline Velocity: ",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                id="budget-baseline-velocity-display",
                                children=(
                                    "Will be captured from Recent Completions "
                                    "(Last 4 Weeks) when you save"
                                ),
                                className="text-info fw-bold",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                    ),
                ],
                className="mb-3 p-3 bg-light rounded border border-info",
                style={"borderWidth": "1px", "borderStyle": "dashed"},
            ),
            # Action button
            html.Div(
                dbc.Button(
                    [
                        html.I(className="fas fa-save"),
                        html.Span("Update Budget"),
                    ],
                    id="save-budget-button",
                    color="primary",
                    className="action-button",
                ),
                className="mb-3",
            ),
            # Delete History Confirmation Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="fas fa-eraser text-danger me-2"),
                                "Clear Budget History",
                            ]
                        ),
                        close_button=True,
                    ),
                    dbc.ModalBody(
                        [
                            html.P(
                                "Are you sure you want to clear all "
                                "budget revision history?",
                                className="mb-3",
                            ),
                            # Data Loss Warning
                            dbc.Alert(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className=(
                                                    "fas fa-exclamation-triangle me-2"
                                                )
                                            ),
                                            html.Strong(
                                                "This will permanently delete:"
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li("All budget revision history"),
                                            html.Li("Historical change tracking"),
                                            html.Li("Audit trail of budget updates"),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.I(className="fas fa-ban me-2"),
                                            html.Strong(
                                                "This action cannot be undone."
                                            ),
                                        ],
                                        className="text-danger",
                                    ),
                                ],
                                color="danger",
                                className="mb-2",
                            ),
                            # Info about what remains
                            dbc.Alert(
                                [
                                    html.I(
                                        className="fas fa-info-circle me-2 text-info"
                                    ),
                                    "Current budget configuration will remain active.",
                                ],
                                color="info",
                                className="mb-0",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="budget-delete-history-cancel-button",
                                color="secondary",
                                outline=True,
                                className="me-auto",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-eraser me-2"),
                                    "Clear History",
                                ],
                                id="budget-delete-history-confirm-button",
                                color="danger",
                            ),
                        ]
                    ),
                ],
                id="budget-delete-history-modal",
                is_open=False,
                backdrop="static",
                centered=True,
                size="md",
            ),
            # Modal for deleting complete budget
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="fas fa-trash text-danger me-2"),
                                "Delete Budget",
                            ]
                        ),
                        close_button=True,
                    ),
                    dbc.ModalBody(
                        [
                            html.P(
                                "Are you sure you want to delete the entire "
                                "budget configuration?",
                                className="mb-3",
                            ),
                            # Data Loss Warning
                            dbc.Alert(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className=(
                                                    "fas fa-exclamation-triangle me-2"
                                                )
                                            ),
                                            html.Strong(
                                                "This will permanently delete:"
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "Budget configuration "
                                                "(time allocated, team cost, total)"
                                            ),
                                            html.Li("All budget revision history"),
                                            html.Li("Historical change tracking"),
                                            html.Li("All budget-related calculations"),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.I(className="fas fa-ban me-2"),
                                            html.Strong(
                                                "This action cannot be undone."
                                            ),
                                        ],
                                        className="text-danger",
                                    ),
                                ],
                                color="danger",
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                'Type "DELETE" to confirm:',
                                                html_for="budget-delete-confirmation-input",
                                            ),
                                            dbc.Input(
                                                id="budget-delete-confirmation-input",
                                                type="text",
                                                placeholder="Type DELETE here...",
                                                className="mb-3",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="budget-delete-complete-cancel-button",
                                color="secondary",
                                outline=True,
                                className="me-auto",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-trash me-2"),
                                    "Delete Budget",
                                ],
                                id="budget-delete-complete-confirm-button",
                                color="danger",
                                disabled=True,
                            ),
                        ]
                    ),
                ],
                id="budget-delete-complete-modal",
                is_open=False,
                backdrop="static",
                centered=True,
                size="md",
            ),
        ]
    )
