"""Forecast analytics module for dashboard - re-export shim.

Public API is preserved here; implementations have been split into:
- forecast_analytics_charts.py: chart generation and forecast history
- forecast_analytics_controls.py: status helpers, on-track card, pace element
- forecast_analytics_summary.py: card builders and section assembly
"""

from __future__ import annotations

from ui.dashboard.forecast_analytics_charts import get_forecast_history  # noqa: F401
from ui.dashboard.forecast_analytics_summary import (  # noqa: F401
    create_forecast_analytics_section,
)

__all__ = ["get_forecast_history", "create_forecast_analytics_section"]
