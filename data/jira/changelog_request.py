import logging

from data.jira.field_utils import extract_jira_field_id as _extract_jira_field_id

logger = logging.getLogger(__name__)


def _build_changelog_jql(config: dict) -> str:

    base_jql = config["jql_query"]

    order_by_clause = ""
    if "ORDER BY" in base_jql.upper():
        import re  # noqa: PLC0415

        match = re.search(r"\s+ORDER\s+BY\s+", base_jql, re.IGNORECASE)
        if match:
            order_by_start = match.start()
            order_by_clause = base_jql[order_by_start:]
            base_jql = base_jql[:order_by_start].strip()

    try:
        from configuration.dora_config import (  # noqa: PLC0415
            get_flow_end_status_names,
        )

        flow_end_statuses = get_flow_end_status_names()
        if flow_end_statuses:
            statuses_str = ", ".join([f'"{s}"' for s in flow_end_statuses])
            jql = f"({base_jql}) AND status IN ({statuses_str}){order_by_clause}"
            logger.debug(f"[JIRA] Filtering completed issues: {statuses_str}")
        else:
            jql = (
                f'({base_jql}) AND status IN ("Done", "Resolved", "Closed")'
                f"{order_by_clause}"
            )
            logger.warning("[JIRA] No completion statuses in config, using defaults")
    except Exception as e:
        logger.warning(f"[JIRA] Failed to load completion statuses: {e}")
        jql = (
            f'({base_jql}) AND status IN ("Done", "Resolved", "Closed")'
            f"{order_by_clause}"
        )

    return jql


def _build_headers(config: dict) -> dict[str, str]:

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if config.get("token"):
        headers["Authorization"] = f"Bearer {config['token']}"
    return headers


def _build_fields_string(config: dict) -> str:

    base_fields = (
        "key,summary,project,created,updated,resolutiondate,status,"
        "issuetype,assignee,priority,resolution,labels,components,fixVersions"
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
                clean_field_id = _extract_jira_field_id(field_id)
                if clean_field_id and clean_field_id not in base_fields:
                    additional_fields.append(clean_field_id)

    if additional_fields:
        fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
    else:
        fields = base_fields

    return fields
