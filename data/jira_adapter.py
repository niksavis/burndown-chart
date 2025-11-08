"""JIRA Issue Adapter for Dict-to-Object conversion.

Converts plain dict JIRA issues from jira_cache.json into objects
that match the JIRA SDK Issue structure expected by calculator functions.

This allows calculators to work with cached data without requiring
the JIRA SDK to be connected.
"""

from typing import Dict, Any, List
from types import SimpleNamespace


def adapt_jira_issue(issue_dict: Dict[str, Any]) -> Any:
    """Convert a dict JIRA issue to an object with .fields attribute.

    Args:
        issue_dict: Dict representation of JIRA issue from jira_cache.json

    Returns:
        Object with .key and .fields attributes matching JIRA SDK structure
    """
    # Create the main issue object
    issue = SimpleNamespace()
    issue.key = issue_dict.get("key")
    issue.id = issue_dict.get("id")

    # Create fields object
    fields_dict = issue_dict.get("fields", {})
    fields = SimpleNamespace()

    # Map all top-level fields
    for field_name, field_value in fields_dict.items():
        if isinstance(field_value, dict):
            # Convert nested dicts to objects (like status, issuetype)
            setattr(fields, field_name, SimpleNamespace(**field_value))
        elif isinstance(field_value, list):
            # Convert lists of dicts to lists of objects (like fixVersions)
            if field_value and isinstance(field_value[0], dict):
                setattr(
                    fields,
                    field_name,
                    [SimpleNamespace(**item) for item in field_value],
                )
            else:
                setattr(fields, field_name, field_value)
        else:
            setattr(fields, field_name, field_value)

    issue.fields = fields

    # Add changelog if present
    if "changelog" in issue_dict:
        changelog_data = issue_dict["changelog"]
        changelog = SimpleNamespace(histories=[])

        if isinstance(changelog_data, dict):
            histories = changelog_data.get("histories", [])

            for history_dict in histories:
                history = SimpleNamespace(created=history_dict.get("created"), items=[])

                for item_dict in history_dict.get("items", []):
                    item = SimpleNamespace(
                        field=item_dict.get("field"),
                        fieldtype=item_dict.get("fieldtype"),
                        fromString=item_dict.get("fromString"),
                        toString=item_dict.get("toString"),
                    )
                    history.items.append(item)

                changelog.histories.append(history)

        issue.changelog = changelog

    return issue


def adapt_jira_issues(issues: List[Dict[str, Any]]) -> List[Any]:
    """Convert a list of dict JIRA issues to objects.

    Args:
        issues: List of dict representations from jira_cache.json

    Returns:
        List of objects with .fields attributes
    """
    return [adapt_jira_issue(issue) for issue in issues]
