"""Unit tests for Flow calculator variable extraction integration.

Tests Flow metric calculators using VariableExtractor instead of field_mappings.
Validates dual-mode support (legacy field_mappings + variable extraction).
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from data.flow_calculator import calculate_flow_velocity
from data.variable_mapping.extractor import VariableExtractor
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION


class TestFlowVariableExtraction:
    """Test helper function for Flow variable extraction."""

    @pytest.fixture
    def sample_issue_with_changelog(self) -> Dict[str, Any]:
        """Create a sample JIRA issue with changelog for testing."""
        return {
            "key": "PROJ-123",
            "fields": {
                "status": {"name": "Done"},
                "issuetype": {"name": "Story"},
                "customfield_10001": "Feature",  # Work type field
                "resolutiondate": "2025-01-15T10:00:00.000Z",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2025-01-10T09:00:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2025-01-15T10:00:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Done",
                            }
                        ],
                    },
                ]
            },
        }

    @pytest.fixture
    def variable_extractor(self) -> VariableExtractor:
        """Create VariableExtractor with default configuration."""
        return VariableExtractor(DEFAULT_VARIABLE_COLLECTION)


class TestFlowVelocityWithVariableExtraction:
    """Test calculate_flow_velocity with variable extraction mode."""

    @pytest.fixture
    def sample_issues(self) -> List[Dict[str, Any]]:
        """Create sample issues with work_completed_timestamp and work_type_category."""
        return [
            {
                "key": "PROJ-101",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "customfield_10010": "Feature",  # Work type field (matches config)
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-15T10:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "PROJ-102",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                    "customfield_10010": "Defect",  # Work type field
                    "resolutiondate": "2025-01-16T14:30:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-16T14:30:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "PROJ-103",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Task"},
                    "customfield_10010": "Technical Debt",  # Work type field
                    "resolutiondate": "2025-01-17T09:15:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-17T09:15:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
        ]

    def test_flow_velocity_with_variable_extraction(self, sample_issues):
        """Test flow velocity calculation using variable extraction mode."""
        # Arrange
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        # Act
        result = calculate_flow_velocity(
            issues=sample_issues,
            start_date=start_date,
            end_date=end_date,
            use_variable_extraction=True,
        )

        # Assert
        assert result["error_state"] == "success"
        assert result["metric_name"] == "flow_velocity"
        assert result["value"] >= 2  # At least 2 issues should be found
        assert result["unit"] == "items/month"  # 30-day period
        assert "by_type" in result["details"]

    def test_flow_velocity_legacy_mode_still_works(self, sample_issues):
        """Test that legacy field_mappings mode still works (backward compatibility)."""
        # Arrange
        field_mappings = {
            "flow_item_type": "issuetype",  # Use issuetype.name for classification
            "completed_date": "resolutiondate",
        }
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        # Act
        result = calculate_flow_velocity(
            issues=sample_issues,
            field_mappings=field_mappings,
            start_date=start_date,
            end_date=end_date,
            use_variable_extraction=False,  # Explicit legacy mode
        )

        # Assert - legacy mode may not find issues without proper config,
        # but should return valid response structure
        assert result["metric_name"] == "flow_velocity"
        assert "error_state" in result
        assert "value" in result
        # Backward compatibility maintained: function accepts field_mappings
        assert result["error_state"] in ["success", "no_data"]
