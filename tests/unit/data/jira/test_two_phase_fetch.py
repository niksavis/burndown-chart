"""Tests for two-phase JIRA fetch behavior and fallback logic."""

from data.jira.two_phase_fetch import (
    build_devops_linked_jql,
    fetch_jira_issues_two_phase,
)


def test_two_phase_falls_back_to_linked_issues_when_fixversion_fetch_empty() -> None:
    """When fixVersion filtering returns no RI tasks, linked fallback should run."""
    user_jql = 'project = "DEV"'
    config = {
        "jql_query": user_jql,
        "devops_projects": ["RI"],
        "devops_task_types": ["Operational Task"],
    }

    dev_issues = [
        {"key": "DEV-2", "fields": {"fixVersions": [{"name": "MS-FLOW-001"}]}},
        {"key": "DEV-1", "fields": {"fixVersions": [{"name": "MS-FLOW-001"}]}},
    ]
    linked_devops_issues = [
        {
            "key": "RI-1",
            "fields": {"fixVersions": [{"name": "R_20260422_www.drei.at_1"}]},
        }
    ]

    jql_calls: list[str] = []

    def fake_fetch(
        config_arg: dict, _max_results: int | None
    ) -> tuple[bool, list[dict]]:
        jql = config_arg["jql_query"]
        jql_calls.append(jql)

        if jql == user_jql:
            return True, dev_issues
        if "fixVersion" in jql:
            return True, []
        if "linkedIssuesOf" in jql:
            return True, linked_devops_issues
        return False, []

    success, merged_issues = fetch_jira_issues_two_phase(
        config=config,
        max_results=100,
        fetch_paginated_func=fake_fetch,
    )

    assert success is True
    assert len(jql_calls) == 3
    assert any("linkedIssuesOf" in jql for jql in jql_calls)

    merged_keys = {issue["key"] for issue in merged_issues}
    assert merged_keys == {"DEV-1", "DEV-2", "RI-1"}


def test_two_phase_uses_linked_fallback_when_no_fixversions_in_dev_issues() -> None:
    """When dev issues have no fixVersions, linked fallback should fetch RI tasks."""
    user_jql = 'project = "DEV"'
    config = {
        "jql_query": user_jql,
        "devops_projects": ["RI"],
        "devops_task_types": ["Operational Task"],
    }

    dev_issues = [
        {"key": "DEV-100", "fields": {"fixVersions": []}},
        {"key": "DEV-101", "fields": {}},
    ]
    linked_devops_issues = [{"key": "RI-77", "fields": {"fixVersions": []}}]

    jql_calls: list[str] = []

    def fake_fetch(
        config_arg: dict, _max_results: int | None
    ) -> tuple[bool, list[dict]]:
        jql = config_arg["jql_query"]
        jql_calls.append(jql)

        if jql == user_jql:
            return True, dev_issues
        if "linkedIssuesOf" in jql:
            return True, linked_devops_issues
        return False, []

    success, merged_issues = fetch_jira_issues_two_phase(
        config=config,
        max_results=100,
        fetch_paginated_func=fake_fetch,
    )

    assert success is True
    assert len(jql_calls) == 2
    assert any("linkedIssuesOf" in jql for jql in jql_calls)

    merged_keys = {issue["key"] for issue in merged_issues}
    assert merged_keys == {"DEV-100", "DEV-101", "RI-77"}


def test_build_devops_linked_jql_batches_large_key_lists() -> None:
    """linkedIssuesOf clauses should be batched to avoid oversized subqueries."""
    issue_keys = [f"DEV-{n}" for n in range(1, 402)]

    jql = build_devops_linked_jql(
        devops_projects=["RI"],
        devops_task_types=["Operational Task"],
        development_issue_keys=issue_keys,
        batch_size=200,
    )

    assert jql.count("linkedIssuesOf(") == 3
    assert " OR " in jql
