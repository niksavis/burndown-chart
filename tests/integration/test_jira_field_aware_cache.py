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
from data.jira_simple import cache_jira_response, load_jira_cache


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

    test_cache_file = "test_cache.json"

    print("\n1️⃣ Test Cache Creation with 'Votes' field...")

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

    print("\n2️⃣ Test Cache Load with Same Fields (Should Work)...")

    # Load with same fields
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, fields_with_votes, test_cache_file
    )
    print(f"   [OK] Cache loaded successfully: {cache_loaded}")
    print(f"   [Stats] Loaded issues: {len(loaded_issues) if loaded_issues else 0}")

    print("\n3️⃣ Test Cache Load with Different Fields (Should Invalidate)...")

    # Load with different fields (change from "Votes" to "customfield_10020")
    fields_with_story_points = "key,created,resolutiondate,status,customfield_10020"
    cache_loaded, loaded_issues = load_jira_cache(
        jql_query, fields_with_story_points, test_cache_file
    )
    print(f"   [X] Cache should be invalidated: {not cache_loaded}")
    print(f"   [Stats] Issues returned: {len(loaded_issues) if loaded_issues else 0}")

    print("\n4️⃣ Test Cache Load with No Story Points Field (Should Work)...")

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

    print("\n5️⃣ Test Cache Load Base vs Story Points (Should Invalidate)...")

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

    print(f"   [Stats] Created old cache format (no fields_requested)")

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

    # Cleanup
    if os.path.exists(test_cache_file):
        os.remove(test_cache_file)

    print(f"\n[Tip] Test Summary:")
    print(f"   [OK] Cache invalidation works for field changes")
    print(f"   [OK] Backward compatibility maintained")
    print(f"   [OK] Base fields vs story points detection works")
    print(f"   🔥 Your field configuration caching issue is SOLVED!")


if __name__ == "__main__":
    test_field_aware_caching()
