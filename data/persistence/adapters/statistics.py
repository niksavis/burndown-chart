"""Data persistence adapters - Statistics save/load operations."""

# Standard library imports
from datetime import datetime
from typing import Dict, Any, List

# Third-party library imports
import pandas as pd

# Application imports
from configuration.settings import logger
from data.persistence.adapters.core import (
    convert_timestamps_to_strings,
)
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)


def save_statistics(data: List[Dict[str, Any]]) -> None:
    """
    Save statistics data to unified JSON file.

    Args:
        data: List of dictionaries containing statistics data
    """
    from data.iso_week_bucketing import get_week_label
    from datetime import datetime

    logger.info(
        f"[Persistence] save_statistics called with {len(data) if data else 0} rows"
    )

    try:
        df = pd.DataFrame(data)
        logger.debug(f"[Persistence] Created DataFrame with {len(df)} rows")

        # Ensure date column is in proper datetime format for sorting
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Sort by date in ascending order (oldest first)
        df = df.sort_values("date", ascending=True)

        # Convert back to string format for storage
        df.loc[:, "date"] = df["date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

        # Convert back to list of dictionaries
        statistics_data = df.to_dict("records")  # type: ignore[assignment]

        # CRITICAL FIX: Ensure week_label exists for all statistics
        # This prevents NULL week_labels in database
        for stat in statistics_data:
            if "week_label" not in stat or not stat["week_label"]:
                if stat.get("date"):
                    try:
                        date_obj = datetime.strptime(stat["date"], "%Y-%m-%d")
                        stat["week_label"] = get_week_label(date_obj)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not calculate week_label for date {stat.get('date')}: {e}"
                        )

        # Ensure any remaining Timestamp objects are converted to strings
        statistics_data = convert_timestamps_to_strings(statistics_data)

        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics in unified data
        unified_data["statistics"] = statistics_data

        # Update metadata - preserve existing source and jira_query unless explicitly overriding
        unified_data["metadata"].update(
            {
                "last_updated": datetime.now().isoformat(),
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info(
            f"[Persistence] ✓ Statistics saved successfully to DB: {len(statistics_data)} rows"
        )
    except Exception as e:
        logger.error(f"[Persistence] ✗ FAILED to save statistics: {e}", exc_info=True)
        raise  # Re-raise so the callback knows it failed


def save_statistics_from_csv_import(data: List[Dict[str, Any]]) -> None:
    """
    Save statistics data from CSV import to unified JSON file.
    This function specifically handles CSV imports and sets appropriate metadata.

    Args:
        data: List of dictionaries containing statistics data
    """
    from data.iso_week_bucketing import get_week_label
    from datetime import datetime as dt_module

    try:
        df = pd.DataFrame(data)

        # Ensure date column is in proper datetime format for sorting
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Sort by date in ascending order (oldest first)
        df = df.sort_values("date", ascending=True)

        # Convert back to string format for storage
        df.loc[:, "date"] = df["date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

        # Convert back to list of dictionaries
        statistics_data = df.to_dict("records")  # type: ignore[assignment]

        # CRITICAL FIX: Ensure week_label exists for all statistics from CSV import
        # This prevents NULL week_labels in database
        for stat in statistics_data:
            if "week_label" not in stat or not stat["week_label"]:
                if stat.get("date"):
                    try:
                        date_obj = dt_module.strptime(stat["date"], "%Y-%m-%d")
                        stat["week_label"] = get_week_label(date_obj)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not calculate week_label for date {stat.get('date')}: {e}"
                        )

        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics in unified data
        unified_data["statistics"] = statistics_data

        # Update metadata specifically for CSV import
        unified_data["metadata"].update(
            {
                "source": "csv_import",  # Set proper source for CSV uploads
                "last_updated": datetime.now().isoformat(),
                "jira_query": "",  # Clear JIRA-specific fields for CSV import
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info("[Cache] Statistics from CSV import saved to database")
    except Exception as e:
        logger.error(f"[Cache] Error saving CSV import statistics: {e}")


def load_statistics() -> tuple:
    """
    Load statistics data via repository pattern (database).

    Returns:
        Tuple (data, is_sample) where:
        - data: List of dictionaries containing statistics data
        - is_sample: Boolean indicating if sample data is being used
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return [], False

        stats_rows = backend.get_statistics(active_profile_id, active_query_id)
        if not stats_rows:
            return [], False

        # Convert to DataFrame for processing
        statistics_df = pd.DataFrame(stats_rows)

        # Rename stat_date to date for compatibility
        if "stat_date" in statistics_df.columns:
            statistics_df["date"] = statistics_df["stat_date"]

        # Parse dates once for consistency
        statistics_df["date"] = pd.to_datetime(
            statistics_df["date"], errors="coerce", format="mixed"
        )

        # CRITICAL FIX: Remove duplicate dates from legacy data
        # Normalize dates and keep only the most recent entry per date
        if "date" in statistics_df.columns and not statistics_df.empty:
            # Normalize dates to YYYY-MM-DD format using apply to avoid type checker issues
            statistics_df["date_normalized"] = statistics_df["date"].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None
            )

            # Sort by date descending and drop duplicates, keeping the first (most recent)
            statistics_df = statistics_df.sort_values("date", ascending=False)
            statistics_df = statistics_df.drop_duplicates(
                subset=["date_normalized"], keep="first"
            )
            statistics_df = statistics_df.sort_values("date", ascending=True)

            # Clean up temporary column
            statistics_df = statistics_df.drop(columns=["date_normalized"])
        statistics_df = statistics_df.sort_values("date", ascending=True)
        statistics_df["date"] = (
            statistics_df["date"]
            .apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "")
            .astype(str)
        )

        data = statistics_df.to_dict("records")  # type: ignore[assignment]
        data = convert_timestamps_to_strings(data)
        logger.info(f"[Cache] Statistics loaded from database: {len(data)} rows")
        return data, False
    except Exception as e:
        logger.error(f"[Cache] Error loading statistics: {e}")
        return [], False
