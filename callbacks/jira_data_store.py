"""JIRA Issues Store Callback.

Populates jira-issues-store with raw JIRA issues data from jira_cache.json.
This store is the source of truth for DORA and Flow metrics calculations.

Auto-registers via @callback decorator.
"""

import logging

from dash import Input, Output, callback

logger = logging.getLogger(__name__)


@callback(
    Output("jira-issues-store", "data"),
    [
        Input("jira-cache-status", "children"),  # Triggers when JIRA data is updated
        Input("current-statistics", "data"),  # Triggers on statistics update
    ],
    prevent_initial_call=False,
)
def populate_jira_issues_store(jira_status, statistics_data):
    """Load raw JIRA issues from database into store.

    Args:
        jira_status: JIRA cache status (triggers refresh)
        statistics_data: Statistics data (triggers refresh)

    Returns:
        Dict with JIRA issues data or None if no data available
    """
    try:
        # Load JIRA issues from database
        from data.persistence.factory import get_backend

        logger.info("===== JIRA STORE CALLBACK START =====")
        logger.info(f"jira_status: {jira_status}")
        logger.info(f"statistics_data type: {type(statistics_data)}")

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        logger.info(f"active_profile_id: {active_profile_id}")
        logger.info(f"active_query_id: {active_query_id}")

        if not active_profile_id or not active_query_id:
            logger.warning(
                "No active profile/query - no JIRA data available - RETURNING NONE"
            )
            return None

        # Get all issues from database
        import time

        start_time = time.perf_counter()
        issues = backend.get_issues(active_profile_id, active_query_id, limit=None)
        db_query_time = time.perf_counter() - start_time

        logger.info(
            f"backend.get_issues() returned {len(issues) if issues else 0} issues in {db_query_time:.3f}s"
        )

        if not issues:
            logger.warning("No issues found in database - RETURNING NONE")
            return None

        # Convert database format to expected format
        # Database uses 'issue_key' but code expects 'key'
        format_start_time = time.perf_counter()
        formatted_issues = []
        for issue in issues:
            formatted_issue = {
                "key": issue.get("issue_key"),
                "summary": issue.get("summary"),
                "status": issue.get("status"),
                "assignee": issue.get("assignee"),
                "issue_type": issue.get("issue_type"),
                "priority": issue.get("priority"),
                "resolution": issue.get("resolution"),
                "created": issue.get("created"),
                "updated": issue.get("updated"),
                "resolved": issue.get("resolved"),
                "story_points": issue.get("points"),
                "project": {
                    "key": issue.get("project_key"),
                    "name": issue.get("project_name"),
                },
                "fix_versions": issue.get("fix_versions"),
                "labels": issue.get("labels"),
                "components": issue.get("components"),
            }
            # Add custom fields if they exist
            custom_fields = issue.get("custom_fields")
            if custom_fields and isinstance(custom_fields, dict):
                formatted_issue.update(custom_fields)

            formatted_issues.append(formatted_issue)
        format_time = time.perf_counter() - format_start_time

        # Load changelog data from database
        changelog_start_time = time.perf_counter()
        changelog_entries = backend.get_changelog_entries(
            active_profile_id, active_query_id
        )

        # Group changelog by issue_key
        changelog_by_issue = {}
        for entry in changelog_entries:
            issue_key = entry.get("issue_key")
            if issue_key not in changelog_by_issue:
                changelog_by_issue[issue_key] = {"histories": []}

            # Format changelog entry
            history_entry = {
                "id": entry.get("history_id"),
                "created": entry.get("created"),
                "field": entry.get("field"),
                "from": entry.get("from_value"),
                "fromString": entry.get("from_string"),
                "to": entry.get("to_value"),
                "toString": entry.get("to_string"),
            }
            changelog_by_issue[issue_key]["histories"].append(history_entry)

        changelog_time = time.perf_counter() - changelog_start_time

        if changelog_entries:
            logger.info(
                f"Loaded changelog data for {len(changelog_by_issue)} issues from database"
            )

        # Merge changelog data into issues
        issues_with_changelog_count = 0
        for issue in formatted_issues:
            issue_key = issue.get("key", "")
            if issue_key and issue_key in changelog_by_issue:
                issue["changelog"] = changelog_by_issue[issue_key]
                issues_with_changelog_count += 1

        if issues_with_changelog_count > 0:
            logger.info(
                f"Merged changelog data into {issues_with_changelog_count} issues"
            )

        # CRITICAL CHANGE: Do NOT filter at store level!
        # Each component (Dashboard, Flow, DORA) must filter what it needs:
        # - Dashboard/Flow: filter_development_issues() for dev project issues only
        # - DORA: Uses BOTH dev projects (for bugs, lead time) AND devops projects (for deployments)
        # Filtering at source breaks DORA metrics which need DevOps issues!

        total_time = time.perf_counter() - start_time
        logger.info(
            f"PERFORMANCE: jira-issues-store population completed in {total_time:.3f}s "
            f"(DB query: {db_query_time:.3f}s, format conversion: {format_time:.3f}s, "
            f"changelog: {changelog_time:.3f}s, {len(formatted_issues)} issues)"
        )

        result = {"issues": formatted_issues, "total_count": len(formatted_issues)}
        logger.info(
            f"===== JIRA STORE CALLBACK RETURNING: {len(formatted_issues)} issues ====="
        )
        # Return ALL issues - each component filters what it needs
        return result

    except Exception as e:
        logger.error(f"Error populating jira-issues-store: {e}", exc_info=True)
        logger.info("===== JIRA STORE CALLBACK RETURNING: None (exception) =====")
        return None
