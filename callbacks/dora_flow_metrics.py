"""Callbacks for DORA and Flow metrics dashboard.

Handles user interactions and metric calculations for DORA/Flow dashboards.
Follows layered architecture: callbacks delegate to data layer for all business logic.
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


# ============================================================================
# Flow Metrics Callbacks
# ============================================================================


@callback(
    Output("flow-metrics-cards-container", "children"),
    Output("flow-loading-state", "children"),
    Input("flow-refresh-button", "n_clicks"),
    Input("flow-time-period-select", "value"),
    prevent_initial_call=False,
)
def update_flow_metrics(
    n_clicks: int | None,
    time_period: str,
) -> tuple:
    """Update Flow metrics display.

    Phase 5 implementation - Delegates to flow_calculator for calculations.

    Args:
        n_clicks: Number of refresh button clicks
        time_period: Selected time period ('7', '30', '90', or 'custom')

    Returns:
        Tuple of (metrics_cards, loading_state)
    """
    # Phase 5 stub - return placeholder
    from ui.flow_metrics_dashboard import create_flow_loading_cards_grid

    placeholder_alert = dbc.Alert(
        "Flow metrics calculation will be implemented after UI integration",
        color="info",
        dismissable=True,
    )

    return create_flow_loading_cards_grid(), placeholder_alert


@callback(
    Output("flow-custom-date-range-container", "style"),
    Input("flow-time-period-select", "value"),
)
def toggle_flow_custom_date_range(time_period: str) -> Dict[str, str]:
    """Show/hide custom date range picker for Flow metrics.

    Args:
        time_period: Selected time period value

    Returns:
        Style dictionary for custom date range container
    """
    if time_period == "custom":
        return {"display": "block"}
    else:
        return {"display": "none"}


@callback(
    Output("flow-distribution-chart-container", "children"),
    Input("flow-time-period-select", "value"),
    prevent_initial_call=False,
)
def update_flow_distribution_chart(time_period: str):
    """Update Flow Distribution chart.

    Args:
        time_period: Selected time period

    Returns:
        Flow distribution chart or placeholder
    """
    # Phase 5 stub - return placeholder
    return dbc.Alert(
        "Distribution chart will be populated with real data after JIRA integration",
        color="info",
    )


@callback(
    Output("dora-flow-subtab-content", "children"),
    Input("dora-flow-subtabs", "active_tab"),
)
def switch_dora_flow_subtab(active_subtab: str):
    """Switch between DORA and Flow metrics dashboards.

    Args:
        active_subtab: Active sub-tab ID ('subtab-dora' or 'subtab-flow')

    Returns:
        Dashboard content for the selected sub-tab
    """
    if active_subtab == "subtab-flow":
        from ui.flow_metrics_dashboard import create_flow_dashboard

        return create_flow_dashboard()
    else:  # Default to DORA
        from ui.dora_metrics_dashboard import create_dora_dashboard

        return create_dora_dashboard()
