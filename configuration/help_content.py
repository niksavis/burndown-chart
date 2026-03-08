"""Backward-compatible re-export shim for configuration.help_content.

The implementation has been split into focused modules:
  - help_content_forecast.py       -- forecast + velocity help
  - help_content_metrics.py        -- scope, stats, charts, bugs, dashboard,
                                      params, flow metrics, forecast help content
  - help_content_comprehensive.py  -- DORA, settings, and comprehensive aggregator

Migration status: All external callers have been migrated to import
directly from the canonical modules. This shim is retained for
backward compatibility only.

Note: FORECAST_HELP_DETAILED is defined in two places historically.
The canonical (second) definition from help_content_comprehensive.py
is the one exported here.
"""

from configuration.help_content_comprehensive import (  # noqa: F401
    COMPREHENSIVE_HELP_CONTENT,
    DORA_METRICS_TOOLTIPS,
    FORECAST_HELP_DETAILED,
    SETTINGS_PANEL_TOOLTIPS,
)
from configuration.help_content_forecast import (  # noqa: F401
    SCOPE_HELP_DETAILED,
    VELOCITY_HELP_DETAILED,
)
from configuration.help_content_metrics import (  # noqa: F401
    BUG_ANALYSIS_TOOLTIPS,
    CHART_HELP_DETAILED,
    DASHBOARD_METRICS_TOOLTIPS,
    FLOW_METRICS_TOOLTIPS,
    FORECAST_HELP_CONTENT,
    PARAMETER_INPUTS_TOOLTIPS,
    STATISTICS_HELP_DETAILED,
)

__all__ = [
    "BUG_ANALYSIS_TOOLTIPS",
    "CHART_HELP_DETAILED",
    "COMPREHENSIVE_HELP_CONTENT",
    "DASHBOARD_METRICS_TOOLTIPS",
    "DORA_METRICS_TOOLTIPS",
    "FLOW_METRICS_TOOLTIPS",
    "FORECAST_HELP_CONTENT",
    "FORECAST_HELP_DETAILED",
    "PARAMETER_INPUTS_TOOLTIPS",
    "SCOPE_HELP_DETAILED",
    "SETTINGS_PANEL_TOOLTIPS",
    "STATISTICS_HELP_DETAILED",
    "VELOCITY_HELP_DETAILED",
]
