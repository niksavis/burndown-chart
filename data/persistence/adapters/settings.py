"""Data persistence adapters - Settings save/load operations (legacy)."""

# Standard library imports
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Third-party library imports
import pandas as pd

# Application imports
from configuration.settings import logger

def save_settings(
    pert_factor,
    deadline,
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
    data_points_count=None,
    show_milestone=None,
    milestone=None,
    show_points=None,
):
    """
    DEPRECATED: Legacy function for single-file mode (not used with profiles).
    Use save_app_settings() instead for profile-based persistence.

    This function is kept for backward compatibility only.
    """
    # Lazy import to avoid circular dependency
    from configuration.settings import (
        DEFAULT_DATA_POINTS_COUNT,
        DEFAULT_ESTIMATED_ITEMS,
        DEFAULT_ESTIMATED_POINTS,
    )

    logger.warning(
        "[Deprecated] save_settings() called - use save_app_settings() for profile-based storage"
    )

    # Delegate to save_app_settings with proper structure
    settings_dict = {
        "forecast_settings": {
            "pert_factor": pert_factor,
            "deadline": deadline,
            "data_points_count": data_points_count
            if data_points_count is not None
            else max(DEFAULT_DATA_POINTS_COUNT, pert_factor * 2),
            "milestone": milestone,
        },
        "project_scope": {
            "total_items": total_items,
            "total_points": total_points,
            "estimated_items": estimated_items
            if estimated_items is not None
            else DEFAULT_ESTIMATED_ITEMS,
            "estimated_points": estimated_points
            if estimated_points is not None
            else DEFAULT_ESTIMATED_POINTS,
        },
        "show_milestone": show_milestone if show_milestone is not None else False,
        "show_points": show_points if show_points is not None else False,
    }
    save_app_settings(**settings_dict)


def load_settings():
    """
    DEPRECATED: Legacy function for single-file mode (not used with profiles).
    Use load_app_settings() instead for profile-based persistence.

    This function is kept for backward compatibility only.
    """
    # Lazy import to avoid circular dependency
    from configuration.settings import (
        DEFAULT_PERT_FACTOR,
        DEFAULT_DEADLINE,
        DEFAULT_TOTAL_ITEMS,
        DEFAULT_TOTAL_POINTS,
        DEFAULT_DATA_POINTS_COUNT,
        DEFAULT_ESTIMATED_ITEMS,
        DEFAULT_ESTIMATED_POINTS,
    )

    logger.warning(
        "[Deprecated] load_settings() called - use load_app_settings() for profile-based storage"
    )

    # Delegate to load_app_settings and flatten the structure
    app_settings = load_app_settings()
    forecast = app_settings.get("forecast_settings", {})

    return {
        "pert_factor": forecast.get("pert_factor", DEFAULT_PERT_FACTOR),
        "deadline": forecast.get("deadline", DEFAULT_DEADLINE),
        "total_items": app_settings.get("total_items", DEFAULT_TOTAL_ITEMS),
        "total_points": app_settings.get("total_points", DEFAULT_TOTAL_POINTS),
        "estimated_items": app_settings.get("estimated_items", DEFAULT_ESTIMATED_ITEMS),
        "estimated_points": app_settings.get(
            "estimated_points", DEFAULT_ESTIMATED_POINTS
        ),
        "data_points_count": forecast.get(
            "data_points_count", DEFAULT_DATA_POINTS_COUNT
        ),
        "show_milestone": app_settings.get("show_milestone", False),
        "milestone": forecast.get("milestone"),
    }


