"""
Status Configuration Form Component

Provides UI for configuring JIRA status lists with subset validation.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_status_config_form(
    completion_statuses=None,
    active_statuses=None,
    flow_start_statuses=None,
    wip_statuses=None,
    available_statuses=None,
):
    """
    Create status list configuration form.

    Args:
        completion_statuses: List of completion status names
        active_statuses: List of active status names
        flow_start_statuses: List of flow start status names
        wip_statuses: List of WIP status names
        available_statuses: List of available status dictionaries from JIRA

    Returns:
        Dash component with status configuration UI
    """
    completion_statuses = completion_statuses or []
    active_statuses = active_statuses or []
    flow_start_statuses = flow_start_statuses or []
    wip_statuses = wip_statuses or []
    available_statuses = available_statuses or []

    # Create options for dropdowns, grouped by category - include current values even if metadata not fetched
    status_options = [
        {
            "label": f"{s.get('name', '')} ({s.get('category_name', 'Unknown')})",
            "value": s.get("name", ""),
        }
        for s in available_statuses
    ]

    # Add current values to options if not already present (ensures they display)
    existing_statuses = {s.get("name", "") for s in available_statuses}
    for status in (
        completion_statuses + active_statuses + flow_start_statuses + wip_statuses
    ):
        if status and status not in existing_statuses:
            status_options.append({"label": status, "value": status})

    return html.Div(
        [
            # Completion Statuses
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Completion ✓ (Required)", className="fw-bold mb-2"
                            ),
                            dcc.Dropdown(
                                id="completion-statuses-dropdown",
                                options=status_options,  # type: ignore  # Dash accepts list[dict]
                                value=completion_statuses,
                                multi=True,
                                placeholder="Select completion statuses...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Issues with these statuses are counted as completed",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Active Statuses
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Active", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="active-statuses-dropdown",
                                options=status_options,  # type: ignore  # Dash accepts list[dict]
                                value=active_statuses,
                                multi=True,
                                placeholder="Select active statuses...",
                                className="mb-2",
                            ),
                            html.Small(
                                "⚠️ Should be subset of WIP statuses",
                                className="text-warning d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Flow Start Statuses
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Flow Start", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="flow-start-statuses-dropdown",
                                options=status_options,  # type: ignore  # Dash accepts list[dict]
                                value=flow_start_statuses,
                                multi=True,
                                placeholder="Select flow start statuses...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Flow Time measurement starts when issues enter these statuses",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # WIP Statuses
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "WIP (Work In Progress)", className="fw-bold mb-2"
                            ),
                            dcc.Dropdown(
                                id="wip-statuses-dropdown",
                                options=status_options,  # type: ignore  # Dash accepts list[dict]
                                value=wip_statuses,
                                multi=True,
                                placeholder="Select WIP statuses...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Issues with these statuses are counted in Work In Progress",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Validation warnings
            html.Div(id="status-config-validation-warnings", className="mt-3"),
            # Auto-detection info
            html.Div(
                id="status-auto-detection-info",
                className="mt-3 alert alert-info",
                style={"display": "none"},
            ),
        ],
        className="p-3",
    )
