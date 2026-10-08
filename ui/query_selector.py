from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_query_dropdown(
    active_query_id: str = "",
    queries: list[dict[str, Any]] | None = None,
    id_suffix: str = "",
) -> dbc.Col:

    if queries is None:
        queries = []

    options = []
    for query in queries:
        label = query.get("name", "Unnamed Query")
        value = query.get("id", "")

        if query.get("is_active", False):
            label += " [Active]"

        options.append({"label": label, "value": value})

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
            style={"marginTop": "2rem"},
        ),
        xs=12,
        lg=6,
        className="mb-3",
    )


def create_query_selector_panel(id_suffix: str = "") -> dbc.Card:

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

    return dbc.Spinner(
        id=f"query-loading-spinner{id_suffix}",
        color="primary",
        type="border",
        size="sm",
        children=html.Div(id=f"query-loading-output{id_suffix}"),
    )


def create_query_info_tooltip(query: dict[str, Any]) -> str:

    name = query.get("name", "Unnamed")
    jql = query.get("jql", "")
    created_at = query.get("created_at", "Unknown")

    jql_display = jql if len(jql) <= 100 else f"{jql[:97]}..."

    return f"""
    <div style='text-align: left;'>
        <strong>{name}</strong><br>
        <small>JQL: {jql_display}</small><br>
        <small>Created: {created_at}</small>
    </div>
    """


def get_query_dropdown_options(queries: list[dict[str, Any]]) -> list[dict[str, str]]:

    options = []
    for query in queries:
        label = query.get("name", "Unnamed Query")
        value = query.get("id", "")

        if query.get("is_active", False):
            label += " [Active]"

        options.append({"label": label, "value": value})

    return options
