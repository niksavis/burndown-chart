#!/usr/bin/env python3
"""
Integration test for the new field-aware cache invalidation system.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import shutil
import tempfile
from datetime import UTC
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def isolated_jira_cache_test():
    """Isolate JIRA cache tests with temp database and profile/query."""
    from datetime import datetime

    from data.database import get_db_connection as real_get_db_connection
    from data.migration.schema import create_schema
    from data.persistence.factory import reset_backend
    from data.persistence.sqlite_backend import SQLiteBackend
    from data.profile_manager import Profile

    # Create temporary directory and database
    temp_dir = tempfile.mkdtemp(prefix="jira_cache_test_")
    temp_profiles_dir = Path(temp_dir) / "profiles"
    temp_profiles_dir.mkdir(parents=True, exist_ok=True)
    temp_db_path = Path(temp_profiles_dir / "test_burndown.db")

    # Initialize temp database with schema
    with real_get_db_connection(temp_db_path) as conn:
        create_schema(conn)
        conn.commit()

    # Create test backend instance
    test_backend = SQLiteBackend(str(temp_db_path))
    reset_backend()

    # Create test profile and query
    now = datetime.now(UTC).isoformat()
    test_profile = Profile(
        id="p_test_cache",
        name="Test Cache Profile",
        description="Test profile for JIRA cache",
        jira_config={"configured": True},
        field_mappings={},
        forecast_settings={},
        project_classification={},
        flow_type_mappings={},
        queries=[],
    )
    test_backend.save_profile(test_profile.to_dict())

    test_query = {
        "id": "q_test_cache",
        "name": "Test Query",
        "jql": "project = TEST",
        "description": "Test query",
        "created_at": now,
        "last_used": now,
    }
    test_backend.save_query("p_test_cache", test_query)

    # Set as active
    test_backend.set_app_state("active_profile_id", "p_test_cache")
    test_backend.set_app_state("active_query_id", "q_test_cache")

    def mock_get_backend(*args, **kwargs):
        return test_backend

    def mock_get_db_connection(db_path=None):
        """Always use test database."""
        return real_get_db_connection(temp_db_path)

    # Patch backend and database connection
    patches = [
        patch("data.persistence.factory.get_backend", side_effect=mock_get_backend),
        patch("data.database.get_db_connection", side_effect=mock_get_db_connection),
        patch(
            "data.persistence.sqlite_backend.get_db_connection",
            side_effect=mock_get_db_connection,
        ),
        patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir),
    ]

    for p in patches:
        p.start()

    yield temp_dir

    for p in patches:
        p.stop()

    reset_backend()
    shutil.rmtree(temp_dir, ignore_errors=True)


# test_field_aware_caching was removed: it tested JSON-file-only caching which was
# replaced by database-first caching with JSON fallback (see data/jira/cache_*.py).
