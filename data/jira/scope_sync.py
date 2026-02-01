"""
JIRA scope sync module.

This module handles the main JIRA data synchronization and scope calculation:
- Fetch issues from JIRA (with caching and delta fetch optimization)
- Fetch changelog for Flow/DORA metrics
- Calculate project scope (total issues, story points, velocity)
- Filter DevOps vs Development issues
- Save to unified database structure
- Progress tracking and atomic database operations
"""

import logging
from typing import Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def sync_jira_scope_and_data(
    jql_query: str | None = None,
    ui_config: Dict | None = None,
    force_refresh: bool = False,
) -> Tuple[bool, str, Dict]:
    """
    Main sync function to get JIRA scope calculation and replace CSV data.

    Args:
        jql_query: JQL query to use (overrides config)
        ui_config: UI configuration dictionary (overrides file config)
        force_refresh: If True, bypass cache and force fresh JIRA fetch

    Returns:
        Tuple of (success, message, scope_data)
    """
    # Import TaskProgress at function level to avoid "possibly unbound" errors
    from data.task_progress import TaskProgress
    from data.jira.config import get_jira_config, validate_jira_config
    from data.jira.cache_validator import validate_cache_file
    from data.jira.field_utils import extract_jira_field_id
    from data.jira.main_fetch import fetch_jira_issues
    from data.jira.changelog_fetcher import fetch_changelog_on_demand
    from data.jira.scope_calculator import calculate_jira_project_scope
    from data.jira.data_transformer import jira_to_csv_format
    from data.jira.cache_validator import invalidate_changelog_cache
    from data.persistence import save_jira_data_unified

    try:
        # Update progress to show we're starting
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                0,
                0,
                "Connecting to JIRA...",
            )
        except Exception:
            pass  # Progress update is optional

        # Load configuration with JQL query from settings or use provided UI config
        if ui_config:
            config = ui_config.copy()
            # Ensure jql_query parameter takes precedence if provided
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        # Validate configuration
        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        # Validate cache file
        if not validate_cache_file(max_size_mb=config["cache_max_size_mb"]):
            return False, "Cache file validation failed", {}

        # Calculate current fields that would be requested (MUST match fetch_jira_issues logic)
        base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"
        additional_fields = []

        # Add story points field
        points_field = config.get("story_points_field", "")
        if points_field and isinstance(points_field, str) and points_field.strip():
            additional_fields.append(points_field)

        # Add field mappings for DORA and Flow metrics
        # field_mappings has structure: {"dora": {"field_name": "field_id"}, "flow": {...}}
        # CRITICAL: Strip =Value filter syntax (e.g., "customfield_11309=PROD" -> "customfield_11309")
        field_mappings = config.get("field_mappings", {})
        for category, mappings in field_mappings.items():
            if isinstance(mappings, dict):
                for field_name, field_id in mappings.items():
                    # Extract clean field ID (strips =Value filter, skips changelog syntax)
                    clean_field_id = extract_jira_field_id(field_id)
                    if clean_field_id and clean_field_id not in base_fields:
                        additional_fields.append(clean_field_id)

        # Build final fields string (must match fetch_jira_issues exactly)
        # Sort additional fields to ensure consistent ordering for cache validation
        if additional_fields:
            current_fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
        else:
            current_fields = base_fields

        # SMART CACHING LOGIC
        logger.debug(f"[JIRA] Sync starting: force_refresh={force_refresh}")
        logger.debug(f"[JIRA] JQL: {config['jql_query'][:50]}...")
        logger.debug(f"[JIRA] Fields: {current_fields}")

        # Step 1: Check if force refresh is requested
        if force_refresh:
            logger.debug("[JIRA] Force refresh - bypassing cache and clearing database")

            # CRITICAL: Clear database cache for this query on force refresh
            # This ensures old issues that no longer match the JQL are removed
            try:
                from data.persistence.factory import get_backend
                from data.database import get_db_connection

                backend = get_backend()
                active_profile_id = backend.get_app_state("active_profile_id")
                active_query_id = backend.get_app_state("active_query_id")

                if active_profile_id and active_query_id:
                    # Delete all data for this query ATOMICALLY (single transaction)
                    # This prevents intermediate states where UI reads partial data
                    db_path = getattr(backend, "db_path", Path("profiles/burndown.db"))
                    with get_db_connection(Path(db_path)) as conn:
                        cursor = conn.cursor()

                        # Execute all deletions in one transaction
                        cursor.execute(
                            "DELETE FROM jira_issues WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        deleted_count = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        stats_deleted = cursor.rowcount

                        # Note: jira_cache table removed - cache metadata derived from jira_issues

                        cursor.execute(
                            "DELETE FROM jira_changelog_entries WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        changelog_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM metrics_data_points WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        metrics_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM project_scope WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        scope_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM task_progress WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        task_deleted = cursor.rowcount

                        # Single commit for all deletions (atomic operation)
                        conn.commit()

                        logger.info(
                            f"[JIRA] Force refresh atomically deleted: {deleted_count} issues, "
                            f"{stats_deleted} statistics, "
                            f"{changelog_deleted} changelog entries, {metrics_deleted} metrics, "
                            f"{scope_deleted} scope, {task_deleted} tasks from database"
                        )

            except Exception as e:
                logger.warning(f"[JIRA] Failed to clear database cache: {e}")

        # Step 2: Fetch from JIRA (includes built-in delta fetch optimization)
        # fetch_jira_issues() handles all caching logic internally:
        # - Loads cache and checks if data changed
        # - Does delta fetch (fetch only updated issues) if count unchanged
        # - Does full fetch only if cache invalid or delta fetch fails
        logger.debug(
            "[JIRA] Calling fetch_jira_issues (handles cache/delta internally)"
        )

        fetch_success, issues = fetch_jira_issues(config, force_refresh=force_refresh)
        if not fetch_success:
            return False, "Failed to fetch JIRA data", {}

        logger.info(f"[JIRA] Fetch complete: {len(issues)} issues")

        # Update progress: Issues fetched, now starting changelog
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Issues fetched, preparing changelog download...",
            )
        except Exception:
            pass

        from data.persistence.factory import get_backend

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
                logger.info(
                    "[JIRA] Delta fetch found no changes, skipping changelog and scope calculation"
                )
                return (
                    True,
                    "No changes detected - using cached data",
                    {
                        "no_changes": True,
                        "skip_metrics": True,
                    },
                )

        # CRITICAL: Invalidate changelog cache when we fetch from JIRA
        # Changelog must stay in sync with issue cache
        invalidate_changelog_cache()

        # PHASE 2: Changelog data fetch
        # Changelog is needed for Flow Time and DORA metrics
        # No need to delete file cache - using database exclusively

        # Fetch it now so metrics calculation has the data it needs
        # CRITICAL: Get profile/query IDs before calling fetch to avoid race condition
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        logger.info("[JIRA] Fetching changelog data for Flow/DORA metrics...")
        changelog_success, changelog_message = fetch_changelog_on_demand(
            config,
            profile_id=active_profile_id,
            query_id=active_query_id,
            progress_callback=None,
        )
        if changelog_success:
            logger.info(f"[JIRA] Changelog fetch successful: {changelog_message}")
        else:
            logger.warning(
                f"[JIRA] Changelog fetch failed (non-critical): {changelog_message}"
            )

        # Update progress: Changelog done, now calculating scope
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Processing issues and calculating scope...",
            )
        except Exception:
            pass

        # CRITICAL: Filter out DevOps project issues for burndown/velocity/statistics
        # DevOps issues are ONLY used for DORA metrics metadata extraction
        devops_projects = config.get("devops_projects", [])
        if devops_projects:
            from data.project_filter import filter_development_issues

            total_issues_count = len(issues)
            issues_for_metrics = filter_development_issues(issues, devops_projects)
            filtered_count = total_issues_count - len(issues_for_metrics)

            if filtered_count > 0:
                logger.info(
                    f"[JIRA] Filtered {filtered_count} DevOps issues, using {len(issues_for_metrics)} dev issues"
                )
        else:
            # No DevOps projects configured, use all issues
            issues_for_metrics = issues

        # Calculate JIRA-based project scope (using ONLY development project issues)
        # Only use story_points_field if it's configured and not empty
        points_field_raw = config.get("story_points_field", "")
        # Defensive: Ensure points_field is a string, not a dict
        if isinstance(points_field_raw, dict):
            logger.warning(
                f"[JIRA] story_points_field is a dict, using empty string: {points_field_raw}"
            )
            points_field = ""
        elif isinstance(points_field_raw, str):
            points_field = points_field_raw.strip()
        else:
            logger.warning(
                f"[JIRA] story_points_field has unexpected type {type(points_field_raw)}, using empty string"
            )
            points_field = ""

        if not points_field:
            # When no points field is configured, pass empty string instead of defaulting to "votes"
            points_field = ""
        scope_data = calculate_jira_project_scope(
            issues_for_metrics, points_field, config
        )
        if not scope_data:
            return False, "Failed to calculate JIRA project scope", {}

        # Transform to CSV format for statistics (using ONLY development project issues)
        csv_data = jira_to_csv_format(issues_for_metrics, config)
        # Note: Empty list is valid when there are no issues, only None indicates error

        # Update progress: Scope calculated, now saving to database
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Saving data to database...",
            )
        except Exception:
            pass

        # Save both statistics and project scope to unified data structure
        if save_jira_data_unified(csv_data, scope_data, config):
            logger.info("[JIRA] Scope calculation and data sync completed successfully")
            return (
                True,
                "JIRA sync and scope calculation completed successfully",
                scope_data,
            )
        else:
            return False, "Failed to save JIRA data to unified structure", {}

    except Exception as e:
        logger.error(f"[JIRA] Error in scope sync: {e}")
        return False, f"JIRA scope sync failed: {e}", {}


def sync_jira_data(
    jql_query: str | None = None, ui_config: Dict | None = None
) -> Tuple[bool, str]:
    """Legacy sync function - calls new scope sync and returns just success/message."""
    try:
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)
        return success, message
    except Exception as e:
        logger.error(f"[JIRA] Error in data sync: {e}")
        return False, f"JIRA sync failed: {e}"
