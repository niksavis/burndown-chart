"""JIRA Issues Store Callback.

Populates jira-issues-store with raw JIRA issues data from jira_cache.json.
This store is the source of truth for DORA and Flow metrics calculations.

Auto-registers via @callback decorator.
"""

from dash import callback, Output, Input
import logging
import json
import os

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
    """Load raw JIRA issues from jira_cache.json into store.

    Args:
        jira_status: JIRA cache status (triggers refresh)
        statistics_data: Statistics data (triggers refresh)

    Returns:
        Dict with JIRA issues data or None if no data available
    """
    try:
        # Load JIRA cache which contains raw issues
        cache_file = "jira_cache.json"

        if not os.path.exists(cache_file):
            logger.warning(f"{cache_file} not found - no JIRA data available")
            return None

        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        if not cache_data:
            logger.warning("Empty JIRA cache file")
            return None

        # Extract issues from cache
        issues = cache_data.get("issues", [])

        if not issues:
            logger.warning("No issues found in JIRA cache")
            return None

        # Load changelog data from separate cache file
        changelog_cache_file = "jira_changelog_cache.json"
        changelog_data = {}

        if os.path.exists(changelog_cache_file):
            try:
                with open(changelog_cache_file, "r", encoding="utf-8") as f:
                    changelog_data = json.load(f)
                logger.info(
                    f"Loaded changelog data for {len(changelog_data)} issues from {changelog_cache_file}"
                )
            except Exception as e:
                logger.warning(f"Failed to load changelog cache: {e}")
        else:
            logger.warning(
                f"{changelog_cache_file} not found - Flow Time and Flow Efficiency metrics may be limited"
            )

        # Merge changelog data into issues
        issues_with_changelog_count = 0
        for issue in issues:
            issue_key = issue.get("key", "")
            if issue_key and issue_key in changelog_data:
                issue["changelog"] = changelog_data[issue_key].get("changelog", {})
                issues_with_changelog_count += 1

        if issues_with_changelog_count > 0:
            logger.info(
                f"Merged changelog data into {issues_with_changelog_count} issues"
            )

        # CRITICAL: Filter DevOps projects at SOURCE before ANY component sees the data
        # This ensures Dashboard, Flow, DORA all work with development projects only
        from data.persistence import load_app_settings
        from data.project_filter import filter_development_issues

        app_settings = load_app_settings()
        devops_projects = app_settings.get("devops_projects", [])

        if devops_projects:
            total_before = len(issues)
            issues = filter_development_issues(issues, devops_projects)
            filtered_count = total_before - len(issues)
            logger.info(
                f"🔍 Filtered {filtered_count} DevOps issues at jira-issues-store level. "
                f"All components will now use {len(issues)} development project issues only."
            )

        logger.info(
            f"Populated jira-issues-store with {len(issues)} issues from {cache_file}"
        )

        # Return filtered issues - ALL components downstream get development projects only
        return {"issues": issues, "total_count": len(issues)}

    except Exception as e:
        logger.error(f"Error populating jira-issues-store: {e}", exc_info=True)
        return None
