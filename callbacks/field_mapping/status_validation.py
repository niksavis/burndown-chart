import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("active-wip-subset-warning", "children"),
    Input("active-statuses-dropdown", "value"),
    Input("wip-statuses-dropdown", "value"),
    State("active-wip-subset-warning", "children"),
    prevent_initial_call=True,
)
def validate_active_wip_subset(active_statuses, wip_statuses, current_warning):

    active_set = set(active_statuses or [])
    wip_set = set(wip_statuses or [])

    not_in_wip = active_set - wip_set

    if not_in_wip:
        status_list = ", ".join(sorted(not_in_wip))
        new_warning = dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Warning: "),
                f"These Active statuses are not in WIP: {status_list}",
            ],
            color="warning",
            className="py-2 px-3 mb-0 small",
        )

        if current_warning and hasattr(current_warning, "children"):
            try:
                current_msg = str(current_warning.children)
                new_msg = str(new_warning.children)
                if current_msg == new_msg:
                    return no_update
            except AttributeError, TypeError:
                pass

        return new_warning

    if current_warning and hasattr(current_warning, "children"):
        return html.Div()

    return no_update


@callback(
    Output("flow-start-wip-subset-warning", "children"),
    Input("flow-start-statuses-dropdown", "value"),
    Input("wip-statuses-dropdown", "value"),
    State("flow-start-wip-subset-warning", "children"),
    prevent_initial_call=True,
)
def validate_flow_start_wip_subset(flow_start_statuses, wip_statuses, current_warning):

    flow_start_set = set(flow_start_statuses or [])
    wip_set = set(wip_statuses or [])

    not_in_wip = flow_start_set - wip_set

    if not_in_wip:
        status_list = ", ".join(sorted(not_in_wip))
        new_warning = dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Warning: "),
                f"These Flow Start statuses are not in WIP: {status_list}",
            ],
            color="warning",
            className="py-2 px-3 mb-0 small",
        )

        if current_warning and hasattr(current_warning, "children"):
            try:
                current_msg = str(current_warning.children)
                new_msg = str(new_warning.children)
                if current_msg == new_msg:
                    return no_update
            except AttributeError, TypeError:
                pass

        return new_warning

    if current_warning and hasattr(current_warning, "children"):
        return html.Div()

    return no_update
