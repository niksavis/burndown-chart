"""Backward-compatible re-export shim for weekly chart functions.

The implementation has been split into focused modules:
  - weekly_chart_items.py        -- items completion chart
  - weekly_chart_points.py       -- points completion chart
  - weekly_chart_items_forecast.py  -- items 4-week forecast chart
  - weekly_chart_points_forecast.py -- points 4-week forecast chart

Migration status: All external callers have been migrated to import
directly from the canonical modules. This shim is retained for
backward compatibility only.

All callers of ``visualization.weekly_charts`` continue to work unchanged.
"""

from visualization.weekly_chart_items import (  # noqa: F401
    create_weekly_items_chart,
)
from visualization.weekly_chart_items_forecast import (  # noqa: F401
    create_weekly_items_forecast_chart,
)
from visualization.weekly_chart_points import (  # noqa: F401
    create_weekly_points_chart,
)
from visualization.weekly_chart_points_forecast import (  # noqa: F401
    create_weekly_points_forecast_chart,
)

__all__ = [
    "create_weekly_items_chart",
    "create_weekly_points_chart",
    "create_weekly_items_forecast_chart",
    "create_weekly_points_forecast_chart",
]
