from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from data.demo.config import AS_OF, START


def _transition(field: str, before: str, after: str, at: datetime) -> dict[str, Any]:
    return {
        "created": at.isoformat(),
        "items": [
            {
                "field": field,
                "fieldtype": "jira",
                "fromString": before,
                "toString": after,
            }
        ],
    }


def _sprint(index: int) -> str:
    start = START + timedelta(weeks=index * 2)
    end = start + timedelta(days=13, hours=17)
    state = "ACTIVE" if end > AS_OF else "CLOSED"
    return (
        f"[id={index + 1},name=Demo Sprint {index + 1},state={state},"
        f"startDate={start.isoformat()},endDate={end.isoformat()}]"
    )


def _issue_fields(
    number: int, week: int, issue_type: str, done: bool
) -> dict[str, Any]:
    created = START + timedelta(weeks=week, hours=9)
    started = created + timedelta(hours=6)
    resolved = created + timedelta(days=2, hours=6) if done else None
    status = (
        "Done"
        if done
        else ["To Do", "In Progress", "Review", "Testing", "Blocked"][number % 5]
    )
    release = {
        "name": f"Demo release {week + 1}",
        "releaseDate": (created + timedelta(days=3)).date().isoformat(),
        "released": week < 7,
    }
    fields = {
        "summary": f"Synthetic {issue_type.lower()} {number}",
        "created": created.isoformat(),
        "updated": (resolved or started).isoformat(),
        "resolutiondate": resolved.isoformat() if resolved else None,
        "status": {
            "name": status,
            "statusCategory": {
                "key": "done"
                if done
                else "new"
                if status == "To Do"
                else "indeterminate"
            },
        },
        "issuetype": {"name": issue_type},
        "project": {"key": "DEMO", "name": "Acme Corp"},
        "priority": {"name": "High" if issue_type == "Bug" else "Medium"},
        "customfield_10001": [0.5, 1.5, 2.5, 3.5][number % 4],
        "customfield_10002": [_sprint(week // 2)],
        "customfield_10003": "PROD" if number % 3 else "TEST",
        "customfield_10004": "Yes" if number % 5 == 0 else "No",
        "fixVersions": [release],
        "labels": ["synthetic-demo"],
        "components": [{"name": "Synthetic component"}],
        "assignee": {"displayName": f"Demo developer {number % 3 + 1}"},
        "parent": {"key": "DEMO-100", "fields": {"summary": "Synthetic delivery epic"}},
        "customfield_10005": {
            "key": "DEMO-100",
            "fields": {"summary": "Synthetic delivery epic"},
        },
    }
    return fields


def _issue(number: int, week: int, issue_type: str, done: bool) -> dict[str, Any]:
    fields = _issue_fields(number, week, issue_type, done)
    created = datetime.fromisoformat(fields["created"])
    started = created + timedelta(hours=6)
    resolved = (
        datetime.fromisoformat(fields["resolutiondate"])
        if fields["resolutiondate"]
        else None
    )
    status = fields["status"]["name"]
    histories = [
        _transition("Sprint", "", f"Demo Sprint {week // 2 + 1}", created),
        _transition("status", "To Do", "In Progress", started),
        _transition("status", "In Progress", "Review", started + timedelta(hours=3)),
        _transition("status", "Review", "Testing", started + timedelta(days=1)),
    ]
    if resolved:
        histories.append(_transition("status", "Testing", "Done", resolved))
    elif status == "To Do":
        histories = histories[:1]
    elif status == "In Progress":
        histories = histories[:2]
    elif status == "Review":
        histories = histories[:3]
    elif status == "Blocked":
        histories.append(
            _transition("status", "Testing", "Blocked", started + timedelta(days=2))
        )
    fields["updated"] = histories[-1]["created"]
    if number % 17 == 0:
        fields.pop("parent")
        fields.pop("customfield_10005")
    if issue_type == "Bug":
        fields["customfield_10003"] = "TEST" if week % 3 == 0 else "PROD"
    return {
        "key": f"DEMO-{number}",
        "id": str(number),
        "fields": fields,
        "changelog": {"histories": histories},
    }


def complete_issues() -> list[dict[str, Any]]:
    issues = []
    for week in range(8):
        for position, issue_type in enumerate(
            ["Story", "Bug", "Task", "Risk", "Story", "Story"]
        ):
            issues.append(
                _issue(week * 6 + position + 1, week, issue_type, position < 4)
            )
        deployment = _issue(week + 200, week, "Operational Task", True)
        deployment["key"] = f"OPS-{week + 1}"
        deployment["fields"]["project"] = {"key": "OPS", "name": "Acme Corp Operations"}
        deployment["fields"]["customfield_10003"] = "PROD"
        issues.append(deployment)
    epic = _issue(100, 0, "Epic", False)
    epic["fields"].pop("parent")
    epic["fields"].pop("customfield_10005")
    issues.append(epic)
    test_deployment = _issue(299, 3, "Operational Task", True)
    test_deployment["key"] = "OPS-99"
    test_deployment["fields"]["project"] = {
        "key": "OPS",
        "name": "Acme Corp Operations",
    }
    test_deployment["fields"]["customfield_10003"] = "TEST"
    issues.append(test_deployment)
    completed = [
        issue
        for issue in issues
        if issue["fields"]["resolutiondate"]
        and issue["fields"]["project"]["key"] == "DEMO"
    ]
    for number, issue in enumerate(completed[:20], start=1):
        resolved = datetime.fromisoformat(issue["fields"]["resolutiondate"])
        for index in range(1, 4):
            transition = resolved - timedelta(hours=number * (4 - index) / 3)
            issue["changelog"]["histories"][index]["created"] = transition.isoformat()
    return issues


def _apply_scenario(issue: dict[str, Any], scenario: str) -> None:
    fields = issue["fields"]
    week = (datetime.fromisoformat(fields["created"]) - START).days // 7
    if scenario == "no-points":
        fields.pop("customfield_10001")
    if scenario == "zero-delivery" or (scenario == "stalled" and week % 2):
        fields["resolutiondate"] = None
        fields["status"] = {
            "name": "In Progress",
            "statusCategory": {"key": "indeterminate"},
        }
        issue["changelog"]["histories"] = [
            entry
            for entry in issue["changelog"]["histories"]
            if entry["items"][0]["field"] == "Sprint"
            or entry["items"][0]["toString"] == "In Progress"
        ]
        fields["updated"] = issue["changelog"]["histories"][-1]["created"]
    if scenario == "completed":
        if fields["resolutiondate"] is None:
            fields["resolutiondate"] = (
                datetime.fromisoformat(fields["created"]) + timedelta(days=3)
            ).isoformat()
        histories = issue["changelog"]["histories"]
        if histories[-1]["items"][0]["toString"] != "Done":
            histories.append(
                _transition(
                    "status",
                    fields["status"]["name"],
                    "Done",
                    datetime.fromisoformat(fields["resolutiondate"]),
                )
            )
        fields["status"] = {"name": "Done", "statusCategory": {"key": "done"}}
        fields["updated"] = fields["resolutiondate"]
    if scenario == "missing-signals":
        issue["changelog"] = {"histories": []}
        fields.pop("fixVersions", None)


def _change_scope(issues: list[dict[str, Any]]) -> None:
    removed = _issue(90, 1, "Story", False)
    removed["fields"]["project"] = {"key": "OUT", "name": "Acme Corp Archive"}
    removed["changelog"]["histories"].append(
        _transition("project", "DEMO", "OUT", START + timedelta(weeks=4))
    )
    removed["fields"]["updated"] = (START + timedelta(weeks=4)).isoformat()
    issues.append(removed)
    changed = next(issue for issue in issues if issue["key"] == "DEMO-42")
    changed["changelog"]["histories"].append(
        _transition("customfield_10001", "2.5", "3.5", AS_OF - timedelta(days=1))
    )
    changed["fields"]["customfield_10001"] = 3.5
    changed["fields"]["updated"] = (AS_OF - timedelta(days=1)).isoformat()


def _apply_delivery_pattern(issues: list[dict[str, Any]], scenario: str) -> None:
    patterns = {
        "accelerating": (1, 2, 2, 3, 3, 4, 5, 6),
        "declining": (6, 5, 4, 3, 3, 2, 2, 1),
    }
    for issue in issues:
        fields = issue["fields"]
        if fields["project"]["key"] != "DEMO" or fields["issuetype"]["name"] == "Epic":
            continue
        number = int(issue["key"].split("-")[1]) - 1
        week, position = divmod(number, 6)
        if scenario in patterns:
            state = (
                "completed" if position < patterns[scenario][week] else "zero-delivery"
            )
            _apply_scenario(issue, state)
        elif scenario == "variable-points":
            fields["customfield_10001"] = week + 1


def scenario_issues(scenario: str) -> list[dict[str, Any]]:
    issues = deepcopy(complete_issues())
    _apply_delivery_pattern(issues, scenario)
    if scenario == "empty":
        return []
    if scenario == "singleton":
        return issues[:1]
    if scenario == "fractional-points":
        selected = issues[:3]
        for issue, points in zip(selected, [2.5, 3.5, 0.5], strict=True):
            issue["fields"]["customfield_10001"] = points
        return selected
    for issue in issues:
        _apply_scenario(issue, scenario)
    if scenario == "reopened":
        issue = issues[0]
        issue["fields"]["resolutiondate"] = None
        issue["fields"]["status"] = {
            "name": "In Progress",
            "statusCategory": {"key": "indeterminate"},
        }
        issue["changelog"]["histories"].append(
            _transition("status", "Done", "In Progress", AS_OF - timedelta(days=2))
        )
        issue["fields"]["updated"] = (AS_OF - timedelta(days=2)).isoformat()
        issues[1]["changelog"]["histories"].append(
            _transition(
                "Sprint", "Demo Sprint 1", "Demo Sprint 2", START + timedelta(days=8)
            )
        )
        issues[1]["fields"]["customfield_10002"] = [_sprint(1)]
        issues[1]["fields"]["updated"] = (START + timedelta(days=8)).isoformat()
        issues[2]["changelog"]["histories"].append(
            _transition("Sprint", "Demo Sprint 1", "", START + timedelta(days=9))
        )
        issues[2]["fields"]["customfield_10002"] = []
        issues[2]["fields"]["updated"] = (START + timedelta(days=9)).isoformat()
    if scenario == "scope-change":
        _change_scope(issues)
    return issues
