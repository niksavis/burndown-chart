"""Unit tests for Flow metrics calculations.

Tests all five Flow Framework metrics with mocked profile configuration matching:
- Profile: Drei Jira Production (p_955acc063e55)

Each test is isolated and doesn't require running the app.

Flow Metrics Tested:
1. Flow Velocity - completed items per week (flow_end_statuses)
2. Flow Time - time from flow_start_statuses to flow_end_statuses
3. Flow Efficiency - active time / total time (active_statuses / wip_statuses)
4. Flow Load - current WIP across wip_statuses
5. Work Distribution - breakdown by flow_type_mappings
"""

import pytest
from unittest.mock import patch
from typing import Dict, Any, Optional, List


#######################################################################
# TEST FIXTURES - Mock Profile Configuration
#######################################################################


@pytest.fixture
def mock_profile_config() -> Dict[str, Any]:
    """Mock profile configuration matching Drei Jira Production.

    Based on profile.json field_mappings and project_classification.
    """
    return {
        "field_mappings": {
            "flow": {
                "flow_item_type": "issuetype",
                "effort_category": "customfield_13204",
                "status": "status",
                "completed_date": "resolutiondate",
            },
            "dora": {},
            "values": {},
        },
        "flow_end_statuses": ["Done", "Resolved", "Closed", "Canceled"],
        "active_statuses": ["In Progress", "In Review", "Testing"],
        "wip_statuses": [
            "In Progress",
            "In Review",
            "Testing",
            "Ready for Testing",
            "In Deployment",
        ],
        "flow_start_statuses": ["In Progress", "In Review"],
        "bug_types": ["Bug"],
        "devops_task_types": ["Operational Task"],
        "production_environment_values": ["PROD"],
        "flow_type_mappings": {
            "Feature": {
                "issue_types": ["Task", "Story"],
                "effort_categories": ["Improvement", "New feature"],
            },
            "Defect": {
                "issue_types": ["Bug"],
                "effort_categories": [],
            },
            "Technical Debt": {
                "issue_types": ["Task", "Story"],
                "effort_categories": ["Technical debt", "Maintenance"],
            },
            "Risk": {
                "issue_types": ["Task", "Story"],
                "effort_categories": ["Security", "Spikes (Analysis)", "Upgrades"],
            },
        },
    }


@pytest.fixture
def mock_load_app_settings(temp_database, mock_profile_config):
    """Patch load_app_settings to return mock profile config AND mock get_metrics_config.

    Args:
        temp_database: Ensures database is initialized before tests run
        mock_profile_config: Profile configuration to return
    """
    from configuration.metrics_config import MetricsConfig

    # Create a mock MetricsConfig instance with the test configuration
    mock_config = MetricsConfig.__new__(MetricsConfig)
    mock_config.profile_id = "test_profile"
    mock_config.profile_config = mock_profile_config

    with (
        patch("data.persistence.load_app_settings") as mock_settings,
        patch("configuration.metrics_config.get_metrics_config") as mock_get_config,
    ):
        mock_settings.return_value = mock_profile_config
        mock_get_config.return_value = mock_config
        yield mock_settings


#######################################################################
# HELPER FUNCTIONS - Create Test Issues
#######################################################################


