"""
Baseline configuration component for the burndown chart application.
"""

import datetime
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State


def create_baseline_config_form(baseline_data=None):
    """Create form for configuring the scope baseline."""
    baseline_data = baseline_data or {"items": 0, "points": 0, "date": ""}

    return html.Div(
        [
            html.H5("Baseline Configuration (Initial Scope)", className="mb-3"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Baseline Date", className="form-label"),
                            dcc.DatePickerSingle(
                                id="baseline-date-input",
                                className="form-control",
                                display_format="YYYY-MM-DD",
                                date=baseline_data["date"] or None,
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Initial Items", className="form-label"),
                            dbc.Input(
                                id="baseline-items-input",
                                type="number",
                                min=0,
                                step=1,
                                value=baseline_data["items"],
                                placeholder="Initial number of items",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Initial Points", className="form-label"),
                            dbc.Input(
                                id="baseline-points-input",
                                type="number",
                                min=0,
                                step=1,
                                value=baseline_data["points"],
                                placeholder="Initial number of points",
                            ),
                        ],
                        width=12,
                        md=6,
                    ),
                ]
            ),
            dbc.Button(
                "Save Baseline",
                id="save-baseline-button",
                color="primary",
                className="mt-3",
            ),
            html.Div(id="baseline-save-result", className="mt-2"),
        ]
    )


@callback(
    Output("baseline-save-result", "children"),
    Output("current-statistics", "data", allow_duplicate=True),
    Input("save-baseline-button", "n_clicks"),
    State("baseline-date-input", "date"),
    State("baseline-items-input", "value"),
    State("baseline-points-input", "value"),
    State("current-statistics", "data"),
    prevent_initial_call=True,
)
def save_baseline(n_clicks, date, items, points, current_statistics):
    """Save the baseline configuration."""
    if not n_clicks:
        return "", current_statistics

    if not current_statistics:
        current_statistics = {"data": [], "baseline": {}, "timestamp": ""}

    # Update baseline
    current_statistics["baseline"] = {
        "items": items or 0,
        "points": points or 0,
        "date": date or "",
    }

    # Update timestamp
    current_statistics["timestamp"] = datetime.now().isoformat()

    return dbc.Alert(
        "Baseline saved successfully!", color="success", duration=4000
    ), current_statistics
