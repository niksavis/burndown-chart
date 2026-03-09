"""HTML report assembly: entry-point generation functions.

Orchestrates data loading, metric calculation, chart generation, and rendering.
Part of data/report/generator.py split.
"""

import logging

from data.profile_manager import get_active_profile_and_query_display_names
from data.query_manager import get_active_profile_id
from data.report.chart_generator import generate_chart_scripts
from data.report.data_loader import load_report_data
from data.report.generator_metrics import calculate_all_metrics
from data.report.renderer import render_template, update_report_progress

logger = logging.getLogger(__name__)


def generate_html_report(
    sections: list[str],
    time_period_weeks: int = 12,
    profile_id: str | None = None,
) -> tuple[str, dict[str, str]]:
    """
    Generate a self-contained HTML report with project metrics snapshot.

    Args:
        sections: List of section identifiers to include in report
        time_period_weeks: Number of weeks to analyze (4, 12, 26, or 52)
        profile_id: Profile ID to generate report for (defaults to active profile)

    Returns:
        Tuple of (HTML string, metadata dict) where metadata contains:
            - profile_name: Display name of the profile
            - query_name: Display name of the query
            - time_period_weeks: Number of weeks in the analysis period

    Raises:
        ValueError: If no sections selected or data is invalid
    """
    if not sections:
        raise ValueError("At least one section must be selected for report generation")

    # Get active profile context

    if not profile_id:
        profile_id = get_active_profile_id()

    context = get_active_profile_and_query_display_names()
    profile_name = context.get("profile_name") or profile_id
    query_name = context.get("query_name") or "Unknown Query"

    logger.info(
        f"Generating HTML report for {profile_name} / {query_name} "
        f"(sections={sections}, weeks={time_period_weeks})"
    )

    # Delegate to specialized modules

    # Load and filter data for the time period
    report_data = load_report_data(profile_id, time_period_weeks)
    report_data["profile_id"] = profile_id  # Add for DORA metrics

    # Calculate all metrics for requested sections
    metrics = calculate_all_metrics(report_data, sections, time_period_weeks)

    # Add statistics to metrics for chart generation
    metrics["statistics"] = report_data["statistics"]

    # Generate Chart.js scripts for visualizations
    chart_scripts = generate_chart_scripts(metrics, sections)

    # Render HTML template
    html = render_template(
        profile_name=profile_name,
        query_name=query_name,
        time_period_weeks=time_period_weeks,
        sections=sections,
        metrics=metrics,
        chart_script="\n".join(chart_scripts),
    )

    logger.info(f"Report generated successfully: {len(html):,} bytes")

    # Return HTML and metadata for filename construction
    metadata = {
        "profile_name": profile_name,
        "query_name": query_name,
        "time_period_weeks": time_period_weeks,
    }
    return html, metadata


def generate_html_report_with_progress(
    sections: list[str],
    time_period_weeks: int = 12,
    profile_id: str | None = None,
) -> tuple[str, dict[str, str]]:
    """
    Generate HTML report with progress updates.

    This is a wrapper around generate_html_report() that provides progress
    updates through the task_progress.json file.

    Args:
        sections: List of section identifiers to include in report
        time_period_weeks: Number of weeks to analyze
        profile_id: Profile ID to generate report for

    Returns:
        Tuple of (HTML string, metadata dict)
    """

    try:
        update_report_progress(10, "Loading data...")
        html, metadata = generate_html_report(sections, time_period_weeks, profile_id)
        update_report_progress(100, "Report complete")
        return html, metadata
    except Exception as e:
        update_report_progress(0, f"Error: {str(e)}")
        raise
