"""JIRA changelog JQL query and field string builders.

Constructs the JQL query and fields parameter string used when fetching
JIRA issues with changelog expansion.
"""

import logging

from configuration.dora_config import get_flow_end_status_names
from data.jira.field_utils import extract_jira_field_id as _extract_jira_field_id

logger = logging.getLogger(__name__)


def _build_changelog_jql(config: dict) -> str:
    """
    Build JQL query for changelog fetch, filtering for completed issues only.

    This reduces data volume by ~60% compared to fetching all issues.

    Args:
        config: Configuration dictionary with base JQL query

    Returns:
        JQL query string filtered for completed issues
    """
    base_jql = config["jql_query"]

    # Extract ORDER BY clause if present (must come at end of final query)
    order_by_clause = ""
    if "ORDER BY" in base_jql.upper():
        # Find ORDER BY position (case-insensitive)
        import re

        match = re.search(r"\s+ORDER\s+BY\s+", base_jql, re.IGNORECASE)
        if match:
            order_by_start = match.start()
            order_by_clause = base_jql[order_by_start:]
            base_jql = base_jql[:order_by_start].strip()

    # Load completion statuses from configuration
    try:
        flow_end_statuses = get_flow_end_status_names()
        if flow_end_statuses:
            statuses_str = ", ".join([f'"{s}"' for s in flow_end_statuses])
            jql = f"({base_jql}) AND status IN ({statuses_str}){order_by_clause}"
            logger.debug(f"[JIRA] Filtering completed issues: {statuses_str}")
        else:
            # Fallback: Use common completion statuses
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
    """
    Build HTTP headers for JIRA API request.

    Args:
        config: Configuration dictionary with token

    Returns:
        Dictionary of HTTP headers
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",  # Required for POST with JSON body
    }
    if config.get("token"):  # Use .get() to safely handle missing token
        headers["Authorization"] = f"Bearer {config['token']}"
    return headers


def _build_fields_string(config: dict) -> str:
    """
    Build fields string for JIRA API request.

    Includes base fields plus story points and field mappings.

    Args:
        config: Configuration dictionary with field mappings

    Returns:
        Comma-separated string of field names
    """

    # Fields to fetch (same as regular fetch + changelog)
    # NOTE: fixVersions is critical for DORA Lead Time calculation (matching dev issues
    # to operational tasks)
    # NOTE: project is critical for filtering DevOps vs Development projects in DORA
    # metrics
    base_fields = (
        "key,summary,project,created,updated,resolutiondate,status,"
        "issuetype,assignee,priority,resolution,labels,components,fixVersions"
    )

    # Add parent field if configured (either standard 'parent' or Epic Link custom
    # field)
    parent_field = (
        config.get("field_mappings", {}).get("general", {}).get("parent_field")
    )
    if parent_field:
        base_fields += f",{parent_field}"

    # Add story points field if specified
    additional_fields = []
    points_field = config.get("story_points_field", "")
    if points_field and isinstance(points_field, str) and points_field.strip():
        additional_fields.append(points_field)

    # Add field mappings for DORA and Flow metrics
    # field_mappings has structure: {"dora": {"field_name": "field_id"}, "flow": {...}}
    # CRITICAL: Strip =Value filter syntax (e.g., "customfield_11309=PROD" ->
    # "customfield_11309")
    field_mappings = config.get("field_mappings", {})
    for _category, mappings in field_mappings.items():
        if isinstance(mappings, dict):
            for _field_name, field_id in mappings.items():
                # Extract clean field ID (strips =Value filter, skips changelog syntax)
                clean_field_id = _extract_jira_field_id(field_id)
                if clean_field_id and clean_field_id not in base_fields:
                    additional_fields.append(clean_field_id)

    # Combine base fields with additional fields
    # Sort additional fields to ensure consistent ordering for cache validation
    if additional_fields:
        fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
    else:
        fields = base_fields

    return fields
