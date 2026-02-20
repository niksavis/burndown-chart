"""Status validation callbacks for field mapping.

Validates relationships between status configurations (Active/WIP, Flow Start/WIP).
"""

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
    """Validate that Active statuses are a subset of WIP statuses.

    Shows a warning alert only when Active contains statuses not in WIP.

    Args:
        active_statuses: List of selected active status names
        wip_statuses: List of selected WIP status names
        current_warning: Current warning content (to avoid unnecessary updates)

    Returns:
        Warning alert if validation fails, empty div otherwise, or no_update if unchanged
    """
    active_set = set(active_statuses or [])
    wip_set = set(wip_statuses or [])

    # Find statuses in Active that are not in WIP
    not_in_wip = active_set - wip_set

    if not_in_wip:
        # Show warning with specific statuses
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

        # Only update if warning changed (prevents focus loss on dropdown)
        if current_warning and hasattr(current_warning, "children"):
            # Warning already shown - check if message is the same
            try:
                current_msg = str(current_warning.children)
                new_msg = str(new_warning.children)
                if current_msg == new_msg:
                    return no_update
            except (AttributeError, TypeError):
                pass  # If comparison fails, update anyway

        return new_warning

    # No issues - only clear if there was a warning before
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
    """Validate that Flow Start statuses are a subset of WIP statuses.

    Shows a warning alert only when Flow Start contains statuses not in WIP.

    Args:
        flow_start_statuses: List of selected flow start status names
        wip_statuses: List of selected WIP status names
        current_warning: Current warning content (to avoid unnecessary updates)

    Returns:
        Warning alert if validation fails, empty div otherwise, or no_update if unchanged
    """
    flow_start_set = set(flow_start_statuses or [])
    wip_set = set(wip_statuses or [])

    # Find statuses in Flow Start that are not in WIP
    not_in_wip = flow_start_set - wip_set

    if not_in_wip:
        # Show warning with specific statuses
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

        # Only update if warning changed (prevents focus loss on dropdown)
        if current_warning and hasattr(current_warning, "children"):
            # Warning already shown - check if message is the same
            try:
                current_msg = str(current_warning.children)
                new_msg = str(new_warning.children)
                if current_msg == new_msg:
                    return no_update
            except (AttributeError, TypeError):
                pass  # If comparison fails, update anyway

        return new_warning

    # No issues - only clear if there was a warning before
    if current_warning and hasattr(current_warning, "children"):
        return html.Div()

    return no_update
