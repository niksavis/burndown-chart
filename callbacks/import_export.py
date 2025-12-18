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
    [
        Output("report-progress-poll-interval", "disabled"),
        Output("generate-report-button-container", "style"),
        Output("report-progress-container", "style", allow_duplicate=True),
    ],
    Input("generate-report-button", "n_clicks"),
    [
        State("report-sections-checklist", "value"),
        State("data-points-input", "value"),
    ],
    prevent_initial_call=True,
)
def start_report_generation(n_clicks, sections, data_points):
    """
    Start background report generation with progress tracking.

    Args:
        n_clicks: Button clicks
        sections: List of sections ["burndown", "dora", "flow"]
        data_points: Number of weeks from Data Points slider

    Returns:
        Tuple of (interval_disabled, button_style, progress_style)
    """
    if not n_clicks:
        return no_update, no_update, no_update

    try:
        from data.query_manager import get_active_profile_id
        from data.task_progress import TaskProgress
        import threading

        profile_id = get_active_profile_id()
        if not profile_id:
            logger.error("No active profile for report generation")
            return no_update, no_update, no_update

        sections = sections or ["burndown"]
        time_period = data_points or 12

        logger.info(
            f"Starting background report generation: sections={sections}, period={time_period} weeks"
        )

        # Initialize task progress immediately to prevent old state from showing
        TaskProgress.start_task("generate_report", "Preparing report...")

        # Immediately write initial progress to prevent bar from showing old completion state
        from pathlib import Path
        import json

        progress_file = Path("task_progress.json")
        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            # Ensure progress starts at 0
            state["report_progress"]["percent"] = 0
            state["report_progress"]["message"] = "Starting..."
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

        # Start report generation in background thread
        def generate_in_background():
            try:
                from data.report_generator import generate_html_report_with_progress

                generate_html_report_with_progress(
                    sections=sections,
                    time_period_weeks=time_period,
                    profile_id=profile_id,
                )
            except Exception as e:
                logger.error(f"Background report generation failed: {e}", exc_info=True)
                TaskProgress.fail_task("generate_report", str(e))

        thread = threading.Thread(target=generate_in_background, daemon=True)
        thread.start()

        # Enable progress polling, hide button, show progress bar
        return (
            False,  # Enable interval
            {"display": "none"},  # Hide button
            {},  # Show progress bar
        )

    except Exception as e:
        logger.error(f"Failed to start report generation: {e}", exc_info=True)
        return no_update, no_update, no_update


@callback(
    [
        Output("report-progress-label", "children"),
        Output("report-progress-bar", "value"),
        Output("report-progress-bar", "color"),
        Output("report-progress-poll-interval", "disabled", allow_duplicate=True),
        Output("report-progress-container", "style", allow_duplicate=True),
        Output("generate-report-button-container", "style", allow_duplicate=True),
        Output("report-download", "data"),
    ],
    Input("report-progress-poll-interval", "n_intervals"),
    prevent_initial_call=True,
)
def poll_report_progress(n_intervals):
    """
    Poll report generation progress and trigger download when complete.

    Args:
        n_intervals: Number of intervals elapsed

    Returns:
        Tuple of (label, value, color, interval_disabled, progress_style, button_style, download_data)
    """
    from data.task_progress import TaskProgress
    from pathlib import Path
    import json

    progress_file = Path("task_progress.json")

    if not progress_file.exists():
        # No progress - hide progress bar, show button
        return (
            "Generating report: 0%",
            0,
            "primary",
            True,  # Disable polling
            {"display": "none"},  # Hide progress
            {},  # Show button
            no_update,
        )

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            progress_data = json.load(f)

        task_id = progress_data.get("task_id")
        if task_id != "generate_report":
            # Different task running - don't interfere
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        status = progress_data.get("status")
        report_progress = progress_data.get("report_progress", {})
        message = report_progress.get("message", "Processing...")
        percent = report_progress.get("percent", 0)
        report_file = report_progress.get(
            "report_file"
        )  # Read from report_progress object

        logger.info(
            f"[Report Progress] status={status}, percent={percent}, message={message}, report_file={report_file}"
        )

        if status == "complete":
            # CRITICAL: Check if this is a stale completion from previous report generation
            # If complete_time is > 3 seconds old, hide immediately without showing success
            complete_time = report_progress.get("complete_time")
            if complete_time:
                from datetime import datetime

                elapsed = (
                    datetime.now() - datetime.fromisoformat(complete_time)
                ).total_seconds()

                if elapsed > 3:
                    # Stale completion - hide immediately without displaying
                    logger.info(
                        f"[Report Progress] Stale completion ({elapsed:.1f}s old), hiding immediately"
                    )
                    return (
                        "Generating report: 0%",
                        0,
                        "primary",
                        True,  # Disable polling
                        {"display": "none"},  # Hide progress
                        {},  # Show button
                        no_update,  # No download
                    )

            # Report generation complete - trigger download
            logger.info(
                f"[Report Progress] Complete status detected, checking report_file: {report_file}"
            )
            if report_file and Path(report_file).exists():
                logger.info(f"Report generation complete: {report_file}")

                # Read report content
                with open(report_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # Get filename from path
                filename = Path(report_file).name

                # Cleanup
                TaskProgress.complete_task("generate_report")
                Path(report_file).unlink(missing_ok=True)  # Delete temp file

                # Trigger download and reset UI
                return (
                    "Report ready!",
                    100,
                    "success",
                    True,  # Disable polling
                    {"display": "none"},  # Hide progress
                    {},  # Show button
                    {
                        "content": html_content,
                        "filename": filename,
                        "type": "text/html",
                    },
                )
            else:
                # No report file - error
                logger.error("Report generation completed but no file found")
                TaskProgress.fail_task("generate_report", "Report file not found")
                return (
                    "Error: Report file not found",
                    100,
                    "danger",
                    True,
                    {"display": "none"},
                    {},
                    no_update,
                )

        elif status == "error":
            # Error occurred
            error_msg = progress_data.get("error", "Unknown error")
            logger.error(f"Report generation error: {error_msg}")
            return (
                f"Error: {error_msg}",
                100,
                "danger",
                True,  # Disable polling
                {},  # Keep showing progress (with error)
                {},  # Show button
                no_update,
            )

        else:
            # In progress - update progress bar
            return (
                f"{message}: {percent:.0f}%",
                percent,
                "primary",
                False,  # Keep polling
                {},  # Keep showing progress
                {"display": "none"},  # Keep button hidden
                no_update,
            )

    except Exception as e:
        logger.error(f"Error polling report progress: {e}", exc_info=True)
        return no_update, no_update, no_update, True, {"display": "none"}, {}, no_update


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
