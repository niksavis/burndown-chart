#!/usr/bin/env python3
"""
Integration test to verify if field name "Votes" works in JIRA API requests.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_jira_field_mapping():
    """Test if 'Votes' field name works vs customfield IDs."""

    print("🧪 Testing JIRA field name mapping...")

    from data.jira_simple import fetch_jira_issues, get_jira_config

    # Test 1: Check what happens with "Votes" as field name
    print("\n1️⃣ Testing with field name 'Votes'...")

    config = get_jira_config()
    print(
        f"   📋 Current config story_points_field: '{config.get('story_points_field', 'Not set')}'"
    )

    # Test the field construction logic
    base_fields = "key,created,resolutiondate,status"
    if config.get("story_points_field") and config["story_points_field"].strip():
        fields = f"{base_fields},{config['story_points_field']}"
        print(f"   🔗 Constructed fields string: '{fields}'")
    else:
        fields = base_fields
        print(f"   🔗 Using base fields only: '{fields}'")

    # Test 2: Make a small API call to see what happens
    print("\n2️⃣ Testing actual API call with 'Votes' field...")

    try:
        # Make a limited API call to test
        success, issues = fetch_jira_issues(
            config, max_results=3
        )  # Only get 3 issues for testing

        if success and issues:
            print(f"   ✅ API call successful, got {len(issues)} issues")

            # Check if Votes field is present in response
            first_issue = issues[0]
            fields_in_response = first_issue.get("fields", {}).keys()
            print(
                f"   📊 Available fields in response: {sorted(list(fields_in_response))}"
            )

            # Specifically check for votes-related fields
            votes_fields = [
                field for field in fields_in_response if "vote" in field.lower()
            ]
            if votes_fields:
                print(f"   🗳️  Found votes-related fields: {votes_fields}")

                # Check actual votes value
                for field in votes_fields:
                    value = first_issue["fields"].get(field)
                    print(f"   📊 {field} value: {value}")
            else:
                print("   ❌ No votes-related fields found in response")

            # Check if direct "Votes" field exists
            if "Votes" in first_issue.get("fields", {}):
                votes_value = first_issue["fields"]["Votes"]
                print(f"   🗳️  Direct 'Votes' field value: {votes_value}")
            else:
                print("   ❌ Direct 'Votes' field not found in response")

        else:
            print(f"   ❌ API call failed: {success}")

    except Exception as e:
        print(f"   💥 Error during API call: {e}")

    # Test 3: Show what standard votes field should be
    print("\n3️⃣ JIRA API Field Name Reference...")
    print("   📚 Standard JIRA field names that should work:")
    print("   • votes - Vote count (if enabled)")
    print("   • votes.votes - Detailed votes info")
    print("   • customfield_XXXXX - Custom fields (instance-specific)")
    print("   • For story points: Usually 'customfield_10020' or similar")

    print("\n🎯 Field Name vs Field ID:")
    print("   • Field Names: 'votes', 'assignee', 'priority', 'labels'")
    print("   • Field IDs: 'customfield_10020', 'customfield_10002', etc.")
    print("   • Standard fields use names, custom fields use IDs")


if __name__ == "__main__":
    test_jira_field_mapping()
