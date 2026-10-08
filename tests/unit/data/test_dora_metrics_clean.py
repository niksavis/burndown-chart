from unittest.mock import patch

from data.dora_metrics import (
    DEPLOYMENT_FREQUENCY_TIERS,
    LEAD_TIME_TIERS,
    _classify_performance_tier,
    _determine_performance_tier,
    calculate_change_failure_rate,
    calculate_deployment_frequency,
    calculate_lead_time_for_changes,
    calculate_mean_time_to_recovery,
)


class TestDeploymentFrequencyClean:
    def _mock_settings(self) -> dict:
        return {
            "field_mappings": {"dora": {}},
            "flow_end_statuses": ["Done", "Resolved", "Closed"],
            "devops_task_types": ["Operational Task"],
            "devops_projects": [],
        }

    def test_deployment_frequency_with_valid_data(self):

        issues = [
            {
                "key": "DEPLOY-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Operational Task"},
                    "fixVersions": [{"name": "v1.0.0", "releaseDate": "2025-11-01"}],
                    "created": "2025-10-25T10:00:00Z",
                },
            },
            {
                "key": "DEPLOY-2",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Operational Task"},
                    "fixVersions": [{"name": "v1.0.0", "releaseDate": "2025-11-01"}],
                    "created": "2025-10-28T14:00:00Z",
                },
            },
            {
                "key": "DEPLOY-3",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Operational Task"},
                    "fixVersions": [
                        {
                            "name": "v1.1.0",
                            "releaseDate": "2025-11-15",
                        }
                    ],
                    "created": "2025-11-10T09:00:00Z",
                },
            },
        ]

        with patch(
            "data.persistence.load_app_settings", return_value=self._mock_settings()
        ):
            result = calculate_deployment_frequency(issues, time_period_days=30)

        assert "error_state" not in result
        assert result["deployment_count"] == 3
        assert result["release_count"] == 2
        assert result["period_days"] == 30
        assert result["value"] > 0
        assert result["deployments_per_week"] > 0
        assert result["releases_per_week"] > 0
        assert result["unit"] in [
            "deployments/day",
            "deployments/week",
            "deployments/month",
        ]
        assert result["performance_tier"] in ["elite", "high", "medium", "low"]
        assert "v1.0.0" in result["release_names"]
        assert "v1.1.0" in result["release_names"]

    def test_deployment_frequency_no_deployments(self):
        issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                },
            }
        ]

        with patch(
            "data.persistence.load_app_settings", return_value=self._mock_settings()
        ):
            result = calculate_deployment_frequency(issues, time_period_days=30)

        assert result["error_state"] == "no_data"
        assert "error_message" in result

    def test_deployment_frequency_empty_issues(self):
        with patch(
            "data.persistence.load_app_settings", return_value=self._mock_settings()
        ):
            result = calculate_deployment_frequency([], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestLeadTimeForChangesClean:
    def test_lead_time_with_valid_data(self):
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "created": "2025-11-01T10:00:00Z",
                    "resolutiondate": "2025-11-03T10:00:00Z",
                    "status": {"name": "Deployed"},
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-03T10:00:00Z",
                            "items": [
                                {
                                    "field": "status",
                                    "toString": "Deployed",
                                }
                            ],
                        }
                    ]
                },
            }
        ]

        result = calculate_lead_time_for_changes(issues, time_period_days=30)

        if "error_state" not in result:
            assert result["value"] > 0
            assert result["unit"] in ["days", "hours"]
            assert result["sample_count"] == 1
            assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_lead_time_no_valid_timestamps(self):
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "status": {"name": "Done"},
                },
            }
        ]

        result = calculate_lead_time_for_changes(issues, time_period_days=30)

        assert result["error_state"] == "no_data"


class TestChangeFailureRateClean:
    def test_change_failure_rate_with_incidents(self):
        deployment_issues = [
            {
                "key": "DEPLOY-1",
                "fields": {
                    "status": {"name": "Deployed"},
                    "customfield_10001": "Production",
                },
            },
            {
                "key": "DEPLOY-2",
                "fields": {
                    "status": {"name": "Deployed"},
                    "customfield_10001": "Production",
                },
            },
        ]

        incident_issues = [
            {
                "key": "INC-1",
                "fields": {
                    "issuetype": {"name": "Incident"},
                    "priority": {"name": "Critical"},
                    "created": "2025-11-02T10:00:00Z",
                    "resolutiondate": "2025-11-02T12:00:00Z",
                },
            }
        ]

        result = calculate_change_failure_rate(
            deployment_issues, incident_issues, time_period_days=30
        )

        if "error_state" not in result:
            assert result["value"] >= 0
            assert result["value"] <= 100
            assert result["unit"] == "%"
            assert result["deployment_count"] > 0
            assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_change_failure_rate_no_deployments(self):
        result = calculate_change_failure_rate([], [], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestMeanTimeToRecoveryClean:
    def test_mttr_with_valid_incidents(self):
        incidents = [
            {
                "key": "INC-1",
                "fields": {
                    "issuetype": {"name": "Incident"},
                    "created": "2025-11-01T10:00:00Z",
                    "resolutiondate": "2025-11-01T14:00:00Z",
                    "status": {"name": "Resolved"},
                },
            }
        ]

        result = calculate_mean_time_to_recovery(incidents, time_period_days=30)

        if "error_state" not in result:
            assert result["value"] > 0
            assert result["unit"] in ["hours", "days"]
            assert result["incident_count"] == 1
            assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_mttr_empty_incidents(self):
        result = calculate_mean_time_to_recovery([], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestPerformanceTierClassification:
    def test_classify_deployment_frequency_elite(self):
        tier = _classify_performance_tier(
            1.5, DEPLOYMENT_FREQUENCY_TIERS, higher_is_better=True
        )
        assert tier == "elite"

    def test_classify_lead_time_high(self):
        tier = _classify_performance_tier(3, LEAD_TIME_TIERS, higher_is_better=False)
        assert tier == "high"

    def test_determine_performance_tier_with_color(self):
        result = _determine_performance_tier(5, LEAD_TIME_TIERS)

        assert result["tier"] == "High"
        assert result["color"] == "blue"

    def test_determine_performance_tier_unknown(self):
        result = _determine_performance_tier(None, LEAD_TIME_TIERS)

        assert result["tier"] == "Unknown"
        assert result["color"] == "secondary"
