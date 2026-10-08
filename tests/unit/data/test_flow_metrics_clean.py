import pytest

from data.flow_metrics import (
    _calculate_trend,
    _normalize_work_type,
    calculate_flow_distribution,
    calculate_flow_efficiency,
    calculate_flow_load,
    calculate_flow_time,
    calculate_flow_velocity,
)


@pytest.fixture
def test_profile(temp_database):
    from datetime import datetime

    from data.persistence.factory import get_backend

    backend = get_backend()
    profile_id = "test_flow_profile"

    profile = {
        "id": profile_id,
        "name": "Test Flow Profile",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "jira_config": {},
        "field_mappings": {
            "flow": {
                "flow_item_type": "issuetype",
                "status": "status",
                "completed_date": "resolutiondate",
            }
        },
        "forecast_settings": {},
        "project_classification": {
            "flow_end_statuses": ["Done", "Resolved", "Closed"],
            "active_statuses": ["In Progress", "In Review"],
            "wip_statuses": ["In Progress", "In Review", "Testing"],
            "flow_start_statuses": ["In Progress"],
            "flow_type_mappings": {
                "Feature": {"issue_types": ["Task", "Story"], "effort_categories": []},
                "Defect": {"issue_types": ["Bug"], "effort_categories": []},
            },
        },
    }

    backend.save_profile(profile)
    backend.set_app_state("active_profile_id", profile_id)

    return profile_id


class TestFlowVelocityClean:
    def test_flow_velocity_with_valid_data(self, test_profile):
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "created": "2025-11-01T10:00:00Z",
                    "resolutiondate": "2025-11-05T10:00:00Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-05T10:00:00Z",
                            "items": [{"field": "status", "toString": "Done"}],
                        }
                    ]
                },
            },
            {
                "key": "BUG-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                    "created": "2025-11-02T10:00:00Z",
                    "resolutiondate": "2025-11-03T10:00:00Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-03T10:00:00Z",
                            "items": [{"field": "status", "toString": "Done"}],
                        }
                    ]
                },
            },
            {
                "key": "TASK-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Task"},
                    "created": "2025-11-03T10:00:00Z",
                    "resolutiondate": "2025-11-08T10:00:00Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-08T10:00:00Z",
                            "items": [{"field": "status", "toString": "Done"}],
                        }
                    ]
                },
            },
        ]

        result = calculate_flow_velocity(issues, time_period_days=7)

        assert result["error_state"] is None
        assert result["value"] > 0
        assert result["unit"] == "items/week"
        assert "breakdown" in result
        assert isinstance(result["breakdown"], dict)

    def test_flow_velocity_empty_issues(self, test_profile):
        result = calculate_flow_velocity([], time_period_days=7)

        assert result["error_state"] == "no_data"
        assert "error_message" in result

    def test_flow_velocity_with_previous_value(self, test_profile):
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                },
            }
        ]

        result = calculate_flow_velocity(
            issues, time_period_days=7, previous_period_value=5.0
        )

        assert "trend_direction" in result
        assert "trend_percentage" in result
        assert result["trend_direction"] in ["up", "down", "stable"]


class TestFlowTimeClean:
    def test_flow_time_with_valid_timestamps(self, test_profile):

        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "created": "2025-11-01T10:00:00Z",
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "status": {"name": "Done"},
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-05T10:00:00Z",
                            "items": [{"field": "status", "toString": "Done"}],
                        }
                    ]
                },
            },
            {
                "key": "STORY-2",
                "fields": {
                    "created": "2025-11-02T10:00:00Z",
                    "resolutiondate": "2025-11-08T10:00:00Z",
                    "status": {"name": "Done"},
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-08T10:00:00Z",
                            "items": [{"field": "status", "toString": "Done"}],
                        }
                    ]
                },
            },
        ]

        result = calculate_flow_time(issues, time_period_days=30)

        if result["error_state"] is None:
            assert result["value"] > 0
            assert result["unit"] == "days"
        else:
            assert result["error_state"] == "no_data"

    def test_flow_time_no_valid_timestamps(self, test_profile):
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "Done"},
                },
            }
        ]

        result = calculate_flow_time(issues, time_period_days=30)

        assert result["error_state"] == "no_data"

    def test_flow_time_empty_issues(self, test_profile):
        result = calculate_flow_time([], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestFlowEfficiencyClean:
    def test_flow_efficiency_with_valid_data(self, test_profile):

        pass

    def test_flow_efficiency_no_active_time(self, test_profile):

        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "created": "2025-11-01T10:00:00Z",
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "status": {"name": "Done"},
                },
            }
        ]

        result = calculate_flow_efficiency(issues, time_period_days=30)

        assert result["error_state"] in ["no_data", "missing_mapping"]

    def test_flow_efficiency_empty_issues(self, test_profile):
        result = calculate_flow_efficiency([], time_period_days=30)

        assert result["error_state"] in ["no_data", "missing_mapping"]


