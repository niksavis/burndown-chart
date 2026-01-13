"""Automatic migration manager for JSON to SQLite database.

Handles automatic detection and execution of ALL data migrations on app startup.
Migrates all 7 JSON file types per data-model.md spec.

This module provides a wrapper around the main migrator module for use by callbacks.
"""

import logging
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime as dt

logger = logging.getLogger(__name__)


def check_migration_needed() -> Tuple[bool, Dict[str, int]]:
    """Check if migration is needed by checking for ALL 7 JSON file types.

    Returns:
        Tuple of (needs_migration, file_counts)
        - needs_migration: True if ANY JSON files exist and DB is incomplete
        - file_counts: Dictionary with counts of ALL JSON files found
    """
    profiles_dir = Path("profiles")

    if not profiles_dir.exists():
        return False, {}

    # Count ALL JSON file types per data-model.md spec
    profiles_registry = profiles_dir / "profiles.json"
    profile_files = list(profiles_dir.glob("*/profile.json"))
    query_files = list(profiles_dir.glob("*/queries/*/query.json"))
    cache_files = list(profiles_dir.glob("*/queries/*/jira_cache.json"))
    changelog_files = list(profiles_dir.glob("*/queries/*/jira_changelog_cache.json"))
    project_data_files = list(profiles_dir.glob("*/queries/*/project_data.json"))
    metrics_files = list(profiles_dir.glob("*/queries/*/metrics_snapshots.json"))
    task_progress_file = Path("task_progress.json")

    file_counts = {
        "profiles_registry": 1 if profiles_registry.exists() else 0,
        "profiles": len(profile_files),
        "queries": len(query_files),
        "jira_cache": len(cache_files),
        "changelog": len(changelog_files),
        "project_data": len(project_data_files),
        "metrics": len(metrics_files),
        "task_progress": 1 if task_progress_file.exists() else 0,
    }

    # If no JSON files exist, no migration needed
    if not any(file_counts.values()):
        logger.debug("No JSON files found, migration not needed")
        return False, file_counts

    # Check if database has data for key tables
    try:
        db_path = profiles_dir / "burndown.db"
        if not db_path.exists():
            logger.info("Database does not exist, migration needed")
            return True, file_counts

        from data.persistence.factory import get_backend

        backend = get_backend()

        # Check if ANY table is empty while JSON files exist
        profiles = backend.list_profiles()
        profiles_count = len(profiles)

        queries_count = 0
        issues_count = 0
        metrics_count = 0
        stats_count = 0

        # Count across all profiles
        for profile in profiles:
            profile_queries = backend.list_queries(profile["id"])
            queries_count += len(profile_queries)

            for query in profile_queries:
                # Count issues
                issues = backend.get_issues(profile["id"], query["id"])
                issues_count += len(issues) if issues else 0

                # Count metrics (get all metrics without filtering)
                metrics = backend.get_metric_values(
                    profile["id"], query["id"], limit=10000
                )
                metrics_count += len(metrics) if metrics else 0

                # Count statistics
                stats = backend.get_statistics(profile["id"], query["id"])
                stats_count += len(stats) if stats else 0

        # If ANY critical table is empty but JSON files exist, migration needed
        has_json_data = (
            file_counts["profiles"] > 0
            or file_counts["queries"] > 0
            or file_counts["jira_cache"] > 0
            or file_counts["metrics"] > 0
            or file_counts["project_data"] > 0
        )

        if has_json_data and (
            profiles_count == 0
            or queries_count == 0
            or issues_count == 0
            or metrics_count == 0
            or stats_count == 0
        ):
            logger.info(
                f"Database incomplete but found {sum(file_counts.values())} JSON files - migration needed"
            )
            logger.debug(
                f"DB counts - profiles:{profiles_count}, queries:{queries_count}, "
                f"issues:{issues_count}, metrics:{metrics_count}, stats:{stats_count}"
            )
            return True, file_counts

        logger.debug("Database appears complete, migration not needed")
        return False, file_counts

    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return True, file_counts  # Assume migration needed if check fails


