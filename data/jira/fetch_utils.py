import logging

import requests

from data.jira.config import generate_config_hash
from data.jira.field_utils import extract_jira_field_id
from data.jira.rate_limiter import get_rate_limiter, retry_with_backoff

logger = logging.getLogger(__name__)


_extract_jira_field_id = extract_jira_field_id
_generate_config_hash = generate_config_hash


def fetch_jira_paginated(
    config: dict, max_results: int | None = None
) -> tuple[bool, list[dict]]:

    return _fetch_jira_paginated(config, max_results)


def _fetch_jira_paginated(
    config: dict, max_results: int | None = None
) -> tuple[bool, list[dict]]:

    try:
        jql = config["jql_query"]
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("[FETCH] API endpoint not configured")
            return False, []

        if config.get("fields"):
            fields = config["fields"]
        else:
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

            if (
                config.get("story_points_field")
                and config["story_points_field"].strip()
            ):
                additional_fields.append(config["story_points_field"])

            field_mappings = config.get("field_mappings", {})
            for _category, mappings in field_mappings.items():
                if isinstance(mappings, dict):
                    for _field_name, field_id in mappings.items():
                        clean_field_id = _extract_jira_field_id(field_id)
                        if clean_field_id and clean_field_id not in base_fields:
                            additional_fields.append(clean_field_id)

            if additional_fields:
                fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
            else:
                fields = base_fields

        page_size = max_results or config.get("max_results", 1000)
        if page_size > 1000:
            page_size = 1000

        headers = {
            "Authorization": f"Bearer {config['token']}",
            "Content-Type": "application/json",
        }

        all_issues = []
        start_at = 0
        total_issues = None
        rate_limiter = get_rate_limiter()

        while True:
            rate_limiter.wait_for_token()

            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "fields": fields,
            }

            success, response = retry_with_backoff(
                requests.get,
                api_endpoint,
                headers=headers,
                params=params,
                timeout=30,
            )

            if not success or response.status_code != 200:
                error_msg = (
                    f"HTTP {response.status_code}"
                    if hasattr(response, "status_code")
                    else "Network error"
                )
                logger.error(f"[FETCH] API error: {error_msg}")

                if hasattr(response, "text"):
                    try:
                        error_data = response.json()
                        logger.error(f"[FETCH] JIRA error: {error_data}")
                    except Exception:
                        logger.error(f"[FETCH] Response: {response.text[:500]}")

                jql_preview = jql[:200] + "..." if len(jql) > 200 else jql
                logger.error(f"[FETCH] Failed JQL: {jql_preview}")

                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.debug(f"[FETCH] Query matched {total_issues} issues")

            all_issues.extend(issues_in_page)

            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
            ):
                break

            start_at += page_size

        logger.debug(f"[FETCH] Fetched {len(all_issues)} issues")
        return True, all_issues

    except Exception as e:
        logger.error(f"[FETCH] Error: {e}", exc_info=True)
        return False, []
