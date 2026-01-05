"""
Budget Settings Component

Profile-level budget configuration UI with two modes:
1. Update Budget (default) - Preserves revision history
2. Reconfigure Budget (opt-in) - Resets budget baseline

Features:
- Time allocation in weeks (defaults to data_points_count)
- Budget total (optional)
- Currency symbol (freeform text, default "€")
- Team cost rate (weekly/daily/hourly with conversion helpers)
- Effective date picker (allows retroactive budget entry)
- Revision reason (optional, for audit trail)
- Help tooltips for guidance

Created: January 4, 2026
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_budget_settings_card() -> html.Div:
    """
    Create budget settings configuration card.

    Two-mode approach:
    - "Update Budget" mode (default): Preserves revision history
    - "Reconfigure Budget" mode (opt-in): Resets baseline with warning modal

    Returns:
        html.Div: Budget settings configuration content
    """
    return html.Div(
        [
            # Hidden stores for budget state
            dcc.Store(id="budget-settings-store", data={}),
            dcc.Store(id="budget-revision-mode-store", data={"mode": "update"}),
            # Section header
            html.Div(
                [
                    html.I(className="fas fa-coins me-2 text-primary"),
                    html.Span("Budget Configuration", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Current Budget Summary Card
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H6("Current Budget", className="text-muted mb-3"),
                            html.Div(id="budget-current-summary", className="small"),
                        ]
                    )
                ],
                className="mb-3",
                id="budget-summary-card",
                style={
                    "display": "none"
                },  # Hidden by default, shown when budget exists
            ),
            # Status indicator
            html.Div(
                id="budget-config-status-indicator",
                className="mb-3",
                children=[
                    html.I(className="fas fa-info-circle text-info me-2"),
                    html.Span("No budget configured", className="text-muted small"),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            # Mode selector (Update vs Reconfigure)
            html.Div(
                [
                    dbc.RadioItems(
                        id="budget-mode-selector",
                        options=[
                            {
                                "label": "Update Budget (preserves history)",
                                "value": "update",
                            },
                            {
                                "label": "Reconfigure Budget (reset baseline)",
                                "value": "reconfigure",
                            },
                        ],
                        value="update",
                        inline=False,
                        className="mb-3",
                    ),
                    # Warning for reconfigure mode
                    dbc.Alert(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Reconfigure mode will delete all budget revision history. ",
                            html.Strong("This cannot be undone."),
                        ],
                        id="budget-reconfigure-warning",
                        color="warning",
                        is_open=False,
                        className="mb-3",
                    ),
                ]
            ),
            # Effective Date Picker (for retroactive budget entry)
            html.Div(
                [
                    dbc.Label(
                        [
                            "Effective Date (optional) ",
                            html.I(
                                className="fas fa-info-circle text-muted ms-1",
                                id="budget-effective-date-tooltip",
                                style={"cursor": "pointer"},
                            ),
                        ]
                    ),
                    dbc.Tooltip(
                        "Date when this budget change takes effect. Leave empty to use current date. "
                        "Use this to enter budget configurations retroactively (e.g., if you're configuring budget 3 months late).",
                        target="budget-effective-date-tooltip",
                        placement="right",
                    ),
                    dcc.DatePickerSingle(
                        id="budget-effective-date-picker",
                        date=None,
                        display_format="YYYY-MM-DD",
                        first_day_of_week=1,
                        placeholder="Current date (default)",
                        className="w-100",
                        style={"fontSize": "0.875rem"},
                    ),
                    html.Small(
                        "Budget revision will be timestamped with this date's ISO week",
                        className="text-muted d-block mt-1",
                    ),
                ],
                className="mb-3",
            ),
            # Time allocation input
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                [
                                    "Time Allocated (weeks) ",
                                    html.I(
                                        className="fas fa-info-circle text-muted ms-1",
                                        id="time-allocated-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ]
                            ),
                            dbc.Tooltip(
                                "Number of weeks allocated for project completion. Defaults to the forecast time period (Data Points range).",
                                target="time-allocated-tooltip",
                                placement="right",
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("±"),
                                    dbc.Input(
                                        id="budget-time-allocated-input",
                                        type="number",
                                        min=1,
                                        step=1,
                                        placeholder="e.g., 12",
                                        className="text-end",
                                    ),
                                    dbc.InputGroupText("weeks"),
                                ]
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label(
                                [
                                    "Budget Total (optional) ",
                                    html.I(
                                        className="fas fa-info-circle text-muted ms-1",
                                        id="budget-total-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ]
                            ),
                            dbc.Tooltip(
                                "Total budget amount. Optional - can be derived from team cost × time. Supports decimals (e.g., 50000.00).",
                                target="budget-total-tooltip",
                                placement="right",
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
                                            "maxWidth": "60px",
                                            "fontWeight": "bold",
                                        },
                                        className="text-center",
                                    ),
                                    dbc.Input(
                                        id="budget-total-input",
                                        type="number",
                                        min=0,
                                        step=10,
                                        placeholder="e.g., 50000",
                                        className="text-end",
                                    ),
                                ]
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                ],
                className="mb-4",
            ),
            # Team cost rate configuration
            html.Div(
                [
                    dbc.Label(
                        [
                            "Team Cost Rate ",
                            html.I(
                                className="fas fa-info-circle text-muted ms-1",
                                id="team-cost-tooltip",
                                style={"cursor": "pointer"},
                            ),
                        ]
                    ),
                    dbc.Tooltip(
                        "Cost of the team per time period. Single source of truth for budget calculations.",
                        target="team-cost-tooltip",
                        placement="right",
                    ),
                    # Cost rate type selector
                    dbc.RadioItems(
                        id="budget-cost-rate-type",
                        options=[
                            {"label": "Weekly (default)", "value": "weekly"},
                            {"label": "Daily (×5 = weekly)", "value": "daily"},
                            {"label": "Hourly (×40 = weekly)", "value": "hourly"},
                        ],
                        value="weekly",
                        inline=True,
                        className="mb-2",
                    ),
                    # Cost input
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("±"),
                            dbc.Input(
                                id="budget-team-cost-input",
                                type="number",
                                min=0,
                                step=10,
                                placeholder="e.g., 4000",
                                className="text-end",
                            ),
                            dbc.InputGroupText(
                                id="budget-cost-rate-unit", children="€/week"
                            ),
                        ]
                    ),
                    # Conversion helper text
                    html.Small(
                        id="budget-cost-conversion-helper",
                        className="text-muted d-block mt-1",
                        children="Enter weekly team cost",
                    ),
                ],
                className="mb-3",
            ),
            # Revision reason (update mode only)
            html.Div(
                [
                    dbc.Label(
                        [
                            "Revision Reason (optional) ",
                            html.I(
                                className="fas fa-info-circle text-muted ms-1",
                                id="revision-reason-tooltip",
                                style={"cursor": "pointer"},
                            ),
                        ]
                    ),
                    dbc.Tooltip(
                        "Document why the budget changed for audit trail and team transparency.",
                        target="revision-reason-tooltip",
                        placement="right",
                    ),
                    dbc.Textarea(
                        id="budget-revision-reason-input",
                        placeholder="e.g., Additional funding approved for Phase 2",
                        rows=1,
                        maxLength=500,
                        style={"resize": "vertical"},
                    ),
                ],
                id="budget-revision-reason-container",
                className="mb-3",
            ),
            # Action buttons
            html.Div(
                [
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-save me-2"), "Save Budget"],
                                id="save-budget-button",
                                color="primary",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-times me-2"), "Cancel"],
                                id="cancel-budget-button",
                                color="secondary",
                                outline=True,
                            ),
                        ],
                        className="w-100",
                    ),
                    dbc.Tooltip(
                        "Discard changes and restore previous budget configuration",
                        target="cancel-budget-button",
                        placement="top",
                    ),
                ],
                className="mb-3",
            ),
            # Budget Revision History Section (Collapsible)
            html.Div(
                [
                    html.Hr(className="my-4"),
                    dbc.Button(
                        [
                            html.I(className="fas fa-history me-2"),
                            html.Span("Budget Revision History", className="fw-bold"),
                            html.I(
                                className="fas fa-chevron-down ms-auto",
                                id="revision-history-chevron",
                            ),
                        ],
                        id="revision-history-toggle",
                        color="link",
                        className="d-flex align-items-center w-100 text-start p-0 text-decoration-none",
                        style={"border": "none"},
                    ),
                    dbc.Collapse(
                        html.Div(
                            id="budget-revision-history",
                            children=[
                                html.P(
                                    "No budget revisions yet. Changes will appear here after you save budget updates.",
                                    className="text-muted small",
                                )
                            ],
                            className="mt-3",
                        ),
                        id="revision-history-collapse",
                        is_open=False,
                    ),
                ],
                id="budget-revision-history-section",
            ),
            # Reconfigure confirmation modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(
                                    className="fas fa-exclamation-triangle text-warning me-2"
                                ),
                                "Confirm Budget Reconfiguration",
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P(
                                [
                                    html.Strong("Warning: "),
                                    "Reconfiguring budget will permanently delete all revision history. "
                                    "This action cannot be undone.",
                                ]
                            ),
                            html.P(
                                "Budget revisions track changes over time and provide valuable audit trails. "
                                "Only reconfigure if you need to reset the budget baseline completely."
                            ),
                            html.Hr(),
                            dbc.Checklist(
                                id="budget-reconfigure-confirm-checkbox",
                                options=[
                                    {
                                        "label": "I understand this will delete all budget revision history",
                                        "value": "confirmed",
                                    }
                                ],
                                value=[],
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="budget-reconfigure-cancel-button",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-trash me-2"),
                                    "Confirm Reconfigure",
                                ],
                                id="budget-reconfigure-confirm-button",
                                color="danger",
                                disabled=True,
                            ),
                        ]
                    ),
                ],
                id="budget-reconfigure-modal",
                is_open=False,
                backdrop="static",
            ),
        ]
    )
