"""Integration tests for field mapping workflow.

Tests the complete workflow of configuring, saving, and using Jira field mappings.
Ensures proper isolation using tempfile and mocking.
"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from data.field_mapper import (
    fetch_available_jira_fields,
    save_field_mappings,
    load_field_mappings,
)


class TestFieldMappingWorkflow:
    """Test complete field mapping configuration workflow."""

    @pytest.fixture
    def temp_settings_file(self):
        """Create temporary settings file for test isolation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name
            # Initialize with empty structure
            json.dump({"field_mappings": {}}, f)

        yield temp_file

        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def mock_jira_fields(self):
        """Mock Jira fields metadata (as expected by validate_field_mapping)."""
        return {
            "customfield_10100": {
                "field_name": "Deployment Date",
                "field_type": "datetime",
                "is_custom": True,
            },
            "customfield_10101": {
                "field_name": "Target Environment",
                "field_type": "select",
                "is_custom": True,
            },
            "customfield_10102": {
                "field_name": "Code Commit Date",
                "field_type": "datetime",
                "is_custom": True,
            },
            "customfield_10103": {
                "field_name": "Incident Flag",
                "field_type": "checkbox",
                "is_custom": True,
            },
        }

    def test_empty_mappings_handling(self, temp_settings_file):
        """Test that system handles empty/no mappings gracefully."""
        with patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file):
            with patch("data.persistence.SETTINGS_FILE", temp_settings_file):
                # Save empty mappings
                success = save_field_mappings({})
                assert success is True

                # Verify can still load
                loaded_again = load_field_mappings()
                assert isinstance(loaded_again, dict)


class TestFieldMappingIntegrationWithCalculator:
    """Test field mapping integration with DORA calculator."""

    def test_calculator_uses_field_mappings(self):
        """Test that DORA calculator retrieves and uses field mappings.

        NOTE: This is a stub test for Phase 4.
        Full implementation will be in Phase 5 when we integrate
        field mappings with actual metric calculations.
        """
        from data.field_mapper import get_mapped_field_id

        test_mappings = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10100",
                }
            }
        }

        with patch("data.field_mapper.load_field_mappings") as mock_load:
            mock_load.return_value = test_mappings

            # Get mapped field ID
            field_id = get_mapped_field_id("dora", "deployment_date")
            assert field_id == "customfield_10100"

            # Try to get unmapped field
            unmapped_field = get_mapped_field_id("dora", "nonexistent_field")
            assert unmapped_field is None
