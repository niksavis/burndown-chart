import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from data.migration.backup import create_backup, restore_backup
from data.migration.schema_manager import initialize_schema, verify_schema
from data.migration.validator import validate_all_profiles
from data.persistence import PersistenceBackend
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)

DEFAULT_PROFILES_PATH = Path("profiles")
DEFAULT_DB_PATH = Path("profiles/burndown.db")


def is_migration_needed() -> bool:

    json_profiles = list(DEFAULT_PROFILES_PATH.glob("*/profile.json"))
    if not json_profiles:
        logger.info("No JSON profiles found - migration not needed")
        return False

    if not DEFAULT_DB_PATH.exists():
        logger.info("Database doesn't exist but JSON profiles found - migration needed")
        return True

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
        json_base = Path("profiles") / profile_id

        profile_json_path = json_base / "profile.json"
        if profile_json_path.exists():
            with open(profile_json_path, encoding="utf-8") as f:
                profile_data = json.load(f)

            jira_config = profile_data.get("jira_config", {})
            if not jira_config:
                jira_config = {
                    "base_url": profile_data.get("jira_url", ""),
                    "token": profile_data.get("jira_token", ""),
                    "configured": profile_data.get("jira_configured", False),
                }

            profile_record = {
                "id": profile_id,
                "name": profile_data.get("name", profile_id),
                "description": profile_data.get("description", ""),
                "created_at": profile_data.get(
                    "created_at", datetime.now().isoformat()
                ),
                "last_used": profile_data.get("last_used", datetime.now().isoformat()),
                "jira_config": jira_config,
                "field_mappings": profile_data.get("field_mappings", {}),
                "forecast_settings": profile_data.get("forecast_settings", {}),
                "project_classification": profile_data.get(
                    "project_classification", {}
                ),
                "flow_type_mappings": profile_data.get("flow_type_mappings", {}),
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

        queries_dir = json_base / "queries"
        if queries_dir.exists():
            for query_dir in queries_dir.iterdir():
                if not query_dir.is_dir():
                    continue

                query_id = query_dir.name
                query_json_path = query_dir / "query.json"

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

                jira_cache_path = query_dir / "jira_cache.json"
                if jira_cache_path.exists():
                    try:
                        with open(jira_cache_path, encoding="utf-8") as f:
                            cache_data = json.load(f)

                        issues = cache_data.get("issues", [])
                        if issues:
                            expires_at = datetime.now() + timedelta(days=30)
                            cache_key = f"migrated_{query_id}"

                            sqlite_backend.save_issues_batch(
                                profile_id, query_id, cache_key, issues, expires_at
                            )
                            stats["issues"] += len(issues)
                            logger.info(
                                f"Migrated {len(issues)} issues for "
                                f"{profile_id}/{query_id}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate JIRA cache for "
                            f"{profile_id}/{query_id}: {e}"
                        )

                project_data_path = query_dir / "project_data.json"
                if project_data_path.exists():
                    try:
                        with open(project_data_path, encoding="utf-8") as f:
                            project_data = json.load(f)

                        if "statistics" in project_data and isinstance(
                            project_data["statistics"], list
                        ):
                            sqlite_backend.save_statistics_batch(
                                profile_id, query_id, project_data["statistics"]
                            )
                            stats["statistics"] += len(project_data["statistics"])

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
                            f"Failed to migrate project data for "
                            f"{profile_id}/{query_id}: {e}"
                        )

                metrics_path = query_dir / "metrics_snapshots.json"
                logger.info(
                    f"Checking for metrics file: {metrics_path}, "
                    f"exists={metrics_path.exists()}"
                )
                if metrics_path.exists():
                    try:
                        logger.info(f"Loading metrics from {metrics_path}")
                        with open(metrics_path, encoding="utf-8") as f:
                            metrics_snapshots = json.load(f)

                        logger.info(
                            f"Loaded {len(metrics_snapshots)} weeks of "
                            "metrics from file"
                        )

                        if metrics_snapshots:
                            for week_label, week_metrics in metrics_snapshots.items():
                                snapshot_date = week_label

                                metric_list = []

                                for metric_name, metric_data in week_metrics.items():
                                    if metric_name == "trends" or not isinstance(
                                        metric_data, dict
                                    ):
                                        continue

                                    metric_value = None

                                    if isinstance(metric_data, dict):
                                        value_fields = [
                                            "value",
                                            "completed_count",
                                            "deployment_count",
                                            "median_days",
                                            "median_hours",
                                            "avg_days",
                                            "wip_count",
                                            "change_failure_rate_percent",
                                            "overall_pct",
                                        ]

                                        for field in value_fields:
                                            if field in metric_data and isinstance(
                                                metric_data[field], (int, float)
                                            ):
                                                metric_value = metric_data[field]
                                                break

                                        if metric_value is None:
                                            metric_value = 0.0

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

                                    metric_record = {
                                        "snapshot_date": snapshot_date,
                                        "metric_category": metric_category,
                                        "metric_name": metric_name,
                                        "metric_value": metric_value,
                                        "metric_unit": metric_data.get("unit", ""),
                                        "excluded_issue_count": 0,
                                        "calculation_metadata": metric_data,
                                    }

                                    metric_list.append(metric_record)

                                if metric_list:
                                    sqlite_backend.save_metrics_batch(
                                        profile_id, query_id, metric_list
                                    )
                                    stats["metrics"] = stats.get("metrics", 0) + len(
                                        metric_list
                                    )

                            logger.info(
                                f"Migrated {stats.get('metrics', 0)} metrics "
                                f"for {profile_id}/{query_id}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate metrics for "
                            f"{profile_id}/{query_id}: {e}"
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

    logger.info("Checking if migration needed")

    if not is_migration_needed():
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
        if not skip_backup:
            backup_path = create_backup(profiles_path)
            logger.info(f"Backup created at {backup_path}")

        logger.info("Initializing database schema")
        initialize_schema(db_path)

        if not verify_schema(db_path):
            raise ValueError("Schema verification failed after initialization")

        sqlite_backend = get_backend("sqlite", str(db_path))

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

        for profile_dir in profile_dirs:
            profile_id = profile_dir.name
            logger.info(f"Migrating profile: {profile_id}")

            try:
                profile_stats = migrate_profile(profile_id, sqlite_backend)

                for key, value in profile_stats.items():
                    total_stats[key] = total_stats.get(key, 0) + value

            except Exception as e:
                logger.error(f"Failed to migrate profile {profile_id}: {e}")
                raise

        logger.info(f"Migration stats: {total_stats}")

        app_state_path = profiles_path / "profiles.json"
        if app_state_path.exists():
            with open(app_state_path, encoding="utf-8") as f:
                app_state_data = json.load(f)

            for key, value in app_state_data.items():
                sqlite_backend.set_app_state(key, str(value))

        active_profile = sqlite_backend.get_app_state("active_profile_id")
        if not active_profile and profile_dirs:
            first_profile_id = profile_dirs[0].name
            sqlite_backend.set_app_state("active_profile_id", first_profile_id)
            logger.info(f"Set active_profile_id to {first_profile_id}")

            first_profile_queries = sqlite_backend.list_queries(first_profile_id)
            if first_profile_queries:
                first_query_id = first_profile_queries[0]["id"]
                sqlite_backend.set_app_state("active_query_id", first_query_id)
                logger.info(f"Set active_query_id to {first_query_id}")

        is_valid, validation_report = validate_all_profiles(profiles_path, db_path)

        if not is_valid:
            logger.error(f"Migration validation failed: {validation_report}")
            raise ValueError(
                "Migration validation failed - data integrity issues detected"
            )

        logger.info("Migration validation passed")

        sqlite_backend.set_app_state("migration_complete", "true")
        sqlite_backend.set_app_state("migration_timestamp", datetime.now().isoformat())

        logger.info("Cleaning up legacy JSON files after successful migration")
        cleanup_json_files(profiles_path)

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

    logger.warning(f"Rolling back migration from {backup_path}")

    try:
        restore_backup(backup_path, profiles_path)

        if db_path.exists():
            logger.info(f"Removing database {db_path}")
            db_path.unlink()

        logger.info("Migration rollback completed")

    except Exception as e:
        logger.error(f"Rollback failed: {e}", extra={"error_type": type(e).__name__})
        raise OSError(f"Migration rollback failed: {e}") from e


def cleanup_json_files(profiles_path: Path = DEFAULT_PROFILES_PATH) -> None:

    logger.info(f"Starting cleanup of legacy JSON files in {profiles_path}")

    if not profiles_path.exists():
        logger.warning(
            f"Profiles path {profiles_path} does not exist - nothing to clean"
        )
        return

    try:
        import shutil  # noqa: PLC0415

        removed_count = 0
        skipped_count = 0

        for item in profiles_path.iterdir():
            if item.name in ["burndown.db", "burndown.db-shm", "burndown.db-wal"]:
                logger.info(f"Keeping database file: {item.name}")
                skipped_count += 1
                continue

            if item.is_dir() and item.name.startswith("p_"):
                logger.info(f"Removing profile directory: {item.name}")
                shutil.rmtree(item)
                removed_count += 1
                continue

            if item.is_file() and item.suffix == ".json":
                logger.info(f"Removing JSON file: {item.name}")
                item.unlink()
                removed_count += 1
                continue

            logger.debug(f"Skipping unknown item: {item.name}")
            skipped_count += 1

        logger.info(
            f"Cleanup complete: removed {removed_count} items, kept "
            f"{skipped_count} database files"
        )

    except Exception as e:
        logger.error(
            f"Cleanup failed: {e}",
            extra={"error_type": type(e).__name__, "profiles_path": str(profiles_path)},
        )
