import logging

import requests

logger = logging.getLogger(__name__)


def extract_epic_keys_from_issues(issues: list[dict], parent_field: str) -> set[str]:

    epic_keys = set()

    for issue in issues:
        fields = issue.get("fields", {})
        parent_data = fields.get(parent_field)

        if not parent_data:
            continue

        if isinstance(parent_data, str):
            epic_key = parent_data.strip()
            if epic_key:
                epic_keys.add(epic_key)
        elif isinstance(parent_data, dict):
            epic_key = parent_data.get("key", "").strip()
            if epic_key:
                epic_keys.add(epic_key)

    logger.info(
        f"[PARENT] Found {len(epic_keys)} unique parent keys referenced by issues"
    )
    return epic_keys


def fetch_epics_from_jira(
    epic_keys: set[str],
    config: dict,
) -> list[dict]:

    if not epic_keys:
        logger.debug("[PARENT] No parent keys to fetch")
        return []

    keys_csv = ", ".join(sorted(epic_keys))
    jql = f"key in ({keys_csv})"

    logger.info(f"[PARENT] Fetching {len(epic_keys)} parent issues from JIRA")
    logger.debug(f"[PARENT] JQL: {jql[:100]}...")

    api_endpoint = config.get("api_endpoint", "")
    auth_token = config.get("auth_token", "")

    if not api_endpoint or not auth_token:
        logger.error("[PARENT] Missing API endpoint or auth token")
        return []

    base_fields = (
        "key,summary,project,created,updated,resolutiondate,status,"
        "issuetype,assignee,priority,resolution,labels,components,fixVersions"
    )

    parent_field = (
        config.get("field_mappings", {}).get("general", {}).get("parent_field")
    )
    if parent_field:
        base_fields += f",{parent_field}"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    epics = []
    start_at = 0
    max_results = 100

    try:
        while True:
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": base_fields,
            }

            response = requests.get(
                f"{api_endpoint}/search",
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            batch = data.get("issues", [])
            epics.extend(batch)

            total = data.get("total", 0)
            logger.debug(f"[PARENT] Fetched {len(epics)}/{total} parent issues")

            if len(epics) >= total:
                break

            start_at += max_results

    except requests.exceptions.RequestException as e:
        logger.error(f"[PARENT] Failed to fetch parent issues: {e}")
        return []

    logger.info(f"[PARENT] Successfully fetched {len(epics)} parent issues")
    return epics


def fetch_epics_for_display(
    issues: list[dict],
    config: dict,
) -> list[dict]:

    parent_field = (
        config.get("field_mappings", {}).get("general", {}).get("parent_field")
    )

    if not parent_field:
        logger.debug("[PARENT] No parent field configured - skipping parent fetch")
        return []

    epic_keys = extract_epic_keys_from_issues(issues, parent_field)

    if not epic_keys:
        logger.debug("[PARENT] No parent keys referenced in issues")
        return []

    epics = fetch_epics_from_jira(epic_keys, config)

    return epics
