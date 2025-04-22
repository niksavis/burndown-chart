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

# Application imports - Layout components
from ui.layout import serve_layout, create_app_layout

# Application imports - Tab components
from ui.tabs import create_tabs, create_tab_content

# Application imports - UI components
from ui.components import (
    create_info_tooltip,
    create_pert_info_table,
    create_trend_indicator,
    create_export_buttons,
    create_validation_message,
    create_compact_trend_indicator,
)

# Application imports - Card components
from ui.cards import (
    create_forecast_graph_card,
    create_forecast_info_card,
    create_pert_analysis_card,
    create_input_parameters_card,
    create_statistics_data_card,
    create_project_status_card,
    create_project_summary_card,
)

#######################################################################
# PUBLIC API
#######################################################################
__all__ = [
    # Components
    "create_info_tooltip",
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
]
