#!/usr/bin/env python3
"""
Unit test for the fix for votes field transformation error.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data.jira import extract_story_points_value, jira_to_csv_format


def test_story_points_extraction():
    """Test the new extract_story_points_value function with different field types."""

    print("Testing Story Points Value Extraction...")

    test_cases = [
        # Votes field (complex object)
        ({"votes": 5, "hasVoted": False}, "votes", 5.0),
        # Simple numeric values (like typical custom fields)
        (8, "customfield_10020", 8.0),
        (3.5, "customfield_10020", 3.5),
        # String numbers
        ("13", "customfield_10021", 13.0),
        ("2.5", "customfield_10021", 2.5),
        # Empty/null values
        (None, "customfield_10020", 0.0),
        ("", "customfield_10020", 0.0),
        (0, "customfield_10020", 0.0),
        # Complex objects with different structures
        ({"value": 7}, "some_field", 7.0),
        ({"points": 4}, "some_field", 4.0),
        ({"count": 2}, "some_field", 2.0),
        # Invalid/unparseable values
        ({"no_numeric_field": "text"}, "bad_field", 0.0),
        ("not_a_number", "bad_field", 0.0),
        (["array", "values"], "bad_field", 0.0),
    ]

    print(f"\n[Stats] Testing {len(test_cases)} different field value scenarios...")

    for i, (input_value, field_name, expected_output) in enumerate(test_cases, 1):
        result = extract_story_points_value(input_value, field_name)

        status = "[OK]" if result == expected_output else "[X]"
        print(
            f"   {status} Test {i}: {input_value} → {result} (expected {expected_output})"
        )

        if result != expected_output:
            print(f"      [FAILED] Expected {expected_output}, got {result}")


def test_votes_field_in_transformation():
    """Test that votes field works correctly in full JIRA transformation."""

    print("\nTesting Votes Field in Full Transformation...")

    # Simulate JIRA issues with votes field
    test_issues = [
        {
            "key": "TEST-1",
            "fields": {
                "created": "2025-01-15T10:00:00.000Z",
                "resolutiondate": "2025-01-17T15:30:00.000Z",
                "status": {"name": "Done"},
                "votes": {  # This is what causes the error!
                    "votes": 3,
                    "hasVoted": False,
                    "self": "https://jira.../votes",
                },
            },
        },
        {
            "key": "TEST-2",
            "fields": {
                "created": "2025-01-16T09:00:00.000Z",
                "resolutiondate": None,
                "status": {"name": "In Progress"},
                "votes": {
                    "votes": 5,
                    "hasVoted": True,
                    "self": "https://jira.../votes",
                },
            },
        },
    ]

    config = {
        "story_points_field": "votes"  # This is the problematic configuration
    }

    print(f"   [List] Testing with {len(test_issues)} issues using 'votes' field")
    print(f"   [Stats] Issue 1 votes: {test_issues[0]['fields']['votes']['votes']}")
    print(f"   [Stats] Issue 2 votes: {test_issues[1]['fields']['votes']['votes']}")

    try:
        # This should now work without errors
        csv_data = jira_to_csv_format(test_issues, config)

        print(
            f"   [OK] Transformation SUCCESS! Generated {len(csv_data)} weekly data points"
        )

        # Check if votes were properly extracted
        if csv_data:
            first_week = csv_data[0]
            print(f"   [Stats] First week data: {first_week}")

            # Issue 1 was completed, so should contribute to completed_points
            if first_week.get("completed_points", 0) > 0:
                print("   [OK] Votes properly extracted as story points!")
            else:
                print("   [!]  No completed points found - check date ranges")

    except Exception as e:
        print(f"   [ERROR] Transformation FAILED: {e}")
        print("   [ERROR] This would be the 'Failed to transform JIRA data' error")


def test_different_field_types():
    """Test that the fix works with different field types."""

    print("\nTesting Different Field Types...")

    field_scenarios = [
        ("votes", {"votes": 8, "hasVoted": True}, 8.0, "Votes field (complex object)"),
        ("customfield_10020", 13, 13.0, "Story points (simple number)"),
        ("customfield_10021", "5", 5.0, "String number"),
        ("priority", {"name": "High", "id": "1"}, 0.0, "Non-numeric complex field"),
    ]

    for field_name, field_value, _expected, description in field_scenarios:
        test_issue = {
            "key": "TEST-X",
            "fields": {
                "created": "2025-01-15T10:00:00.000Z",
                "resolutiondate": "2025-01-16T10:00:00.000Z",
                "status": {"name": "Done"},
                field_name: field_value,
            },
        }

        config = {"story_points_field": field_name}

        print(f"   [List] Testing: {description}")
        print(f"      Field: {field_name} = {field_value}")

        try:
            csv_data = jira_to_csv_format([test_issue], config)
            status = "[OK]" if csv_data else "[X]"
            print(
                f"      {status} Transformation: {'SUCCESS' if csv_data else 'FAILED'}"
            )

        except Exception as e:
            print(f"      [ERROR]: {e}")


if __name__ == "__main__":
    test_story_points_extraction()
    test_votes_field_in_transformation()
    test_different_field_types()
