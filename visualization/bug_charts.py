"""
Bug Analysis Chart Module

Re-export shim: preserves the original public API while delegating
implementation to the focused sub-modules:
  - visualization.bug_charts_trend        (mobile helpers + trend chart)
  - visualization.bug_charts_distribution (investment/distribution chart)
  - visualization.bug_charts_forecast     (forecast chart)
"""

#######################################################################
# RE-EXPORTS
#######################################################################
from visualization.bug_charts_distribution import (  # noqa: F401
    create_bug_investment_chart,
)
from visualization.bug_charts_forecast import (  # noqa: F401
    create_bug_forecast_chart,
)
from visualization.bug_charts_trend import (  # noqa: F401
    apply_mobile_chart_optimizations,
    create_bug_trend_chart,
    create_mobile_optimized_chart,
    get_mobile_chart_config,
    get_mobile_chart_layout,
    get_mobile_hover_template,
)