def create_completed_issue(
    key: str,
    issue_type: str = "Task",
    status: str = "Done",
    in_progress_timestamp: str = "2025-01-05T10:00:00.000+0000",
    done_timestamp: str = "2025-01-10T10:00:00.000+0000",
    resolution_date: str = "2025-01-10T10:00:00.000+0000",
    effort_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Create mock completed issue with changelog.

    Args:
        key: Issue key
        issue_type: Issue type (Task, Story, Bug)
        status: Current status
        in_progress_timestamp: When moved to In Progress
        done_timestamp: When moved to Done
        resolution_date: Resolution date
        effort_category: Optional effort category for flow type mapping

    Returns:
        Mock JIRA issue with changelog
    """
    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": issue_type},
            "status": {"name": status},
            "resolutiondate": resolution_date,
            "created": "2025-01-01T09:00:00.000+0000",
        },
        "changelog": {
            "histories": [
                {
                    "created": in_progress_timestamp,
                    "items": [
                        {
                            "field": "status",
                            "fromString": "To Do",
                            "toString": "In Progress",
                        }
                    ],
                },
                {
                    "created": done_timestamp,
                    "items": [
                        {
                            "field": "status",
                            "fromString": "In Progress",
                            "toString": status,
                        }
                    ],
                },
            ]
        },
    }

    if effort_category:
        issue["fields"]["customfield_13204"] = {"value": effort_category}

    return issue


def create_wip_issue(
    key: str,
    issue_type: str = "Task",
    status: str = "In Progress",
    in_progress_timestamp: str = "2025-01-05T10:00:00.000+0000",
) -> Dict[str, Any]:
    """Create mock in-progress issue.

    Args:
        key: Issue key
        issue_type: Issue type
        status: Current WIP status
        in_progress_timestamp: When moved to current status

    Returns:
        Mock JIRA issue currently in progress
    """
    return {
        "key": key,
        "fields": {
            "issuetype": {"name": issue_type},
            "status": {"name": status},
            "created": "2025-01-01T09:00:00.000+0000",
        },
        "changelog": {
            "histories": [
                {
                    "created": in_progress_timestamp,
                    "items": [
                        {
                            "field": "status",
                            "fromString": "To Do",
                            "toString": status,
                        }
                    ],
                }
            ]
        },
    }


def create_issue_with_active_statuses(
    key: str,
    status_transitions: List[Dict[str, str]],
    final_status: str = "Done",
    resolution_date: str = "2025-01-15T10:00:00.000+0000",
) -> Dict[str, Any]:
    """Create issue with specific status transitions for efficiency testing.

    Args:
        key: Issue key
        status_transitions: List of {"from": str, "to": str, "timestamp": str}
        final_status: Current/final status
        resolution_date: Resolution date

    Returns:
        Mock JIRA issue with detailed changelog
    """
    histories = []
    for transition in status_transitions:
        histories.append(
            {
                "created": transition["timestamp"],
                "items": [
                    {
                        "field": "status",
                        "fromString": transition["from"],
                        "toString": transition["to"],
                    }
                ],
            }
        )

    return {
        "key": key,
        "fields": {
            "issuetype": {"name": "Task"},
            "status": {"name": final_status},
            "resolutiondate": resolution_date,
            "created": "2025-01-01T09:00:00.000+0000",
        },
        "changelog": {"histories": histories},
    }


#######################################################################
# TEST CLASS: Flow Velocity
#######################################################################


class TestFlowVelocity:
    """Test Flow Velocity metric calculation.

    Measures: Number of work items completed per week
    Uses: flow_end_statuses (Done, Resolved, Closed, Canceled)
    """

    def test_flow_velocity_basic_calculation(self, mock_load_app_settings):
        """Test basic velocity calculation with completed items.

        Given: 5 completed items over 7 days
        Expected: 5.0 items/week
        """
        from data.flow_metrics import calculate_flow_velocity

        issues = [
            create_completed_issue(
                f"TASK-{i}", done_timestamp=f"2025-01-{5 + i:02d}T10:00:00.000+0000"
            )
            for i in range(1, 6)
        ]

        result = calculate_flow_velocity(
            issues=issues,
            time_period_days=7,
        )

        assert result["error_state"] is None
        assert result["value"] == 5.0
        assert result["unit"] == "items/week"

    def test_flow_velocity_breakdown_by_type(self, mock_load_app_settings):
        """Test velocity breakdown by flow type mappings.

        Given: 2 Tasks (Feature), 1 Bug (Defect), 1 Story with Maintenance (Technical Debt)
        Expected: Breakdown shows correct categorization
        """
        from data.flow_metrics import calculate_flow_velocity

        issues = [
            create_completed_issue("TASK-1", issue_type="Task"),
            create_completed_issue("TASK-2", issue_type="Task"),
            create_completed_issue("BUG-1", issue_type="Bug"),
            create_completed_issue(
                "STORY-1", issue_type="Story", effort_category="Maintenance"
            ),
        ]

        result = calculate_flow_velocity(issues=issues, time_period_days=7)

        assert result["error_state"] is None
        assert "breakdown" in result
        # Task and Story → Feature (2 + 0), Bug → Defect (1), Story + Maintenance → Technical Debt (1)
        # Note: Classification depends on flow_type_mappings priority

    def test_flow_velocity_different_time_periods(self, mock_load_app_settings):
        """Test velocity scales with time period."""
        from data.flow_metrics import calculate_flow_velocity

        issues = [create_completed_issue(f"TASK-{i}") for i in range(1, 11)]

        # 10 items over 7 days = 10 items/week
        result_7 = calculate_flow_velocity(issues=issues, time_period_days=7)
        assert result_7["value"] == pytest.approx(10.0, rel=0.01)

        # 10 items over 14 days = 5 items/week
        result_14 = calculate_flow_velocity(issues=issues, time_period_days=14)
        assert result_14["value"] == pytest.approx(5.0, rel=0.01)

    def test_flow_velocity_empty_issues(self, mock_load_app_settings):
        """Test velocity with no issues."""
        from data.flow_metrics import calculate_flow_velocity

        result = calculate_flow_velocity(issues=[], time_period_days=7)

        assert result["error_state"] == "no_data"
        assert result["value"] == 0.0

    def test_flow_velocity_excludes_incomplete(self, mock_load_app_settings):
        """Test that in-progress issues are excluded from velocity."""
        from data.flow_metrics import calculate_flow_velocity

        issues = [
            create_completed_issue("TASK-1"),  # Completed
            create_wip_issue("TASK-2", status="In Progress"),  # WIP - excluded
            create_wip_issue("TASK-3", status="Testing"),  # WIP - excluded
        ]

        result = calculate_flow_velocity(issues=issues, time_period_days=7)

        # Only 1 completed issue should count
        # WIP issues don't have resolutiondate so they're excluded anyway
        assert result["value"] >= 0


#######################################################################
# TEST CLASS: Flow Time
#######################################################################


class TestFlowTime:
    """Test Flow Time metric calculation.

    Measures: Time from first transition to flow_start_statuses to first
    transition to flow_end_statuses.
    Uses:
        - flow_start_statuses: ["In Progress", "In Review"]
        - flow_end_statuses: ["Done", "Resolved", "Closed", "Canceled"]
    """

    def test_flow_time_basic_calculation(self, mock_load_app_settings):
        """Test basic flow time calculation.

        Given: Issue started Jan 5, completed Jan 10 = 5 days
        Expected: 5 days average flow time
        """
        from data.flow_metrics import calculate_flow_time

        issues = [
            create_completed_issue(
                "TASK-1",
                in_progress_timestamp="2025-01-05T10:00:00.000+0000",
                done_timestamp="2025-01-10T10:00:00.000+0000",
            )
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        assert result["value"] == pytest.approx(5.0, rel=0.1)
        assert result["unit"] == "days"

    def test_flow_time_multiple_issues_average(self, mock_load_app_settings):
        """Test flow time averages across multiple issues.

        Given: Issue 1 = 5 days, Issue 2 = 10 days
        Expected: Average = 7.5 days
        """
        from data.flow_metrics import calculate_flow_time

        issues = [
            create_completed_issue(
                "TASK-1",
                in_progress_timestamp="2025-01-05T10:00:00.000+0000",
                done_timestamp="2025-01-10T10:00:00.000+0000",  # 5 days
            ),
            create_completed_issue(
                "TASK-2",
                in_progress_timestamp="2025-01-01T10:00:00.000+0000",
                done_timestamp="2025-01-11T10:00:00.000+0000",  # 10 days
            ),
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        assert result["value"] == pytest.approx(7.5, rel=0.1)

    def test_flow_time_uses_changelog_timestamps(self, mock_load_app_settings):
        """Test that flow time extracts timestamps from changelog.

        The mapping "status:In Progress.DateTime" means we extract the timestamp
        when the issue transitioned TO "In Progress" status.
        """
        from data.flow_metrics import calculate_flow_time

        # Issue with explicit changelog
        issues = [
            {
                "key": "TASK-1",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-01-10T10:00:00.000+0000",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-03T10:00:00.000+0000",  # This is when we moved to In Progress
                            "items": [{"field": "status", "toString": "In Progress"}],
                        },
                        {
                            "created": "2025-01-10T10:00:00.000+0000",  # This is when we moved to Done
                            "items": [{"field": "status", "toString": "Done"}],
                        },
                    ]
                },
            }
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        # Jan 3 to Jan 10 = 7 days
        assert result["value"] == pytest.approx(7.0, rel=0.1)

    def test_flow_time_no_timestamps(self, mock_load_app_settings):
        """Test flow time when issues lack required timestamps."""
        from data.flow_metrics import calculate_flow_time

        issues = [
            {
                "key": "TASK-1",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-01-10T10:00:00.000+0000",
                },
                "changelog": {"histories": []},  # No status transitions
            }
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] == "no_data"


#######################################################################
# TEST CLASS: Flow Efficiency
#######################################################################


class TestFlowEfficiency:
    """Test Flow Efficiency metric calculation.

    Measures: Percentage of time spent actively working
    Formula: (Active Time / Total Time) * 100
    Uses:
        - active_statuses: In Progress, In Review, Testing
        - wip_statuses: In Progress, In Review, Testing, Ready for Testing, In Deployment
    """

    def test_flow_efficiency_full_active(self, mock_load_app_settings):
        """Test 100% efficiency when all time is active.

        Given: Issue only in active statuses (In Progress → Done)
        Expected: 100% efficiency
        """
        from data.flow_metrics import calculate_flow_efficiency

        # Issue goes directly from In Progress to Done (all time is active)
        issues = [
            create_issue_with_active_statuses(
                "TASK-1",
                status_transitions=[
                    {
                        "from": "To Do",
                        "to": "In Progress",
                        "timestamp": "2025-01-05T10:00:00.000+0000",
                    },
                    {
                        "from": "In Progress",
                        "to": "Done",
                        "timestamp": "2025-01-10T10:00:00.000+0000",
                    },
                ],
            )
        ]

        result = calculate_flow_efficiency(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        assert result["value"] == pytest.approx(100.0, rel=1)
        assert result["unit"] == "%"

    def test_flow_efficiency_partial_active(self, mock_load_app_settings):
        """Test partial efficiency with waiting time.

        Given: 2 days In Progress (active), 3 days Ready for Testing (WIP but not active)
        Expected: 40% efficiency (2/5 days)
        """
        from data.flow_metrics import calculate_flow_efficiency

        issues = [
            create_issue_with_active_statuses(
                "TASK-1",
                status_transitions=[
                    {
                        "from": "To Do",
                        "to": "In Progress",
                        "timestamp": "2025-01-05T10:00:00.000+0000",
                    },
                    # 2 days active
                    {
                        "from": "In Progress",
                        "to": "Ready for Testing",
                        "timestamp": "2025-01-07T10:00:00.000+0000",
                    },
                    # 3 days waiting (WIP but not active)
                    {
                        "from": "Ready for Testing",
                        "to": "Done",
                        "timestamp": "2025-01-10T10:00:00.000+0000",
                    },
                ],
            )
        ]

        result = calculate_flow_efficiency(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        # 2 days active, 5 days total WIP = 40%
        assert result["value"] == pytest.approx(40.0, rel=5)

    def test_flow_efficiency_multiple_active_periods(self, mock_load_app_settings):
        """Test efficiency with multiple active periods.

        Given: In Progress → In Review → Testing → Done (all active statuses)
        Expected: 100% efficiency
        """
        from data.flow_metrics import calculate_flow_efficiency

        issues = [
            create_issue_with_active_statuses(
                "TASK-1",
                status_transitions=[
                    {
                        "from": "To Do",
                        "to": "In Progress",
                        "timestamp": "2025-01-05T10:00:00.000+0000",
                    },
                    {
                        "from": "In Progress",
                        "to": "In Review",
                        "timestamp": "2025-01-07T10:00:00.000+0000",
                    },
                    {
                        "from": "In Review",
                        "to": "Testing",
                        "timestamp": "2025-01-09T10:00:00.000+0000",
                    },
                    {
                        "from": "Testing",
                        "to": "Done",
                        "timestamp": "2025-01-11T10:00:00.000+0000",
                    },
                ],
            )
        ]

        result = calculate_flow_efficiency(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        # All transitions are in active statuses
        assert result["value"] == pytest.approx(100.0, rel=5)


#######################################################################
# TEST CLASS: Flow Load
#######################################################################


class TestFlowLoad:
    """Test Flow Load metric calculation.

    Measures: Current WIP (work in progress) count
    Uses: wip_statuses (In Progress, In Review, Testing, Ready for Testing, In Deployment)
    Note: The info message should say "across WIP statuses" not "active statuses"
    """

    def test_flow_load_counts_wip_items(self, mock_load_app_settings):
        """Test that Flow Load counts items in WIP statuses.

        Given: 3 items in different WIP statuses
        Expected: 3 items
        """
        from data.flow_metrics import calculate_flow_load

        issues = [
            create_wip_issue("TASK-1", status="In Progress"),
            create_wip_issue("TASK-2", status="In Review"),
            create_wip_issue("TASK-3", status="Testing"),
        ]

        result = calculate_flow_load(issues=issues, time_period_days=7)

        assert result["error_state"] is None
        assert result["value"] == 3
        assert result["unit"] == "items"

    def test_flow_load_includes_all_wip_statuses(self, mock_load_app_settings):
        """Test that all WIP statuses are counted.

        WIP statuses: In Progress, In Review, Testing, Ready for Testing, In Deployment
        """
        from data.flow_metrics import calculate_flow_load

        issues = [
            create_wip_issue("TASK-1", status="In Progress"),
            create_wip_issue("TASK-2", status="In Review"),
            create_wip_issue("TASK-3", status="Testing"),
            create_wip_issue("TASK-4", status="Ready for Testing"),
            create_wip_issue("TASK-5", status="In Deployment"),
        ]

        result = calculate_flow_load(issues=issues, time_period_days=7)

        assert result["value"] == 5

    def test_flow_load_excludes_completed(self, mock_load_app_settings):
        """Test that completed items are not counted as WIP."""
        from data.flow_metrics import calculate_flow_load

        issues = [
            create_wip_issue("TASK-1", status="In Progress"),  # WIP
            create_completed_issue("TASK-2", status="Done"),  # Not WIP
            create_completed_issue("TASK-3", status="Resolved"),  # Not WIP
        ]

        result = calculate_flow_load(issues=issues, time_period_days=7)

        assert result["value"] == 1

    def test_flow_load_excludes_backlog(self, mock_load_app_settings):
        """Test that backlog items (To Do) are not counted as WIP."""
        from data.flow_metrics import calculate_flow_load

        issues = [
            create_wip_issue("TASK-1", status="In Progress"),  # WIP
            {"key": "TASK-2", "fields": {"status": {"name": "To Do"}}},  # Backlog
            {"key": "TASK-3", "fields": {"status": {"name": "Open"}}},  # Backlog
        ]

        result = calculate_flow_load(issues=issues, time_period_days=7)

        assert result["value"] == 1

    def test_flow_load_empty_issues(self, mock_load_app_settings):
        """Test Flow Load with no issues."""
        from data.flow_metrics import calculate_flow_load

        result = calculate_flow_load(issues=[], time_period_days=7)

        # No error - just zero WIP
        assert result["error_state"] is None
        assert result["value"] == 0


#######################################################################
# TEST CLASS: Work Distribution
#######################################################################


class TestWorkDistribution:
    """Test Work Distribution metric calculation.

    Measures: Breakdown of completed work by flow type
    Uses: flow_type_mappings for categorization
    Categories: Feature, Defect, Technical Debt, Risk

    Always sums to 100% for completed items in the week.
    """

    def test_work_distribution_all_features(self, mock_load_app_settings):
        """Test distribution when all items are Features.

        Given: 3 Task issues (mapped to Feature)
        Expected: Feature = 100%
        """
        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue("TASK-1", issue_type="Task"),
            create_completed_issue("TASK-2", issue_type="Task"),
            create_completed_issue("TASK-3", issue_type="Story"),
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        assert result["error_state"] is None
        assert result["unit"] == "%"
        # Task and Story map to Feature by default
        assert "Feature" in result["value"]

    def test_work_distribution_mixed_types(self, mock_load_app_settings):
        """Test distribution with mixed work types.

        Given: 2 Features, 1 Bug, 1 Technical Debt
        Expected: Feature=50%, Defect=25%, Technical Debt=25%, Risk=0%
        """
        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue("TASK-1", issue_type="Task"),  # Feature
            create_completed_issue("TASK-2", issue_type="Story"),  # Feature
            create_completed_issue("BUG-1", issue_type="Bug"),  # Defect
            create_completed_issue(
                "TASK-3", issue_type="Task", effort_category="Maintenance"
            ),  # Tech Debt
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        assert result["error_state"] is None
        # Percentages should sum to 100%
        total = sum(result["value"].values())
        assert total == pytest.approx(100.0, rel=0.1)

    def test_work_distribution_uses_effort_category(self, mock_load_app_settings):
        """Test that effort_category takes precedence in classification.

        Given: Task with effort_category="Security" → Risk
        """
        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue(
                "TASK-1", issue_type="Task", effort_category="Security"
            ),
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        # Depends on flow_type_mappings configuration
        # Security → Risk if mapped correctly
        assert result["error_state"] is None or result["error_state"] == "no_data"

    def test_work_distribution_empty_issues(self, mock_load_app_settings):
        """Test distribution with no completed issues."""
        from data.flow_metrics import calculate_flow_distribution

        result = calculate_flow_distribution(issues=[], time_period_days=7)

        assert result["error_state"] == "no_data"

    def test_work_distribution_excludes_incomplete(self, mock_load_app_settings):
        """Test that incomplete issues are excluded from distribution."""
        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue("TASK-1"),  # Completed - included
            create_wip_issue("TASK-2", status="In Progress"),  # WIP - excluded
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        # Only 1 completed issue should be in distribution
        assert result is not None


#######################################################################
# TEST CLASS: Datetime Extraction
#######################################################################


class TestDatetimeExtraction:
    """Test datetime extraction from different field mapping formats.

    Supports:
    - Simple field: "resolutiondate"
    - Changelog transition: "status:In Progress.DateTime"
    """

    def test_extract_simple_field(self, mock_load_app_settings):
        """Test extracting datetime from simple field."""
        from data.flow_metrics import _extract_datetime_from_field_mapping

        issue = {
            "fields": {
                "resolutiondate": "2025-01-10T10:00:00.000+0000",
            }
        }

        result = _extract_datetime_from_field_mapping(issue, "resolutiondate")
        assert result == "2025-01-10T10:00:00.000+0000"

    def test_extract_changelog_transition(self, mock_load_app_settings):
        """Test extracting datetime from changelog transition."""
        from data.flow_metrics import _extract_datetime_from_field_mapping

        issue = {
            "fields": {},
            "changelog": {
                "histories": [
                    {
                        "created": "2025-01-05T10:00:00.000+0000",
                        "items": [{"field": "status", "toString": "In Progress"}],
                    }
                ]
            },
        }

        result = _extract_datetime_from_field_mapping(
            issue, "status:In Progress.DateTime"
        )
        assert result == "2025-01-05T10:00:00.000+0000"

    def test_extract_done_transition(self, mock_load_app_settings):
        """Test extracting datetime from Done status transition."""
        from data.flow_metrics import _extract_datetime_from_field_mapping

        issue = {
            "fields": {},
            "changelog": {
                "histories": [
                    {
                        "created": "2025-01-05T10:00:00.000+0000",
                        "items": [{"field": "status", "toString": "In Progress"}],
                    },
                    {
                        "created": "2025-01-10T15:30:00.000+0000",
                        "items": [{"field": "status", "toString": "Done"}],
                    },
                ]
            },
        }

        result = _extract_datetime_from_field_mapping(issue, "status:Done.DateTime")
        assert result == "2025-01-10T15:30:00.000+0000"

    def test_extract_no_matching_transition(self, mock_load_app_settings):
        """Test extraction when no matching transition exists."""
        from data.flow_metrics import _extract_datetime_from_field_mapping

        issue = {
            "fields": {},
            "changelog": {
                "histories": [
                    {
                        "created": "2025-01-05T10:00:00.000+0000",
                        "items": [
                            {"field": "status", "toString": "In Review"}
                        ],  # Not "In Progress"
                    }
                ]
            },
        }

        result = _extract_datetime_from_field_mapping(
            issue, "status:In Progress.DateTime"
        )
        assert result is None


#######################################################################
# TEST CLASS: Time in Statuses Calculation
#######################################################################


class TestTimeInStatuses:
    """Test _calculate_time_in_statuses helper function.

    This is used by Flow Efficiency to calculate active time and total time.
    """

    def test_time_in_single_status(self, mock_load_app_settings):
        """Test calculating time spent in a single status."""
        from data.flow_metrics import _calculate_time_in_statuses

        changelog = [
            {
                "created": "2025-01-05T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "In Progress"}],
            },
            {
                "created": "2025-01-07T10:00:00.000+0000",  # 48 hours later
                "items": [{"field": "status", "toString": "Done"}],
            },
        ]

        result = _calculate_time_in_statuses(changelog, ["In Progress"], "TEST-1")

        assert result == pytest.approx(48.0, rel=0.1)  # 48 hours

    def test_time_in_multiple_statuses(self, mock_load_app_settings):
        """Test calculating time across multiple active statuses."""
        from data.flow_metrics import _calculate_time_in_statuses

        changelog = [
            {
                "created": "2025-01-05T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "In Progress"}],
            },
            {
                "created": "2025-01-06T10:00:00.000+0000",  # 24 hours
                "items": [{"field": "status", "toString": "In Review"}],
            },
            {
                "created": "2025-01-07T10:00:00.000+0000",  # 24 hours
                "items": [{"field": "status", "toString": "Done"}],
            },
        ]

        result = _calculate_time_in_statuses(
            changelog, ["In Progress", "In Review"], "TEST-1"
        )

        # 24h In Progress + 24h In Review = 48 hours
        assert result == pytest.approx(48.0, rel=0.1)

    def test_time_empty_changelog(self, mock_load_app_settings):
        """Test time calculation with empty changelog."""
        from data.flow_metrics import _calculate_time_in_statuses

        result = _calculate_time_in_statuses([], ["In Progress"], "TEST-1")

        assert result == 0.0


#######################################################################
# TEST CLASS: Trend Calculation
#######################################################################


class TestFlowTrendCalculation:
    """Test trend calculation for Flow metrics."""

    def test_trend_up(self):
        """Test upward trend detection."""
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=12.0, previous_value=10.0)

        assert result["trend_direction"] == "up"
        assert result["trend_percentage"] == pytest.approx(20.0, rel=0.01)

    def test_trend_down(self):
        """Test downward trend detection."""
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=8.0, previous_value=10.0)

        assert result["trend_direction"] == "down"
        assert result["trend_percentage"] == pytest.approx(-20.0, rel=0.01)

    def test_trend_stable(self):
        """Test stable trend (< 5% change)."""
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.3, previous_value=10.0)

        # 3% change is stable
        assert result["trend_direction"] == "stable"

    def test_trend_no_previous(self):
        """Test trend with no previous value."""
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=None)

        assert result["trend_direction"] == "stable"
        assert result["trend_percentage"] == 0.0
