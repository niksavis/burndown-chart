"""
JSON-to-SQLite migration orchestrator.

Handles automatic migration from legacy JSON file structure to normalized SQLite database.
Runs once on first app launch when JSON profiles exist but database doesn't.

Migration Flow:
1. Detect migration needed (JSON exists, SQLite doesn't or not migrated)
2. Create backup of profiles/ directory
3. Initialize SQLite schema
4. Migrate each profile:
   - Profile configuration → profiles table
   - Queries → queries table
   - JIRA cache → jira_issues + jira_changelog_entries tables
   - Project data → project_statistics + project_scope tables
   - Metrics snapshots → metrics_data_points table
5. Validate migration (compare record counts)
6. Mark migration complete in app_state
7. Cleanup old backups (keep 5 most recent)

Usage:
    from data.migration.migrator import run_migration_if_needed

    # At app startup
    run_migration_if_needed()
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from data.migration.backup import create_backup, restore_backup
from data.migration.schema_manager import initialize_schema, verify_schema
from data.persistence import PersistenceBackend
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)

DEFAULT_PROFILES_PATH = Path("profiles")
DEFAULT_DB_PATH = Path("profiles/burndown.db")


def is_migration_needed() -> bool:
    """
    Check if migration from JSON to SQLite is needed.

    Returns:
        bool: True if migration needed, False otherwise

    Conditions for migration:
    - Legacy JSON profiles exist (profiles/{id}/profile.json)
    - Database doesn't exist OR migration_complete flag not set

    Example:
        >>> from data.migration.migrator import is_migration_needed
        >>> if is_migration_needed():
        ...     print("Migration required")
    """
    # Check if JSON profiles exist
    json_profiles = list(DEFAULT_PROFILES_PATH.glob("*/profile.json"))
    if not json_profiles:
        logger.info("No JSON profiles found - migration not needed")
        return False

    # Check if database exists
    if not DEFAULT_DB_PATH.exists():
        logger.info("Database doesn't exist but JSON profiles found - migration needed")
        return True

    # Check migration_complete flag
    try:
        backend = get_backend("sqlite", str(DEFAULT_DB_PATH))
        migration_status = backend.get_app_state("migration_complete")

        if migration_status == "true":
            logger.info("Migration already complete")
            return False
        else:
            logger.info("Database exists but migration not complete - migration needed")
            return True

    except Exception as e:
        logger.warning(
            f"Failed to check migration status: {e} - assuming migration needed"
        )
        return True


def migrate_profile(
    profile_id: str,
    sqlite_backend: PersistenceBackend,
) -> dict[str, int]:
    """
    Migrate single profile from JSON to SQLite.

    Args:
        profile_id: Profile identifier
        sqlite_backend: Target SQLite backend

    Returns:
        dict: Migration statistics (profiles, queries, issues, etc.)

    Raises:
        ValueError: If profile migration fails

    Example:
        >>> stats = migrate_profile("kafka", sqlite_backend)
        >>> print(f"Migrated {stats['issues']} issues")
    """
    logger.info(f"Migrating profile: {profile_id}")

    stats = {
        "profiles": 0,
        "queries": 0,
        "issues": 0,
        "changelog_entries": 0,
        "statistics": 0,
        "scope": 0,
        "metrics": 0,
    }

    try:
        import json
        from datetime import datetime, timedelta
        from pathlib import Path

        json_base = Path("profiles") / profile_id

        # Step 1: Migrate profile configuration
        profile_json_path = json_base / "profile.json"
        if profile_json_path.exists():
            with open(profile_json_path, encoding="utf-8") as f:
                profile_data = json.load(f)

            # Extract JIRA config - handle both old and new formats
            jira_config = profile_data.get("jira_config", {})
            if not jira_config:
                # Fallback to old format if jira_config doesn't exist
                jira_config = {
                    "base_url": profile_data.get("jira_url", ""),
                    "token": profile_data.get("jira_token", ""),
                    "configured": profile_data.get("jira_configured", False),
                }

            # Extract profile fields - match SQLiteBackend schema exactly
            profile_record = {
                "id": profile_id,
                "name": profile_data.get("name", profile_id),
                "description": profile_data.get("description", ""),
                "created_at": profile_data.get(
                    "created_at", datetime.now().isoformat()
                ),
                "last_used": profile_data.get("last_used", datetime.now().isoformat()),
                # Direct fields matching schema
                "jira_config": jira_config,
                "field_mappings": profile_data.get("field_mappings", {}),
                "forecast_settings": profile_data.get("forecast_settings", {}),
                "project_classification": profile_data.get(
                    "project_classification", {}
                ),
                "flow_type_mappings": profile_data.get("flow_type_mappings", {}),
                # Convert boolean flags (might be stored as lists from Dash components)
                "show_milestone": (
                    bool(profile_data.get("show_milestone"))
                    if not isinstance(profile_data.get("show_milestone"), list)
                    else len(profile_data.get("show_milestone", [])) > 0
                ),
                "show_points": (
                    bool(profile_data.get("show_points", True))
                    if not isinstance(profile_data.get("show_points"), list)
                    else len(profile_data.get("show_points", [])) > 0
                ),
            }

            sqlite_backend.save_profile(profile_record)
            stats["profiles"] = 1
            logger.info(f"Migrated profile: {profile_id}")

        # Step 2: Migrate queries
        queries_dir = json_base / "queries"
        if queries_dir.exists():
            for query_dir in queries_dir.iterdir():
                if not query_dir.is_dir():
                    continue

                query_id = query_dir.name
                query_json_path = query_dir / "query.json"

                # Read query metadata
                if query_json_path.exists():
                    with open(query_json_path, encoding="utf-8") as f:
                        query_data = json.load(f)
                else:
                    query_data = {"name": query_id.replace("_", " ").title()}

                query_record = {
                    "id": query_id,
                    "profile_id": profile_id,
                    "name": query_data.get("name", query_id),
                    "jql": query_data.get("jql", ""),
                    "created_at": query_data.get(
                        "created_at", datetime.now().isoformat()
                    ),
                    "last_used": query_data.get(
                        "last_used", datetime.now().isoformat()
                    ),
                }

                sqlite_backend.save_query(profile_id, query_record)
                stats["queries"] += 1

                # Step 3: Migrate JIRA cache (issues)
                jira_cache_path = query_dir / "jira_cache.json"
                if jira_cache_path.exists():
                    try:
                        with open(jira_cache_path, encoding="utf-8") as f:
                            cache_data = json.load(f)

                        issues = cache_data.get("issues", [])
                        if issues:
                            # Set default expiry to 30 days from now (migration)
                            expires_at = datetime.now() + timedelta(days=30)
                            cache_key = f"migrated_{query_id}"

                            sqlite_backend.save_issues_batch(
                                profile_id, query_id, cache_key, issues, expires_at
                            )
                            stats["issues"] += len(issues)
                            logger.info(
                                f"Migrated {len(issues)} issues for {profile_id}/{query_id}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate JIRA cache for {profile_id}/{query_id}: {e}"
                        )

                # Step 4: Migrate project data (statistics + scope)
                project_data_path = query_dir / "project_data.json"
                if project_data_path.exists():
                    try:
                        with open(project_data_path, encoding="utf-8") as f:
                            project_data = json.load(f)

                        # Migrate statistics
                        if "statistics" in project_data and isinstance(
                            project_data["statistics"], list
                        ):
                            sqlite_backend.save_statistics_batch(
                                profile_id, query_id, project_data["statistics"]
                            )
                            stats["statistics"] += len(project_data["statistics"])

                        # Migrate scope - check both "project_scope" (v2.0) and "scope" (legacy)
                        scope_data = project_data.get(
                            "project_scope"
                        ) or project_data.get("scope")
                        if scope_data:
                            sqlite_backend.save_scope(profile_id, query_id, scope_data)
                            stats["scope"] += 1

                        logger.info(
                            f"Migrated project data for {profile_id}/{query_id}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate project data for {profile_id}/{query_id}: {e}"
                        )

                # Step 5: Migrate metrics snapshots (DORA/Flow metrics)
                metrics_path = query_dir / "metrics_snapshots.json"
                logger.info(
                    f"Checking for metrics file: {metrics_path}, exists={metrics_path.exists()}"
                )
                if metrics_path.exists():
                    try:
                        logger.info(f"Loading metrics from {metrics_path}")
                        with open(metrics_path, encoding="utf-8") as f:
                            metrics_snapshots = json.load(f)

                        logger.info(
                            f"Loaded {len(metrics_snapshots)} weeks of metrics from file"
                        )

                        if metrics_snapshots:
                            # Process each week's metrics
                            for week_label, week_metrics in metrics_snapshots.items():
                                # Keep ISO week label format (e.g., "2025-W42")
                                # This matches what load_snapshots() expects
                                snapshot_date = week_label

                                # Build metric list for batch save
                                metric_list = []

                                # Process each metric
                                for metric_name, metric_data in week_metrics.items():
                                    # Skip non-metric entries like "trends"
                                    if metric_name == "trends" or not isinstance(
                                        metric_data, dict
                                    ):
                                        continue

                                    # Extract primary value for metric_value column
                                    metric_value = None

                                    if isinstance(metric_data, dict):
                                        # Try common value field names in order of preference
                                        value_fields = [
                                            "value",  # Generic
                                            "completed_count",  # Flow velocity, Flow time
                                            "deployment_count",  # DORA deployment frequency
                                            "median_days",  # Flow time
                                            "median_hours",  # Lead time, MTTR
                                            "avg_days",  # Flow time
                                            "wip_count",  # Flow load
                                            "change_failure_rate_percent",  # CFR
                                            "overall_pct",  # Flow efficiency
                                        ]

                                        for field in value_fields:
                                            if field in metric_data and isinstance(
                                                metric_data[field], (int, float)
                                            ):
                                                metric_value = metric_data[field]
                                                break

                                        # If still no value, use 0.0
                                        if metric_value is None:
                                            metric_value = 0.0

                                    # Determine metric category
                                    if (
                                        "dora" in metric_name.lower()
                                        or "deployment" in metric_name.lower()
                                        or "lead_time" in metric_name.lower()
                                        or "change_failure" in metric_name.lower()
                                        or "mttr" in metric_name.lower()
                                    ):
                                        metric_category = "dora"
                                    elif "flow" in metric_name.lower():
                                        metric_category = "flow"
                                    else:
                                        metric_category = "custom"

                                    # Create metric record with FULL original data in calculation_metadata
                                    metric_record = {
                                        "snapshot_date": snapshot_date,
                                        "metric_category": metric_category,
                                        "metric_name": metric_name,
                                        "metric_value": metric_value,
                                        "metric_unit": metric_data.get("unit", ""),
                                        "excluded_issue_count": 0,
                                        "calculation_metadata": metric_data,  # Store FULL dict
                                    }

                                    metric_list.append(metric_record)

                                # Batch save all metrics for this week
                                if metric_list:
                                    sqlite_backend.save_metrics_batch(
                                        profile_id, query_id, metric_list
                                    )
                                    stats["metrics"] = stats.get("metrics", 0) + len(
                                        metric_list
                                    )

                            logger.info(
                                f"Migrated {stats.get('metrics', 0)} metrics for {profile_id}/{query_id}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate metrics for {profile_id}/{query_id}: {e}"
                        )

        logger.info(f"Profile {profile_id} migration complete: {stats}")

    except Exception as e:
        logger.error(f"Profile migration failed for {profile_id}: {e}")
        raise ValueError(f"Failed to migrate profile {profile_id}: {e}") from e

    return stats


def run_migration_if_needed(
    profiles_path: Path = DEFAULT_PROFILES_PATH,
    db_path: Path = DEFAULT_DB_PATH,
    skip_backup: bool = False,
) -> bool:
    """
    Orchestrate migration from JSON to SQLite if needed.

    Safe to call multiple times - checks if migration needed first.
    Creates backup before migration, validates after, marks complete.

    Args:
        profiles_path: Path to profiles directory
        db_path: Path to target database
        skip_backup: If True, skip backup creation (for testing only)

    Returns:
        bool: True if migration completed (or already done), False if failed

    Example:
        >>> from data.migration.migrator import run_migration_if_needed
        >>> if run_migration_if_needed():
        ...     print("Migration successful")
    """
    logger.info("Checking if migration needed")

    # Check if migration needed
    if not is_migration_needed():
        # Even if no migration needed, ensure schema exists for fresh installations
        if not db_path.exists():
            logger.info("Fresh installation detected - initializing empty database")
            try:
                initialize_schema(db_path)
                logger.info("Database schema initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize schema: {e}", exc_info=True)
                return False
        return True

    logger.info("Starting JSON to SQLite migration")
    start_time = datetime.now()

    backup_path = None

    try:
        # Step 1: Create backup
        if not skip_backup:
            backup_path = create_backup(profiles_path)
            logger.info(f"Backup created at {backup_path}")

        # Step 2: Initialize schema
        logger.info("Initializing database schema")
        initialize_schema(db_path)

        if not verify_schema(db_path):
            raise ValueError("Schema verification failed after initialization")

        # Step 3: Migrate all profiles
        sqlite_backend = get_backend("sqlite", str(db_path))

        # Find all JSON profile directories
        profile_dirs = [
            d
            for d in profiles_path.iterdir()
            if d.is_dir() and (d / "profile.json").exists()
        ]

        total_stats = {
            "profiles": 0,
            "queries": 0,
            "issues": 0,
            "changelog_entries": 0,
            "statistics": 0,
            "scope": 0,
            "metrics": 0,
        }

        # Migrate each profile
        for profile_dir in profile_dirs:
            profile_id = profile_dir.name
            logger.info(f"Migrating profile: {profile_id}")

            try:
                profile_stats = migrate_profile(profile_id, sqlite_backend)

                # Accumulate stats
                for key, value in profile_stats.items():
                    total_stats[key] = total_stats.get(key, 0) + value

            except Exception as e:
                logger.error(f"Failed to migrate profile {profile_id}: {e}")
                raise  # Fail fast - don't continue if any profile fails

        logger.info(f"Migration stats: {total_stats}")

        # Step 4: Migrate app_state and ensure active profile/query are set
        app_state_path = profiles_path / "profiles.json"
        if app_state_path.exists():
            with open(app_state_path, encoding="utf-8") as f:
                app_state_data = json.load(f)

            # Save app state to database
            for key, value in app_state_data.items():
                sqlite_backend.set_app_state(key, str(value))

        # Ensure active profile/query are set (if profiles exist)
        active_profile = sqlite_backend.get_app_state("active_profile_id")
        if not active_profile and profile_dirs:
            # Set first profile as active
            first_profile_id = profile_dirs[0].name
            sqlite_backend.set_app_state("active_profile_id", first_profile_id)
            logger.info(f"Set active_profile_id to {first_profile_id}")

            # Set first query as active
            first_profile_queries = sqlite_backend.list_queries(first_profile_id)
            if first_profile_queries:
                first_query_id = first_profile_queries[0]["id"]
                sqlite_backend.set_app_state("active_query_id", first_query_id)
                logger.info(f"Set active_query_id to {first_query_id}")

        # Step 5: Validate migration
        from data.migration.validator import validate_all_profiles

        is_valid, validation_report = validate_all_profiles(profiles_path, db_path)

        if not is_valid:
            logger.error(f"Migration validation failed: {validation_report}")
            raise ValueError(
                "Migration validation failed - data integrity issues detected"
            )

        logger.info("Migration validation passed")

        # Step 5: Mark migration complete
        sqlite_backend.set_app_state("migration_complete", "true")
        sqlite_backend.set_app_state("migration_timestamp", datetime.now().isoformat())

        # Step 6: Clean up JSON files (data is now in database and backed up)
        logger.info("Cleaning up legacy JSON files after successful migration")
        cleanup_json_files(profiles_path)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Migration completed successfully",
            extra={
                "duration_seconds": duration,
                "backup_path": str(backup_path) if backup_path else None,
            },
        )

        return True

    except Exception as e:
        logger.error(
            f"Migration failed: {e}",
            extra={"error_type": type(e).__name__},
        )

        # Attempt rollback if backup exists
        if backup_path and backup_path.exists():
            logger.warning("Attempting rollback from backup")
            try:
                restore_backup(backup_path, profiles_path)
                logger.info("Rollback successful")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")

        return False


def rollback_migration(
    backup_path: Path,
    profiles_path: Path = DEFAULT_PROFILES_PATH,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """
    Rollback failed migration.

    Restores profiles from backup and removes database.

    Args:
        backup_path: Path to backup to restore from
        profiles_path: Target profiles directory
        db_path: Database file to remove

    Raises:
        IOError: If rollback fails

    Example:
        >>> from data.migration.migrator import rollback_migration
        >>> rollback_migration(Path("backups/migration-20251229-143045"))
    """
    logger.warning(f"Rolling back migration from {backup_path}")

    try:
        # Restore profiles from backup
        restore_backup(backup_path, profiles_path)

        # Remove database file
        if db_path.exists():
            logger.info(f"Removing database {db_path}")
            db_path.unlink()

        logger.info("Migration rollback completed")

    except Exception as e:
        logger.error(f"Rollback failed: {e}", extra={"error_type": type(e).__name__})
        raise OSError(f"Migration rollback failed: {e}") from e


def cleanup_json_files(profiles_path: Path = DEFAULT_PROFILES_PATH) -> None:
    """
    Clean up legacy JSON files after successful migration.

    Removes all profile directories and JSON files, keeping only:
    - burndown.db (database file)
    - burndown.db-shm (database shared memory)
    - burndown.db-wal (database write-ahead log)

    All JSON data is already backed up in backups/migration-{timestamp}/ directory.

    Args:
        profiles_path: Path to profiles directory to clean

    Example:
        >>> from data.migration.migrator import cleanup_json_files
        >>> cleanup_json_files(Path("profiles"))
    """
    logger.info(f"Starting cleanup of legacy JSON files in {profiles_path}")

    if not profiles_path.exists():
        logger.warning(
            f"Profiles path {profiles_path} does not exist - nothing to clean"
        )
        return

    try:
        import shutil

        removed_count = 0
        skipped_count = 0

        # Iterate through profiles directory
        for item in profiles_path.iterdir():
            # Keep database files
            if item.name in ["burndown.db", "burndown.db-shm", "burndown.db-wal"]:
                logger.info(f"Keeping database file: {item.name}")
                skipped_count += 1
                continue

            # Remove profile directories (p_*/
            if item.is_dir() and item.name.startswith("p_"):
                logger.info(f"Removing profile directory: {item.name}")
                shutil.rmtree(item)
                removed_count += 1
                continue

            # Remove JSON files (profiles.json, etc.)
            if item.is_file() and item.suffix == ".json":
                logger.info(f"Removing JSON file: {item.name}")
                item.unlink()
                removed_count += 1
                continue

            # Log any other files/directories (shouldn't normally exist)
            logger.debug(f"Skipping unknown item: {item.name}")
            skipped_count += 1

        logger.info(
            f"Cleanup complete: removed {removed_count} items, kept {skipped_count} database files"
        )

    except Exception as e:
        logger.error(
            f"Cleanup failed: {e}",
            extra={"error_type": type(e).__name__, "profiles_path": str(profiles_path)},
        )
        # Don't raise - cleanup failure shouldn't fail the entire migration
        # Data is still in database and backed up, just extra files remain
