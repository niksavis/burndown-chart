import logging

logger = logging.getLogger(__name__)


def extract_parent_keys(issues: list[dict], parent_field: str) -> set[str]:

    if not parent_field:
        return set()

    parent_keys = set()

    for issue in issues:
        parent_value = issue.get(parent_field)

        if not parent_value and parent_field.startswith("customfield_"):
            custom_fields = issue.get("custom_fields", {})
            parent_value = custom_fields.get(parent_field)

        if not parent_value:
            continue

        if isinstance(parent_value, dict):
            parent_key = parent_value.get("key")
        elif isinstance(parent_value, str):
            parent_key = parent_value.strip()
        else:
            parent_key = None

        if parent_key:
            parent_keys.add(parent_key)

    return parent_keys


def filter_parent_issues(
    issues: list[dict], parent_field: str, log_prefix: str = "FILTER"
) -> list[dict]:

    if not parent_field:
        logger.debug(f"[{log_prefix}] No parent field configured - no filtering")
        return issues

    parent_keys = extract_parent_keys(issues, parent_field)

    if not parent_keys:
        logger.debug(f"[{log_prefix}] No parent keys found - no filtering")
        return issues

    issues_before = len(issues)
    filtered = [i for i in issues if i.get("issue_key") not in parent_keys]
    filtered_count = issues_before - len(filtered)

    if filtered_count > 0:
        logger.info(
            f"[{log_prefix}] Filtered out {filtered_count} parent issues "
            f"(found {len(parent_keys)} unique parent keys)"
        )

    return filtered
