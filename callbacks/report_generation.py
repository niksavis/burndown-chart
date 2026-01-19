"""Callbacks for HTML report generation (simplified synchronous version)."""

import logging
from dash import callback, Output, Input, State, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("report-weeks-display", "children"),
    Input("data-points-input", "value"),
    prevent_initial_call=False,
)
def update_report_weeks_display(data_points):
    """Update the report weeks display to match the Data Points slider."""
    if data_points is None:
        logger.debug("Report weeks display: data_points is None, defaulting to 12")
        return "12"
    logger.debug(f"Report weeks display updated to: {data_points}")
    return str(data_points)


@callback(
    Output("report-download", "data"),
    Output("app-notifications", "children", allow_duplicate=True),
    Input("generate-report-button", "n_clicks"),
    [
        State("report-sections-checklist", "value"),
        State("data-points-input", "value"),
    ],
    prevent_initial_call=True,
)
def generate_and_download_report(n_clicks, sections, data_points):
    """Generate report synchronously and trigger download (simplified - no progress bar)."""
    if not n_clicks:
        return no_update, no_update

    try:
        from data.query_manager import get_active_profile_id
        from data.report_generator import generate_html_report
        from datetime import datetime
        from ui.toast_notifications import create_warning_toast, create_error_toast

        try:
            profile_id = get_active_profile_id()
        except ValueError:
            # No active profile - user hasn't set up any data yet
            logger.warning("Report generation attempted with no active profile")
            toast = create_warning_toast(
                "Please create a profile and fetch JIRA data before generating reports.",
                header="No Data Available",
                duration=5000,
            )
            return no_update, toast

        if not profile_id:
            logger.error("No active profile for report generation")
            toast = create_warning_toast(
                "Please create a profile and fetch JIRA data before generating reports.",
                header="No Data Available",
                duration=5000,
            )
            return no_update, toast

        sections = sections or ["burndown"]
        time_period = data_points or 12

        logger.info(
            f"Generating report: sections={sections}, time_period={time_period}w (raw data_points={data_points})"
        )

        # Generate report (blocks until complete)
        html_content, metadata = generate_html_report(
            sections=sections,
            time_period_weeks=time_period,
            profile_id=profile_id,
        )

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = metadata["profile_name"].replace(" ", "_").replace("/", "_")
        query_name = metadata["query_name"].replace(" ", "_").replace("/", "_")
        filename = f"{timestamp}_{profile_name}_{query_name}_{time_period}w.html"

        logger.info(f"Report generated: {filename} ({len(html_content):,} bytes)")

        # Trigger download using content (path doesn't work for HTML)
        return {"content": html_content, "filename": filename}, no_update

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        from ui.toast_notifications import create_error_toast

        toast = create_error_toast(
            f"Report generation failed: {str(e)}",
            header="Report Generation Error",
            duration=6000,
        )
        return no_update, toast


# Progress polling callback removed - using simple synchronous generation instead


@callback(
    Output("report-size-estimate", "children"),
    Input("report-sections-checklist", "value"),
)
def update_report_size_estimate(sections):
    """Estimate report file size based on selected sections."""
    sections = sections or []
    base_size = 50  # KB
    section_sizes = {"burndown": 300, "dora": 500, "flow": 500, "budget": 100}
    total_kb = base_size + sum(section_sizes.get(s, 0) for s in sections)
    size_mb = total_kb / 1024
    return f"Estimated size: ~{size_mb:.1f} MB"
