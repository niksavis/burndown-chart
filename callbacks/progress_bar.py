"""Progress bar callback for tracking Update Data operations."""

import logging
import json
from pathlib import Path
from dash import callback, Output, Input
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


@callback(
    [
        Output("update-data-progress-container", "style"),
        Output("progress-label", "children"),
        Output("progress-bar", "value"),
        Output("progress-bar", "color"),
        Output("progress-bar", "animated"),
        Output("progress-poll-interval", "disabled"),
    ],
    [Input("progress-poll-interval", "n_intervals")],
    prevent_initial_call=True,
)
def update_progress_bars(n_intervals):
    """
    Poll task_progress.json and update progress bar.

    Args:
        n_intervals: Number of intervals elapsed (polling trigger)

    Returns:
        Tuple of (container_style, label, value, color, animated, interval_disabled)
    """
    from datetime import datetime

    # Read task progress file
    progress_file = Path("task_progress.json")

    if not progress_file.exists():
        # No progress file - hide progress bar and disable polling
        return (
            {"display": "none"},
            "Processing: 0%",
            0,
            "primary",
            True,
            True,
        )

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            progress_data = json.load(f)

        status = progress_data.get("status", "idle")

        # Handle complete status - show success for 3 seconds then cleanup
        if status == "complete":
            complete_time = progress_data.get("complete_time")
            if complete_time:
                elapsed = (
                    datetime.now() - datetime.fromisoformat(complete_time)
                ).total_seconds()
                if elapsed >= 3:
                    # 3 seconds elapsed - cleanup and hide
                    try:
                        progress_file.unlink()
                        logger.info("[Progress] Cleaned up completed task file")
                    except Exception as e:
                        logger.error(f"[Progress] Failed to cleanup: {e}")
                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                    )
                else:
                    # Show success message
                    message = progress_data.get("message", "✓ Complete")
                    return (
                        {"display": "block", "minHeight": "60px"},
                        message,
                        100,
                        "success",
                        False,  # Not animated when complete
                        False,  # Keep polling for cleanup
                    )
            # No complete_time, hide immediately
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
            )

        # If task is idle or error, hide progress bar
        if status in ["idle", "error"]:
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
            )

        # Show progress container with fixed height
        container_style = {"display": "block", "minHeight": "60px"}

        # Get current phase
        phase = progress_data.get("phase", "fetch")

        # Get progress for current phase
        if phase == "fetch":
            progress = progress_data.get("fetch_progress", {})
            phase_label = "Fetching"
            color = "primary"  # Blue
        else:  # calculate
            progress = progress_data.get("calculate_progress", {})
            phase_label = "Calculating"
            color = "success"  # Green

        percent = progress.get("percent", 0)
        current = progress.get("current", 0)
        total = progress.get("total", 0)
        message = progress.get("message", "")

        if total > 0:
            label = f"{phase_label}: {percent:.0f}% ({current}/{total})"
            if message:
                label += f" - {message}"
        else:
            label = f"{phase_label}: {message or 'Preparing...'}"

        return (
            container_style,
            label,
            percent,
            color,
            True,  # Animated during progress
            False,  # Keep polling enabled
        )

    except Exception as e:
        logger.error(f"[Progress] Error reading progress file: {e}")
        return (
            {"display": "none"},
            "Processing: 0%",
            0,
            "primary",
            True,
            True,
        )


@callback(
    Output("progress-poll-interval", "disabled", allow_duplicate=True),
    Input("update-data-unified", "n_clicks"),
    prevent_initial_call=True,
)
def start_progress_polling(n_clicks):
    """
    Enable progress polling when Update Data button is clicked.

    Args:
        n_clicks: Number of button clicks

    Returns:
        False to enable polling
    """
    if not n_clicks:
        raise PreventUpdate

    logger.info("[Progress] Update Data clicked - enabling progress polling")
    return False  # Enable polling
