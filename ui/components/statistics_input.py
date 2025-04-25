"""
Statistics input components for the burndown chart application.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_statistics_input_form():
    """Create form for inputting daily statistics."""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Date", className="form-label"),
                            dcc.DatePickerSingle(
                                id="statistics-date-input",
                                className="form-control",
                                display_format="YYYY-MM-DD",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                ]
            ),
            html.Hr(className="my-2"),
            html.H6("Completed Work", className="mb-2"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Completed Items", className="form-label"),
                            dbc.Input(
                                id="completed-items-input",
                                type="number",
                                min=0,
                                step=1,
                                placeholder="Number of items completed",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Completed Points", className="form-label"),
                            dbc.Input(
                                id="completed-points-input",
                                type="number",
                                min=0,
                                step=1,
                                placeholder="Number of points completed",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                ]
            ),
            html.Hr(className="my-2"),
            html.H6("Created Work (Scope Changes)", className="mb-2"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Created Items", className="form-label"),
                            dbc.Input(
                                id="created-items-input",
                                type="number",
                                min=0,
                                step=1,
                                placeholder="Number of items created",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Created Points", className="form-label"),
                            dbc.Input(
                                id="created-points-input",
                                type="number",
                                min=0,
                                step=1,
                                placeholder="Number of points created",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                ]
            ),
            dbc.Button(
                "Add Entry",
                id="add-statistics-button",
                color="primary",
                className="mt-3",
            ),
        ]
    )
