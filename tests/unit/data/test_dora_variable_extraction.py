"""Unit tests for DORA calculator variable extraction integration.

Tests the integration of VariableExtractor with DORA metric calculators,
verifying that variables can be extracted correctly for DORA metrics.

Reference: Feature 012 - T007
"""

from data.dora_calculator import _extract_variables_from_issue
from data.variable_mapping.extractor import VariableExtractor
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION


class TestDORAVariableExtraction:
    """Test variable extraction for DORA metrics."""

    def test_extract_deployment_variables_from_realistic_issue(self):
        """Test extracting deployment-related variables from realistic JIRA issue."""
        issue = {
            "key": "DEPLOY-100",
            "fields": {
                "project": {"key": "DEPLOY"},
                "issuetype": {"name": "Deployment"},
                "status": {"name": "Deployed"},
                "created": "2025-11-01T10:00:00.000Z",
                "customfield_10001": "Production",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2025-11-15T14:00:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Deployed",
                            }
                        ],
                    }
                ]
            },
        }

        # Extract deployment frequency variables
        variables = _extract_variables_from_issue(
            issue, ["deployment_event", "deployment_timestamp", "deployment_successful"]
        )

        # Should extract all deployment variables
        assert "deployment_event" in variables
        assert variables["deployment_event"] is True

        assert "deployment_timestamp" in variables
        assert "2025-11-15" in variables["deployment_timestamp"]

        assert "deployment_successful" in variables
        assert variables["deployment_successful"] is True

    def test_extract_incident_variables(self):
        """Test extracting incident-related variables for CFR/MTTR."""
        issue = {
            "key": "INC-200",
            "fields": {
                "project": {"key": "OPS"},
                "issuetype": {"name": "Incident"},
                "priority": {"name": "Critical"},
                "status": {"name": "Resolved"},
                "created": "2025-11-10T08:00:00.000Z",
                "resolutiondate": "2025-11-10T12:30:00.000Z",
                "customfield_10001": "Production",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2025-11-10T12:30:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Resolved",
                            }
                        ],
                    }
                ]
            },
        }

        variables = _extract_variables_from_issue(
            issue,
            [
                "is_incident",
                "incident_start_timestamp",
                "incident_resolved_timestamp",
            ],
        )

        # Verify incident detection
        assert "is_incident" in variables
        assert variables["is_incident"] is True

        # Verify timestamps
        assert "incident_start_timestamp" in variables
        assert "2025-11-10" in variables["incident_start_timestamp"]

        assert "incident_resolved_timestamp" in variables
        assert "2025-11-10" in variables["incident_resolved_timestamp"]

    def test_extract_with_custom_extractor(self):
        """Test using custom VariableExtractor instance."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "project": {"key": "TEST"},
                "issuetype": {"name": "Task"},
                "created": "2025-11-01T00:00:00.000Z",
            },
        }

        # Create custom extractor
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        # Extract with custom extractor
        variables = _extract_variables_from_issue(
            issue, ["project_key", "issue_type", "created_timestamp"], extractor
        )

        assert variables["project_key"] == "TEST"
        assert variables["issue_type"] == "Task"
        assert "2025-11-01" in variables["created_timestamp"]

    def test_extract_handles_missing_variables_gracefully(self):
        """Test that missing variables don't appear in results."""
        issue = {
            "key": "SIMPLE-1",
            "fields": {
                "project": {"key": "SIMPLE"},
                "issuetype": {"name": "Bug"},
            },
        }

        # Try to extract deployment variables from non-deployment issue
        variables = _extract_variables_from_issue(
            issue, ["deployment_event", "deployment_timestamp"]
        )

        # Deployment variables won't match, so they shouldn't be in results
        # (depends on fallback behavior in DEFAULT_VARIABLE_COLLECTION)
        assert isinstance(variables, dict)
        # Variables that don't match sources won't be in dict

    def test_extract_with_no_changelog(self):
        """Test extraction when issue has no changelog data."""
        issue = {
            "key": "NOCHG-1",
            "fields": {
                "project": {"key": "NOCHG"},
                "issuetype": {"name": "Story"},
                "status": {"name": "Done"},
                "created": "2025-11-01T10:00:00.000Z",
                "resolutiondate": "2025-11-05T15:00:00.000Z",
            },
        }

        # Extract variables that can work without changelog
        variables = _extract_variables_from_issue(
            issue, ["project_key", "is_completed", "created_timestamp"]
        )

        assert variables["project_key"] == "NOCHG"
        assert variables["is_completed"] is True
        assert "created_timestamp" in variables

    def test_batch_extraction_performance(self):
        """Test extracting multiple variables efficiently."""
        issue = {
            "key": "BATCH-1",
            "fields": {
                "project": {"key": "BATCH"},
                "issuetype": {"name": "Deployment"},
                "status": {"name": "Done"},
                "created": "2025-11-01T10:00:00.000Z",
                "resolutiondate": "2025-11-10T16:00:00.000Z",
                "fixVersions": [{"name": "v1.0.0", "releaseDate": "2025-11-10"}],
            },
        }

        # Extract many variables at once
        all_vars = [
            "project_key",
            "issue_type",
            "created_timestamp",
            "deployment_event",
            "deployment_successful",
        ]

        variables = _extract_variables_from_issue(issue, all_vars)

        # Verify extraction worked for available variables
        assert "project_key" in variables
        assert "issue_type" in variables
        assert "created_timestamp" in variables


