"""
Migration Testing Module

Tests for CSV-to-JSON data migration functionality.

NOTE: These tests are for legacy CSV-to-JSON migration which has been replaced
by SQLite database migration. Tests are skipped as the functionality no longer exists.
"""

import unittest
import pytest
from unittest.mock import patch
from datetime import datetime


@pytest.mark.skip(reason="CSV-to-JSON migration replaced by SQLite migration")
class TestDataMigration(unittest.TestCase):
    """Test CSV-to-JSON migration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_csv_data = [
            {
                "date": "2024-01-01",
                "completed_items": 5,
                "completed_points": 13,
                "created_items": 2,
                "created_points": 5,
            },
            {
                "date": "2024-01-02",
                "completed_items": 3,
                "completed_points": 8,
                "created_items": 1,
                "created_points": 3,
            },
        ]

        self.sample_project_data = {
            "total_items": 50,
            "total_points": 200,
            "estimated_items": 45,
            "estimated_points": 180,
        }

    @patch("data.persistence.load_statistics")
    @patch("data.persistence.load_project_data")
    def test_migrate_csv_to_json(self, mock_load_project, mock_load_stats):
        """Test basic CSV to JSON migration."""
        # Setup mocks
        mock_load_stats.return_value = (self.sample_csv_data, False)
        mock_load_project.return_value = self.sample_project_data

        # Import after patching
        from data.persistence import migrate_csv_to_json  # type: ignore[attr-defined]

        with patch("data.persistence.save_unified_project_data") as mock_save:
            result = migrate_csv_to_json()

            # Verify structure
            self.assertIn("project_scope", result)
            self.assertIn("statistics", result)
            self.assertIn("metadata", result)

            # Verify project scope
            scope = result["project_scope"]
            self.assertEqual(scope["total_items"], 50)
            self.assertEqual(scope["total_points"], 200)

            # Verify statistics
            stats = result["statistics"]
            self.assertEqual(len(stats), 2)
            self.assertEqual(stats[0]["date"], "2024-01-01")
            self.assertEqual(stats[0]["completed_items"], 5)

            # Verify metadata
            metadata = result["metadata"]
            self.assertEqual(metadata["version"], "2.0")
            self.assertEqual(metadata["source"], "csv_import")

            # Verify save was called
            mock_save.assert_called_once()

    def test_validate_project_data_structure(self):
        """Test project data structure validation."""
        from data.schema import validate_project_data_structure

        # Valid structure
        valid_data = {
            "project_scope": {
                "total_items": 50,
                "total_points": 200,
                "estimated_items": 45,
                "estimated_points": 180,
                "remaining_items": 40,
                "remaining_points": 160,
            },
            "statistics": [
                {
                    "date": "2024-01-01",
                    "completed_items": 5,
                    "completed_points": 13,
                    "created_items": 2,
                    "created_points": 5,
                    "velocity_items": 5,
                    "velocity_points": 13,
                }
            ],
            "metadata": {
                "source": "test",
                "last_updated": datetime.now().isoformat(),
                "version": "2.0",
                "jira_query": "",
            },
        }

        self.assertTrue(validate_project_data_structure(valid_data))

        # Invalid structure - missing required fields
        invalid_data = {
            "project_scope": {
                "total_items": 50
                # Missing other required fields
            }
        }

        self.assertFalse(validate_project_data_structure(invalid_data))

    def test_get_default_unified_data(self):
        """Test default unified data structure."""
        from data.schema import get_default_unified_data

        default_data = get_default_unified_data()

        # Verify structure
        self.assertIn("project_scope", default_data)
        self.assertIn("statistics", default_data)
        self.assertIn("metadata", default_data)

        # Verify default values
        scope = default_data["project_scope"]
        self.assertEqual(scope["total_items"], 0)
        self.assertEqual(scope["total_points"], 0)

        # Verify statistics is empty list
        self.assertEqual(default_data["statistics"], [])

        # Verify metadata
        metadata = default_data["metadata"]
        self.assertEqual(metadata["version"], "2.0")

    @patch("data.persistence.load_unified_project_data")
    def test_get_project_statistics(self, mock_load):
        """Test getting statistics from unified data."""
        mock_load.return_value = {"statistics": self.sample_csv_data}

        from data.persistence import get_project_statistics

        stats = get_project_statistics()
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]["date"], "2024-01-01")

    @patch("data.persistence.load_unified_project_data")
    def test_get_project_scope(self, mock_load):
        """Test getting project scope from unified data."""
        mock_load.return_value = {"project_scope": self.sample_project_data}

        from data.persistence import get_project_scope

        scope = get_project_scope()
        self.assertEqual(scope["total_items"], 50)
        self.assertEqual(scope["total_points"], 200)

    def test_migration_functions_available(self):
        """Test that migration functions are available in persistence module."""
        from data.persistence import migrate_csv_to_json, _backup_legacy_files  # type: ignore[attr-defined]

        # These should be callable
        self.assertTrue(callable(migrate_csv_to_json))
        self.assertTrue(callable(_backup_legacy_files))


@pytest.mark.skip(reason="CSV-to-JSON migration replaced by SQLite migration")
class TestMigrationScript(unittest.TestCase):
    """Test migration functionality."""

    def test_migration_functions_integrated(self):
        """Test that migration functions are now part of persistence module."""
        from data.persistence import migrate_csv_to_json  # type: ignore[attr-defined]

        # The migration function should exist and be callable
        self.assertTrue(callable(migrate_csv_to_json))

        # Test that it has the correct return type annotation
        import inspect

        sig = inspect.signature(migrate_csv_to_json)
        self.assertTrue(hasattr(sig, "return_annotation"))


if __name__ == "__main__":
    unittest.main()
