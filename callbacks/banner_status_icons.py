"""
Banner Status Icons Callback

Animates profile and query icons in the top banner during operations.
Provides visual feedback even when Settings panel is closed.
"""

import logging
import json
from dash import callback, Output, Input

logger = logging.getLogger(__name__)


@callback(
    [
        Output("profile-status-icon", "className"),
        Output("query-status-icon", "className"),
    ],
    Input("progress-poll-interval", "n_intervals"),
    prevent_initial_call=True,
)
def update_banner_status_icons(n_intervals):
    """Update banner icons based on task progress.

    Visual feedback:
    - Profile icon: Changes color during operations (orange during operation)
    - Query icon: Animates/spins during fetch, changes during calculate

    Args:
        n_intervals: Polling interval counter

    Returns:
        Tuple of (profile icon class, query icon class)
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        progress_data = backend.get_task_state()

        if not progress_data:
            # No operation in progress - return default icons
            return "fas fa-folder me-1", "fas fa-search me-1"

        status = progress_data.get("status", "idle")
        phase = progress_data.get("phase", "fetch")
        cancelled = progress_data.get("cancelled", False)

        # Check if operation is in progress AND not cancelled
        if status != "in_progress" or cancelled:
            # Operation complete, error, or cancelled - return to default
            return "fas fa-folder me-1", "fas fa-search me-1"

        # Operation in progress - apply visual feedback
        # Profile icon: Change color to indicate activity
        profile_icon_class = "fas fa-folder me-1 text-warning"

        # Query icon: Different animation based on phase
        if phase == "fetch":
            # Fetch phase: Spinning magnifying glass
            query_icon_class = "fas fa-spinner fa-spin me-1 text-warning"
        elif phase == "calculate":
            # Calculate phase: Calculator/chart icon spinning
            query_icon_class = "fas fa-calculator fa-pulse me-1 text-success"
        else:
            # Fallback: Animated search
            query_icon_class = "fas fa-search fa-pulse me-1 text-warning"

        return profile_icon_class, query_icon_class

    except (json.JSONDecodeError, IOError) as e:
        logger.debug(f"[BannerStatus] Could not read progress file: {e}")
        return "fas fa-folder me-1", "fas fa-search me-1"
    except Exception as e:
        logger.error(f"[BannerStatus] Error updating status icons: {e}")
        return "fas fa-folder me-1", "fas fa-search me-1"
