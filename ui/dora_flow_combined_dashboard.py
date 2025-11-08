"""Combined DORA and Flow Metrics Dashboard.

Provides a tabbed interface for viewing both DORA metrics and Flow metrics
in a single dashboard view.
"""

import dash_bootstrap_components as dbc
from dash import html


def create_dora_flow_combined_dashboard() -> dbc.Container:
    """Create the combined DORA and Flow metrics dashboard with sub-tabs.

    Returns:
        dbc.Container with tabbed interface for DORA and Flow metrics
    """
    return dbc.Container(
        [
            # Sub-tabs for DORA vs Flow metrics
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
            # Content div that will be filled based on active sub-tab
            html.Div(id="dora-flow-subtab-content"),
        ],
        fluid=True,
        className="dora-flow-combined-dashboard py-4",
    )
