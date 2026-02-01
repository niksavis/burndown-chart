"""
Helper Functions for Settings Callbacks

This module contains utility functions used by settings callbacks.
Functions here are pure utilities with no Dash callback decorators.
"""

from configuration import logger


def normalize_show_points(value):
    """
    Normalize show_points value to boolean.

    Handles various input types:
    - List (from checkbox): ["show"] → True, [] → False
    - Integer (from database): 1 → True, 0 → False
    - Boolean: True/False → True/False

    Args:
        value: show_points value from checkbox, database, or settings

    Returns:
        bool: Normalized boolean value
    """
    if isinstance(value, list):
        # Checkbox format: ["show"] or []
        return "show" in value
    elif isinstance(value, int):
        # Database format: 1 or 0
        return value != 0
    elif isinstance(value, bool):
        # Already boolean
        return value
    else:
        # Unknown format, default to False
        return False


def get_data_points_info(value: int, min_val: int, max_val: int) -> str:
    """
    Generate info text about data points selection.

    Args:
        value: Current data points value
        min_val: Minimum data points value
        max_val: Maximum data points value

    Returns:
        str: Info text describing the selection
    """
    if min_val == max_val:
        return "Using all available data points"

    percent = (
        ((value - min_val) / (max_val - min_val) * 100) if max_val > min_val else 100
    )

    if value == min_val:
        return f"Using minimum data points ({value} points, most recent data only)"
    elif value == max_val:
        return f"Using all available data points ({value} points)"
    else:
        return (
            f"Using {value} most recent data points ({percent:.0f}% of available data)"
        )


def calculate_remaining_work_for_data_window(data_points_count, statistics):
    """
    Get current remaining work scope - this does NOT depend on the data window.

    The Data Points slider filters the time window for forecasting/statistics,
    but "Remaining" always means CURRENT remaining work (what's left to do now).

    Args:
        data_points_count: Number of data points (weeks) - used for logging only
        statistics: List of statistics data points - not used, kept for compatibility

    Returns:
        Tuple: (estimated_items, remaining_items, estimated_points, remaining_points_str, calc_results)
               or None if calculation cannot be performed
    """
    if not data_points_count:
        return None

    try:
        from data.persistence import load_unified_project_data

        # Load unified data to get current scope
        unified_data = load_unified_project_data()
        project_scope = unified_data.get("project_scope", {})

        # CRITICAL FIX: Parameter panel shows CURRENT remaining work, NOT windowed scope
        # The slider filters statistics for forecasting, but remaining work is always current
        estimated_items = project_scope.get("estimated_items", 0)
        remaining_items = project_scope.get("remaining_items", 0)
        estimated_points = project_scope.get("estimated_points", 0)
        remaining_points = project_scope.get("remaining_total_points", 0)

        # Calculate avg points per item for calc_results
        avg_points_per_item = 0
        if remaining_items > 0:
            avg_points_per_item = remaining_points / remaining_items

        logger.info("[PARAM PANEL] Current remaining work (independent of slider):")
        logger.info(
            f"  Estimated items: {estimated_items}, Remaining items: {remaining_items}"
        )
        logger.info(
            f"  Estimated points: {estimated_points:.1f}, Remaining points: {remaining_points:.1f}"
        )
        logger.info(f"  Avg: {avg_points_per_item:.2f} points/item")

        calc_results = {
            "total_points": remaining_points,
            "avg_points_per_item": avg_points_per_item,
        }

        return (
            estimated_items,
            int(remaining_items),
            estimated_points,
            f"{remaining_points:.0f}",
            calc_results,
        )

    except Exception as e:
        logger.error(f"Error calculating remaining work for data window: {e}")
        return None
