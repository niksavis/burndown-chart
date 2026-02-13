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
                    html.I(className="fas fa-info-circle text-info me-2"),
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
            updated_str = dt.strftime("%Y-%m-%d")
        except Exception:
            updated_str = updated_at[:10] if len(updated_at) >= 10 else updated_at

    if created_at:
        try:
            from datetime import datetime

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


def _create_budget_total_display(
    time_allocated: Optional[int] = None,
    team_cost: Optional[float] = None,
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
                className="d-flex align-items-center w-100 text-start p-0 text-decoration-none text-danger mb-2",
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
                                            "Delete all budget revision history and reset baseline.",
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
                    className="p-3 border border-danger rounded mt-2",
                ),
                id="budget-danger-zone-collapse",
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
                                children="Will be captured from Recent Completions (Last 4 Weeks) when you save",
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
                                "Are you sure you want to clear all budget revision history?",
                                className="mb-3",
                            ),
                            # Data Loss Warning
                            dbc.Alert(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-exclamation-triangle me-2"
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
                                    html.I(className="fas fa-info-circle me-2"),
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
                                "Are you sure you want to delete the entire budget configuration?",
                                className="mb-3",
                            ),
                            # Data Loss Warning
                            dbc.Alert(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-exclamation-triangle me-2"
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
                                                "Budget configuration (time allocated, team cost, total)"
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
