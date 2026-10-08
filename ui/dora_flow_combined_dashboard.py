import dash_bootstrap_components as dbc
from dash import html


def create_dora_flow_combined_dashboard() -> dbc.Container:

    return dbc.Container(
        [
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="DORA Metrics",
                        tab_id="subtab-dora",
                        labelClassName="fw-medium",
                        activeLabelClassName="text-primary fw-bold",
                    ),
                    dbc.Tab(
                        label="Flow Metrics",
                        tab_id="subtab-flow",
                        labelClassName="fw-medium",
                        activeLabelClassName="text-primary fw-bold",
                    ),
                ],
                id="dora-flow-subtabs",
                active_tab="subtab-dora",
                className="mb-4 nav-tabs-modern",
            ),
            html.Div(id="dora-flow-subtab-content"),
        ],
        fluid=True,
        className="dora-flow-combined-dashboard py-4",
    )
