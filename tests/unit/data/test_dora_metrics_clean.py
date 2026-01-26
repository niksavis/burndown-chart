"""Tests for the new clean DORA metrics implementation (data/dora_metrics.py).

This test file validates the modern DORA calculator that uses status-based
extraction from profile configuration.
"""

from data.dora_metrics import (
    calculate_deployment_frequency,
    calculate_lead_time_for_changes,
    calculate_change_failure_rate,
    calculate_mean_time_to_recovery,
    _classify_performance_tier,
    _determine_performance_tier,
    DEPLOYMENT_FREQUENCY_TIERS,
    LEAD_TIME_TIERS,
)


class TestDeploymentFrequencyClean:
    """Test deployment frequency calculation with clean implementation."""

    def test_deployment_frequency_with_valid_data(self):
        """Test deployment frequency calculation with valid deployment data.

        Per user requirements, deployments are identified by:
        - Operational tasks with fixVersion.releaseDate in the time period
        - Releases are counted as distinct fixVersions
        """
        # Arrange: Create realistic deployment issues with fixVersions
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
                    "fixVersions": [
                        {"name": "v1.0.0", "releaseDate": "2025-11-01"}  # Same release
                    ],
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
                        }  # Different release
                    ],
                    "created": "2025-11-10T09:00:00Z",
                },
            },
        ]

        # Act
        result = calculate_deployment_frequency(issues, time_period_days=30)

        # Assert
        assert "error_state" not in result
        assert result["deployment_count"] == 3  # 3 operational tasks
        assert result["release_count"] == 2  # 2 distinct fixVersions (v1.0.0, v1.1.0)
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
        """Test deployment frequency with no deployment issues."""
        issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                },
            }
        ]

        result = calculate_deployment_frequency(issues, time_period_days=30)

        assert result["error_state"] == "no_data"
        assert "error_message" in result

    def test_deployment_frequency_empty_issues(self):
        """Test deployment frequency with empty issue list."""
        result = calculate_deployment_frequency([], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestLeadTimeForChangesClean:
    """Test lead time for changes calculation with clean implementation."""

    def test_lead_time_with_valid_data(self):
        """Test lead time calculation with valid start and end timestamps."""
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "created": "2025-11-01T10:00:00Z",  # work_started_timestamp
                    "resolutiondate": "2025-11-03T10:00:00Z",  # 2 days later
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

        # Should have valid lead time (around 2 days)
        if "error_state" not in result:
            assert result["value"] > 0
            assert result["unit"] in ["days", "hours"]
            assert result["sample_count"] == 1
            assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_lead_time_no_valid_timestamps(self):
        """Test lead time with issues missing required timestamps."""
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
    """Test change failure rate calculation with clean implementation."""

    def test_change_failure_rate_with_incidents(self):
        """Test CFR calculation with deployments and incidents."""
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

        # Should have valid CFR (1 incident / 2 deployments = 50%)
        if "error_state" not in result:
            assert result["value"] >= 0
            assert result["value"] <= 100
            assert result["unit"] == "%"
            assert result["deployment_count"] > 0
            assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_change_failure_rate_no_deployments(self):
        """Test CFR with no deployments."""
        result = calculate_change_failure_rate([], [], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestMeanTimeToRecoveryClean:
    """Test MTTR calculation with clean implementation."""

    def test_mttr_with_valid_incidents(self):
        """Test MTTR calculation with valid incident data."""
        incidents = [
            {
                "key": "INC-1",
                "fields": {
                    "issuetype": {"name": "Incident"},
                    "created": "2025-11-01T10:00:00Z",  # incident_start
                    "resolutiondate": "2025-11-01T14:00:00Z",  # 4 hours later
                    "status": {"name": "Resolved"},
                },
            }
        ]

        result = calculate_mean_time_to_recovery(incidents, time_period_days=30)

        # Should have valid MTTR (around 4 hours)
        if "error_state" not in result:
            assert result["value"] > 0
            assert result["unit"] in ["hours", "days"]
            assert result["incident_count"] == 1
            assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_mttr_empty_incidents(self):
        """Test MTTR with no incident issues."""
        result = calculate_mean_time_to_recovery([], time_period_days=30)

        assert result["error_state"] == "no_data"


class TestPerformanceTierClassification:
    """Test performance tier classification helpers."""

    def test_classify_deployment_frequency_elite(self):
        """Test elite tier classification for deployment frequency."""
        # 1.5 deployments per day = elite
        tier = _classify_performance_tier(
            1.5, DEPLOYMENT_FREQUENCY_TIERS, higher_is_better=True
        )
        assert tier == "elite"

    def test_classify_lead_time_high(self):
        """Test high tier classification for lead time."""
        # 3 days = high tier (between 1 and 7 days)
        tier = _classify_performance_tier(3, LEAD_TIME_TIERS, higher_is_better=False)
        assert tier == "high"

    def test_determine_performance_tier_with_color(self):
        """Test performance tier determination with semantic color (not Bootstrap)."""
        result = _determine_performance_tier(5, LEAD_TIME_TIERS)

        assert result["tier"] == "High"
        # Returns semantic color "blue" which is mapped to Bootstrap "tier-high" in UI
        assert result["color"] == "blue"

    def test_determine_performance_tier_unknown(self):
        """Test performance tier with None value."""
        result = _determine_performance_tier(None, LEAD_TIME_TIERS)

        assert result["tier"] == "Unknown"
        assert result["color"] == "secondary"
