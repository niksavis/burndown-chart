"""HTML report generation package.

Exports the main report generation functions.
"""

# Import from new modular structure
from data.report.generator import (
    generate_html_report,
    generate_html_report_with_progress,
)

__all__ = [
    "generate_html_report",
    "generate_html_report_with_progress",
]
