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

    if not sections:
        raise ValueError("At least one section must be selected for report generation")

    if not profile_id:
        profile_id = get_active_profile_id()

    context = get_active_profile_and_query_display_names()
    profile_name = context.get("profile_name") or profile_id
    query_name = context.get("query_name") or "Unknown Query"

    logger.info(
        f"Generating HTML report for {profile_name} / {query_name} "
        f"(sections={sections}, weeks={time_period_weeks})"
    )

    report_data = load_report_data(profile_id, time_period_weeks)
    report_data["profile_id"] = profile_id

    metrics = calculate_all_metrics(report_data, sections, time_period_weeks)

    metrics["statistics"] = report_data["statistics"]

    chart_scripts = generate_chart_scripts(metrics, sections)

    html = render_template(
        profile_name=profile_name,
        query_name=query_name,
        time_period_weeks=time_period_weeks,
        sections=sections,
        metrics=metrics,
        chart_script="\n".join(chart_scripts),
    )

    logger.info(f"Report generated successfully: {len(html):,} bytes")

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

    try:
        update_report_progress(10, "Loading data...")
        html, metadata = generate_html_report(sections, time_period_weeks, profile_id)
        update_report_progress(100, "Report complete")
        return html, metadata
    except Exception as e:
        update_report_progress(0, f"Error: {str(e)}")
        raise
