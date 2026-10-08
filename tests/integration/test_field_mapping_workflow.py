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
    @pytest.fixture(autouse=True)
    def isolate_profiles(self):
        from data.database import get_db_connection
        from data.migration.schema import create_schema
        from data.persistence.factory import reset_backend

        _tmpdir = tempfile.TemporaryDirectory(prefix="field_mapping_test_")
        temp_dir = _tmpdir.name
        temp_profiles_dir = Path(temp_dir) / "profiles"
        temp_profiles_dir.mkdir(parents=True, exist_ok=True)
        temp_db_path = temp_profiles_dir / "test_burndown.db"

        with get_db_connection(temp_db_path) as conn:
            create_schema(conn)
            conn.commit()

        patches = [
            patch("data.persistence.factory.DEFAULT_SQLITE_PATH", str(temp_db_path)),
            patch("data.database.DB_PATH", temp_db_path),
            patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir),
        ]

        for p in patches:
            p.start()

        reset_backend()

        profile_id = create_profile("Field Mapping Test", {})
        switch_profile(profile_id)

        try:
            yield temp_dir
        finally:
            for p in patches:
                p.stop()

            reset_backend()
            _tmpdir.cleanup()

    @pytest.fixture
    def mock_jira_fields(self):
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
        success = save_field_mappings({})
        assert success is True

        loaded_again = load_field_mappings()
        assert isinstance(loaded_again, dict)


class TestFieldMappingIntegrationWithCalculator:
    def test_calculator_uses_field_mappings(self):

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

            field_id = get_mapped_field_id("dora", "deployment_date")
            assert field_id == "customfield_10100"

            unmapped_field = get_mapped_field_id("dora", "nonexistent_field")
            assert unmapped_field is None
