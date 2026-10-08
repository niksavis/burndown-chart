from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_profile_config() -> dict[str, Any]:

    return {
        "field_mappings": {
            "dora": {
                "deployment_date": "fixVersions",
                "target_environment": "customfield_11309=PROD",
                "code_commit_date": "status:In Progress.DateTime",
                "incident_detected_at": "created",
                "incident_resolved_at": "fixVersions",
                "change_failure": "customfield_12708=Yes",
                "affected_environment": "customfield_11309=PROD",
                "severity_level": "customfield_11000",
            },
            "flow": {
                "flow_item_type": "issuetype",
                "effort_category": "customfield_13204",
                "status": "status",
                "completed_date": "resolutiondate",
            },
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
    }


@pytest.fixture
def mock_load_app_settings(mock_profile_config):
    with (
        patch("data.persistence.load_app_settings") as mock,
        patch("data.dora._mttr.load_app_settings") as mock_mttr,
        patch("data.dora._lead_time.load_app_settings") as mock_lead,
    ):
        mock.return_value = mock_profile_config
        mock_mttr.return_value = mock_profile_config
        mock_lead.return_value = mock_profile_config
        yield mock


def create_operational_task(
    key: str,
    status: str = "Done",
    fix_version_name: str = "Release_2025_01",
    release_date: str = "2025-01-15",
    change_failure: str | None = None,
) -> dict[str, Any]:

    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": "Operational Task"},
            "status": {"name": status},
            "fixVersions": [
                {
                    "id": f"fv-{fix_version_name}",
                    "name": fix_version_name,
                    "releaseDate": release_date,
                    "released": True,
                }
            ],
            "project": {"key": "RI"},
        },
    }

    if change_failure is not None:
        issue["fields"]["customfield_12708"] = {"value": change_failure}

    return issue


def create_development_issue(
    key: str,
    status: str = "Done",
    fix_version_name: str = "Release_2025_01",
    in_progress_timestamp: str = "2025-01-01T10:00:00.000+0000",
    resolution_date: str | None = None,
) -> dict[str, Any]:

    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": "Task"},
            "status": {"name": status},
            "fixVersions": [
                {
                    "id": f"fv-{fix_version_name}",
                    "name": fix_version_name,
                }
            ],
            "project": {"key": "A935"},
            "created": "2024-12-15T09:00:00.000+0000",
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
                }
            ]
        },
    }

    if resolution_date:
        issue["fields"]["resolutiondate"] = resolution_date

    return issue


def create_bug_issue(
    key: str,
    status: str = "Done",
    fix_version_name: str | None = None,
    created: str = "2025-01-10T08:00:00.000+0000",
    resolution_date: str | None = None,
    affected_environment: str = "PROD",
) -> dict[str, Any]:

    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": "Bug"},
            "status": {"name": status},
            "project": {"key": "A935"},
            "created": created,
            "customfield_11309": {"value": affected_environment},
        },
    }

    if fix_version_name:
        issue["fields"]["fixVersions"] = [
            {
                "id": f"fv-{fix_version_name}",
                "name": fix_version_name,
            }
        ]

    if resolution_date:
        issue["fields"]["resolutiondate"] = resolution_date

    return issue


