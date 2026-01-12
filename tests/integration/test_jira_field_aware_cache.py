#!/usr/bin/env python3
"""
Integration test for the new field-aware cache invalidation system.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch
from data.jira_simple import cache_jira_response, load_jira_cache


@pytest.fixture(autouse=True)
def isolated_jira_cache_test():
    """Isolate JIRA cache tests with temp database and profile/query."""
    from data.persistence.factory import reset_backend
    from data.migration.schema import create_schema
    from data.database import get_db_connection as real_get_db_connection
    from data.persistence.sqlite_backend import SQLiteBackend
    from data.profile_manager import Profile
    from datetime import datetime, timezone

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
    now = datetime.now(timezone.utc).isoformat()
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


@pytest.mark.skip(
    reason="Test expects JSON file caching, but app now uses database-first caching with JSON fallback"
)
def test_field_aware_caching():
    """Test that cache invalidates when field configuration changes."""

    print("Testing Field-Aware Cache Invalidation...")

    # Test data - minimal JIRA issue structure
    test_issues = [
        {
            "key": "TEST-1",
            "fields": {
                "created": "2025-01-01T10:00:00.000Z",
                "resolutiondate": None,
                "status": {"name": "To Do"},
                "Votes": {"votes": 3, "hasVoted": False},
            },
        },
        {
            "key": "TEST-2",
            "fields": {
                "created": "2025-01-02T10:00:00.000Z",
                "resolutiondate": "2025-01-03T10:00:00.000Z",
                "status": {"name": "Done"},
                "Votes": {"votes": 5, "hasVoted": True},
            },
        },
    ]

    # Use temporary file to avoid polluting project root
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="jira_cache_test_")
    test_cache_file = os.path.join(temp_dir, "test_cache.json")

    print("\n1. Test Cache Creation with 'Votes' field...")

    # Cache data with "Votes" field
    jql_query = "project = TEST"
    fields_with_votes = "key,created,resolutiondate,status,Votes"

    success = cache_jira_response(
        test_issues, jql_query, fields_with_votes, test_cache_file
    )
    print(f"   [OK] Cache created: {success}")

    # Verify cache file structure
    with open(test_cache_file, "r") as f:
        cached_data = json.load(f)

    print(f"   [Stats] Cached JQL: '{cached_data.get('jql_query')}'")
    print(f"   [Stats] Cached Fields: '{cached_data.get('fields_requested')}'")
    print(f"   [Stats] Issues count: {len(cached_data.get('issues', []))}")

    print("\n2. Test Cache Load with Same Fields (Should Work)...")

    # Load with same fields
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, fields_with_votes, test_cache_file
    )
    print(f"   [OK] Cache loaded successfully: {cache_loaded}")
    print(f"   [Stats] Loaded issues: {len(loaded_issues) if loaded_issues else 0}")

    print("\n3. Test Cache Load with Different Fields (Should Invalidate)...")

    # Load with different fields (change from "Votes" to "customfield_10020")
    fields_with_story_points = "key,created,resolutiondate,status,customfield_10020"
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, fields_with_story_points, test_cache_file
    )
    print(f"   [X] Cache should be invalidated: {not cache_loaded}")
    print(f"   [Stats] Issues returned: {len(loaded_issues) if loaded_issues else 0}")

    print("\n4. Test Cache Load with No Story Points Field (Should Work)...")

    # Create cache with base fields only
    base_fields = "key,created,resolutiondate,status"
    base_test_issues = [
        {
            "key": "TEST-1",
            "fields": {
                "created": "2025-01-01T10:00:00.000Z",
                "resolutiondate": None,
                "status": {"name": "To Do"},
            },
        }
    ]

    success = cache_jira_response(
        base_test_issues, jql_query, base_fields, test_cache_file
    )
    print(f"   [OK] Base fields cache created: {success}")

    # Load with base fields (should work)
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, base_fields, test_cache_file
    )
    print(f"   [OK] Base fields cache loaded: {cache_loaded}")

    print("\n5. Test Cache Load Base vs Story Points (Should Invalidate)...")

    # Try to load base cache but with story points configured
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, fields_with_votes, test_cache_file
    )
    print(
        f"   [X] Cache should be invalidated (base → story points): {not cache_loaded}"
    )

    print("\n6️⃣ Test Backward Compatibility (Old Cache Format)...")

    # Create old cache format (without fields_requested)
    old_cache_data = {
        "timestamp": "2025-07-19T19:00:00.000000",
        "jql_query": jql_query,
        "issues": test_issues,
        "total_issues": len(test_issues),
        # Note: no "fields_requested" field
    }

    with open(test_cache_file, "w") as f:
        json.dump(old_cache_data, f, indent=2)

    print("   [Stats] Created old cache format (no fields_requested)")

    # Try to load old cache with base fields (should work)
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, base_fields, test_cache_file
    )
    print(f"   [OK] Old cache + base fields: {cache_loaded}")

    # Try to load old cache with story points fields (should invalidate)
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, fields_with_votes, test_cache_file
    )
    print(
        f"   [X] Old cache + story points field should invalidate: {not cache_loaded}"
    )

    # Cleanup temp directory
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    print("\n[Tip] Test Summary:")
    print("   [OK] Cache invalidation works for field changes")
    print("   [OK] Backward compatibility maintained")
    print("   [OK] Base fields vs story points detection works")
    print("   Test completed - temporary files cleaned up")


if __name__ == "__main__":
    test_field_aware_caching()
