import hashlib
import json
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from data.database import get_db_connection
from data.exceptions import ConfigurationError, JiraError, PersistenceError
from data.jira.cache_validator import invalidate_changelog_cache, validate_cache_file
from data.jira.changelog_fetcher import fetch_changelog_on_demand
from data.jira.config import get_jira_config, validate_jira_config
from data.jira.data_transformer import jira_to_csv_format
from data.jira.epic_fetch import fetch_epics_for_display
from data.jira.field_utils import extract_jira_field_id
from data.jira.main_fetch import fetch_jira_issues
from data.jira.parent_filter import filter_out_parent_types
from data.jira.query_builder import (
    build_jql_with_parent_types,
    extract_parent_types_from_config,
)
from data.jira.scope_calculator import calculate_jira_project_scope
from data.parent_filter import filter_parent_issues
from data.project_filter import filter_development_issues
from data.task_progress import TaskProgress

logger = logging.getLogger(__name__)


def get_backend():  # noqa: PLC0415
    from data.persistence.factory import get_backend as _get_backend  # noqa: PLC0415

    return _get_backend()


def load_app_settings():  # noqa: PLC0415
    from data.persistence import load_app_settings as _load  # noqa: PLC0415

    return _load()


def save_jira_data_unified(*args, **kwargs):  # noqa: PLC0415
    from data.persistence import save_jira_data_unified as _save  # noqa: PLC0415

    return _save(*args, **kwargs)


