"""UI Cards Module - Dashboard Component Library

This package provides modular card components for building dashboard layouts.
Each submodule focuses on a specific type of card or responsibility.

ARCHITECTURE:
    - Atomic cards (atomic_cards.py): Reusable building blocks
    - Metric cards (metric_cards.py): Standardized metric displays
    - Analysis cards (analysis_cards.py): PERT and analysis visualizations
    - Forecast cards (forecast_cards.py): PERT forecast displays
    - Input cards (input_cards.py): Data input and configuration forms
    - Data cards (data_cards.py): Data table displays
    - Legacy cards: Deprecated card functions (avoid for new code)

USAGE:
    from ui.cards import create_info_card, create_unified_metric_card

    # Atomic card
    card = create_info_card(
        title="Velocity",
        value=8.5,
        unit="items/week",
        icon="tachometer-alt"
    )

    # Unified metric card
    metric = create_unified_metric_card(
        icon="chart-line",
        value=42,
        unit="points",
        title="Remaining Work"
    )

PUBLIC API:
    Atomic Cards:
        - create_info_card: Generic info display with icon
        - create_dashboard_metrics_card: Dashboard metrics overview

    Metric Cards:
        - create_unified_metric_card: Standardized metric display
        - create_unified_metric_row: Row container for metrics

    Analysis Cards:
        - create_pert_analysis_card: PERT timeline visualization

    Forecast Cards:
        - create_forecast_graph_card: Chart container with tabs
        - create_forecast_info_card: Methodology explanation
        - create_items_forecast_info_card: Items/week forecast
        - create_points_forecast_info_card: Points/week forecast

    Input Cards:
        - create_input_parameters_card: Settings and data input form

    Data Cards:
        - create_statistics_data_card: Weekly data table

    Legacy Cards (DEPRECATED):
        - create_project_status_card: Legacy status summary
        - create_project_summary_card: Legacy dashboard
"""

# Atomic card components (reusable building blocks)
# Analysis cards
from ui.cards.analysis_cards import create_pert_analysis_card
from ui.cards.atomic_cards import (
    create_dashboard_metrics_card,
    create_info_card,
)

# Data table cards
from ui.cards.data_cards import create_statistics_data_card

# Forecast cards
from ui.cards.forecast_cards import (
    create_forecast_graph_card,
    create_forecast_info_card,
    create_items_forecast_info_card,
    create_points_forecast_info_card,
)

# Input/configuration cards
from ui.cards.input_cards import create_input_parameters_card

# Legacy cards (deprecated - avoid for new features)
from ui.cards.legacy_status_cards import create_project_status_card
from ui.cards.legacy_summary_cards import create_project_summary_card

# Metric cards (unified design pattern)
from ui.cards.metric_cards import (
    create_unified_metric_card,
    create_unified_metric_row,
)

__all__ = [
    # Atomic cards
    "create_info_card",
    "create_dashboard_metrics_card",
    # Metric cards
    "create_unified_metric_card",
    "create_unified_metric_row",
    # Analysis cards
    "create_pert_analysis_card",
    # Forecast cards
    "create_forecast_graph_card",
    "create_forecast_info_card",
    "create_items_forecast_info_card",
    "create_points_forecast_info_card",
    # Input cards
    "create_input_parameters_card",
    # Data cards
    "create_statistics_data_card",
    # Legacy cards (deprecated)
    "create_project_status_card",
    "create_project_summary_card",
]
