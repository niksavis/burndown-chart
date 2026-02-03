"""Data persistence adapters - Project data save/load operations."""

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

def save_project_data(
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
    metadata=None,
):
    """
    DEPRECATED: Use save_unified_project_data() instead.
    Save project-specific data via repository pattern.

    Args:
        total_items: Total number of items
        total_points: Total number of points
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        metadata: Additional project metadata (e.g., JIRA sync info)
    """
    logger.warning(
        "[Deprecated] save_project_data() called - use save_unified_project_data() instead"
    )

    try:
        from data.persistence.factory import get_backend

        # Lazy import to avoid circular dependency
        from configuration.settings import (
            DEFAULT_ESTIMATED_ITEMS,
            DEFAULT_ESTIMATED_POINTS,
        )

        backend = get_backend()

        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.error("[Cache] No active profile/query to save project data to")
            return

        scope_data = {
            "total_items": total_items,
            "total_points": total_points,
            "estimated_items": estimated_items
            if estimated_items is not None
            else DEFAULT_ESTIMATED_ITEMS,
            "estimated_points": estimated_points
            if estimated_points is not None
            else DEFAULT_ESTIMATED_POINTS,
            "metadata": metadata if metadata is not None else {},
        }

        backend.save_scope(active_profile_id, active_query_id, scope_data)
        logger.info("[Cache] Project data saved to database")
    except Exception as e:
        logger.error(f"[Cache] Error saving project data: {e}")


def load_project_data() -> Dict[str, Any]:
    """
    Load project-specific data via repository pattern (database).

    Returns:
        Dictionary containing project data or default values if not found
    """
    # Lazy import to avoid circular dependency
    from configuration.settings import (
        DEFAULT_TOTAL_ITEMS,
        DEFAULT_TOTAL_POINTS,
        DEFAULT_ESTIMATED_ITEMS,
        DEFAULT_ESTIMATED_POINTS,
    )

    default_data = {
        "total_items": DEFAULT_TOTAL_ITEMS,
        "total_points": DEFAULT_TOTAL_POINTS,
        "estimated_items": DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": DEFAULT_ESTIMATED_POINTS,
        "metadata": {},
    }

    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return default_data

        scope = backend.get_scope(active_profile_id, active_query_id)
        if not scope:
            return default_data

        return {
            "total_items": scope.get("total_items", DEFAULT_TOTAL_ITEMS),
            "total_points": scope.get("total_points", DEFAULT_TOTAL_POINTS),
            "estimated_items": scope.get("estimated_items", DEFAULT_ESTIMATED_ITEMS),
            "estimated_points": scope.get("estimated_points", DEFAULT_ESTIMATED_POINTS),
            "metadata": {},
        }
    except Exception as e:
        logger.error(f"[Cache] Error loading project data: {e}")
        return default_data


