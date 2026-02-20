"""Integration tests for field mapping workflow.

Tests the complete workflow of configuring, saving, and using Jira field mappings.
Ensures proper isolation using tempfile and mocking.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from data.field_mapper import (
    load_field_mappings,
    save_field_mappings,
)
from data.profile_manager import create_profile, switch_profile


class TestFieldMappingWorkflow:
    """Test complete field mapping configuration workflow."""

    @pytest.fixture(autouse=True)
    def isolate_profiles(self):
        """Create isolated profile environment for field mapping tests."""
        from data.database import get_db_connection
        from data.migration.schema import create_schema
        from data.persistence.factory import reset_backend
        from data.persistence.sqlite_backend import SQLiteBackend

        temp_dir = tempfile.mkdtemp(prefix="field_mapping_test_")
        temp_profiles_dir = Path(temp_dir) / "profiles"
        temp_profiles_dir.mkdir(parents=True, exist_ok=True)
        temp_db_path = str(temp_profiles_dir / "test_burndown.db")

        # Initialize temp database with schema
        with get_db_connection(Path(temp_db_path)) as conn:
            create_schema(conn)
            conn.commit()

        # Create test backend instance
        test_backend = SQLiteBackend(temp_db_path)

        # Reset and patch get_backend to always return our test backend
        reset_backend()

        def mock_get_backend(*args, **kwargs):
            return test_backend

        # Patch both the factory and all module imports
        patches = [
            patch("data.persistence.factory.get_backend", side_effect=mock_get_backend),
            patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir),
        ]

        for p in patches:
            p.start()

        # Create and switch to a test profile
        profile_id = create_profile("Field Mapping Test", {})
        switch_profile(profile_id)

        yield temp_dir

        for p in patches:
            p.stop()

        reset_backend()
        shutil.rmtree(temp_dir, ignore_errors=True)

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

    def test_empty_mappings_handling(self):
        """Test that system handles empty/no mappings gracefully."""
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