class TestDeploymentFrequency:
    def test_deployment_frequency_basic_calculation(self, mock_load_app_settings):

        from data.dora_metrics import calculate_deployment_frequency

        issues = [
            create_operational_task(
                "RI-1", fix_version_name="Release_1", release_date="2025-01-05"
            ),
            create_operational_task(
                "RI-2", fix_version_name="Release_1", release_date="2025-01-05"
            ),
            create_operational_task(
                "RI-3", fix_version_name="Release_2", release_date="2025-01-15"
            ),
            create_operational_task(
                "RI-4", fix_version_name="Release_3", release_date="2025-01-25"
            ),
            create_operational_task(
                "RI-5", fix_version_name="Release_3", release_date="2025-01-25"
            ),
        ]

        result = calculate_deployment_frequency(
            issues=issues,
            time_period_days=30,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )

        assert result["deployment_count"] == 5, "Should count 5 deployments"
        assert result["release_count"] == 3, "Should count 3 distinct releases"
        assert set(result["release_names"]) == {"Release_1", "Release_2", "Release_3"}

        assert result["deployments_per_week"] == pytest.approx(5 / 30 * 7, rel=0.01)
        assert result["releases_per_week"] == pytest.approx(3 / 30 * 7, rel=0.01)

        assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_deployment_frequency_no_issues(self, mock_load_app_settings):
        from data.dora_metrics import calculate_deployment_frequency

        result = calculate_deployment_frequency(
            issues=[],
            time_period_days=30,
        )

        assert result["error_state"] == "no_data"
        assert "No issues" in result["error_message"]

    def test_deployment_frequency_incomplete_issues_excluded(
        self, mock_load_app_settings
    ):
        from data.dora_metrics import calculate_deployment_frequency

        issues = [
            create_operational_task(
                "RI-1", status="Done", fix_version_name="Release_1"
            ),
            create_operational_task(
                "RI-2", status="In Progress", fix_version_name="Release_1"
            ),
            create_operational_task(
                "RI-3", status="Done", fix_version_name="Release_2"
            ),
        ]

        result = calculate_deployment_frequency(
            issues=issues,
            time_period_days=30,
        )

        assert result["deployment_count"] == 2, "Should only count completed tasks"

    def test_deployment_frequency_no_release_date_excluded(
        self, mock_load_app_settings
    ):
        from data.dora_metrics import calculate_deployment_frequency

        issue_no_release = {
            "key": "RI-1",
            "fields": {
                "issuetype": {"name": "Operational Task"},
                "status": {"name": "Done"},
                "fixVersions": [
                    {
                        "id": "fv-1",
                        "name": "No-Release-Date",
                    }
                ],
            },
        }

        issues = [
            issue_no_release,
            create_operational_task("RI-2", fix_version_name="Release_1"),
        ]

        result = calculate_deployment_frequency(
            issues=issues,
            time_period_days=30,
        )

        assert result["deployment_count"] == 1, (
            "Should only count issues with releaseDate"
        )

    def test_deployment_frequency_performance_tiers(self, mock_load_app_settings):
        from data.dora_metrics import calculate_deployment_frequency

        elite_issues = [
            create_operational_task(f"RI-{i}", fix_version_name=f"R{i}")
            for i in range(28)
        ]
        result = calculate_deployment_frequency(elite_issues, time_period_days=7)
        assert result["performance_tier"] == "elite"

        low_issues = [create_operational_task("RI-1")]
        result = calculate_deployment_frequency(low_issues, time_period_days=60)
        assert result["performance_tier"] == "low"


class TestLeadTimeForChanges:
    @pytest.fixture
    def fixversion_release_map(self) -> dict[str, datetime]:
        return {
            "Release_2025_01": datetime(2025, 1, 15, 0, 0, tzinfo=UTC),
            "Release_2025_02": datetime(2025, 2, 1, 0, 0, tzinfo=UTC),
        }

    def test_lead_time_basic_calculation(
        self, mock_load_app_settings, fixversion_release_map
    ):

        from data.dora_metrics import calculate_lead_time_for_changes

        issues = [
            create_development_issue(
                "A935-1",
                fix_version_name="Release_2025_01",
                in_progress_timestamp="2025-01-05T10:00:00.000+0000",
            ),
            create_development_issue(
                "A935-2",
                fix_version_name="Release_2025_01",
                in_progress_timestamp="2025-01-10T10:00:00.000+0000",
            ),
        ]

        result = calculate_lead_time_for_changes(
            issues=issues,
            time_period_days=30,
            fixversion_release_map=fixversion_release_map,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )
        assert result["sample_count"] == 2
        assert result["value"] == pytest.approx(7.5, rel=0.1)
        assert result["unit"] == "days"
        assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_lead_time_no_matching_fixversion(self, mock_load_app_settings):
        from data.dora_metrics import calculate_lead_time_for_changes

        issues = [
            create_development_issue(
                "A935-1",
                fix_version_name="Unknown_Release",
            )
        ]

        result = calculate_lead_time_for_changes(
            issues=issues,
            fixversion_release_map={},
        )

        assert result["error_state"] == "no_data"
        assert (
            "missing deployment" in result["error_message"].lower()
            or "no fixversion match" in result["error_message"].lower()
        )

    def test_lead_time_missing_in_progress_timestamp(
        self, mock_load_app_settings, fixversion_release_map
    ):
        from data.dora_metrics import calculate_lead_time_for_changes

        issue = {
            "key": "A935-1",
            "fields": {
                "status": {"name": "Done"},
                "fixVersions": [{"name": "Release_2025_01"}],
            },
            "changelog": {"histories": []},
        }

        result = calculate_lead_time_for_changes(
            issues=[issue],
            fixversion_release_map=fixversion_release_map,
        )

        assert result["error_state"] == "no_data"
        assert "missing start" in result["error_message"].lower()

    def test_lead_time_hours_unit_for_short_times(self, mock_load_app_settings):
        from data.dora_metrics import calculate_lead_time_for_changes

        release_map = {
            "Release_Quick": datetime(2025, 1, 1, 22, 0, tzinfo=UTC),
        }
        issues = [
            create_development_issue(
                "A935-1",
                fix_version_name="Release_Quick",
                in_progress_timestamp="2025-01-01T10:00:00.000+0000",
            )
        ]

        result = calculate_lead_time_for_changes(
            issues=issues,
            fixversion_release_map=release_map,
        )

        assert result["unit"] == "hours"
        assert result["value"] == pytest.approx(12, rel=0.1)
        assert result["performance_tier"] == "elite"


