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

# Refactored component modules (extracted from components.py)
from ui.form_components import (
    create_input_field,
    create_labeled_input,
    create_validation_message,
)
from ui.jql_components import (
    create_character_count_display,
    create_character_count_state,
    count_jql_characters,
    is_jql_keyword,
    should_show_character_warning,
    JQL_KEYWORDS,
)
from ui.trend_components import (
    create_compact_trend_indicator,
    create_trend_indicator,
    TREND_COLORS,
    TREND_ICONS,
)
from ui.component_utilities import (
    create_export_buttons,
    create_error_alert,
)
from ui.pert_components import (
    create_pert_info_table,
)
from ui.parameter_panel import (
    create_parameter_panel,
    create_parameter_bar_collapsed,
    create_settings_tab_content,
    create_parameter_panel_expanded,
    create_mobile_parameter_fab,
    create_mobile_parameter_bottom_sheet,
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
    # Form Components
    "create_input_field",
    "create_labeled_input",
    "create_validation_message",
    # JQL Components
    "create_character_count_display",
    "create_character_count_state",
    "count_jql_characters",
    "is_jql_keyword",
    "should_show_character_warning",
    "JQL_KEYWORDS",
    # Trend Components
    "create_compact_trend_indicator",
    "create_trend_indicator",
    "TREND_COLORS",
    "TREND_ICONS",
    # Component Utilities
    "create_export_buttons",
    "create_error_alert",
    # PERT Components
    "create_pert_info_table",
    # Parameter Panel Components (User Story 1)
    "create_parameter_panel",
    "create_parameter_bar_collapsed",
    "create_settings_tab_content",
    "create_parameter_panel_expanded",
    "create_mobile_parameter_fab",
    "create_mobile_parameter_bottom_sheet",
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
