"""Data persistence adapters - Unified project data operations."""

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

def load_unified_project_data() -> Dict[str, Any]:
    """
    Load unified project data via repository pattern (database).

    QUERY-LEVEL DATA: Statistics and project scope are query-specific.

    Returns:
        Dict: Unified project data structure
    """
    from data.schema import get_default_unified_data

    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return get_default_unified_data()

        # Build unified data from backend
        data = get_default_unified_data()

        # Load project scope
        scope = backend.get_scope(active_profile_id, active_query_id)
        if scope:
            data["project_scope"].update(scope)
            logger.info(
                f"[Cache] Loaded scope from DB - Total: {scope.get('total_items')}, "
                f"Completed: {scope.get('completed_items')}, "
                f"Remaining: {scope.get('remaining_items')}"
            )

        # Load statistics
        stats_rows = backend.get_statistics(active_profile_id, active_query_id)
        statistics = []
        if stats_rows:
            for row in stats_rows:
                stat = dict(row)
                if "stat_date" in stat:
                    stat["date"] = stat["stat_date"]
                statistics.append(stat)
            data["statistics"] = statistics

        logger.info(
            f"[Cache] Loaded unified data from database for {active_profile_id}/{active_query_id}: {len(statistics)} stats"
        )
        if statistics:
            logger.info(
                f"[Cache] First stat: date={statistics[0].get('date')}, items={statistics[0].get('remaining_items')}, points={statistics[0].get('remaining_total_points')}"
            )
            logger.info(
                f"[Cache] Last stat: date={statistics[-1].get('date')}, items={statistics[-1].get('remaining_items')}, points={statistics[-1].get('remaining_total_points')}"
            )
        return data

    except Exception as e:
        logger.error(f"[Cache] Error loading unified project data: {e}")
        return get_default_unified_data()


def save_unified_project_data(data: Dict[str, Any]) -> None:
    """
    Save unified project data via repository pattern (database).

    QUERY-LEVEL DATA: Statistics and project scope are query-specific.

    Args:
        data: Unified project data dictionary
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("[Cache] Cannot save - no active profile/query")
            return

        # Save project scope
        if "project_scope" in data:
            backend.save_scope(
                active_profile_id, active_query_id, data["project_scope"]
            )

        # Save statistics as batch (list)
        if "statistics" in data and data["statistics"]:
            stat_list = []
            for stat in data["statistics"]:
                stat_data = dict(stat)
                # Convert "date" to "stat_date" for database compatibility
                if "date" in stat_data:
                    if "stat_date" not in stat_data or not stat_data["stat_date"]:
                        stat_data["stat_date"] = stat_data["date"]

                # CRITICAL FIX: Normalize stat_date to YYYY-MM-DD format to prevent duplicates
                # Issue: Dates with timestamps (YYYY-MM-DD-HHMMSS) vs plain dates (YYYY-MM-DD)
                # created duplicate database entries because ON CONFLICT only works with exact string match
                if stat_data.get("stat_date"):
                    try:
                        # Parse date in any format and normalize to YYYY-MM-DD
                        parsed_date = pd.to_datetime(
                            stat_data["stat_date"], format="mixed", errors="coerce"
                        )
                        if pd.notna(parsed_date):
                            stat_data["stat_date"] = parsed_date.strftime("%Y-%m-%d")
                        else:
                            logger.warning(
                                f"[Cache] Could not parse date: {stat_data['stat_date']}"
                            )
                            continue
                    except Exception as e:
                        logger.warning(
                            f"[Cache] Error normalizing date {stat_data.get('stat_date')}: {e}"
                        )
                        continue

                # Ensure stat_date exists (required field)
                if not stat_data.get("stat_date"):
                    logger.warning(
                        f"[Cache] Skipping statistic with no date: {stat_data}"
                    )
                    continue
                stat_list.append(stat_data)
            if stat_list:
                backend.save_statistics_batch(
                    active_profile_id, active_query_id, stat_list
                )
                logger.info(f"[Cache] Saved {len(stat_list)} statistics to database")
            else:
                logger.warning(
                    "[Cache] No valid statistics to save (all missing dates)"
                )

        logger.info("[Cache] Saved unified project data to database")
    except Exception as e:
        logger.error(f"[Cache] Error saving unified project data: {e}")
        raise


