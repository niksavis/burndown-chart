"""
Comprehensive Dashboard Package - Modular Analytics Platform

A modular dashboard package providing deep insights into project health,
team performance, and delivery forecasts. Organized into focused section modules.

Public API exports all dashboard section creators and utility functions.
"""

from __future__ import annotations

# Utility functions
from ui.dashboard.utils import (
    safe_divide,
    format_date_relative,
    calculate_project_health_score,
    get_health_status,
    get_brief_health_reason,
    create_metric_card,
    create_mini_sparkline,
    create_progress_ring,
)

# Section creators
from ui.dashboard.executive_summary import (
    create_executive_summary_section,
)
from ui.dashboard.throughput_analytics import (
    create_throughput_analytics_section,
)
from ui.dashboard.forecast_analytics import (
    get_forecast_history,
    create_forecast_analytics_section,
)
from ui.dashboard.activity_quality import (
    create_recent_activity_section,
    create_quality_scope_section,
)
from ui.dashboard.insights_engine import (
    create_insights_section,
)


__all__ = [
    # Utilities
    "safe_divide",
    "format_date_relative",
    "calculate_project_health_score",
    "get_health_status",
    "get_brief_health_reason",
    "create_metric_card",
    "create_mini_sparkline",
    "create_progress_ring",
    # Section creators
    "create_executive_summary_section",
    "create_throughput_analytics_section",
    "get_forecast_history",
    "create_forecast_analytics_section",
    "create_recent_activity_section",
    "create_quality_scope_section",
    "create_insights_section",
]