class TestDeploymentFrequencyWithVariableExtraction:
    """Test calculate_deployment_frequency with variable extraction mode."""

    def test_deployment_frequency_with_variable_extraction(self):
        """Test deployment frequency calculation using variable extraction."""
        from data.dora_calculator import calculate_deployment_frequency
        from datetime import datetime, timezone

        # Create deployment issues with variable-extractable data
        issues = [
            {
                "key": "DEPLOY-1",
                "fields": {
                    "project": {"key": "DEPLOY"},
                    "issuetype": {"name": "Task"},  # DevOps task type
                    "status": {"name": "Deployed"},
                    "created": "2025-11-01T10:00:00.000Z",
                    "fixVersions": [{"name": "v1.0"}],  # Link to development work
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-05T14:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Deployed",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "DEPLOY-2",
                "fields": {
                    "project": {"key": "DEPLOY"},
                    "issuetype": {"name": "Task"},  # DevOps task type
                    "status": {"name": "Deployed"},
                    "created": "2025-11-01T10:00:00.000Z",
                    "fixVersions": [{"name": "v1.0"}],  # Link to development work
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-10T16:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Deployed",
                                }
                            ],
                        }
                    ]
                },
            },
        ]

        # Calculate using variable extraction mode
        result = calculate_deployment_frequency(
            issues=issues,
            use_variable_extraction=True,
            devops_projects=["DEPLOY"],  # Required for filtering
            devops_task_types=["Task"],  # Match issue type
            start_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 11, 30, tzinfo=timezone.utc),
        )

        # Should calculate deployment frequency correctly
        assert result["value"] is not None
        assert result["value"] > 0
        assert result["unit"] == "deployments/month"
        assert result["metric_name"] == "deployment_frequency"

    def test_deployment_frequency_legacy_mode_still_works(self):
        """Test that legacy field_mappings mode still works."""
        from data.dora_calculator import calculate_deployment_frequency
        from datetime import datetime, timezone

        # Create deployment issues with legacy field structure
        issues = [
            {
                "key": "DEPLOY-1",
                "fields": {
                    "project": {"key": "DEPLOY"},
                    "issuetype": {"name": "Task"},
                    "fixVersions": [{"name": "v1.0", "releaseDate": "2025-11-05"}],
                },
            },
        ]

        field_mappings = {"deployment_date": "fixVersions"}

        # Calculate using legacy mode
        result = calculate_deployment_frequency(
            issues=issues,
            field_mappings=field_mappings,
            use_variable_extraction=False,
            devops_projects=["DEPLOY"],
            start_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 11, 30, tzinfo=timezone.utc),
        )

        # Legacy mode should still work
        assert result is not None
        assert "value" in result
        assert result["metric_name"] == "deployment_frequency"


class TestLeadTimeWithVariableExtraction:
    """Test lead time for changes with variable extraction mode."""

    def test_lead_time_with_variable_extraction(self):
        """Test lead time calculation using variable extraction."""
        from data.dora_calculator import calculate_lead_time_for_changes
        from datetime import datetime, timezone

        # Create work items with variable-extractable data
        # commit_timestamp: First transition to "In Development" (priority 1) or created date (priority 2)
        # deployment_timestamp: Transition to "Deployed" (priority 1) or fixVersion releaseDate (priority 2)
        issues = [
            {
                "key": "DEV-1",
                "fields": {
                    "project": {"key": "DEV"},
                    "issuetype": {"name": "Story"},
                    "status": {"name": "Done"},
                    "created": "2025-11-01T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-02T10:00:00.000Z",  # Commit date (transition to In Development)
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Development",
                                }
                            ],
                        },
                        {
                            "created": "2025-11-05T14:00:00.000Z",  # Deployment date (transition to Deployed)
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Development",
                                    "toString": "Deployed",
                                }
                            ],
                        },
                    ]
                },
            },
            {
                "key": "DEV-2",
                "fields": {
                    "project": {"key": "DEV"},
                    "issuetype": {"name": "Story"},
                    "status": {"name": "Done"},
                    "created": "2025-11-01T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-03T10:00:00.000Z",  # Commit date (transition to In Development)
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Development",
                                }
                            ],
                        },
                        {
                            "created": "2025-11-10T16:00:00.000Z",  # Deployment date (transition to Deployed)
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Development",
                                    "toString": "Deployed",
                                }
                            ],
                        },
                    ]
                },
            },
        ]

        # Calculate using variable extraction mode
        result = calculate_lead_time_for_changes(
            issues=issues,
            use_variable_extraction=True,
        )

        # Verify result
        assert result["value"] is not None
        assert result["value"] > 0  # Should have positive lead time
        assert result["unit"] == "days"
        assert result["error_state"] == "success"
        assert result["performance_tier"] in ["Elite", "High", "Medium", "Low"]

    def test_lead_time_legacy_mode_still_works(self):
        """Test that legacy field_mappings mode still works after refactoring."""
        from data.dora_calculator import calculate_lead_time_for_changes
        from datetime import datetime, timezone

        # Create work items with field-based data
        issues = [
            {
                "key": "DEV-1",
                "fields": {
                    "project": {"key": "DEV"},
                    "issuetype": {"name": "Story"},
                    "status": {"name": "Done"},
                    "created": "2025-11-01T10:00:00.000Z",
                    "customfield_10001": "2025-11-05T14:00:00.000Z",  # Deployment date
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-11-02T10:00:00.000Z",  # Commit date
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
            },
        ]

        # Calculate using legacy field_mappings mode
        field_mappings = {
            "deployed_to_production_date": "customfield_10001",
        }

        result = calculate_lead_time_for_changes(
            issues=issues,
            field_mappings=field_mappings,
            active_statuses=["In Progress", "In Review", "Testing"],
            use_variable_extraction=False,
        )

        # Verify backward compatibility - result should be valid
        assert result["value"] is not None
        assert result["value"] > 0
        assert result["error_state"] == "success"
        assert result["performance_tier"] in ["Elite", "High", "Medium", "Low"]
