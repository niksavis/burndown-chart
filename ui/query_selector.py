"""Query Selector Component for Profile Workspace Switching.

This module provides UI components for selecting and managing queries within profiles.
Integrates with data.query_manager for query operations.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_query_dropdown(
    active_query_id: str = "",
    queries: list[dict[str, Any]] | None = None,
    id_suffix: str = "",
) -> dbc.Col:
    """Create query selection dropdown.

    Args:
        active_query_id: Currently active query ID
        queries: List of query dicts with 'id', 'name', 'is_active' keys
        id_suffix: Optional suffix for component IDs (for multiple instances)

    Returns:
        Bootstrap column containing query dropdown
    """
    if queries is None:
        queries = []

    # Build dropdown options
    options = []
    for query in queries:
        label = query.get("name", "Unnamed Query")
        value = query.get("id", "")

        # Add indicator for active query
        if query.get("is_active", False):
            label += " [Active]"

        options.append({"label": label, "value": value})

    # Determine initial value
    value = (
        active_query_id
        if active_query_id
        else (queries[0].get("id", "") if queries else "")
    )

    return dbc.Col(
        [
            html.Label(
                "Query",
                htmlFor=f"query-selector{id_suffix}",
                className="form-label fw-bold mb-1",
            ),
            dcc.Dropdown(
                id=f"query-selector{id_suffix}",
                options=options,
                value=value,
                placeholder="Select a query...",
                clearable=False,
            ),
        ],
        xs=12,
        lg=6,
        className="mb-3",
    )


def create_query_actions(id_suffix: str = "") -> dbc.Col:
    """Create query action buttons (create, edit, delete).

    Args:
        id_suffix: Optional suffix for component IDs

    Returns:
        Bootstrap column containing action buttons
    """
    return dbc.Col(
        dbc.ButtonGroup(
            [
                dbc.Button(
                    [html.I(className="fas fa-plus me-1"), "New"],
                    id=f"create-query-btn{id_suffix}",
                    color="primary",
                    size="sm",
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="fas fa-edit me-1"), "Edit"],
                    id=f"edit-query-btn{id_suffix}",
                    color="secondary",
                    size="sm",
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="fas fa-trash me-1"), "Delete"],
                    id=f"delete-query-btn{id_suffix}",
                    color="danger",
                    size="sm",
                    outline=True,
                ),
            ],
            className="w-100",
            style={"marginTop": "2rem"},  # Push buttons down to align with dropdown
        ),
        xs=12,
        lg=6,
        className="mb-3",
    )


def create_query_selector_panel(id_suffix: str = "") -> dbc.Card:
    """Create complete query selector panel with dropdown and actions.

    Args:
        id_suffix: Optional suffix for component IDs

    Returns:
        Bootstrap card containing query selector
    """
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        create_query_dropdown(id_suffix=id_suffix),
                        create_query_actions(id_suffix=id_suffix),
                    ],
                    className="g-2",
                ),
                # Empty state message (hidden by default, shown via callback)
                dbc.Alert(
                    [
                        html.I(className="fas fa-search me-2"),
                        "No queries in this profile yet. ",
                        html.A(
                            "Create your first query →",
                            id=f"empty-state-create-link{id_suffix}",
                            className="alert-link",
                            href="#",
                        ),
                    ],
                    id=f"query-empty-state{id_suffix}",
                    color="info",
                    className="mb-0 d-none",
                    dismissable=False,
                ),
            ]
        ),
        className="mb-3",
    )


def create_query_loading_indicator(id_suffix: str = "") -> dbc.Spinner:
    """Create loading spinner for query switching operations.

    Args:
        id_suffix: Optional suffix for component ID

    Returns:
        Bootstrap spinner component
    """
    return dbc.Spinner(
        id=f"query-loading-spinner{id_suffix}",
        color="primary",
        type="border",
        size="sm",
        children=html.Div(id=f"query-loading-output{id_suffix}"),
    )


def create_query_info_tooltip(query: dict[str, Any]) -> str:
    """Generate tooltip text for query with metadata.

    Args:
        query: Query dict with 'name', 'jql', 'created_at' keys

    Returns:
        HTML string for tooltip content
    """
    name = query.get("name", "Unnamed")
    jql = query.get("jql", "")
    created_at = query.get("created_at", "Unknown")

    # Truncate long JQL for tooltip
    jql_display = jql if len(jql) <= 100 else f"{jql[:97]}..."

    return f"""
    <div style='text-align: left;'>
        <strong>{name}</strong><br>
        <small>JQL: {jql_display}</small><br>
        <small>Created: {created_at}</small>
    </div>
    """


def get_query_dropdown_options(queries: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert query list to dropdown options format.

    Args:
        queries: List of query dicts from list_queries_for_profile()

    Returns:
        List of dicts with 'label' and 'value' keys for dropdown
    """
    options = []
    for query in queries:
        label = query.get("name", "Unnamed Query")
        value = query.get("id", "")

        # Add active indicator
        if query.get("is_active", False):
            label += " [Active]"

        options.append({"label": label, "value": value})

    return options
