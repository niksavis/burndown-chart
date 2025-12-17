"""Callbacks for import/export functionality (full profile export)."""

from datetime import datetime
import logging
from dash import callback, Output, Input, State, no_update
from data.import_export import export_profile_enhanced
from data.query_manager import get_active_profile_id

logger = logging.getLogger(__name__)


@callback(
    Output("export-profile-download", "data"),
    Input("export-profile-button", "n_clicks"),
    [
        State("export-type-radio", "value"),
        State("export-options-checklist", "value"),
    ],
    prevent_initial_call=True,
)
def export_full_profile(n_clicks, export_type, options):
    """
    Export full profile as ZIP file.

    Args:
        n_clicks: Button clicks
        export_type: "quick" or "full"
        options: List of options ["metrics", "queries", "cache", "credentials"]

    Returns:
        dcc.send_file object for ZIP download
    """
    if not n_clicks:
        return no_update

    try:
        profile_id = get_active_profile_id()
        if not profile_id:
            logger.error("No active profile for export")
            return no_update

        # Map UI options to export parameters
        options = options or []
        include_cache = "cache" in options
        include_queries = "queries" in options
        export_type_param = export_type if export_type == "full" else "quick"

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = profile_id.replace(" ", "_").replace("/", "_")
        filename = f"profile_{profile_name}_{timestamp}.zip"
        export_path = f"profiles/{profile_id}/export_{timestamp}.zip"

        logger.info(
            f"Starting profile export: type={export_type_param}, cache={include_cache}, queries={include_queries}"
        )

        # Call backend export function
        export_profile_enhanced(
            profile_id=profile_id,
            export_path=export_path,
            include_cache=include_cache,
            include_queries=include_queries,
            export_type=export_type_param,
        )

        logger.info(f"Profile export completed: {export_path}")

        # Return download trigger
        return {"path": export_path, "filename": filename}

    except Exception as e:
        logger.error(f"Profile export failed: {e}", exc_info=True)
        return no_update


@callback(
    Output("export-options-collapse", "is_open"),
    Input("export-type-radio", "value"),
)
def toggle_export_options(export_type):
    """Show/hide export options based on export type selection."""
    return export_type == "full"


@callback(
    Output("export-size-estimate", "children"),
    [
        Input("export-options-checklist", "value"),
        Input("export-type-radio", "value"),
    ],
)
def update_export_size_estimate(options, export_type):
    """
    Calculate estimated export size based on selected options.

    Args:
        options: List of selected options
        export_type: "quick" or "full"

    Returns:
        Formatted size estimate string
    """
    options = options or []

    # Base sizes
    base_size = 50  # KB (profile.json, manifest)
    metrics_size = 100 if "metrics" in options else 0  # KB
    queries_size = 200 if "queries" in options else 0  # KB
    cache_size = 15000 if "cache" in options else 0  # KB (~15 MB for JIRA cache)

    total_kb = base_size + metrics_size + queries_size + cache_size

    # Format size display
    if total_kb < 1024:
        size_str = f"{total_kb} KB"
    else:
        size_mb = total_kb / 1024
        size_str = f"{size_mb:.1f} MB"

    return f"Estimated size: {size_str}"


@callback(
    Output("report-weeks-display", "children"),
    Input("data-points-input", "value"),
    prevent_initial_call=False,
)
def update_report_weeks_display(data_points):
    """
    Update the report weeks display to match the Data Points slider.

    Args:
        data_points: Current value of data points slider

    Returns:
        String with number of weeks
    """
    if data_points is None:
        return "12"
    return str(data_points)


@callback(
    Output("report-download", "data"),
    Input("generate-report-button", "n_clicks"),
    [
        State("report-sections-checklist", "value"),
        State("data-points-input", "value"),
    ],
    prevent_initial_call=True,
)
def generate_report(n_clicks, sections, data_points):
    """
    Generate HTML report with selected sections using Data Points slider value.

    Args:
        n_clicks: Button clicks
        sections: List of sections ["burndown", "dora", "flow"]
        data_points: Number of weeks from Data Points slider

    Returns:
        dcc.send_file object for HTML download
    """
    if not n_clicks:
        return no_update

    try:
        from data.report_generator import generate_html_report
        from data.query_manager import get_active_profile_id

        profile_id = get_active_profile_id()
        if not profile_id:
            logger.error("No active profile for report generation")
            return no_update

        sections = sections or ["burndown"]
        time_period = data_points or 12

        logger.info(
            f"Generating report: sections={sections}, period={time_period} weeks"
        )

        # Generate report HTML (returns HTML content and metadata with display names)
        html_content, metadata = generate_html_report(
            sections=sections,
            time_period_weeks=time_period,
            profile_id=profile_id,
        )

        # Generate filename: YYYYMMDD_HHMMSS_ProfileName_QueryName_Xw.html
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = metadata["profile_name"].replace(" ", "_").replace("/", "_")
        query_name = metadata["query_name"].replace(" ", "_").replace("/", "_")
        weeks = metadata["time_period_weeks"]
        filename = f"{timestamp}_{profile_name}_{query_name}_{weeks}w.html"

        logger.info(f"Report generated: {len(html_content)} bytes, {filename}")

        # Return HTML download
        return {
            "content": html_content,
            "filename": filename,
            "type": "text/html",
        }

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return no_update


@callback(
    Output("report-size-estimate", "children"),
    Input("report-sections-checklist", "value"),
)
def update_report_size_estimate(sections):
    """
    Estimate report file size based on selected sections.

    Args:
        sections: List of selected sections

    Returns:
        Formatted size estimate string
    """
    sections = sections or []

    # Base HTML template size
    base_size = 50  # KB

    # Estimate per section (with embedded Plotly charts)
    section_sizes = {
        "burndown": 300,  # KB (chart data + JS)
        "dora": 500,  # KB (multiple charts)
        "flow": 500,  # KB (multiple charts)
    }

    total_kb = base_size + sum(section_sizes.get(s, 0) for s in sections)

    # Format size display
    size_mb = total_kb / 1024
    return f"Estimated size: ~{size_mb:.1f} MB"
