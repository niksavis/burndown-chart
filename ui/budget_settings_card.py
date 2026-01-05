"""
Budget Settings Component - Redesigned

Profile-level budget configuration UI with lean/agile budgeting methodology:
- Always-visible current budget state with live metrics
- Explicit Budget Total calculation modes (auto vs manual)
- Simplified update flow (no reconfigure mode)
- Progressive disclosure for advanced features
- Unified terminology aligned with reports

Features:
- Time allocation in weeks
- Total Budget (auto-calculated or manual override)
- Currency symbol (freeform text, default "€")
- Team cost rate (weekly/daily/hourly with conversion helpers)
- Effective date picker (collapsible, for retroactive budget entry)
- Revision reason (optional, for audit trail)
- Revision history (collapsible)
- Help tooltips for guidance

Created: January 4, 2026
Last Updated: January 5, 2026 - Redesign per budget_analysis_and_proposal.md
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import Optional, Dict, Any


def _create_current_budget_card_content(
    budget_data: Optional[Dict[str, Any]] = None,
    live_metrics: Optional[Dict[str, Any]] = None,
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
                    html.I(className="fas fa-info-circle text-muted me-2"),
                    "Current Budget (Not Configured)",
                ],
                className="mb-3",
            ),
            html.P(
                "No budget configured yet. Configure your budget below to start tracking costs.",
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
            from datetime import datetime

            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            updated_str = dt.strftime("%b %d, %Y")
        except Exception:
            updated_str = updated_at[:10] if len(updated_at) >= 10 else updated_at

    if created_at:
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_str = dt.strftime("%b %d, %Y")
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
    budget_data: Optional[Dict[str, Any]] = None,
    live_metrics: Optional[Dict[str, Any]] = None,
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
    if not budget_data or not show_placeholder:
        card_color = "light"
    else:
        card_color = "success-subtle"

    return dbc.Card(
        dbc.CardBody(
            content,
            style={"padding": "0.75rem 1rem"},
        ),
        id="budget-current-card",
        className=f"mb-2 border-{card_color.split('-')[0]} shadow-sm",
        style={"backgroundColor": f"var(--bs-{card_color})"},
    )


def _create_budget_total_mode_selector(
    current_mode: str = "auto",
    time_allocated: Optional[int] = None,
    team_cost: Optional[float] = None,
    currency_symbol: str = "€",
) -> html.Div:
    """
    Create radio buttons for explicit Budget Total calculation mode.

    Args:
        current_mode: "auto" or "manual" - default calculation mode
        time_allocated: Current time allocated in weeks (for auto-calc preview)
        team_cost: Current team cost per week (for auto-calc preview)
        currency_symbol: Currency symbol for display

    Returns:
        html.Div: Budget total mode selector with preview

    Component IDs:
        - budget-total-mode: RadioItems ("auto" | "manual")
        - budget-total-auto-preview: Preview of calculated value
        - budget-total-manual-input: Input for manual override
        - budget-currency-symbol-input: Currency symbol input
    """
    # Calculate auto value for preview
    auto_value = 0
    if time_allocated and team_cost:
        auto_value = time_allocated * team_cost

    return html.Div(
        [
            dbc.Label(
                [
                    "Total Budget Calculation ",
                    html.I(
                        className="fas fa-info-circle text-muted ms-1",
                        id="budget-total-mode-tooltip",
                        style={"cursor": "pointer"},
                    ),
                ],
                className="mb-1",
                style={"fontSize": "0.875rem", "fontWeight": "600"},
            ),
            dbc.Tooltip(
                "Choose how to calculate Total Budget. Auto mode derives from Time × Team Cost. "
                "Manual mode lets you specify exact amount (e.g., for non-team costs like contractors, licenses).",
                target="budget-total-mode-tooltip",
                placement="right",
            ),
            dbc.RadioItems(
                id="budget-total-mode",
                options=[
                    {
                        "label": "Auto (Time × Cost)",
                        "value": "auto",
                    },
                    {
                        "label": "Manual override",
                        "value": "manual",
                    },
                ],
                value=current_mode,
                inline=True,
                className="mb-2",
                style={"fontSize": "0.875rem"},
            ),
            # Auto-calculate preview (shown when auto mode selected)
            html.Div(
                [
                    html.Span(
                        [
                            html.I(
                                className="fas fa-arrow-right text-primary me-2",
                                style={"fontSize": "0.75rem"},
                            ),
                            "Calculated: ",
                            html.Span(
                                id="budget-total-auto-preview",
                                children=f"{currency_symbol}{auto_value:,.2f}",
                                className="fw-bold",
                            ),
                        ],
                        style={"fontSize": "0.875rem"},
                    ),
                ],
                id="budget-total-auto-container",
                className="ms-3 mb-2",
                style={"display": "block" if current_mode == "auto" else "none"},
            ),
            # Manual input (shown when manual mode selected)
            html.Div(
                [
                    html.Div(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        id="budget-total-manual-currency",
                                        children=currency_symbol,
                                        style={"padding": "0.25rem 0.5rem"},
                                    ),
                                    dbc.Input(
                                        id="budget-total-manual-input",
                                        type="number",
                                        min=0,
                                        step=10,
                                        placeholder="e.g., 60000",
                                        className="text-end",
                                        style={"maxWidth": "150px"},
                                        size="sm",
                                    ),
                                ],
                                size="sm",
                                style={"maxWidth": "220px", "display": "inline-flex"},
                            ),
                            html.Small(
                                [
                                    html.I(
                                        className="fas fa-exclamation-triangle me-1"
                                    ),
                                    "Overrides auto-calculation above",
                                ],
                                className="text-warning ms-1",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        className="d-flex align-items-center",
                    ),
                ],
                id="budget-total-manual-container",
                className="mb-2",
                style={"display": "none" if current_mode == "auto" else "block"},
            ),
        ],
        className="mb-2",
    )


def _create_advanced_options_collapse() -> html.Div:
    """
    Create collapsible section for revision history.

    Returns:
        html.Div: Collapsible revision history section

    Component IDs:
        - budget-revision-history-toggle: Toggle button
        - budget-revision-history-collapse: Collapse container
        - budget-revision-history: Content div for revision list
    """
    return html.Div(
        [
            dbc.Button(
                [
                    html.I(className="fas fa-history me-2"),
                    "Revision History",
                    html.I(
                        className="fas fa-chevron-down ms-auto",
                        id="budget-revision-history-chevron",
                    ),
                ],
                id="budget-revision-history-toggle",
                color="link",
                className="d-flex align-items-center w-100 text-start p-0 text-decoration-none mb-2",
                style={"border": "none"},
            ),
            dbc.Collapse(
                html.Div(
                    [
                        # Revision History Content
                        html.Div(
                            id="budget-revision-history",
                            children=[
                                html.P(
                                    "No budget revisions yet. Changes will appear here after you save budget updates.",
                                    className="text-muted small",
                                )
                            ],
                            className="mb-3",
                        ),
                        html.Hr(className="my-3"),
                        # Danger Zone - Delete All History
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-exclamation-triangle text-danger me-2"
                                        ),
                                        "Danger Zone",
                                    ],
                                    className="text-danger mb-2",
                                ),
                                # Danger Zone buttons in 2 columns
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.P(
                                                    "Delete all budget revision history and reset baseline.",
                                                    className="text-muted small mb-2",
                                                    style={"fontSize": "0.75rem"},
                                                ),
                                                dbc.Button(
                                                    [
                                                        html.I(
                                                            className="fas fa-trash me-2"
                                                        ),
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
                                                    "Completely remove budget configuration and all data.",
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
                            className="p-3 border border-danger rounded",
                        ),
                    ],
                    className="mt-3",
                ),
                id="budget-revision-history-collapse",
                is_open=False,
            ),
        ],
        className="mb-3",
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
            # Section header
            html.Div(
                [
                    html.I(className="fas fa-coins me-2 text-primary"),
                    html.Span("Budget Configuration", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            # Current Budget Card (Always Visible)
            _create_current_budget_card(budget_data=None, show_placeholder=True),
            html.Hr(className="my-3"),
            # Main Budget Configuration Row - Time Allocated, Team Cost, Effective Date, Reason
            dbc.Row(
                [
                    # Time Allocated (col 1)
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Time Allocated ",
                                    html.I(
                                        className="fas fa-info-circle text-muted ms-1",
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
                                        className="fas fa-info-circle text-muted ms-1",
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
                                        step=10,
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
                                        className="fas fa-info-circle text-muted ms-1",
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
                                        className="fas fa-info-circle text-muted ms-1",
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
            # Budget Total Calculation Mode Selector (Row 2)
            _create_budget_total_mode_selector(current_mode="auto"),
            # Action buttons
            html.Div(
                [
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-save me-2"),
                                    "Save Budget Update",
                                ],
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
            html.Hr(className="my-3"),
            # Advanced Options (Collapsible)
            _create_advanced_options_collapse(),
            # Delete History Confirmation Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(
                                    className="fas fa-exclamation-triangle text-danger me-2"
                                ),
                                "Confirm Delete Budget History",
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P(
                                [
                                    html.Strong("Warning: "),
                                    "This will permanently delete all budget revision history and reset the budget baseline. "
                                    "This action cannot be undone.",
                                ],
                                className="text-danger",
                            ),
                            html.P(
                                "Budget revisions track changes over time and provide valuable audit trails. "
                                "Only delete history if you need to completely reset the budget tracking."
                            ),
                            html.Hr(),
                            dbc.Checklist(
                                id="budget-delete-history-confirm-checkbox",
                                options=[
                                    {
                                        "label": "I understand this will permanently delete all budget revision history",
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
                                id="budget-delete-history-cancel-button",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-trash me-2"),
                                    "Confirm Delete History",
                                ],
                                id="budget-delete-history-confirm-button",
                                color="danger",
                                disabled=True,
                            ),
                        ]
                    ),
                ],
                id="budget-delete-history-modal",
                is_open=False,
                backdrop="static",
            ),
            # Modal for deleting complete budget
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(
                                    className="fas fa-times-circle text-danger me-2"
                                ),
                                "Delete Budget Completely",
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P(
                                [
                                    html.Strong("Warning: "),
                                    "This will permanently delete the entire budget configuration including all history and revisions. "
                                    "This action cannot be undone.",
                                ],
                                className="text-danger",
                            ),
                            html.P(
                                "You will need to reconfigure the budget from scratch if you proceed. "
                                "Consider using 'Reset Budget Baseline' instead if you only want to clear the revision history."
                            ),
                            html.Hr(),
                            dbc.Checklist(
                                id="budget-delete-complete-confirm-checkbox",
                                options=[
                                    {
                                        "label": "I understand this will permanently delete the entire budget configuration",
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
                                id="budget-delete-complete-cancel-button",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-times-circle me-2"),
                                    "Confirm Delete Budget",
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
            ),
        ]
    )
