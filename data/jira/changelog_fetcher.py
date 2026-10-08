import logging
from datetime import UTC, datetime, timedelta

from data.exceptions import JiraError, PersistenceError
from data.jira.changelog_pagination import fetch_jira_issues_with_changelog

logger = logging.getLogger(__name__)


def get_backend():  # noqa: PLC0415
    from data.persistence.factory import (  # noqa: PLC0415
        get_backend as _get_backend,
    )

    return _get_backend()


__all__ = ["fetch_changelog_on_demand", "fetch_jira_issues_with_changelog"]


def fetch_changelog_on_demand(
    config: dict,
    profile_id: str | None = None,
    query_id: str | None = None,
    progress_callback=None,
    issue_keys: list[str] | None = None,
) -> tuple[bool, str]:

    logger.info("Fetching changelog for profile/query: %s/%s", profile_id, query_id)

    try:
        logger.info("[JIRA] Fetching changelog data for Flow Time and DORA metrics")
        if progress_callback:
            progress_callback("[Stats] Starting changelog download...")

        backend = get_backend()

        if not profile_id:
            profile_id = backend.get_app_state("active_profile_id")
        if not query_id:
            query_id = backend.get_app_state("active_query_id")

        if not profile_id or not query_id:
            logger.error("[Database] No active profile/query - cannot fetch changelog")
            return False, "No active profile/query"

        cached_issue_keys = set()
        try:
            existing_entries = backend.get_changelog_entries(
                profile_id=profile_id, query_id=query_id
            )
            cached_issue_keys = set(
                entry.get("issue_key")
                for entry in existing_entries
                if entry.get("issue_key")
            )
            logger.info(
                f"[Database] Loaded {len(cached_issue_keys)} unique issues "
                f"with changelog from database"
            )
        except (
            AttributeError,
            PersistenceError,
            TypeError,
            ValueError,
        ) as e:
            logger.warning(f"[Database] Could not load existing changelog: {e}")
            cached_issue_keys = set()

        issues_needing_changelog: list[str] | None = []
        if issue_keys:
            issues_needing_changelog = sorted(set(issue_keys))
            logger.info(
                f"[JIRA] Changelog refresh: targeting "
                f"{len(issues_needing_changelog)} issues"
            )
            if progress_callback:
                progress_callback(
                    f"Targeted changelog refresh: "
                    f"{len(issues_needing_changelog)} issues"
                )
        else:
            try:
                all_issues = backend.get_issues(
                    profile_id=profile_id, query_id=query_id
                )
                all_issue_keys: list[str] = [
                    str(issue.get("issue_key"))
                    for issue in all_issues
                    if issue.get("issue_key")
                ]

                issues_needing_changelog = [
                    key for key in all_issue_keys if key not in cached_issue_keys
                ]

                logger.info(
                    f"[JIRA] Changelog analysis: {len(all_issue_keys)} total, "
                    f"{len(cached_issue_keys)} cached, "
                    f"{len(issues_needing_changelog)} need fetch"
                )

                if issues_needing_changelog:
                    logger.info(
                        f"[Database] Optimized fetch: Only "
                        f"{len(issues_needing_changelog)} new issues"
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
                            f"[OK] All {len(cached_issue_keys)} issues "
                            f"already cached - skipping download"
                        )
                    return (
                        True,
                        f"[OK] Changelog already cached for all "
                        f"{len(cached_issue_keys)} issues",
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

        changelog_fetch_success, issues_with_changelog = (
            fetch_jira_issues_with_changelog(
                config,
                issue_keys=issues_needing_changelog,
                progress_callback=progress_callback,
            )
        )

        if changelog_fetch_success:
            try:
                total_histories_before = 0
                total_histories_after = 0
                issues_processed = 0
                changelog_entries_batch = []

                for issue in issues_with_changelog:
                    issue_key = issue.get("key", "")
                    if not issue_key:
                        continue

                    changelog_full = issue.get("changelog", {})
                    histories = changelog_full.get("histories", [])
                    total_histories_before += len(histories)

                    tracked_fields = ["status"]

                    sprint_field_id = (
                        config.get("field_mappings", {})
                        .get("general", {})
                        .get("sprint_field")
                    )
                    if sprint_field_id:
                        tracked_fields.append(sprint_field_id)
                        tracked_fields.append("Sprint")
                        logger.info(
                            f"[JIRA] Tracking sprint field: "
                            f"{sprint_field_id} and 'Sprint'"
                        )

                    if issues_processed == 0 and histories:
                        unique_fields = set()
                        for hist in histories[:5]:
                            for item in hist.get("items", []):
                                unique_fields.add(item.get("field"))
                        logger.info(
                            f"[JIRA] Sample changelog field names for {issue_key}: "
                            f"{sorted(unique_fields)}"
                        )

                    filtered_histories = []
                    for history in histories:
                        items = history.get("items", [])

                        tracked_items = [
                            item
                            for item in items
                            if item.get("field") in tracked_fields
                            or item.get("fieldId") in tracked_fields
                        ]

                        if tracked_items:
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

                    for history in filtered_histories:
                        change_date = history.get("created", "")
                        items = history.get("items", [])
                        for item in items:
                            field_name = item.get("field")
                            field_id = item.get("fieldId")

                            if field_id and field_id in tracked_fields:
                                final_field_name = field_id
                            elif field_name and field_name in tracked_fields:
                                final_field_name = field_name
                            else:
                                continue

                            changelog_entries_batch.append(
                                {
                                    "issue_key": issue_key,
                                    "change_date": change_date,
                                    "author": "",
                                    "field_name": final_field_name,
                                    "field_type": "jira",
                                    "old_value": item.get("fromString"),
                                    "new_value": item.get("toString"),
                                }
                            )

                    issues_processed += 1

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

                if progress_callback:
                    progress_callback(
                        f"Finalizing changelog data for {issues_processed} issues..."
                    )

                reduction_pct = (
                    (
                        100
                        * (total_histories_before - total_histories_after)
                        / total_histories_before
                    )
                    if total_histories_before > 0
                    else 0
                )

                try:
                    backend = get_backend()
                    utc_now = datetime.now(UTC)
                    expires_at = utc_now + timedelta(hours=24)

                    if changelog_entries_batch:
                        backend.save_changelog_batch(
                            profile_id=profile_id,
                            query_id=query_id,
                            entries=changelog_entries_batch,
                            expires_at=expires_at,
                        )

                        logger.info(
                            f"[Database] Saved {len(changelog_entries_batch)} "
                            f"changelog entries to database for {profile_id}/{query_id}"
                        )
                        logger.info(
                            f"[Database] Optimized changelog: "
                            f"{total_histories_before} → "
                            f"{total_histories_after} histories "
                            f"({reduction_pct:.1f}% reduction)"
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
                    f"[OK] Changelog: {newly_fetched} newly fetched + "
                    f"{previously_cached} already cached = {total_cached} total issues "
                    f"(saved {reduction_pct:.0f}% size)",
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
