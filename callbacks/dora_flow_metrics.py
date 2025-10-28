"""Callbacks for DORA and Flow metrics dashboard.

Handles user interactions and metric calculations for DORA/Flow dashboards.
Follows layered architecture: callbacks delegate to data layer for all business logic.

NOTE: Phase 3 implementation - Callbacks are stubs that will be fully implemented in Phase 4+
when integrating with actual field mappings and Jira data.
"""

from dash import callback, Output, Input
import dash_bootstrap_components as dbc
from typing import Dict
import logging

logger = logging.getLogger(__name__)


@callback(
    Output("dora-metrics-cards-container", "children"),
    Output("dora-loading-state", "children"),
    Input("dora-refresh-button", "n_clicks"),
    Input("dora-time-period-select", "value"),
    prevent_initial_call=False,
)
def update_dora_metrics(
    n_clicks: int | None,
    time_period: str,
) -> tuple:
    """Update DORA metrics display.

    STUB: Phase 3 - Returns placeholder content.
    Phase 4+ will delegate to data layer for metric calculation.

    Args:
        n_clicks: Number of refresh button clicks
        time_period: Selected time period ('7', '30', '90', or 'custom')

    Returns:
        Tuple of (metrics_cards, loading_state)
    """
    # Phase 3 stub - return placeholder
    from ui.dora_metrics_dashboard import create_dora_loading_cards_grid

    placeholder_alert = dbc.Alert(
        "DORA metrics calculation will be implemented in Phase 4",
        color="info",
        dismissable=True,
    )

    return create_dora_loading_cards_grid(), placeholder_alert


@callback(
    Output("dora-custom-date-range-container", "style"),
    Input("dora-time-period-select", "value"),
)
def toggle_custom_date_range(time_period: str) -> Dict[str, str]:
    """Show/hide custom date range picker based on time period selection.

    Args:
        time_period: Selected time period value

    Returns:
        Style dictionary for custom date range container
    """
    if time_period == "custom":
        return {"display": "block"}
    else:
        return {"display": "none"}
