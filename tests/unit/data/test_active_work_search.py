"""Unit tests for Active Work search grammar."""

from data.active_work_search import filter_timeline_by_query, is_strict_query_valid


def _timeline() -> list[dict]:
    return [
        {
            "epic_key": "E-1",
            "child_issues": [
                {
                    "issue_key": "A-1",
                    "summary": "Backend and frontend task",
                    "assignee": "Jack",
                    "issue_type": "Bug",
                    "project_key": "A942",
                    "project_name": "Project A",
                    "labels": ["Backend", "Frontend"],
                    "components": ["API"],
                    "health_indicators": {"is_completed": False},
                },
                {
                    "issue_key": "A-2",
                    "summary": "Backend only",
                    "assignee": "Jane",
                    "issue_type": "Task",
                    "project_key": "A942",
                    "project_name": "Project A",
                    "labels": ["Backend"],
                    "components": ["DB"],
                    "health_indicators": {"is_completed": False},
                },
                {
                    "issue_key": "A-3",
                    "summary": "Frontend only",
                    "assignee": "Kiss,Mate",
                    "issue_type": "Task",
                    "project_key": "A942",
                    "project_name": "Project A",
                    "labels": ["Frontend"],
                    "components": ["UI"],
                    "health_indicators": {"is_completed": False},
                },
            ],
        }
    ]


def _issue_keys(filtered: list[dict]) -> list[str]:
    keys: list[str] = []
    for epic in filtered:
        keys.extend(issue["issue_key"] for issue in epic.get("child_issues", []))
    return keys


def test_semicolon_is_or_within_field() -> None:
    filtered = filter_timeline_by_query(_timeline(), "labels:backend;frontend")
    assert set(_issue_keys(filtered)) == {"A-1", "A-2", "A-3"}


def test_comma_is_and_within_field() -> None:
    filtered = filter_timeline_by_query(_timeline(), "labels:backend,frontend")
    assert _issue_keys(filtered) == ["A-1"]


def test_field_and_operator_and() -> None:
    filtered = filter_timeline_by_query(
        _timeline(), "labels:backend;frontend & assignee:jack"
    )
    assert _issue_keys(filtered) == ["A-1"]


def test_parentheses_with_or_and() -> None:
    filtered = filter_timeline_by_query(
        _timeline(),
        '(labels:backend,frontend | assignee:"kiss,mate") & issuetype:task',
    )
    assert _issue_keys(filtered) == ["A-3"]


def test_strict_query_valid_for_enum_values() -> None:
    assert is_strict_query_valid(_timeline(), "labels:Backend,Frontend & assignee:Jack")


def test_strict_query_invalid_for_unknown_enum_value() -> None:
    assert not is_strict_query_valid(_timeline(), "labels:BackendX")


def test_strict_query_allows_summary_free_text() -> None:
    assert is_strict_query_valid(_timeline(), "summary:anything-you-type")


def test_filter_supports_quoted_value_with_comma() -> None:
    filtered = filter_timeline_by_query(_timeline(), 'assignee:"kiss,mate"')
    assert _issue_keys(filtered) == ["A-3"]


def test_strict_query_valid_for_quoted_comma_value() -> None:
    assert is_strict_query_valid(_timeline(), 'assignee:"Kiss,Mate"')


def test_strict_query_invalid_for_unquoted_comma_value() -> None:
    assert not is_strict_query_valid(_timeline(), "assignee:Kiss,Mate")
