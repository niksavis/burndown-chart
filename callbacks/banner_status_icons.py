"""
Banner Status Icons Callback

Animates profile and query icons in the top banner during operations.
Provides visual feedback even when Settings panel is closed.

Visual States:
- Default: Blue folder + search (idle)
- Update Data: Orange folder + spinner (background JIRA sync)
- UI Operations: Purple spinner (query/slider changes trigger recalc)
"""

import json
import logging
from datetime import datetime

from dash import Input, Output, State, callback, ctx

logger = logging.getLogger(__name__)


@callback(
    [
        Output("profile-status-icon", "className"),
        Output("query-status-icon", "className"),
    ],
    [
        Input("progress-poll-interval", "n_intervals"),
        Input("query-selector", "value"),
        Input("pert-factor-slider", "value"),
        Input("data-points-input", "value"),
        Input("calculation-results", "data"),
    ],
    [
        State("profile-status-icon", "className"),
    ],
    prevent_initial_call=False,  # Allow initial call to set default state on load
)
def update_banner_status_icons(
    n_intervals,
    query_value,
    pert_value,
    data_points_value,
    calc_results,
    current_profile_class,
):
    """Update banner icons based on task progress and UI operations.

    Priority:
    1. Update Data (orange) - background JIRA operations
    2. UI operations (purple spinner) - query/slider changes
    3. Idle (blue) - no operations

    Args:
        n_intervals: Polling interval for Update Data
        query_value: Query selector (triggers recalc)
        pert_value: PERT slider (triggers recalc)
        data_points_value: Data points slider (triggers recalc)
        calc_results: Signals calculation completion
        current_profile_class: Current icon state

    Returns:
        Tuple of (profile icon class, query icon class)
    """
    trigger_id = ctx.triggered_id if ctx.triggered else None

    # Handle initial load: return default idle state immediately
    if not ctx.triggered:
        logger.debug("[BannerStatus] Initial load - showing default idle icons")
        return "fas fa-folder me-1", "fas fa-search me-1"

    try:
        from data.persistence.factory import get_backend
        from utils.datetime_utils import parse_iso_datetime

        backend = get_backend()
        progress_data = backend.get_task_state()

        # PRIORITY 1: Update Data operation (highest priority - background sync)
        if progress_data:
            status = progress_data.get("status", "idle")
            phase = progress_data.get("phase", "fetch")
            cancelled = progress_data.get("cancelled", False)

            if status == "in_progress" and not cancelled:
                if phase == "postprocess":
                    postprocess_time = progress_data.get("postprocess_time")
                    postprocess_timestamp = parse_iso_datetime(postprocess_time)
                    if postprocess_timestamp:
                        elapsed = (
                            datetime.now() - postprocess_timestamp
                        ).total_seconds()
                        if elapsed >= 5:
                            logger.warning(
                                "[BannerStatus] Stale postprocess detected, showing idle icons"
                            )
                            return (
                                "fas fa-folder me-1",
                                "fas fa-search me-1",
                            )
                    else:
                        logger.warning(
                            "[BannerStatus] Invalid postprocess_time, showing idle icons"
                        )
                        return "fas fa-folder me-1", "fas fa-search me-1"

                # Background operation active - orange indicators
                profile_icon_class = "fas fa-folder me-1 text-warning"

                if phase == "fetch":
                    query_icon_class = "fas fa-spinner fa-spin me-1 text-warning"
                elif phase == "calculate":
                    query_icon_class = "fas fa-spinner fa-spin me-1 text-success"
                else:
                    query_icon_class = "fas fa-search me-1 text-success"

                return profile_icon_class, query_icon_class

        # PRIORITY 2: UI operations (query switch, slider changes)
        if trigger_id in ["query-selector", "pert-factor-slider", "data-points-input"]:
            # UI change detected - show purple spinner (recalculation starting)
            return "fas fa-spinner fa-spin me-1 text-purple", "fas fa-search me-1"

        # PRIORITY 3: Calculation complete - clear loading state
        if trigger_id == "calculation-results":
            # If we were showing purple, clear it
            if current_profile_class and "text-purple" in current_profile_class:
                return "fas fa-folder me-1", "fas fa-search me-1"

        # DEFAULT: No operation - blue icons
        return "fas fa-folder me-1", "fas fa-search me-1"

    except (OSError, json.JSONDecodeError) as e:
        logger.debug(f"[BannerStatus] Could not read progress file: {e}")
        return "fas fa-folder me-1", "fas fa-search me-1"
    except Exception as e:
        logger.error(f"[BannerStatus] Error updating status icons: {e}")
        return "fas fa-folder me-1", "fas fa-search me-1"
