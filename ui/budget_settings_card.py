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
    if not budget_data or not show_placeholder:
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
    week_label = budget_data.get("week_label", "")

    # Format updated timestamp
    if updated_at:
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            updated_str = dt.strftime("%Y-%m-%d")
        except Exception:
            updated_str = updated_at[:10]
    else:
        updated_str = "Unknown"

    content = [
        html.H6(
            [
                html.I(className="fas fa-chart-line text-success me-2"),
                "Current Budget (Active)",
            ],
            className="mb-3",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Strong("Total Budget: "),
                        html.Span(f"{currency}{total:,.2f}"),
                    ],
                    className="mb-2",
                ),
                html.Div(
                    [
                        html.Strong("Time Allocated: "),
                        html.Span(f"{time_allocated} weeks"),
                    ],
                    className="mb-2",
                ),
                html.Div(
                    [
                        html.Strong("Team Cost: "),
                        html.Span(f"{currency}{team_cost:,.2f}/week"),
                    ],
                    className="mb-2",
                ),
                html.Div(
                    [
                        html.Strong("Last Updated: "),
                        html.Span(f"{updated_str}"),
                        (
                            html.Span(f" (Week {week_label})", className="text-muted")
                            if week_label
                            else ""
                        ),
                    ],
                    className="mb-0",
                ),
            ],
            className="small",
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
        dbc.CardBody(content),
        id="budget-current-card",
        className=f"mb-3 border-{card_color.split('-')[0]}",
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
                className="fw-bold",
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
                        "label": "Auto-calculate (Time × Team Cost) [recommended]",
                        "value": "auto",
                    },
                    {
                        "label": "Manual override (specify exact amount)",
                        "value": "manual",
                    },
                ],
                value=current_mode,
                className="mb-2",
            ),
            # Auto-calculate preview (shown when auto mode selected)
            html.Div(
                [
                    html.I(className="fas fa-arrow-right text-muted me-2"),
                    html.Span("Calculated: ", className="text-muted small"),
                    html.Span(
                        id="budget-total-auto-preview",
                        children=f"{currency_symbol}{auto_value:,.2f}",
                        className="fw-bold",
                    ),
                ],
                id="budget-total-auto-container",
                className="ms-4 mb-3",
                style={"display": "block" if current_mode == "auto" else "none"},
            ),
            # Manual input (shown when manual mode selected)
            html.Div(
                [
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id="budget-currency-symbol-input",
                                type="text",
                                maxLength=3,
                                placeholder="€",
                                value=currency_symbol,
                                style={"maxWidth": "60px", "fontWeight": "bold"},
                                className="text-center",
                            ),
                            dbc.Input(
                                id="budget-total-manual-input",
                                type="number",
                                min=0,
                                step=10,
                                placeholder="e.g., 60000",
                                className="text-end",
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Alert(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Manual override active. Use this when budget includes non-team costs "
                            "(e.g., external contractors, licenses, infrastructure).",
                        ],
                        color="warning",
                        className="small py-2 mb-0",
                    ),
                ],
                id="budget-total-manual-container",
                className="ms-4 mb-3",
                style={"display": "none" if current_mode == "auto" else "block"},
            ),
        ],
        className="mb-4",
    )


