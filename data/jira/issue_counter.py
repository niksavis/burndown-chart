"""
JIRA Issue Counter

Fast issue counting without fetching full data (incremental fetch optimization).
"""


import requests

from configuration import logger


def check_jira_issue_count(jql_query: str, config: dict) -> tuple[bool, int]:
    """
    Fast check: Get issue count from JIRA without fetching full issue data.

    This is a lightweight query (< 1 second) that returns only the total count.
    Used to detect if cache is stale before doing a full refresh.

    Args:
        jql_query: JQL query to count issues for
        config: JIRA configuration with API endpoint and token

    Returns:
        Tuple of (success: bool, count: int)
    """
    try:
        url = config["api_endpoint"]  # API endpoint already includes /search

        headers = {"Accept": "application/json"}
        if config.get("token"):
            headers["Authorization"] = f"Bearer {config['token']}"

        # maxResults=0 returns only total count (no issue data)
        params = {
            "jql": jql_query,
            "maxResults": 0,  # Don't fetch issues, just count
            "fields": "key",  # Minimal field to reduce payload
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total", 0)
            logger.info(f"[JIRA] Count check: {total_count} issues matched")
            return True, total_count
        else:
            # Log JQL for debugging when count check fails
            jql_preview = jql_query[:100] + "..." if len(jql_query) > 100 else jql_query
            logger.warning(
                f"[JIRA] Count check failed: HTTP {response.status_code} for JQL: {jql_preview}"
            )
            if response.status_code == 404:
                logger.warning(
                    "[JIRA] 404 error - API endpoint might be incorrect or JQL syntax invalid"
                )
            return False, 0

    except Exception as e:
        jql_preview = jql_query[:100] + "..." if len(jql_query) > 100 else jql_query
        logger.warning(f"[JIRA] Count check failed: {e} for JQL: {jql_preview}")
        return False, 0
