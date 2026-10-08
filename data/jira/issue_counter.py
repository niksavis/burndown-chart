import logging

import requests

logger = logging.getLogger(__name__)


def check_jira_issue_count(jql_query: str, config: dict) -> tuple[bool, int]:

    try:
        url = config["api_endpoint"]

        headers = {"Accept": "application/json"}
        if config.get("token"):
            headers["Authorization"] = f"Bearer {config['token']}"

        params = {
            "jql": jql_query,
            "maxResults": 0,
            "fields": "key",
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total", 0)
            logger.info(f"[JIRA] Count check: {total_count} issues matched")
            return True, total_count
        else:
            jql_preview = jql_query[:100] + "..." if len(jql_query) > 100 else jql_query
            logger.warning(
                "[JIRA] Count check failed: "
                f"HTTP {response.status_code} for JQL: {jql_preview}"
            )
            if response.status_code == 404:
                logger.warning(
                    "[JIRA] 404 error - API endpoint might be incorrect "
                    "or JQL syntax invalid"
                )
            return False, 0

    except Exception as e:
        jql_preview = jql_query[:100] + "..." if len(jql_query) > 100 else jql_query
        logger.warning(f"[JIRA] Count check failed: {e} for JQL: {jql_preview}")
        return False, 0