def _create_advanced_options_collapse() -> html.Div:
    """
    Create collapsible section for advanced options (Effective Date, Revision History).

    Returns:
        html.Div: Collapsible advanced options section

    Component IDs:
        - advanced-options-toggle: Button to expand/collapse
        - advanced-options-collapse: Collapse container
        - budget-effective-date-picker: DatePickerSingle for retroactive dates
        - budget-revision-history-toggle: Toggle for revision history
        - budget-revision-history-collapse: Revision history container
        - budget-revision-history: Content div for revision list
    """
    return html.Div(
        [
            dbc.Button(
                [
                    html.I(className="fas fa-cog me-2"),
                    "Advanced Options",
                    html.I(
                        className="fas fa-chevron-down ms-auto",
                        id="advanced-options-chevron",
                    ),
                ],
                id="advanced-options-toggle",
                color="link",
                className="d-flex align-items-center w-100 text-start p-0 text-decoration-none mb-2",
                style={"border": "none"},
            ),
            dbc.Collapse(
                html.Div(
                    [
                        # Effective Date Picker
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
                        html.Hr(className="my-3"),
                        # Revision History Section
                        html.Div(
                            [
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-history me-2"),
                                        html.Span(
                                            "Revision History", className="fw-bold"
                                        ),
                                        html.I(
                                            className="fas fa-chevron-down ms-auto",
                                            id="budget-revision-history-chevron",
                                        ),
                                    ],
                                    id="budget-revision-history-toggle",
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
                                    id="budget-revision-history-collapse",
                                    is_open=False,
                                ),
                            ],
                            className="mb-3",
                        ),
                        html.Hr(className="my-3"),
                        # Danger Zone - Delete All History
                        html.Div(
                            [
                                html.H6(
                                    [
                                        html.I(
                                            className="fas fa-exclamation-triangle text-danger me-2"
                                        ),
                                        "Danger Zone",
                                    ],
                                    className="text-danger mb-2",
                                ),
                                html.P(
                                    "Delete all budget revision history and reset baseline. This action cannot be undone.",
                                    className="text-muted small mb-2",
                                ),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-trash me-2"),
                                        "Reset Budget Baseline...",
                                    ],
                                    id="budget-delete-history-button",
                                    color="danger",
                                    outline=True,
                                    size="sm",
                                ),
                            ],
                            className="p-3 border border-danger rounded",
                        ),
                    ],
                    className="mt-3",
                ),
                id="advanced-options-collapse",
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
                    html.Span("Budget Configuration", className="fw-bold fs-5"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Current Budget Card (Always Visible)
            _create_current_budget_card(budget_data=None, show_placeholder=True),
            html.Hr(className="my-4"),
            # Update Budget Section Header
            html.H6(
                [
                    html.I(className="fas fa-edit me-2 text-primary"),
                    "Update Budget",
                ],
                className="mb-3",
            ),
            # Time Allocated and Team Cost Row
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
                                "Number of weeks allocated for project completion. Use forecast time period or project deadline.",
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
                            html.Small(
                                id="budget-time-current-value",
                                className="text-muted d-block mt-1",
                                children="Current: Not set",
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label(
                                [
                                    "Team Cost ",
                                    html.I(
                                        className="fas fa-info-circle text-muted ms-1",
                                        id="team-cost-tooltip",
                                        style={"cursor": "pointer"},
                                    ),
                                ]
                            ),
                            dbc.Tooltip(
                                "Weekly cost of your team. Use total blended rate for all team members. Single source of truth for cost calculations.",
                                target="team-cost-tooltip",
                                placement="right",
                            ),
                            # Cost rate type selector
                            dbc.RadioItems(
                                id="budget-cost-rate-type",
                                options=[
                                    {"label": "Weekly", "value": "weekly"},
                                    {"label": "Daily (×5)", "value": "daily"},
                                    {"label": "Hourly (×40)", "value": "hourly"},
                                ],
                                value="weekly",
                                inline=True,
                                className="mb-2 small",
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
                            html.Small(
                                id="budget-cost-current-value",
                                className="text-muted d-block mt-1",
                                children="Current: Not set",
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                ],
                className="mb-4",
            ),
            # Budget Total Calculation Mode Selector
            _create_budget_total_mode_selector(current_mode="auto"),
            # Revision Reason
            html.Div(
                [
                    dbc.Label(
                        [
                            "Reason for Change (optional) ",
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
                        rows=2,
                        maxLength=500,
                        style={"resize": "vertical"},
                    ),
                ],
                className="mb-3",
            ),
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
                className="mb-4",
            ),
            html.Hr(className="my-4"),
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
        ]
    )
