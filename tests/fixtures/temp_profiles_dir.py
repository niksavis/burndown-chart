import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_profiles_dir():

    with tempfile.TemporaryDirectory() as temp_dir:
        profiles_dir = Path(temp_dir) / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)

        profiles_file = profiles_dir / "profiles.json"

        with (
            patch("data.profile_manager.PROFILES_DIR", profiles_dir),
            patch("data.profile_manager.PROFILES_FILE", profiles_file),
        ):
            yield profiles_dir


@pytest.fixture
def temp_profiles_dir_with_default():

    with tempfile.TemporaryDirectory() as temp_dir:
        profiles_dir = Path(temp_dir) / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)

        default_profile_dir = profiles_dir / "default"
        default_queries_dir = default_profile_dir / "queries"
        default_query_dir = default_queries_dir / "default"
        default_query_dir.mkdir(parents=True, exist_ok=True)

        db_path = profiles_dir / "burndown.db"
        from data.migration.schema_manager import initialize_schema

        initialize_schema(db_path=db_path)

        profiles_file = profiles_dir / "profiles.json"

        with (
            patch("data.profile_manager.PROFILES_DIR", profiles_dir),
            patch("data.profile_manager.PROFILES_FILE", profiles_file),
            patch("data.database.DB_PATH", db_path),
            patch("data.persistence.factory.DEFAULT_SQLITE_PATH", str(db_path)),
        ):
            import data.persistence.factory as factory

            factory._backend_instance = None

            from datetime import UTC, datetime

            from data.persistence.factory import get_backend

            now = datetime.now(UTC).isoformat()
            backend = get_backend()
            backend.save_profile(
                {
                    "id": "default",
                    "name": "Default Profile",
                    "description": "Default profile for testing",
                    "created_at": now,
                    "last_used": now,
                    "jira_config": {
                        "configured": True,
                        "jira_url": "https://example.atlassian.net",
                        "jira_token": "test_secret_token",
                        "username": "testuser@example.com",
                    },
                    "field_mappings": {},
                    "forecast_settings": {},
                    "project_classification": {},
                    "flow_type_mappings": {},
                }
            )

            yield profiles_dir