def sync_jira_scope_and_data(
    jql_query: str | None = None,
    ui_config: dict | None = None,
    force_refresh: bool = False,
) -> tuple[bool, str, dict]:

    try:
        logger.warning("=" * 80)
        logger.warning(
            "[SCOPE_SYNC] sync_jira_scope_and_data STARTED - CODE VERSION 2026-02-04"
        )
        logger.warning("=" * 80)

        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                0,
                0,
                "Connecting to JIRA...",
            )
        except AttributeError, RuntimeError, TypeError, ValueError:
            pass

        if ui_config:
            config = ui_config.copy()
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        parent_types = extract_parent_types_from_config(config)
        if parent_types:
            original_jql = config.get("jql_query", "")
            modified_jql = build_jql_with_parent_types(original_jql, parent_types)
            config["jql_query"] = modified_jql
            logger.info(
                f"[Sync] Modified JQL to include {len(parent_types)} parent type(s): "
                f"{', '.join(parent_types)}"
            )

        if not validate_cache_file(max_size_mb=config["cache_max_size_mb"]):
            return False, "Cache file validation failed", {}

        base_fields = (
            "key,summary,project,created,updated,resolutiondate,status,"
            "issuetype,assignee,priority,resolution,labels,components,"
            "fixVersions"
        )

        parent_field = (
            config.get("field_mappings", {}).get("general", {}).get("parent_field")
        )
        if parent_field:
            base_fields += f",{parent_field}"

        additional_fields = []

        points_field = config.get("story_points_field", "")
        if points_field and isinstance(points_field, str) and points_field.strip():
            additional_fields.append(points_field)

        field_mappings = config.get("field_mappings", {})
        for _category, mappings in field_mappings.items():
            if isinstance(mappings, dict):
                for _field_name, field_id in mappings.items():
                    clean_field_id = extract_jira_field_id(field_id)
                    if clean_field_id and clean_field_id not in base_fields:
                        additional_fields.append(clean_field_id)

        if additional_fields:
            current_fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
        else:
            current_fields = base_fields

        logger.debug(f"[JIRA] Sync starting: force_refresh={force_refresh}")
        logger.debug(f"[JIRA] JQL: {config['jql_query'][:50]}...")
        logger.debug(f"[JIRA] Fields: {current_fields}")

        if force_refresh:
            logger.debug("[JIRA] Force refresh - bypassing cache and clearing database")

            try:
                backend = get_backend()
                active_profile_id = backend.get_app_state("active_profile_id")
                active_query_id = backend.get_app_state("active_query_id")

                if active_profile_id and active_query_id:
                    db_path = getattr(backend, "db_path", Path("profiles/burndown.db"))
                    with get_db_connection(Path(db_path)) as conn:
                        cursor = conn.cursor()

                        cursor.execute(
                            "DELETE FROM jira_issues "
                            "WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        deleted_count = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM project_statistics "
                            "WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        stats_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM jira_changelog_entries "
                            "WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        changelog_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM metrics_data_points "
                            "WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        metrics_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM project_scope "
                            "WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        scope_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM task_progress "
                            "WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        task_deleted = cursor.rowcount

                        conn.commit()

                        logger.info(
                            "[JIRA] Force refresh atomically deleted: "
                            f"{deleted_count} issues, "
                            f"{stats_deleted} statistics, "
                            f"{changelog_deleted} changelog entries, "
                            f"{metrics_deleted} metrics, "
                            f"{scope_deleted} scope, {task_deleted} tasks from database"
                        )

            except (
                OSError,
                PersistenceError,
                sqlite3.Error,
                TypeError,
                ValueError,
            ) as e:
                logger.warning(f"[JIRA] Failed to clear database cache: {e}")

        logger.debug(
            "[JIRA] Calling fetch_jira_issues (handles cache/delta internally)"
        )

        fetch_success, issues = fetch_jira_issues(config, force_refresh=force_refresh)
        if not fetch_success:
            return False, "Failed to fetch JIRA data", {}

        logger.info(f"[JIRA] Fetch complete: {len(issues)} issues")

        try:
            logger.info("[PARENT] Starting parent fetch...")
            parent_types = extract_parent_types_from_config(config)

            if not parent_types:
                logger.info(
                    "[PARENT] Calling fetch_epics_for_display "
                    f"(legacy) with {len(issues)} issues"
                )
                parents = fetch_epics_for_display(issues, config)
                if parents:
                    logger.info(
                        f"[PARENT] Fetched {len(parents)} parent issues "
                        "for display (legacy path)"
                    )
                    issues.extend(parents)
                    logger.info(
                        f"[PARENT] Extended issues list to {len(issues)} "
                        f"total (includes {len(parents)} parents)"
                    )
                else:
                    logger.info("[PARENT] No parent issues to fetch (legacy)")
            else:
                logger.info(
                    "[PARENT] Skipping separate parent fetch - "
                    f"{len(parent_types)} parent "
                    f"type(s) already included in main query: {', '.join(parent_types)}"
                )
        except (
            ImportError,
            JiraError,
            KeyError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as e:
            logger.error(
                f"[PARENT] Failed to fetch parent issues (non-fatal): {e}",
                exc_info=True,
            )

        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Issues fetched, preparing changelog download...",
            )
        except AttributeError, RuntimeError, TypeError, ValueError:
            pass

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")
        last_delta_key = None
        if active_profile_id and active_query_id:
            last_delta_key = (
                f"last_delta_changed_count:{active_profile_id}:{active_query_id}"
            )

        if not force_refresh and last_delta_key:
            last_delta_count = backend.get_app_state(last_delta_key)
            if last_delta_count == "0":
                current_settings = load_app_settings()
                relevant_settings = {
                    "development_projects": current_settings.get(
                        "development_projects", []
                    ),
                    "devops_projects": current_settings.get("devops_projects", []),
                    "field_mappings": current_settings.get("field_mappings", {}),
                    "flow_type_mappings": current_settings.get(
                        "flow_type_mappings", {}
                    ),
                    "devops_task_types": current_settings.get("devops_task_types", []),
                    "bug_types": current_settings.get("bug_types", []),
                    "story_types": current_settings.get("story_types", []),
                    "task_types": current_settings.get("task_types", []),
                    "flow_start_statuses": current_settings.get(
                        "flow_start_statuses", []
                    ),
                    "wip_statuses": current_settings.get("wip_statuses", []),
                    "flow_end_statuses": current_settings.get("flow_end_statuses", []),
                    "active_statuses": current_settings.get("active_statuses", []),
                    "production_environment_values": current_settings.get(
                        "production_environment_values", []
                    ),
                    "affected_environment_values": current_settings.get(
                        "affected_environment_values", []
                    ),
                    "target_environment_values": current_settings.get(
                        "target_environment_values", []
                    ),
                }
                current_hash = hashlib.md5(  # nosec B324 — non-crypto cache key
                    json.dumps(relevant_settings, sort_keys=True).encode(),
                    usedforsecurity=False,
                ).hexdigest()

                settings_hash_key = (
                    f"settings_hash:{active_profile_id}:{active_query_id}"
                )
                last_hash = backend.get_app_state(settings_hash_key)

                if last_hash and last_hash == current_hash:
                    logger.info(
                        "[JIRA] Delta fetch found no changes and "
                        "settings unchanged, skipping metrics"
                    )
                    return (
                        True,
                        "No changes detected - using cached data",
                        {
                            "no_changes": True,
                            "skip_metrics": True,
                        },
                    )
                else:
                    logger.info(
                        "[JIRA] No new data but settings changed - "
                        "will recalculate metrics"
                    )
                    backend.set_app_state(settings_hash_key, current_hash)

        invalidate_changelog_cache()

        logger.info("[JIRA] Saving issues to database before changelog fetch...")

        try:
            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")

            if active_profile_id and active_query_id:
                utc_now = datetime.now(UTC)
                expires_at = utc_now + timedelta(hours=24)
                cache_key = f"issues:{active_profile_id}:{active_query_id}"

                backend.save_issues_batch(
                    profile_id=active_profile_id,
                    query_id=active_query_id,
                    cache_key=cache_key,
                    issues=issues,
                    expires_at=expires_at,
                )
                logger.info(
                    f"[JIRA] Saved {len(issues)} issues to database "
                    "before changelog fetch"
                )
            else:
                logger.warning("[JIRA] No active profile/query, cannot save issues")
        except (
            OSError,
            PersistenceError,
            sqlite3.Error,
            TypeError,
            ValueError,
        ) as e:
            logger.error(
                f"[JIRA] Failed to save issues before changelog fetch: {e}",
                exc_info=True,
            )

        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        issue_keys = []
        delta_keys_key = None
        if active_profile_id and active_query_id:
            delta_keys_key = (
                f"last_delta_changed_keys:{active_profile_id}:{active_query_id}"
            )
        if delta_keys_key:
            try:
                delta_keys_raw = backend.get_app_state(delta_keys_key) or "[]"
                parsed_keys = json.loads(delta_keys_raw)
                if isinstance(parsed_keys, list):
                    issue_keys = [str(key) for key in parsed_keys if key]
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"[JIRA] Failed to parse delta keys for changelog refresh: {e}"
                )

        logger.info("[JIRA] Fetching changelog data for Flow/DORA metrics...")
        changelog_success, changelog_message = fetch_changelog_on_demand(
            config,
            profile_id=active_profile_id,
            query_id=active_query_id,
            progress_callback=None,
            issue_keys=issue_keys or None,
        )
        if delta_keys_key:
            backend.set_app_state(delta_keys_key, "[]")
        if changelog_success:
            logger.info(f"[JIRA] Changelog fetch successful: {changelog_message}")
        else:
            logger.warning(
                f"[JIRA] Changelog fetch failed (non-critical): {changelog_message}"
            )

        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Processing issues and calculating scope...",
            )
        except AttributeError, RuntimeError, TypeError, ValueError:
            pass

        parent_field = (
            config.get("field_mappings", {}).get("general", {}).get("parent_field")
        )
        if parent_field:
            issues = filter_parent_issues(issues, parent_field, log_prefix="JIRA SYNC")

        development_projects = config.get("development_projects", [])
        devops_projects = config.get("devops_projects", [])

        logger.info(
            "[JIRA] Project filtering config: "
            f"development={development_projects or 'NONE'}, "
            f"devops={devops_projects or 'NONE'}"
        )

        if development_projects or devops_projects:
            total_issues_count = len(issues)
            issues_for_metrics = filter_development_issues(
                issues, development_projects, devops_projects
            )
            filtered_count = total_issues_count - len(issues_for_metrics)

            if filtered_count > 0:
                logger.info(
                    f"[JIRA] Filtered to {len(issues_for_metrics)} "
                    "development project issues "
                    f"(excluded {filtered_count})"
                )
            else:
                logger.info(
                    f"[JIRA] No issues filtered - all "
                    f"{len(issues_for_metrics)} issues match "
                    "development projects"
                )
        else:
            logger.warning(
                "[JIRA] NO PROJECT FILTERING: "
                f"Using all {len(issues)} issues "
                "(configure development_projects "
                "in JIRA Mappings -> Projects tab)"
            )
            issues_for_metrics = issues

        if parent_types:
            total_before_parent_filter = len(issues_for_metrics)
            issues_for_metrics = filter_out_parent_types(
                issues_for_metrics, parent_types
            )
            parent_filtered_count = total_before_parent_filter - len(issues_for_metrics)

            if parent_filtered_count > 0:
                logger.info(
                    f"[JIRA] Excluded {parent_filtered_count} "
                    "parent issue(s) from metrics "
                    f"(types: {', '.join(parent_types)})"
                )

        points_field_raw = config.get("story_points_field", "")
        if isinstance(points_field_raw, dict):
            logger.warning(
                "[JIRA] story_points_field is a dict, "
                f"using empty string: {points_field_raw}"
            )
            points_field = ""
        elif isinstance(points_field_raw, str):
            points_field = points_field_raw.strip()
        else:
            logger.warning(
                "[JIRA] story_points_field has unexpected type "
                f"{type(points_field_raw)}, using empty string"
            )
            points_field = ""

        if not points_field:
            points_field = ""
        scope_data = calculate_jira_project_scope(
            issues_for_metrics, points_field, config
        )
        if not scope_data:
            return False, "Failed to calculate JIRA project scope", {}

        csv_data = jira_to_csv_format(issues_for_metrics, config)

        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Saving data to database...",
            )
        except AttributeError, RuntimeError, TypeError, ValueError:
            pass

        if save_jira_data_unified(csv_data, scope_data, config):
            logger.info("[JIRA] Scope calculation and data sync completed successfully")
            return (
                True,
                "JIRA sync and scope calculation completed successfully",
                scope_data,
            )
        else:
            return False, "Failed to save JIRA data to unified structure", {}

    except (
        ConfigurationError,
        JiraError,
        KeyError,
        PersistenceError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[JIRA] Error in scope sync: {e}")
        return False, f"JIRA scope sync failed: {e}", {}


def sync_jira_data(
    jql_query: str | None = None, ui_config: dict | None = None
) -> tuple[bool, str]:
    try:
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)
        return success, message
    except (
        ConfigurationError,
        JiraError,
        KeyError,
        PersistenceError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[JIRA] Error in data sync: {e}")
        return False, f"JIRA sync failed: {e}"