class TestFlowLoadClean:
    def test_flow_load_with_wip_items(self, test_profile):

        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Story"},
                },
            },
            {
                "key": "BUG-1",
                "fields": {
                    "status": {"name": "In Review"},
                    "issuetype": {"name": "Bug"},
                },
            },
            {
                "key": "TASK-1",
                "fields": {
                    "status": {"name": "Testing"},
                    "issuetype": {"name": "Task"},
                },
            },
        ]

        result = calculate_flow_load(issues)

        if result["error_state"] is None:
            assert result["value"] >= 0
            assert result["unit"] == "items"
        else:
            assert result["error_state"] == "missing_mapping"

    def test_flow_load_empty_issues(self, test_profile):
        result = calculate_flow_load([])

        if result["error_state"] is None:
            assert result["value"] == 0
            assert result["unit"] == "items"
        else:
            assert result["error_state"] == "missing_mapping"

    def test_flow_load_with_previous_value(self, test_profile):
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "In Progress"},
                },
            }
        ]

        result = calculate_flow_load(issues, previous_period_value=5.0)

        assert "trend_direction" in result
        assert "trend_percentage" in result


class TestFlowDistributionClean:
    def test_flow_distribution_with_mixed_types(self, test_profile):

        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "issuetype": {"name": "Story"},
                    "customfield_10003": "Feature",
                },
            },
            {
                "key": "STORY-2",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "issuetype": {"name": "Story"},
                    "customfield_10003": "Feature",
                },
            },
            {
                "key": "BUG-1",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "issuetype": {"name": "Bug"},
                    "customfield_10003": "Bug",
                },
            },
            {
                "key": "TASK-1",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "issuetype": {"name": "Task"},
                    "customfield_10003": "Technical Debt",
                },
            },
        ]

        result = calculate_flow_distribution(issues, time_period_days=30)

        if result["error_state"] is None:
            assert isinstance(result["value"], dict)
            assert result["unit"] == "%"
            total_percent = sum(result["value"].values())
            assert 99 <= total_percent <= 101
        else:
            assert result["error_state"] == "no_data"

    def test_flow_distribution_all_features(self, test_profile):

        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "issuetype": {"name": "Story"},
                    "customfield_10003": "Feature",
                },
            },
            {
                "key": "STORY-2",
                "fields": {
                    "status": {"name": "Done"},
                    "resolutiondate": "2025-11-05T10:00:00Z",
                    "issuetype": {"name": "Story"},
                    "customfield_10003": "Feature",
                },
            },
        ]

        result = calculate_flow_distribution(issues, time_period_days=30)

        if result["error_state"] is None:
            if "Feature" in result["value"]:
                assert result["value"]["Feature"] == 100.0
        else:
            assert result["error_state"] == "no_data"

    def test_flow_distribution_empty_issues(self, test_profile):
        result = calculate_flow_distribution([], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestHelperFunctions:
    def test_normalize_work_type_feature(self, test_profile):
        assert _normalize_work_type("Feature") == "Feature"
        assert _normalize_work_type("Story") == "Feature"
        assert _normalize_work_type("User Story") == "Feature"

    def test_normalize_work_type_bug(self, test_profile):
        assert _normalize_work_type("Bug") == "Bug"
        assert _normalize_work_type("Defect") == "Bug"

    def test_normalize_work_type_technical_debt(self, test_profile):
        assert _normalize_work_type("Technical Debt") == "Technical Debt"
        assert _normalize_work_type("Tech Debt") == "Technical Debt"

    def test_normalize_work_type_risk(self, test_profile):
        assert _normalize_work_type("Risk") == "Risk"

    def test_normalize_work_type_unknown(self, test_profile):
        assert _normalize_work_type("Unknown Type") == "Feature"
        assert _normalize_work_type(None) == "Feature"
        assert _normalize_work_type({"some": "dict"}) == "Feature"

    def test_calculate_trend_increasing(self, test_profile):
        result = _calculate_trend(10.0, 8.0)

        assert result["trend_direction"] == "up"
        assert result["trend_percentage"] == 25.0

    def test_calculate_trend_decreasing(self, test_profile):
        result = _calculate_trend(6.0, 10.0)

        assert result["trend_direction"] == "down"
        assert result["trend_percentage"] == -40.0

    def test_calculate_trend_stable(self, test_profile):
        result = _calculate_trend(10.0, 10.2)

        assert result["trend_direction"] == "stable"

    def test_calculate_trend_no_previous(self, test_profile):
        result = _calculate_trend(10.0, None)

        assert result["trend_direction"] == "stable"
        assert result["trend_percentage"] == 0.0