def run_migration() -> Tuple[bool, Dict[str, int], str]:
    """Run the COMPLETE migration process for ALL 7 JSON file types.

    Delegates to the actual migration orchestrator in data.migration.migrator.

    Returns:
        Tuple of (success, counts, message)
        - success: True if migration completed successfully
        - counts: Dictionary with counts of ALL migrated items
        - message: User-friendly status message
    """
    try:
        from data.migration.migrator import run_migration_if_needed

        logger.info("Starting complete migration of ALL JSON data to database")

        # Run the actual migration using the migrator module
        success = run_migration_if_needed()

        if not success:
            return False, {}, "Migration failed"

        # Get statistics from database to report back
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Count migrated items by querying database
        counts = {
            "profiles": 0,
            "queries": 0,
            "issues": 0,
            "changelog": 0,
            "metrics": 0,
            "statistics": 0,
            "scope": 0,
            "task_progress": 0,
        }

        try:
            # Get counts from database
            profiles = backend.list_profiles()
            counts["profiles"] = len(profiles)

            for profile in profiles:
                queries = backend.list_queries(profile["id"])
                counts["queries"] += len(queries)

                for query in queries:
                    # Get issue count
                    issues = backend.get_issues(profile["id"], query["id"])
                    counts["issues"] += len(issues) if issues else 0

                    # Get statistics count
                    stats = backend.get_statistics(profile["id"], query["id"])
                    counts["statistics"] += len(stats) if stats else 0

                    # Get metrics count (get all metrics without filtering)
                    metrics = backend.get_metric_values(
                        profile["id"], query["id"], limit=10000
                    )
                    counts["metrics"] += len(metrics) if metrics else 0

        except Exception as e:
            logger.warning(f"Failed to get migration counts: {e}")

        total_items = sum(counts.values())
        message = f"Successfully migrated {total_items:,} items to database"

        logger.info(f"Migration complete: {counts}")

        return True, counts, message

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False, {}, f"Migration failed: {str(e)}"


def get_migration_status() -> Dict[str, Any]:
    """Get current migration status for UI display.

    Returns:
        Dictionary with migration status information
    """
    needs_migration, file_counts = check_migration_needed()

    return {
        "needs_migration": needs_migration,
        "json_files_found": file_counts,
        "total_json_files": sum(file_counts.values()),
    }


def cleanup_json_files_after_migration() -> bool:
    """Clean up ALL JSON data files after successful migration.

    Creates a timestamped backup, then removes ALL migrated JSON files:
    - profiles.json (registry)
    - profiles/*/profile.json (profile config)
    - profiles/*/queries/ directories (all query data)
    - task_progress.json (root level)

    Keeps only: burndown.db (all data migrated)

    Returns:
        True if cleanup succeeded, False otherwise
    """
    try:
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return True

        # Create backup directory with timestamp
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = profiles_dir.parent / f"profiles_backup_{timestamp}"

        logger.info(f"Creating backup before cleanup: {backup_dir}")

        # Backup entire profiles directory structure
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(profiles_dir, backup_dir)

        # Also backup task_progress.json if it exists
        task_progress_file = Path("task_progress.json")
        if task_progress_file.exists():
            shutil.copy2(task_progress_file, backup_dir / "task_progress.json")

        logger.info(f"Backup created at: {backup_dir}")

        # Now clean up JSON files from profiles directory
        files_deleted = 0
        dirs_deleted = 0

        # 1. Remove profiles.json (registry)
        profiles_json = profiles_dir / "profiles.json"
        if profiles_json.exists():
            profiles_json.unlink()
            files_deleted += 1
            logger.info("Removed profiles.json")

        # 2. Remove profile.json and queries directories from each profile
        for profile_dir in profiles_dir.iterdir():
            if not profile_dir.is_dir() or not profile_dir.name.startswith("p_"):
                continue

            # Remove profile.json
            profile_json = profile_dir / "profile.json"
            if profile_json.exists():
                profile_json.unlink()
                files_deleted += 1
                logger.info(f"Removed {profile_json}")

            # Remove entire queries directory (contains all query data)
            queries_dir = profile_dir / "queries"
            if queries_dir.exists():
                logger.info(f"Removing queries directory: {queries_dir}")
                shutil.rmtree(queries_dir)
                dirs_deleted += 1

        # 3. Remove task_progress.json (root level)
        if task_progress_file.exists():
            task_progress_file.unlink()
            files_deleted += 1
            logger.info("Removed task_progress.json")

        logger.info(
            f"Cleanup complete: removed {files_deleted} JSON files and {dirs_deleted} queries directories"
        )
        logger.info(f"Backup preserved at: {backup_dir}")
        logger.info("All data now in database: profiles/burndown.db")

        return True

    except Exception as e:
        logger.error(f"Error during JSON cleanup: {e}", exc_info=True)
        return False
