"""
Sample profile and query data fixtures for testing.

Provides realistic test data that matches the profile/query data model.
"""

from typing import Dict, List

import pytest


@pytest.fixture
def sample_profile_data() -> Dict:
    """
    Generate realistic profile configuration data.

    Returns:
        dict: Profile configuration matching profile.json structure

    Example:
        def test_profile_creation(sample_profile_data):
            profile = Profile.from_dict(sample_profile_data)
            assert profile.name == "Test Profile"
    """
    return {
        "id": "profile-test-001",
        "name": "Test Profile",
        "description": "Test profile for unit tests",
        "created_at": "2025-11-13T10:00:00.000000",
        "last_used": "2025-11-13T10:00:00.000000",
        "forecast_settings": {
            "pert_factor": 1.5,
            "deadline": "2025-12-31",
            "data_points_count": 12,
        },
        "jira_config": {
            "base_url": "https://jira.example.com",
            "token": "test-token-12345",
            "api_version": "v2",
            "points_field": "customfield_10002",
            "cache_size_mb": 100,
            "max_results_per_call": 100,
        },
        "field_mappings": {
            "deployment_date": "customfield_10001",
            "deployment_successful": "customfield_10002",
            "work_type": "customfield_10005",
            "work_item_size": "customfield_10002",
        },
        "project_config": {
            "devops_projects": [],
            "development_projects": ["TEST"],
            "devops_task_types": ["Task", "Sub-task"],
            "bug_types": ["Bug"],
            "story_types": ["Story"],
            "task_types": ["Task"],
        },
        "queries": [],
    }


@pytest.fixture
def sample_query_data() -> Dict:
    """
    Generate realistic query configuration data.

    Returns:
        dict: Query configuration matching query.json structure

    Example:
        def test_query_creation(sample_query_data):
            query = Query.from_dict(sample_query_data)
            assert query.jql_query == "project = TEST"
    """
    return {
        "id": "query-test-001",
        "name": "Test Query",
        "description": "Test query for unit tests",
        "jql_query": "project = TEST AND created >= -12w ORDER BY created DESC",
        "created_at": "2025-11-13T10:00:00.000000",
        "last_used": "2025-11-13T10:00:00.000000",
    }


@pytest.fixture
def sample_profiles_registry() -> Dict:
    """
    Generate realistic profiles registry data.

    Returns:
        dict: Profiles registry matching profiles.json structure

    Example:
        def test_switch_profile(sample_profiles_registry):
            registry = sample_profiles_registry
            assert registry["active_profile_id"] == "profile-test-001"
    """
    return {
        "version": "3.0",
        "active_profile_id": "profile-test-001",
        "active_query_id": "query-test-001",
        "profiles": [
            {
                "id": "profile-test-001",
                "name": "Test Profile",
                "description": "Test profile for unit tests",
                "created_at": "2025-11-13T10:00:00.000000",
                "last_used": "2025-11-13T10:00:00.000000",
                "jira_base_url": "https://jira.example.com",
                "pert_factor": 1.5,
                "deadline": "2025-12-31",
                "default_query_id": "query-test-001",
                "query_count": 1,
            }
        ],
    }


@pytest.fixture
def multiple_profile_configs() -> List[Dict]:
    """
    Generate multiple profile configurations for testing multi-profile scenarios.

    Returns:
        list: List of profile configurations

    Example:
        def test_multiple_profiles(multiple_profile_configs):
            assert len(multiple_profile_configs) == 3
            assert multiple_profile_configs[0]["name"] == "Apache Kafka Analysis"
    """
    return [
        {
            "id": "profile-kafka-001",
            "name": "Apache Kafka Analysis",
            "description": "Apache Kafka project analysis with 1.5x PERT factor",
            "forecast_settings": {
                "pert_factor": 1.5,
                "deadline": "2025-12-31",
                "data_points_count": 12,
            },
            "jira_config": {
                "base_url": "https://issues.apache.org/jira",
                "points_field": "customfield_10016",
            },
            "queries": [],
        },
        {
            "id": "profile-infra-002",
            "name": "Infrastructure Team",
            "description": "Infrastructure tracking with conservative 2.0x PERT",
            "forecast_settings": {
                "pert_factor": 2.0,
                "deadline": "2025-06-30",
                "data_points_count": 12,
            },
            "jira_config": {
                "base_url": "https://jira.example.com",
                "points_field": "customfield_10002",
            },
            "queries": [],
        },
        {
            "id": "profile-product-003",
            "name": "Product Team Sprint",
            "description": "Product team sprint analysis with 1.3x PERT",
            "forecast_settings": {
                "pert_factor": 1.3,
                "deadline": "2025-11-30",
                "data_points_count": 12,
            },
            "jira_config": {
                "base_url": "https://company.atlassian.net",
                "points_field": "customfield_10016",
            },
            "queries": [],
        },
    ]


@pytest.fixture
def multiple_query_configs() -> List[Dict]:
    """
    Generate multiple query configurations for testing multi-query scenarios.

    Returns:
        list: List of query configurations

    Example:
        def test_multiple_queries(multiple_query_configs):
            assert len(multiple_query_configs) == 3
            assert "12 Weeks" in multiple_query_configs[0]["name"]
    """
    return [
        {
            "id": "query-12w-001",
            "name": "Last 12 Weeks",
            "description": "Last 12 weeks for sprint retrospective analysis",
            "jql_query": "project = TEST AND created >= -12w ORDER BY created DESC",
            "created_at": "2025-11-01T10:00:00.000000",
            "last_used": "2025-11-13T10:00:00.000000",
        },
        {
            "id": "query-52w-002",
            "name": "Last 52 Weeks",
            "description": "Yearly analysis for long-term trends",
            "jql_query": "project = TEST AND created >= -52w ORDER BY created DESC",
            "created_at": "2025-11-01T10:30:00.000000",
            "last_used": "2025-11-12T14:30:00.000000",
        },
        {
            "id": "query-bugs-003",
            "name": "Bugs Only",
            "description": "Bug analysis for quality metrics",
            "jql_query": "project = TEST AND type = Bug AND created >= -12w",
            "created_at": "2025-11-01T11:00:00.000000",
            "last_used": "2025-11-11T16:00:00.000000",
        },
    ]
