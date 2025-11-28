"""Integration test: Verify field mapping isolation across profile deletion/recreation.

Bug Report (Feature 010 Phase 4 - Testing):
"After deleting the Apache profile and recreating a new Apache profile,
and opening the Configure JIRA Mappings dialog, the old mappings were still there."

Root Cause:
The field-mapping-state-store (dcc.Store with storage_type="memory") was persisting
field mappings in browser memory across profile switches, causing old data to appear
in newly created profiles with the same name.

Fix:
Added callback clear_field_mapping_state_on_profile_switch() that clears the
state store whenever the profile selector value changes.

Test Strategy:
This integration test verifies that:
1. Creating a profile with field mappings works correctly
2. Deleting the profile removes all data including mappings
3. Recreating a profile with the SAME NAME shows empty/default mappings
4. The state store is properly cleared on profile switch
"""

import pytest

# Import profile management functions
from data.profile_manager import (
    create_profile,
    delete_profile,
    switch_profile,
    list_profiles,
    PROFILES_DIR,
)
from data.persistence import load_app_settings


class TestProfileFieldMappingIsolation:
    """Test data isolation when deleting and recreating profiles with same name."""

    @pytest.fixture(autouse=True)
    def cleanup_test_profiles(self):
        """Clean up any test profiles before and after each test."""
        yield
        # Cleanup after test
        try:
            profiles = list_profiles()
            for profile in profiles:
                if profile["name"].startswith("TestProfile"):
                    try:
                        delete_profile(profile["id"])
                    except Exception as e:
                        print(
                            f"Cleanup: Could not delete profile {profile['name']}: {e}"
                        )
        except Exception as e:
            print(f"Cleanup error: {e}")

    def test_field_mappings_cleared_on_profile_recreation(self):
        """Verify field mappings are isolated per profile and cleared on deletion.

        Scenario (Bug 1 reproduction):
        1. Create profile "Apache" with field mappings
        2. Delete profile "Apache"
        3. Create new profile "Apache" (same name, different ID)
        4. Verify new profile has EMPTY field mappings (not old mappings)
        """
        # Step 1: Create profile with field mappings
        initial_settings = {
            "description": "Test Apache profile with mappings",
            "pert_factor": 1.2,
            "deadline": "2025-12-31",
            "data_points_count": 20,
            "jira_config": {"base_url": "https://jira.example.com"},
            "field_mappings": {
                "deployment_date": "fixVersions",
                "target_environment": "customfield_10001",
                "code_commit_date": "customfield_10002",
            },
            "project_classification": {
                "development_projects": ["KAFKA", "SPARK"],
                "devops_projects": ["INFRA"],
            },
        }

        profile_id_v1 = create_profile("TestProfile-Apache", initial_settings)
        switch_profile(profile_id_v1)

        # Verify initial mappings are saved
        settings_v1 = load_app_settings()
        assert settings_v1["field_mappings"]["deployment_date"] == "fixVersions"
        assert (
            settings_v1["field_mappings"]["target_environment"] == "customfield_10001"
        )
        assert settings_v1["development_projects"] == ["KAFKA", "SPARK"]

        print(
            f"[OK] Step 1: Created profile '{profile_id_v1}' with field mappings and project classifications"
        )

        # Step 2: Delete profile
        delete_profile(profile_id_v1)

        # Verify profile directory is deleted
        profile_dir_v1 = PROFILES_DIR / profile_id_v1
        assert not profile_dir_v1.exists(), "Profile directory should be deleted"
        print(
            f"[OK] Step 2: Deleted profile '{profile_id_v1}' and verified directory removed"
        )

        # Step 3: Create new profile with SAME NAME but different settings
        new_settings = {
            "description": "New Apache profile - should have empty mappings",
            "pert_factor": 1.5,
            "deadline": "2026-06-30",
            "data_points_count": 15,
            "jira_config": {},  # Empty JIRA config
            "field_mappings": {},  # Empty field mappings
            "project_classification": {
                "development_projects": [],  # Empty projects
                "devops_projects": [],
            },
        }

        profile_id_v2 = create_profile("TestProfile-Apache", new_settings)
        switch_profile(profile_id_v2)

        # Verify different profile ID (new profile, not resurrection)
        assert profile_id_v1 != profile_id_v2, (
            "New profile should have different ID than deleted profile"
        )
        print(f"[OK] Step 3: Created new profile '{profile_id_v2}' with empty mappings")

        # Step 4: Verify new profile has EMPTY field mappings
        settings_v2 = load_app_settings()

        # Critical assertions: New profile should NOT have old mappings
        assert settings_v2.get("field_mappings", {}) == {}, (
            "New profile should have empty field_mappings"
        )
        assert settings_v2.get("development_projects", []) == [], (
            "New profile should have empty development_projects"
        )
        assert settings_v2.get("devops_projects", []) == [], (
            "New profile should have empty devops_projects"
        )

        # Verify new settings are correctly set (flattened structure from load_app_settings)
        assert settings_v2["pert_factor"] == 1.5
        assert settings_v2["deadline"] == "2026-06-30"
        assert settings_v2["data_points_count"] == 15

        print(
            "[OK] Step 4: Verified new profile has EMPTY field mappings and project classifications"
        )
        print(
            "[OK] TEST PASSED: Field mappings are properly isolated and cleared on profile deletion/recreation"
        )

    def test_field_mappings_persist_across_profile_switches(self):
        """Verify field mappings persist when switching between profiles (not deleting).

        This ensures our fix doesn't break normal profile switching behavior.
        """
        # Create two profiles with different mappings
        settings_profile_a = {
            "description": "Profile A",
            "field_mappings": {
                "deployment_date": "fixVersions",
                "target_environment": "customfield_10001",
            },
            "project_classification": {
                "development_projects": ["PROJECT-A"],
            },
        }

        settings_profile_b = {
            "description": "Profile B",
            "field_mappings": {
                "deployment_date": "customfield_20001",
                "code_commit_date": "customfield_20002",
            },
            "project_classification": {
                "development_projects": ["PROJECT-B"],
            },
        }

        profile_a_id = create_profile("TestProfile-A", settings_profile_a)
        profile_b_id = create_profile("TestProfile-B", settings_profile_b)

        # Switch to Profile A
        switch_profile(profile_a_id)
        settings_a = load_app_settings()
        assert settings_a["field_mappings"]["deployment_date"] == "fixVersions"
        assert settings_a["development_projects"] == ["PROJECT-A"]
        print("[OK] Profile A: Mappings loaded correctly")

        # Switch to Profile B
        switch_profile(profile_b_id)
        settings_b = load_app_settings()
        assert settings_b["field_mappings"]["deployment_date"] == "customfield_20001"
        assert "code_commit_date" in settings_b["field_mappings"]
        assert settings_b["development_projects"] == ["PROJECT-B"]
        print("[OK] Profile B: Mappings loaded correctly")

        # Switch back to Profile A
        switch_profile(profile_a_id)
        settings_a_again = load_app_settings()
        assert settings_a_again["field_mappings"]["deployment_date"] == "fixVersions"
        assert settings_a_again["development_projects"] == ["PROJECT-A"]
        print("[OK] Profile A (switch back): Mappings still correct")

        print(
            "[OK] TEST PASSED: Field mappings persist correctly across profile switches"
        )

    def test_state_store_cleared_on_profile_switch_callback(self):
        """Verify the callback clears state store on ACTUAL profile switch.

        This tests the fix directly: clear_field_mapping_state_on_profile_switch()
        callback should only clear when profile actually changes, not when set to same value.
        """
        from dash import no_update
        from callbacks.field_mapping import (
            clear_field_mapping_state_on_profile_switch,
        )

        # Create two profiles
        profile_a_id = create_profile(
            "TestProfile-StateStore-A", {"field_mappings": {"dora": {"key": "value"}}}
        )
        profile_b_id = create_profile(
            "TestProfile-StateStore-B", {"field_mappings": {}}
        )

        # Test 1: First profile set (no previous profile) - should mark profile without clearing
        state_before_first_switch = {}  # Empty state initially
        result = clear_field_mapping_state_on_profile_switch(
            profile_a_id, state_before_first_switch, {}
        )

        # Should preserve empty state and just add profile ID (render_tab_content will init from settings)
        assert result[0] == {"_profile_id": profile_a_id}, (
            f"First profile set should only add profile ID, got {result[0]}"
        )
        assert result[1] == no_update, "Metadata should not be cleared on first set"
        print(
            f"[OK] First profile set: Marks profile ID as {profile_a_id}, preserves state"
        )

        # Test 2: Same profile again (simulates page refresh/reopen modal) - should NOT clear
        state_with_data = {
            "_profile_id": profile_a_id,
            "field_mappings": {"dora": {"deployment_date": "fixVersions"}},
        }
        result = clear_field_mapping_state_on_profile_switch(
            profile_a_id, state_with_data, {"some": "metadata"}
        )

        assert result == (no_update, no_update), (
            "Same profile should not clear state (no_update expected)"
        )
        print(f"[OK] Same profile ({profile_a_id}): Preserves state (no_update)")

        # Test 3: Actual profile change - should clear state and update profile ID
        result = clear_field_mapping_state_on_profile_switch(
            profile_b_id, state_with_data, {"some": "metadata"}
        )

        assert result[0] == {"_profile_id": profile_b_id}, (
            f"Profile switch should update profile ID to {profile_b_id}, got {result[0]}"
        )
        assert result[1] == {}, "Metadata should be cleared on profile switch"
        print(
            f"[OK] Profile switch ({profile_a_id} → {profile_b_id}): Clears state and updates ID"
        )

        print(
            "[OK] TEST PASSED: Callback correctly handles profile switches and same-profile sets"
        )


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
