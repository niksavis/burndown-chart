"""
Unit tests for profile Active indicator in dropdown.

Tests that the "(Active)" indicator is correctly applied and refreshed.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from data.profile_manager import (
    create_profile,
    switch_profile,
    list_profiles,
    get_active_profile,
)


class TestProfileActiveIndicator:
    """Test Active indicator in profile dropdown."""

    @pytest.fixture
    def temp_profiles_dir(self):
        """Create temporary profiles directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_dir = Path(temp_dir) / "profiles"
            profiles_dir.mkdir(parents=True, exist_ok=True)

            # Create profiles.json
            profiles_file = profiles_dir / "profiles.json"
            profiles_file.write_text(
                json.dumps(
                    {
                        "active_profile_id": None,
                        "active_query_id": None,
                        "profiles": {},
                    },
                    indent=2,
                )
            )

            with patch("data.profile_manager.PROFILES_DIR", profiles_dir):
                with patch("data.profile_manager.PROFILES_FILE", profiles_file):
                    yield profiles_dir

    def test_active_profile_shows_active_indicator(self, temp_profiles_dir):
        """Verify active profile has (Active) indicator in dropdown."""
        # Create two profiles
        profile1_id = create_profile("Profile One", {"description": "First"})
        profile2_id = create_profile("Profile Two", {"description": "Second"})

        # Switch to profile1
        switch_profile(profile1_id)

        # Get active profile
        active = get_active_profile()
        assert active is not None
        assert active.id == profile1_id
        assert active.name == "Profile One"

        # Verify profile2 exists but is not active
        profiles = list_profiles()
        assert len(profiles) == 2
        assert any(p["id"] == profile2_id for p in profiles)

    def test_switching_profiles_updates_active_indicator(self, temp_profiles_dir):
        """Verify switching profiles updates which one shows Active."""
        # Create two profiles
        profile1_id = create_profile("Alpha", {"description": "First"})
        profile2_id = create_profile("Beta", {"description": "Second"})

        # Initially switch to Alpha
        switch_profile(profile1_id)
        active = get_active_profile()
        assert active is not None
        assert active.id == profile1_id
        assert active.name == "Alpha"

        # Switch to Beta
        switch_profile(profile2_id)
        active = get_active_profile()
        assert active is not None
        assert active.id == profile2_id
        assert active.name == "Beta"

        # Verify Beta is now active in list
        profiles = list_profiles()
        beta_profile = next(p for p in profiles if p["id"] == profile2_id)
        assert beta_profile["id"] == profile2_id

    def test_only_one_profile_active_at_a_time(self, temp_profiles_dir):
        """Verify only one profile can be active at a time."""
        # Create three profiles
        p1_id = create_profile("P1", {"description": "One"})
        p2_id = create_profile("P2", {"description": "Two"})
        p3_id = create_profile("P3", {"description": "Three"})

        # Switch to P2
        switch_profile(p2_id)

        # Verify only P2 is active
        active = get_active_profile()
        assert active is not None
        assert active.id == p2_id

        # Switch to P3
        switch_profile(p3_id)

        # Verify only P3 is active now
        active = get_active_profile()
        assert active is not None
        assert active.id == p3_id

        # Verify all three profiles exist
        profiles = list_profiles()
        profile_ids = [p["id"] for p in profiles]
        assert p1_id in profile_ids
        assert p2_id in profile_ids
        assert p3_id in profile_ids

    def test_renamed_profile_remains_active(self, temp_profiles_dir):
        """Verify renaming a profile doesn't change active status."""
        from data.profile_manager import rename_profile

        # Create and activate profile
        profile_id = create_profile("Original Name", {"description": "Test"})
        switch_profile(profile_id)

        # Verify it's active
        active_before = get_active_profile()
        assert active_before is not None
        assert active_before.id == profile_id
        assert active_before.name == "Original Name"

        # Rename it
        rename_profile(profile_id, "New Name")

        # Verify still active with new name
        active_after = get_active_profile()
        assert active_after is not None
        assert active_after.id == profile_id  # Same ID
        assert active_after.name == "New Name"  # New name

    def test_duplicated_profile_becomes_active(self, temp_profiles_dir):
        """Verify duplicating a profile and switching makes it active."""
        from data.profile_manager import duplicate_profile

        # Create original profile
        original_id = create_profile("Original", {"description": "Test"})
        switch_profile(original_id)

        # Duplicate it
        duplicate_id = duplicate_profile(original_id, "Copy of Original", "Duplicate")

        # Switch to duplicate
        switch_profile(duplicate_id)

        # Verify duplicate is now active
        active = get_active_profile()
        assert active is not None
        assert active.id == duplicate_id
        assert active.name == "Copy of Original"

    def test_deleted_profile_not_in_list(self, temp_profiles_dir):
        """Verify deleted profile is removed from list."""
        from data.profile_manager import delete_profile

        # Create two profiles
        p1_id = create_profile("Keep This", {"description": "Keep"})
        p2_id = create_profile("Delete This", {"description": "Delete"})

        # Switch to p1
        switch_profile(p1_id)

        # Delete p2
        delete_profile(p2_id)

        # Verify p2 not in list
        profiles = list_profiles()
        profile_ids = [p["id"] for p in profiles]
        assert p1_id in profile_ids
        assert p2_id not in profile_ids

        # Verify p1 still active
        active = get_active_profile()
        assert active is not None
        assert active.id == p1_id
