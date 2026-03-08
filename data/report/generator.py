"""HTML report generator coordinator.

Re-export shim. Implementation is split across focused modules:
- generator_assembly: generate_html_report, generate_html_report_with_progress
- generator_metrics: calculate_all_metrics, calculate_executive_summary
- generator_recommendations: calculate_recommendations
"""

from data.report.generator_assembly import (  # noqa: F401
    generate_html_report,
    generate_html_report_with_progress,
)
from data.report.generator_metrics import (  # noqa: F401
    calculate_all_metrics,
    calculate_executive_summary,
)
from data.report.generator_recommendations import (  # noqa: F401
    calculate_recommendations,
)
