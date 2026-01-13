#!/usr/bin/env python3
"""Clear metric snapshots to force recalculation.

This utility clears metrics for the active profile/query combination.
Use this when you need to force recalculation due to:
- Field mapping changes
- Configuration changes
- Data quality issues

NOTE: This is now automatic during "Update Data" operation.
You only need this script for manual cleanup.

Usage:
    python data/clear_metrics_cache.py

    Or import as module:
    from data.clear_metrics_cache import clear_active_query_metrics
"""

import sqlite3
import sys


def clear_active_query_metrics(
    db_path: str = "profiles/burndown.db",
) -> tuple[int, str, str]:
    """Clear metrics for the active profile/query combination.

    Args:
        db_path: Path to SQLite database (default: profiles/burndown.db)

    Returns:
        Tuple of (deleted_count, profile_id, query_id)

    Raises:
        ValueError: If no active profile/query found
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get active profile and query
    cursor.execute("SELECT value FROM app_state WHERE key = 'active_profile_id'")
    active_profile_row = cursor.fetchone()
    active_profile_id = active_profile_row[0] if active_profile_row else None

    cursor.execute("SELECT value FROM app_state WHERE key = 'active_query_id'")
    active_query_row = cursor.fetchone()
    active_query_id = active_query_row[0] if active_query_row else None

    if not active_profile_id or not active_query_id:
        conn.close()
        raise ValueError("No active profile/query found in database")

    # Delete metrics for active profile/query
    cursor.execute(
        "DELETE FROM metrics_data_points WHERE profile_id = ? AND query_id = ?",
        (active_profile_id, active_query_id),
    )
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted, active_profile_id, active_query_id


def main():
    """Command-line interface for clearing metrics."""
    try:
        deleted, profile_id, query_id = clear_active_query_metrics()
        print(f"✓ Deleted {deleted} metric snapshots for {profile_id}/{query_id}.")
        print("Next time you click 'Update Data', metrics will be recalculated.")
        print()
        print("NOTE: This is now automatic during Update Data operation.")
        print("You only need this script for manual cleanup.")
        return 0
    except ValueError as e:
        print(f"Error: {e}")
        print("Please open the app and select a profile/query first.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
