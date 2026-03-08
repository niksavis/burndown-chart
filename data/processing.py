"""Data Processing Module — public aggregation shim.

All implementation has been split into focused sub-modules.
This module re-exports every public symbol for backward compatibility
and serves as the canonical import point for callers that need multiple
symbols from this domain.

Migration policy: Do NOT migrate callers away from this shim.
The breadth of callers and variety of imported symbols make direct
imports from canonical modules impractical. This shim is the correct
aggregation point for the data.processing domain.

Canonical modules (for single-symbol imports within the domain itself):
  data.processing_core            — basic transformations and velocity
  data.processing_rates           — PERT rate calculation
  data.processing_daily_forecast  — daily burndown / burnup forecasting
  data.processing_averages        — weekly averages and medians
  data.processing_weekly_forecast — weekly PERT forecast
  data.processing_statistics      — trend analysis and baseline
  data.processing_dashboard       — Dashboard / PERT-timeline metrics
"""

from data.processing_averages import (  # noqa: F401
    calculate_weekly_averages,
)
from data.processing_core import (  # noqa: F401
    calculate_total_points,
    calculate_velocity_from_dataframe,
    compute_cumulative_values,
    compute_weekly_throughput,
    read_and_clean_data,
)
from data.processing_daily_forecast import (  # noqa: F401
    daily_forecast,
    daily_forecast_burnup,
)
from data.processing_dashboard import (  # noqa: F401
    calculate_dashboard_metrics,
    calculate_pert_timeline,
)
from data.processing_rates import calculate_rates  # noqa: F401
from data.processing_statistics import (  # noqa: F401
    calculate_performance_trend,
    establish_baseline,
    process_statistics_data,
)
from data.processing_weekly_forecast import generate_weekly_forecast  # noqa: F401

__all__ = [
    "calculate_dashboard_metrics",
    "calculate_performance_trend",
    "calculate_pert_timeline",
    "calculate_rates",
    "calculate_total_points",
    "calculate_velocity_from_dataframe",
    "calculate_weekly_averages",
    "compute_cumulative_values",
    "compute_weekly_throughput",
    "daily_forecast",
    "daily_forecast_burnup",
    "establish_baseline",
    "generate_weekly_forecast",
    "process_statistics_data",
    "read_and_clean_data",
]
