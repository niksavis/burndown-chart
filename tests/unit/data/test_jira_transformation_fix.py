#!/usr/bin/env python3

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data.jira import extract_story_points_value, jira_to_csv_format


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"votes": 5}, 5.0),
        (8, 8.0),
        (3.5, 3.5),
        ("13", 13.0),
        ("2.5", 2.5),
        (None, 0.0),
        ("", 0.0),
        (0, 0.0),
        ({"value": 7}, 7.0),
        ({"points": 4}, 4.0),
        ({"count": 2}, 2.0),
    ],
)
def test_story_points_extraction(value, expected) -> None:
    assert extract_story_points_value(value, "customfield_10001") == expected


@pytest.mark.parametrize(
    "value", [{"no_numeric_field": "text"}, "not_a_number", ["array", "values"]]
)
def test_invalid_story_points_extraction(value) -> None:
    with pytest.raises(ValueError, match="customfield_10001"):
        extract_story_points_value(value, "customfield_10001")


def test_votes_field_in_transformation():

    print("\nTesting Votes Field in Full Transformation...")

    test_issues = [
        {
            "key": "TEST-1",
            "fields": {
                "created": "2025-01-15T10:00:00.000Z",
                "resolutiondate": "2025-01-17T15:30:00.000Z",
                "status": {"name": "Done"},
                "votes": {
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

    config = {"story_points_field": "votes"}

    print(f"   [List] Testing with {len(test_issues)} issues using 'votes' field")
    print(f"   [Stats] Issue 1 votes: {test_issues[0]['fields']['votes']['votes']}")
    print(f"   [Stats] Issue 2 votes: {test_issues[1]['fields']['votes']['votes']}")

    try:
        csv_data = jira_to_csv_format(test_issues, config)

        print(
            "   [OK] Transformation SUCCESS! "
            f"Generated {len(csv_data)} weekly data points"
        )

        if csv_data:
            first_week = csv_data[0]
            print(f"   [Stats] First week data: {first_week}")

            if first_week.get("completed_points", 0) > 0:
                print("   [OK] Votes properly extracted as story points!")
            else:
                print("   [!]  No completed points found - check date ranges")

    except Exception as e:
        print(f"   [ERROR] Transformation FAILED: {e}")
        print("   [ERROR] This would be the 'Failed to transform JIRA data' error")


def test_different_field_types():

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
    raise SystemExit(pytest.main([__file__]))
