"""Sprint charts visualization package.

Provides sprint progress bars, chart builders, and status utilities.
Public API mirrors the former flat module for backwards compatibility.
"""

from ._charts import (
    create_sprint_summary_card,
    create_sprint_timeline_chart,
    create_status_distribution_pie,
)
from ._health import _calculate_issue_health_priority, _sort_issues_by_health_priority
from ._progress_bars import create_sprint_progress_bars
from ._status import STATUS_COLORS

__all__ = [
    # Public API
    "create_sprint_progress_bars",
    "create_sprint_summary_card",
    "create_sprint_timeline_chart",
    "create_status_distribution_pie",
    # Private symbols exposed for test compatibility
    "_calculate_issue_health_priority",
    "_sort_issues_by_health_priority",
    # Shared constant
    "STATUS_COLORS",
]
