"""
UI Module

This module contains UI components for the Burndown Chart application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# None required

# Third-party library imports
# None required

# Application imports
from ui.cards import (
    create_forecast_graph_card,
    create_forecast_info_card,
    create_input_parameters_card,
    create_pert_analysis_card,
    create_project_status_card,
    create_project_summary_card,
    create_statistics_data_card,
)
from ui.components import (
    create_compact_trend_indicator,
    create_export_buttons,
    create_pert_info_table,
    create_trend_indicator,
    create_validation_message,
)
from ui.layout import create_app_layout, serve_layout
from ui.tabs import create_tab_content, create_tabs

# Import scope metrics components
from ui.scope_metrics import (
    create_scope_creep_indicator,
    create_scope_growth_chart,
    create_enhanced_stability_gauge,
    create_scope_creep_alert,
    create_scope_metrics_dashboard,
)

#######################################################################
# PUBLIC API
#######################################################################
__all__ = [
    # Components
    "create_pert_info_table",
    "create_trend_indicator",
    "create_export_buttons",
    "create_validation_message",
    "create_compact_trend_indicator",
    # Cards
    "create_forecast_graph_card",
    "create_forecast_info_card",
    "create_pert_analysis_card",
    "create_input_parameters_card",
    "create_statistics_data_card",
    "create_project_status_card",
    "create_project_summary_card",
    # Layout
    "serve_layout",
    "create_app_layout",
    # Tabs
    "create_tabs",
    "create_tab_content",
    # Scope Metrics Components
    "create_scope_creep_indicator",
    "create_scope_growth_chart",
    "create_enhanced_stability_gauge",
    "create_scope_creep_alert",
    "create_scope_metrics_dashboard",
]
