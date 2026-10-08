import pytest


@pytest.fixture
def sample_jira_issue() -> dict:

    return {
        "key": "TEST-1",
        "id": "10001",
        "fields": {
            "summary": "Test issue for unit tests",
            "description": "This is a test issue description",
            "created": "2025-11-01T10:00:00.000+0000",
            "updated": "2025-11-13T10:00:00.000+0000",
            "status": {
                "name": "Done",
                "id": "10001",
            },
            "issuetype": {
                "name": "Story",
                "id": "10001",
            },
            "priority": {
                "name": "Medium",
                "id": "3",
            },
            "project": {
                "key": "TEST",
                "name": "Test Project",
            },
            "customfield_10002": 5,
        },
    }


@pytest.fixture
def sample_jira_cache_data(sample_jira_issue) -> dict:

    return {
        "version": "2.0",
        "jql_query": "project = TEST AND created >= -12w ORDER BY created DESC",
        "fields": (
            "key,summary,status,created,updated,issuetype,priority,customfield_10002"
        ),
        "cached_at": "2025-11-13T10:00:00.000000",
        "issue_count": 150,
        "issues": [sample_jira_issue] * 150,
    }


@pytest.fixture
def sample_jira_response_page_1() -> dict:

    base_issue = {
        "key": "TEST-",
        "fields": {
            "summary": "Test issue",
            "created": "2025-11-01T10:00:00.000+0000",
            "status": {"name": "Done"},
            "issuetype": {"name": "Story"},
            "customfield_10002": 5,
        },
    }

    issues = []
    for i in range(1, 101):
        issue = base_issue.copy()
        issue["key"] = f"TEST-{i}"
        issue["fields"] = base_issue["fields"].copy()
        issue["fields"]["summary"] = f"Test issue {i}"
        issues.append(issue)

    return {
        "startAt": 0,
        "maxResults": 100,
        "total": 150,
        "issues": issues,
    }


@pytest.fixture
def sample_jira_response_page_2() -> dict:

    base_issue = {
        "key": "TEST-",
        "fields": {
            "summary": "Test issue",
            "created": "2025-11-01T10:00:00.000+0000",
            "status": {"name": "Done"},
            "issuetype": {"name": "Story"},
            "customfield_10002": 5,
        },
    }

    issues = []
    for i in range(101, 151):
        issue = base_issue.copy()
        issue["key"] = f"TEST-{i}"
        issue["fields"] = base_issue["fields"].copy()
        issue["fields"]["summary"] = f"Test issue {i}"
        issues.append(issue)

    return {
        "startAt": 100,
        "maxResults": 100,
        "total": 150,
        "issues": issues,
    }


@pytest.fixture
def large_jira_cache_50mb() -> bytes:

    import json

    base_issue = {
        "key": "PERF-",
        "fields": {
            "summary": "Performance test issue with long description" * 100,
            "description": "Long description for performance testing" * 500,
            "created": "2025-11-01T10:00:00.000+0000",
            "status": {"name": "Done"},
            "issuetype": {"name": "Story"},
            "customfield_10002": 5,
        },
    }

    target_size = 50 * 1024 * 1024
    issues = []
    issue_size = len(json.dumps(base_issue))
    num_issues = target_size // issue_size

    for i in range(num_issues):
        issue = base_issue.copy()
        issue["key"] = f"PERF-{i}"
        issue["fields"] = base_issue["fields"].copy()
        issues.append(issue)

    cache_data = {
        "version": "2.0",
        "jql_query": "project = PERF",
        "cached_at": "2025-11-13T10:00:00.000000",
        "issue_count": len(issues),
        "issues": issues,
    }

    return json.dumps(cache_data).encode("utf-8")