class TestChangeFailureRate:
    def test_cfr_basic_calculation(self, mock_load_app_settings):

        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", change_failure="Yes"),
            create_operational_task("RI-2", change_failure="No"),
            create_operational_task("RI-3", change_failure="Yes"),
            create_operational_task("RI-4", change_failure="No"),
            create_operational_task("RI-5", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
            time_period_days=30,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )
        assert result["total_deployments"] == 5
        assert result["failed_deployments"] == 2
        assert result["value"] == pytest.approx(40.0, rel=0.01)
        assert result["unit"] == "%"

    def test_cfr_zero_failures(self, mock_load_app_settings):
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", change_failure="No"),
            create_operational_task("RI-2", change_failure="No"),
            create_operational_task("RI-3", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["value"] == 0.0
        assert result["performance_tier"] == "elite"

    def test_cfr_all_failures(self, mock_load_app_settings):
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", change_failure="Yes"),
            create_operational_task("RI-2", change_failure="Yes"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["value"] == 100.0
        assert result["performance_tier"] == "low"

    def test_cfr_release_tracking(self, mock_load_app_settings):
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task(
                "RI-1", fix_version_name="R1", change_failure="Yes"
            ),
            create_operational_task("RI-2", fix_version_name="R1", change_failure="No"),
            create_operational_task("RI-3", fix_version_name="R2", change_failure="No"),
            create_operational_task("RI-4", fix_version_name="R2", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["total_deployments"] == 4
        assert result["failed_deployments"] == 1
        assert result["total_releases"] == 2
        assert result["failed_releases"] == 1
        assert "R1" in result["failed_release_names"]

    def test_cfr_incomplete_issues_excluded(self, mock_load_app_settings):
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", status="Done", change_failure="Yes"),
            create_operational_task("RI-2", status="In Progress", change_failure="Yes"),
            create_operational_task("RI-3", status="Done", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["total_deployments"] == 2
        assert result["failed_deployments"] == 1
        assert result["value"] == 50.0

    def test_cfr_performance_tiers(self, mock_load_app_settings):
        from data.dora_metrics import calculate_change_failure_rate

        issues = [create_operational_task(f"RI-{i}") for i in range(10)]
        issues[0]["fields"]["customfield_12708"] = {"value": "Yes"}
        result = calculate_change_failure_rate(issues, [])
        assert result["performance_tier"] == "elite"

        issues = [
            create_operational_task("RI-1", change_failure="Yes"),
            create_operational_task("RI-2", change_failure="Yes"),
        ]
        result = calculate_change_failure_rate(issues, [])
        assert result["performance_tier"] == "low"


class TestMeanTimeToRecovery:
    @pytest.fixture
    def fixversion_release_map(self) -> dict[str, datetime]:
        return {
            "Hotfix_2025_01": datetime(2025, 1, 12, 10, 0, tzinfo=UTC),
        }

    def test_mttr_resolution_mode(self, mock_load_app_settings):

        from data.dora_metrics import calculate_mean_time_to_recovery

        mock_load_app_settings.return_value["field_mappings"]["dora"][
            "incident_resolved_at"
        ] = "resolutiondate"

        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date="2025-01-10T20:00:00.000+0000",
            ),
            create_bug_issue(
                "A935-2",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date="2025-01-11T08:00:00.000+0000",
            ),
        ]

        result = calculate_mean_time_to_recovery(
            incident_issues=bugs,
            time_period_days=30,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )
        assert result["incident_count"] == 2
        assert result["value"] == pytest.approx(18, rel=0.1)
        assert result["unit"] == "hours"

    def test_mttr_deployment_mode(self, mock_load_app_settings, fixversion_release_map):

        from data.dora_metrics import calculate_mean_time_to_recovery

        bugs = [
            create_bug_issue(
                "A935-1",
                fix_version_name="Hotfix_2025_01",
                created="2025-01-10T08:00:00.000+0000",
            )
        ]

        result = calculate_mean_time_to_recovery(
            incident_issues=bugs,
            fixversion_release_map=fixversion_release_map,
        )

        assert "error_state" not in result
        assert result["incident_count"] == 1
        assert result["unit"] == "days"
        assert result["value"] == pytest.approx(50 / 24, rel=0.1)

    def test_mttr_no_incidents(self, mock_load_app_settings):
        from data.dora_metrics import calculate_mean_time_to_recovery

        result = calculate_mean_time_to_recovery(
            incident_issues=[],
        )

        assert result["error_state"] == "no_data"

    def test_mttr_missing_resolution(self, mock_load_app_settings):
        from data.dora_metrics import calculate_mean_time_to_recovery

        mock_load_app_settings.return_value["field_mappings"]["dora"][
            "incident_resolved_at"
        ] = "resolutiondate"

        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date=None,
            )
        ]

        result = calculate_mean_time_to_recovery(
            incident_issues=bugs,
        )

        assert result["error_state"] == "no_data"
        assert "missing end" in result["error_message"].lower()

    def test_mttr_performance_tiers(self, mock_load_app_settings):
        from data.dora_metrics import calculate_mean_time_to_recovery

        mock_load_app_settings.return_value["field_mappings"]["dora"][
            "incident_resolved_at"
        ] = "resolutiondate"

        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date="2025-01-10T08:30:00.000+0000",
            )
        ]
        result = calculate_mean_time_to_recovery(bugs)
        assert result["performance_tier"] == "elite"

        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-01T08:00:00.000+0000",
                resolution_date="2025-01-15T08:00:00.000+0000",
            )
        ]
        result = calculate_mean_time_to_recovery(bugs)
        assert result["performance_tier"] == "low"


