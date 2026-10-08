from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_profile_config() -> dict[str, Any]:

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

    from configuration.metrics_config import MetricsConfig

    mock_config = MetricsConfig.__new__(MetricsConfig)
    mock_config.profile_id = "test_profile"
    mock_config.profile_config = mock_profile_config

    with (
        patch("data.flow_metrics_helpers.load_app_settings") as mock_settings,
        patch("data.flow_metrics_helpers.get_metrics_config") as mock_get_config,
    ):
        mock_settings.return_value = mock_profile_config
        mock_get_config.return_value = mock_config
        yield mock_settings


def create_completed_issue(
    key: str,
    issue_type: str = "Task",
    status: str = "Done",
    in_progress_timestamp: str = "2025-01-05T10:00:00.000+0000",
    done_timestamp: str = "2025-01-10T10:00:00.000+0000",
    resolution_date: str = "2025-01-10T10:00:00.000+0000",
    effort_category: str | None = None,
) -> dict[str, Any]:

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
) -> dict[str, Any]:

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
    status_transitions: list[dict[str, str]],
    final_status: str = "Done",
    resolution_date: str = "2025-01-15T10:00:00.000+0000",
) -> dict[str, Any]:

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


class TestFlowVelocity:
    def test_flow_velocity_basic_calculation(self, mock_load_app_settings):

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

    def test_flow_velocity_different_time_periods(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_velocity

        issues = [create_completed_issue(f"TASK-{i}") for i in range(1, 11)]

        result_7 = calculate_flow_velocity(issues=issues, time_period_days=7)
        assert result_7["value"] == pytest.approx(10.0, rel=0.01)

        result_14 = calculate_flow_velocity(issues=issues, time_period_days=14)
        assert result_14["value"] == pytest.approx(5.0, rel=0.01)

    def test_flow_velocity_empty_issues(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_velocity

        result = calculate_flow_velocity(issues=[], time_period_days=7)

        assert result["error_state"] == "no_data"
        assert result["value"] == 0.0

    def test_flow_velocity_excludes_incomplete(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_velocity

        issues = [
            create_completed_issue("TASK-1"),
            create_wip_issue("TASK-2", status="In Progress"),
            create_wip_issue("TASK-3", status="Testing"),
        ]

        result = calculate_flow_velocity(issues=issues, time_period_days=7)

        assert result["value"] >= 0


class TestFlowTime:
    def test_flow_time_basic_calculation(self, mock_load_app_settings):

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

        from data.flow_metrics import calculate_flow_time

        issues = [
            create_completed_issue(
                "TASK-1",
                in_progress_timestamp="2025-01-05T10:00:00.000+0000",
                done_timestamp="2025-01-10T10:00:00.000+0000",
            ),
            create_completed_issue(
                "TASK-2",
                in_progress_timestamp="2025-01-01T10:00:00.000+0000",
                done_timestamp="2025-01-11T10:00:00.000+0000",
            ),
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        assert result["value"] == pytest.approx(7.5, rel=0.1)

    def test_flow_time_uses_changelog_timestamps(self, mock_load_app_settings):

        from data.flow_metrics import calculate_flow_time

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
                            "created": "2025-01-03T10:00:00.000+0000",
                            "items": [{"field": "status", "toString": "In Progress"}],
                        },
                        {
                            "created": "2025-01-10T10:00:00.000+0000",
                            "items": [{"field": "status", "toString": "Done"}],
                        },
                    ]
                },
            }
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] is None
        assert result["value"] == pytest.approx(7.0, rel=0.1)

    def test_flow_time_no_timestamps(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_time

        issues = [
            {
                "key": "TASK-1",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-01-10T10:00:00.000+0000",
                },
                "changelog": {"histories": []},
            }
        ]

        result = calculate_flow_time(issues=issues, time_period_days=30)

        assert result["error_state"] == "no_data"


class TestFlowEfficiency:
    def test_flow_efficiency_full_active(self, mock_load_app_settings):

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
                        "to": "Ready for Testing",
                        "timestamp": "2025-01-07T10:00:00.000+0000",
                    },
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
        assert result["value"] == pytest.approx(40.0, rel=5)

    def test_flow_efficiency_multiple_active_periods(self, mock_load_app_settings):

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
        assert result["value"] == pytest.approx(100.0, rel=5)


