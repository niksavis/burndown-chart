"""
Sample JIRA cache data fixtures for testing.

Provides mock JIRA API response data for testing without real API calls.
"""

from typing import Dict

import pytest


@pytest.fixture
def sample_jira_issue() -> Dict:
    """
    Generate a single realistic JIRA issue.

    Returns:
        dict: JIRA issue in API response format

    Example:
        def test_issue_processing(sample_jira_issue):
            assert sample_jira_issue["key"] == "TEST-1"
            assert sample_jira_issue["fields"]["summary"]
    """
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
            "customfield_10002": 5,  # Story points
        },
    }


@pytest.fixture
def sample_jira_cache_data(sample_jira_issue) -> Dict:
    """
    Generate realistic JIRA cache file content.

    Returns:
        dict: Complete JIRA cache structure

    Example:
        def test_cache_loading(sample_jira_cache_data):
            issues = sample_jira_cache_data["issues"]
            assert len(issues) > 0
    """
    return {
        "version": "2.0",
        "jql_query": "project = TEST AND created >= -12w ORDER BY created DESC",
        "fields": "key,summary,status,created,updated,issuetype,priority,customfield_10002",
        "cached_at": "2025-11-13T10:00:00.000000",
        "issue_count": 150,
        "issues": [sample_jira_issue] * 150,  # Simulate 150 issues
    }


@pytest.fixture
def sample_jira_response_page_1() -> Dict:
    """
    Generate first page of paginated JIRA API response.

    Returns:
        dict: JIRA API response page 1 (100 issues)

    Example:
        def test_pagination(sample_jira_response_page_1):
            assert sample_jira_response_page_1["total"] == 150
            assert len(sample_jira_response_page_1["issues"]) == 100
    """
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
    for i in range(1, 101):  # Issues 1-100
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
def sample_jira_response_page_2() -> Dict:
    """
    Generate second page of paginated JIRA API response.

    Returns:
        dict: JIRA API response page 2 (remaining 50 issues)

    Example:
        def test_pagination_complete(sample_jira_response_page_2):
            assert sample_jira_response_page_2["startAt"] == 100
            assert len(sample_jira_response_page_2["issues"]) == 50
    """
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
    for i in range(101, 151):  # Issues 101-150
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
    """
    Generate large JIRA cache data (~50MB) for migration performance testing.

    Returns:
        bytes: JSON-encoded cache data (~50MB)

    Example:
        def test_migration_large_cache(large_jira_cache_50mb):
            # Test migration performance with large cache
            assert len(large_jira_cache_50mb) > 50 * 1024 * 1024
    """
    import json

    # Create large cache by duplicating issues
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

    # Generate enough issues to reach ~50MB
    target_size = 50 * 1024 * 1024  # 50MB
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