class TestFixVersionMatcher:
    def test_build_fixversion_release_map(self):
        from data.fixversion_matcher import build_fixversion_release_map

        op_tasks = [
            create_operational_task(
                "RI-1", fix_version_name="R1", release_date="2025-01-15"
            ),
            create_operational_task(
                "RI-2", fix_version_name="R2", release_date="2025-01-20"
            ),
            create_operational_task(
                "RI-3", fix_version_name="R1", release_date="2025-01-15"
            ),
        ]

        result = build_fixversion_release_map(
            operational_tasks=op_tasks,
            flow_end_statuses=["Done", "Resolved", "Closed"],
        )

        assert len(result) == 2
        assert "R1" in result
        assert "R2" in result
        assert result["R1"] == datetime(2025, 1, 15)
        assert result["R2"] == datetime(2025, 1, 20)

    def test_get_deployment_date_for_issue(self):
        from data.fixversion_matcher import get_deployment_date_for_issue

        release_map = {
            "Release_1": datetime(2025, 1, 15, tzinfo=UTC),
            "Release_2": datetime(2025, 2, 1, tzinfo=UTC),
        }

        issue = create_development_issue("A935-1", fix_version_name="Release_1")
        result = get_deployment_date_for_issue(issue, release_map)
        assert result == datetime(2025, 1, 15, tzinfo=UTC)

        issue["fields"]["fixVersions"] = [
            {"name": "Release_2"},
            {"name": "Release_1"},
        ]
        result = get_deployment_date_for_issue(issue, release_map)
        assert result == datetime(2025, 1, 15, tzinfo=UTC)

        issue["fields"]["fixVersions"] = [{"name": "Unknown_Release"}]
        result = get_deployment_date_for_issue(issue, release_map)
        assert result is None

    def test_filter_issues_deployed_in_week(self):
        from data.fixversion_matcher import filter_issues_deployed_in_week

        release_map = {
            "Week1": datetime(2025, 1, 8, tzinfo=UTC),
            "Week2": datetime(2025, 1, 15, tzinfo=UTC),
            "Week0": datetime(2025, 1, 1, tzinfo=UTC),
        }

        issues = [
            create_development_issue("A-1", fix_version_name="Week1"),
            create_development_issue("A-2", fix_version_name="Week2"),
            create_development_issue("A-3", fix_version_name="Week0"),
        ]

        week_start = datetime(2025, 1, 6, tzinfo=UTC)
        week_end = datetime(2025, 1, 13, tzinfo=UTC)

        result = filter_issues_deployed_in_week(
            issues, release_map, week_start, week_end
        )

        assert len(result) == 1
        assert result[0]["key"] == "A-1"