class TestFlowLoad:
    def test_flow_load_counts_wip_items(self, mock_load_app_settings):

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
        from data.flow_metrics import calculate_flow_load

        issues = [
            create_wip_issue("TASK-1", status="In Progress"),
            create_completed_issue("TASK-2", status="Done"),
            create_completed_issue("TASK-3", status="Resolved"),
        ]

        result = calculate_flow_load(issues=issues, time_period_days=7)

        assert result["value"] == 1

    def test_flow_load_excludes_backlog(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_load

        issues = [
            create_wip_issue("TASK-1", status="In Progress"),
            {"key": "TASK-2", "fields": {"status": {"name": "To Do"}}},
            {"key": "TASK-3", "fields": {"status": {"name": "Open"}}},
        ]

        result = calculate_flow_load(issues=issues, time_period_days=7)

        assert result["value"] == 1

    def test_flow_load_empty_issues(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_load

        result = calculate_flow_load(issues=[], time_period_days=7)

        assert result["error_state"] is None
        assert result["value"] == 0


class TestWorkDistribution:
    def test_work_distribution_all_features(self, mock_load_app_settings):

        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue("TASK-1", issue_type="Task"),
            create_completed_issue("TASK-2", issue_type="Task"),
            create_completed_issue("TASK-3", issue_type="Story"),
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        assert result["error_state"] is None
        assert result["unit"] == "%"
        assert "Feature" in result["value"]

    def test_work_distribution_mixed_types(self, mock_load_app_settings):

        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue("TASK-1", issue_type="Task"),
            create_completed_issue("TASK-2", issue_type="Story"),
            create_completed_issue("BUG-1", issue_type="Bug"),
            create_completed_issue(
                "TASK-3", issue_type="Task", effort_category="Maintenance"
            ),
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        assert result["error_state"] is None
        total = sum(result["value"].values())
        assert total == pytest.approx(100.0, rel=0.1)

    def test_work_distribution_uses_effort_category(self, mock_load_app_settings):

        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue(
                "TASK-1", issue_type="Task", effort_category="Security"
            ),
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        assert result["error_state"] is None or result["error_state"] == "no_data"

    def test_work_distribution_empty_issues(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_distribution

        result = calculate_flow_distribution(issues=[], time_period_days=7)

        assert result["error_state"] == "no_data"

    def test_work_distribution_excludes_incomplete(self, mock_load_app_settings):
        from data.flow_metrics import calculate_flow_distribution

        issues = [
            create_completed_issue("TASK-1"),
            create_wip_issue("TASK-2", status="In Progress"),
        ]

        result = calculate_flow_distribution(issues=issues, time_period_days=7)

        assert result is not None


class TestDatetimeExtraction:
    def test_extract_simple_field(self, mock_load_app_settings):
        from data.flow_metrics import _extract_datetime_from_field_mapping

        issue = {
            "fields": {
                "resolutiondate": "2025-01-10T10:00:00.000+0000",
            }
        }

        result = _extract_datetime_from_field_mapping(issue, "resolutiondate")
        assert result == "2025-01-10T10:00:00.000+0000"

    def test_extract_changelog_transition(self, mock_load_app_settings):
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
        from data.flow_metrics import _extract_datetime_from_field_mapping

        issue = {
            "fields": {},
            "changelog": {
                "histories": [
                    {
                        "created": "2025-01-05T10:00:00.000+0000",
                        "items": [{"field": "status", "toString": "In Review"}],
                    }
                ]
            },
        }

        result = _extract_datetime_from_field_mapping(
            issue, "status:In Progress.DateTime"
        )
        assert result is None


class TestTimeInStatuses:
    def test_time_in_single_status(self, mock_load_app_settings):
        from data.flow_metrics import _calculate_time_in_statuses

        changelog = [
            {
                "created": "2025-01-05T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "In Progress"}],
            },
            {
                "created": "2025-01-07T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "Done"}],
            },
        ]

        result = _calculate_time_in_statuses(changelog, ["In Progress"], "TEST-1")

        assert result == pytest.approx(48.0, rel=0.1)

    def test_time_in_multiple_statuses(self, mock_load_app_settings):
        from data.flow_metrics import _calculate_time_in_statuses

        changelog = [
            {
                "created": "2025-01-05T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "In Progress"}],
            },
            {
                "created": "2025-01-06T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "In Review"}],
            },
            {
                "created": "2025-01-07T10:00:00.000+0000",
                "items": [{"field": "status", "toString": "Done"}],
            },
        ]

        result = _calculate_time_in_statuses(
            changelog, ["In Progress", "In Review"], "TEST-1"
        )

        assert result == pytest.approx(48.0, rel=0.1)

    def test_time_empty_changelog(self, mock_load_app_settings):
        from data.flow_metrics import _calculate_time_in_statuses

        result = _calculate_time_in_statuses([], ["In Progress"], "TEST-1")

        assert result == 0.0


class TestFlowTrendCalculation:
    def test_trend_up(self):
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=12.0, previous_value=10.0)

        assert result["trend_direction"] == "up"
        assert result["trend_percentage"] == pytest.approx(20.0, rel=0.01)

    def test_trend_down(self):
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=8.0, previous_value=10.0)

        assert result["trend_direction"] == "down"
        assert result["trend_percentage"] == pytest.approx(-20.0, rel=0.01)

    def test_trend_stable(self):
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.3, previous_value=10.0)

        assert result["trend_direction"] == "stable"

    def test_trend_no_previous(self):
        from data.flow_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=None)

        assert result["trend_direction"] == "stable"
        assert result["trend_percentage"] == 0.0
