"""
JIRA changelog fetching module.

Provides fetch_changelog_on_demand for incremental changelog retrieval
with caching, progress reporting, and resilience features.

For paginated bulk fetching, see data.jira.changelog_pagination.
"""

import logging
from datetime import UTC, datetime, timedelta

from data.exceptions import JiraError, PersistenceError
from data.jira.changelog_pagination import fetch_jira_issues_with_changelog

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ["fetch_changelog_on_demand", "fetch_jira_issues_with_changelog"]


def fetch_changelog_on_demand(
    config: dict,
    profile_id: str | None = None,
    query_id: str | None = None,
    progress_callback=None,
    issue_keys: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Fetch changelog data separately for Flow Time and DORA metrics with incremental
    saving.

    OPTIMIZATION: Only fetches changelog for issues NOT already in cache.
    This dramatically improves performance on subsequent "Update Data" operations.

    RESILIENCE FEATURES:
    - Saves progress after each page (prevents data loss on timeout)
    - Retries failed requests up to 3 times
    - Returns partial results if download incomplete
    - Uses 90-second timeout for large changelog payloads

    Args:
        config: JIRA configuration dictionary with API endpoint, token, etc.
        profile_id: Profile ID to fetch changelog for (if None, reads from app_state)
        query_id: Query ID to fetch changelog for (if None, reads from app_state)
        progress_callback: Optional callback function(message: str) for progress updates
        issue_keys: Optional list of issue keys to refresh even if cached

    Returns:
        Tuple of (success, message)
    """

    logger.info("Fetching changelog for profile/query: %s/%s", profile_id, query_id)

    try:
        logger.info("[JIRA] Fetching changelog data for Flow Time and DORA metrics")
        if progress_callback:
            progress_callback("[Stats] Starting changelog download...")

        # Get active profile and query from database if not provided
        from data.persistence.factory import get_backend

        backend = get_backend()

        if not profile_id:
            profile_id = backend.get_app_state("active_profile_id")
        if not query_id:
            query_id = backend.get_app_state("active_query_id")

        if not profile_id or not query_id:
            logger.error("[Database] No active profile/query - cannot fetch changelog")
            return False, "No active profile/query"

        # Load existing changelog from database to determine what's already cached
        cached_issue_keys = set()
        try:
            existing_entries = backend.get_changelog_entries(
                profile_id=profile_id, query_id=query_id
            )
            # Get unique issue keys from existing entries
            cached_issue_keys = set(
                entry.get("issue_key")
                for entry in existing_entries
                if entry.get("issue_key")
            )
            logger.info(
                f"[Database] Loaded {len(cached_issue_keys)} unique issues with changelog from database"
            )
        except (
            AttributeError,
            PersistenceError,
            TypeError,
            ValueError,
        ) as e:
            logger.warning(f"[Database] Could not load existing changelog: {e}")
            cached_issue_keys = set()

        # Get all issues from database to determine which need changelog fetching
        issues_needing_changelog: list[str] | None = []
        if issue_keys:
            issues_needing_changelog = sorted(set(issue_keys))
            logger.info(
                f"[JIRA] Changelog refresh: targeting {len(issues_needing_changelog)} issues"
            )
            if progress_callback:
                progress_callback(
                    f"Targeted changelog refresh: {len(issues_needing_changelog)} issues"
                )
        else:
            try:
                all_issues = backend.get_issues(
                    profile_id=profile_id, query_id=query_id
                )
                # Database returns flat format with issue_key column
                all_issue_keys: list[str] = [
                    str(issue.get("issue_key"))
                    for issue in all_issues
                    if issue.get("issue_key")
                ]

                # Find issues not in changelog cache
                issues_needing_changelog = [
                    key for key in all_issue_keys if key not in cached_issue_keys
                ]

                logger.info(
                    f"[JIRA] Changelog analysis: {len(all_issue_keys)} total, "
                    f"{len(cached_issue_keys)} cached, {len(issues_needing_changelog)} need fetch"
                )

                if issues_needing_changelog:
                    logger.info(
                        f"[Database] Optimized fetch: Only {len(issues_needing_changelog)} new issues"
                    )
                    if progress_callback:
                        progress_callback(
                            f"Smart fetch: {len(issues_needing_changelog)} new issues "
                            f"({len(cached_issue_keys)} already cached)"
                        )
                else:
                    logger.info(
                        "[Database] All issues have changelog cached, skipping fetch"
                    )
                    if progress_callback:
                        progress_callback(
                            f"[OK] All {len(cached_issue_keys)} issues already cached - skipping download"
                        )
                    return (
                        True,
                        f"[OK] Changelog already cached for all {len(cached_issue_keys)} issues",
                    )

            except (
                AttributeError,
                PersistenceError,
                TypeError,
                ValueError,
            ) as e:
                logger.warning(
                    "[Database] Could not analyze issues from database: "
                    f"{e}, fetching all changelog"
                )
                issues_needing_changelog = None

        # Fetch changelog (only for issues not in cache if we have the list)
        changelog_fetch_success, issues_with_changelog = (
            fetch_jira_issues_with_changelog(
                config,
                issue_keys=issues_needing_changelog,  # Only fetch missing issues
                progress_callback=progress_callback,
            )
        )

        if changelog_fetch_success:
            # CRITICAL OPTIMIZATION: Filter changelog to ONLY status transitions
            # This dramatically reduces cache file size (from 1M+ lines to ~50K)
            try:
                total_histories_before = 0
                total_histories_after = 0
                issues_processed = 0
                # Collect entries for batch database insert
                changelog_entries_batch = []

                for issue in issues_with_changelog:
                    issue_key = issue.get("key", "")
                    if not issue_key:
                        continue

                    changelog_full = issue.get("changelog", {})
                    histories = changelog_full.get("histories", [])
                    total_histories_before += len(histories)

                    # Filter to ONLY histories that contain tracked field changes
                    # TRACKED FIELDS: status (for Flow metrics), sprint field ID (for
                    # Sprint Tracker)
                    # Note: Sprint is a custom field (typically customfield_10020) that
                    # varies by instance
                    tracked_fields = ["status"]  # Always track status

                    # Add sprint field if detected (from field mappings)
                    # CRITICAL: JIRA uses field display name in changelog, not custom
                    # field ID
                    # E.g., changelog has "Sprint", not "customfield_10005"
                    sprint_field_id = (
                        config.get("field_mappings", {})
                        .get("general", {})
                        .get("sprint_field")
                    )
                    if sprint_field_id:
                        tracked_fields.append(
                            sprint_field_id
                        )  # Track custom field ID (for fallback)
                        tracked_fields.append(
                            "Sprint"
                        )  # Track display name (JIRA default)
                        logger.info(
                            f"[JIRA] Tracking sprint field: "
                            f"{sprint_field_id} and 'Sprint'"
                        )

                    # DEBUG: Log unique field names from first issue to diagnose sprint
                    # field mismatch
                    if issues_processed == 0 and histories:
                        unique_fields = set()
                        for hist in histories[:5]:  # Check first 5 histories
                            for item in hist.get("items", []):
                                unique_fields.add(item.get("field"))
                        logger.info(
                            f"[JIRA] Sample changelog field names for {issue_key}: {sorted(unique_fields)}"
                        )

                    filtered_histories = []
                    for history in histories:
                        items = history.get("items", [])

                        # Keep only tracked field change items
                        # JIRA changelog items have BOTH:
                        #   "field": "Sprint" (display name)
                        #   "fieldId": "customfield_10005" (actual field ID)
                        # We must check BOTH to catch all changes
                        tracked_items = [
                            item
                            for item in items
                            if item.get("field") in tracked_fields
                            or item.get("fieldId") in tracked_fields
                        ]

                        if tracked_items:
                            # Build minimal history entry with only what we need
                            filtered_histories.append(
                                {
                                    "created": history.get("created"),
                                    "items": [
                                        {
                                            "field": item.get("field"),
                                            "fromString": item.get("fromString"),
                                            "toString": item.get("toString"),
                                        }
                                        for item in tracked_items
                                    ],
                                }
                            )

                    total_histories_after += len(filtered_histories)

                    # CRITICAL: Include ALL fields needed for DORA, Flow, and Sprint
                    # metrics
                    # - project: Filter Development vs DevOps projects
                    # - fixVersions: Match dev issues with operational tasks
                    # - status: Filter completed/deployed issues, track state
                    # transitions
                    # - sprint: Track sprint assignment changes (Sprint Tracker feature)
                    # - issuetype: Filter "Operational Task" issues
                    # - created: Used in some calculations
                    # - resolutiondate: Fallback for deployment dates
                    # Prepare changelog entries for database batch insert
                    for history in filtered_histories:
                        change_date = history.get("created", "")
                        items = history.get("items", [])
                        for item in items:
                            # Check both field name and fieldId
                            field_name = item.get("field")
                            field_id = item.get("fieldId")

                            # Use fieldId if it matches tracked fields (for custom
                            # fields like sprint)
                            # Otherwise use field name (for standard fields like status)
                            if field_id and field_id in tracked_fields:
                                final_field_name = field_id
                            elif field_name and field_name in tracked_fields:
                                final_field_name = field_name
                            else:
                                continue  # Skip if neither matches

                            changelog_entries_batch.append(
                                {
                                    "issue_key": issue_key,
                                    "change_date": change_date,
                                    "author": "",  # Not stored in optimized cache
                                    "field_name": final_field_name,
                                    "field_type": "jira",
                                    "old_value": item.get("fromString"),
                                    "new_value": item.get("toString"),
                                }
                            )

                    issues_processed += 1

                    # LOG PROGRESS: Every 50 issues to show activity without impacting
                    # performance
                    if issues_processed > 0 and issues_processed % 50 == 0:
                        logger.info(
                            f"[JIRA] Processing changelog: {issues_processed}/"
                            f"{len(issues_with_changelog)} issues"
                        )
                        if progress_callback:
                            progress_callback(
                                f"Processing changelog: {issues_processed}/"
                                f"{len(issues_with_changelog)} issues"
                            )

                # Final save: Save to DATABASE only
                if progress_callback:
                    progress_callback(
                        f"Finalizing changelog data for {issues_processed} issues..."
                    )

                # Calculate optimization percentage (used in logging and return value)
                reduction_pct = (
                    (
                        100
                        * (total_histories_before - total_histories_after)
                        / total_histories_before
                    )
                    if total_histories_before > 0
                    else 0
                )

                # Save all collected changelog entries to database in single batch
                try:
                    backend = get_backend()
                    utc_now = datetime.now(UTC)
                    expires_at = utc_now + timedelta(hours=24)

                    if changelog_entries_batch:
                        # Save to database using batch insert
                        backend.save_changelog_batch(
                            profile_id=profile_id,
                            query_id=query_id,
                            entries=changelog_entries_batch,
                            expires_at=expires_at,
                        )

                        logger.info(
                            f"[Database] Saved {len(changelog_entries_batch)} changelog entries to database for {profile_id}/{query_id}"
                        )
                        logger.info(
                            f"[Database] Optimized changelog: {total_histories_before} → {total_histories_after} histories ({reduction_pct:.1f}% reduction)"
                        )
                    else:
                        logger.info(
                            "[Database] No changelog entries to save "
                            "(no status changes found)"
                        )

                except (
                    AttributeError,
                    PersistenceError,
                    TypeError,
                    ValueError,
                ) as db_error:
                    logger.error(
                        f"[Database] Failed to save changelog to database: {db_error}",
                        exc_info=True,
                    )
                    return False, f"Failed to save changelog to database: {db_error}"

                # Calculate how many were newly fetched vs already cached
                newly_fetched = len(issues_with_changelog)
                total_cached = len(cached_issue_keys) + newly_fetched
                previously_cached = len(cached_issue_keys)

                if progress_callback:
                    progress_callback(
                        f"[OK] Changelog complete: {newly_fetched} fetched, "
                        f"{previously_cached} cached, {total_cached} total"
                    )

                return (
                    True,
                    f"[OK] Changelog: {newly_fetched} newly fetched + {previously_cached} already cached = {total_cached} total issues (saved {reduction_pct:.0f}% size)",
                )
            except (
                JiraError,
                KeyError,
                PersistenceError,
                RuntimeError,
                TypeError,
                ValueError,
            ) as e:
                logger.warning(f"[Cache] Failed to save changelog data: {e}")
                return False, f"Failed to cache changelog: {e}"
        else:
            logger.warning(
                "[JIRA] Failed to fetch changelog, Flow metrics may be limited"
            )
            return False, "Failed to fetch changelog data from JIRA"

    except (
        JiraError,
        KeyError,
        PersistenceError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[JIRA] Error fetching changelog on demand: {e}")
        return False, f"Changelog fetch failed: {e}"