class TestFieldValueParsing:
    def test_parse_field_value_filter_simple(self):
        from data.dora_metrics import parse_field_value_filter

        field_id, filter_values = parse_field_value_filter("customfield_11309")
        assert field_id == "customfield_11309"
        assert filter_values is None

    def test_parse_field_value_filter_single_value(self):
        from data.dora_metrics import parse_field_value_filter

        field_id, filter_values = parse_field_value_filter("customfield_11309=PROD")
        assert field_id == "customfield_11309"
        assert filter_values == ["PROD"]

    def test_parse_field_value_filter_multiple_values(self):
        from data.dora_metrics import parse_field_value_filter

        field_id, filter_values = parse_field_value_filter(
            "customfield_11309=PROD|Production|Live"
        )
        assert field_id == "customfield_11309"
        assert filter_values == ["PROD", "Production", "Live"]

    def test_check_field_value_match_string(self):
        from data.dora_metrics import check_field_value_match

        issue = {"fields": {"customfield_11309": "PROD"}}
        assert check_field_value_match(issue, "customfield_11309", ["PROD"]) is True
        assert check_field_value_match(issue, "customfield_11309", ["DEV"]) is False
        assert check_field_value_match(issue, "customfield_11309", ["prod"]) is True

    def test_check_field_value_match_dict(self):
        from data.dora_metrics import check_field_value_match

        issue = {"fields": {"customfield_11309": {"value": "PROD", "id": "123"}}}
        assert check_field_value_match(issue, "customfield_11309", ["PROD"]) is True
        assert check_field_value_match(issue, "customfield_11309", ["DEV"]) is False

    def test_is_production_environment(self):
        from data.dora_metrics import is_production_environment

        issue = {"fields": {"customfield_11309": {"value": "PROD"}}}
        assert is_production_environment(issue, "customfield_11309=PROD") is True
        assert is_production_environment(issue, "customfield_11309=DEV") is False

        assert (
            is_production_environment(
                issue, "customfield_11309", fallback_values=["PROD"]
            )
            is True
        )


class TestTrendCalculation:
    def test_trend_up(self):
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=5.0)
        assert result["trend_direction"] == "up"
        assert result["trend_percentage"] == pytest.approx(100.0, rel=0.01)

    def test_trend_down(self):
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=5.0, previous_value=10.0)
        assert result["trend_direction"] == "down"
        assert result["trend_percentage"] == pytest.approx(-50.0, rel=0.01)

    def test_trend_stable(self):
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=9.8)
        assert result["trend_direction"] == "stable"

    def test_trend_no_previous(self):
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=None)
        assert result["trend_direction"] == "stable"
        assert result["trend_percentage"] == 0.0
