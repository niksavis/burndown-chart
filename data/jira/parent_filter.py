import logging
from typing import Any

logger = logging.getLogger(__name__)


def filter_out_parent_types(
    issues: list[dict[str, Any]], parent_types: list[str]
) -> list[dict[str, Any]]:

    if not parent_types:
        return issues

    parent_types_lower = {pt.lower() for pt in parent_types}

    filtered_issues = []
    excluded_count = 0

    for issue in issues:
        try:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                issue_type = issue["fields"]["issuetype"]["name"]
            else:
                issue_type = issue.get("issue_type", "")

            if issue_type.lower() in parent_types_lower:
                excluded_count += 1
                logger.debug(
                    f"[ParentFilter] Excluding {issue_type} issue: "
                    f"{issue.get('key', 'UNKNOWN')}"
                )
                continue

            filtered_issues.append(issue)

        except (KeyError, TypeError) as e:
            logger.warning(
                "[ParentFilter] Could not determine issue type for "
                f"{issue.get('key', 'UNKNOWN')}: {e}"
            )
            filtered_issues.append(issue)

    logger.info(
        f"[ParentFilter] Filtered {len(issues)} issues → {len(filtered_issues)} "
        f"(excluded {excluded_count} parent issues)"
    )

    return filtered_issues


def extract_parent_types_from_issues(
    issues: list[dict[str, Any]],
) -> list[dict[str, str]]:

    issue_types = set()

    for issue in issues:
        try:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                issue_type = issue["fields"]["issuetype"]["name"]
            else:
                issue_type = issue.get("issue_type", "")

            if issue_type:
                issue_types.add(issue_type)

        except KeyError, TypeError:
            continue

    return sorted(
        [{"name": t, "key": t.upper()} for t in issue_types], key=lambda x: x["name"]
    )
