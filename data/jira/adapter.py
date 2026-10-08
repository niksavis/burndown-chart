from types import SimpleNamespace
from typing import Any


def adapt_jira_issue(issue_dict: dict[str, Any]) -> Any:

    issue = SimpleNamespace()
    issue.key = issue_dict.get("key")
    issue.id = issue_dict.get("id")

    fields_dict = issue_dict.get("fields", {})
    fields = SimpleNamespace()

    for field_name, field_value in fields_dict.items():
        if isinstance(field_value, dict):
            setattr(fields, field_name, SimpleNamespace(**field_value))
        elif isinstance(field_value, list):
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


def adapt_jira_issues(issues: list[dict[str, Any]]) -> list[Any]:

    return [adapt_jira_issue(issue) for issue in issues]
