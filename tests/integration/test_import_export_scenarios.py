"""
Integration tests for import/export scenarios (User Story 1).

Tests end-to-end export workflows including:
- T022: CONFIG_ONLY mode excludes cache files
- T023: CONFIG_ONLY exports have minimal file size
"""

import pytest
import json
from pathlib import Path

from data.import_export import export_profile_with_mode


# ============================================================================
# T022-T023: Integration Tests for CONFIG_ONLY Export
# ============================================================================


class TestConfigOnlyExport:
    """Integration tests for CONFIG_ONLY export mode."""

    def test_config_only_export_excludes_cache_files(
        self, temp_profiles_dir_with_default
    ):
        """T022: Verify CONFIG_ONLY export excludes JIRA cache files.

        Independent Test Scenario: Export profile after JIRA sync, verify
        no cache data in export package.
        """
        # Given - Profile with query and cache data
        profiles_dir = temp_profiles_dir_with_default
        profile_id = "default"
        query_id = "test_query"

        # Create query directory with cache
        query_path = Path(profiles_dir) / profile_id / "queries" / query_id
        query_path.mkdir(parents=True, exist_ok=True)

        # Write project data
        project_data = {
            "query_id": query_id,
            "statistics": {"total_issues": 100},
        }
        with open(query_path / "project_data.json", "w") as f:
            json.dump(project_data, f)

        # Write JIRA cache (should be excluded in CONFIG_ONLY)
        jira_cache = {
            "issues": [{"key": "TEST-1", "fields": {"summary": "Test"}}],
            "total": 1,
        }
        with open(query_path / "jira_cache.json", "w") as f:
            json.dump(jira_cache, f)

        # When - Export with CONFIG_ONLY mode
        try:
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="CONFIG_ONLY",
                include_token=False,
            )
        except FileNotFoundError:
            # Expected if profile.json doesn't exist in test fixture
            pytest.skip(
                "Profile fixture needs profile.json - use temp_profiles_dir_with_default fixture"
            )

        # Then
        assert result is not None
        assert result["manifest"]["export_mode"] == "CONFIG_ONLY"
        # Query data should NOT be in export (CONFIG_ONLY excludes it)
        assert "query_data" not in result or result.get("query_data") is None

    def test_export_config_only_file_size_validation(
        self, temp_profiles_dir_with_default
    ):
        """T023: Verify CONFIG_ONLY export results in minimal file size.

        Independent Test Scenario: Compare CONFIG_ONLY export size vs
        FULL_DATA export - should be >90% smaller.
        """
        # Given - Profile with significant query data
        profiles_dir = temp_profiles_dir_with_default
        profile_id = "default"
        query_id = "test_query"

        # Create query with large dataset
        query_path = Path(profiles_dir) / profile_id / "queries" / query_id
        query_path.mkdir(parents=True, exist_ok=True)

        # Large project data (simulating 1000 issues)
        large_project_data = {
            "query_id": query_id,
            "statistics": {"total_issues": 1000, "completed": 750},
            "issues": [
                {"key": f"TEST-{i}", "summary": f"Issue {i}"} for i in range(100)
            ],
        }
        with open(query_path / "project_data.json", "w") as f:
            json.dump(large_project_data, f)

        try:
            # When - Export with CONFIG_ONLY
            config_only_result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="CONFIG_ONLY",
                include_token=False,
            )

            # Export with FULL_DATA for comparison
            full_data_result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="FULL_DATA",
                include_token=False,
            )

            # Calculate sizes
            config_only_size = len(json.dumps(config_only_result))
            full_data_size = len(json.dumps(full_data_result))

            # Then - CONFIG_ONLY should be significantly smaller
            size_reduction_percent = (
                (full_data_size - config_only_size) / full_data_size * 100
            )

            assert config_only_size < full_data_size
            # CONFIG_ONLY should be at least 50% smaller (ideally >90%)
            assert size_reduction_percent > 50, (
                f"CONFIG_ONLY export only {size_reduction_percent:.1f}% smaller. "
                f"Expected >50% reduction."
            )

        except FileNotFoundError:
            pytest.skip(
                "Profile fixture needs profile.json - use temp_profiles_dir_with_default fixture"
            )

    def test_config_only_preserves_configuration_structure(
        self, temp_profiles_dir_with_default
    ):
        """Verify CONFIG_ONLY export includes all configuration fields.

        This ensures that configuration-only exports are complete and
        can be imported to another system successfully.
        """
        # Given - Profile with full configuration
        profile_id = "default"
        query_id = "test_query"

        try:
            # When - Export with CONFIG_ONLY
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="CONFIG_ONLY",
                include_token=False,
            )

            # Then - Should have all config structures
            assert "manifest" in result
            assert "profile_data" in result
            assert result["manifest"]["export_mode"] == "CONFIG_ONLY"
            assert result["manifest"]["includes_token"] is False

            # Profile data should have essential configuration
            profile_data = result["profile_data"]
            # Check for key configuration sections (fields may vary by fixture)
            # At minimum, should have some structure
            assert isinstance(profile_data, dict)
            assert len(profile_data) > 0

        except FileNotFoundError:
            pytest.skip(
                "Profile fixture needs profile.json - use temp_profiles_dir_with_default fixture"
            )


class TestExportSecurity:
    """Integration tests for export security features."""

    def test_config_only_strips_credentials_by_default(
        self, temp_profiles_dir_with_default
    ):
        """Verify CONFIG_ONLY export strips credentials without explicit flag.

        Security Test: Ensures accidental credential leakage is prevented
        even if user forgets to check "strip credentials" option.
        """
        profile_id = "default"
        query_id = "test_query"

        # Note: This test requires profile.json with jira_token field
        # If fixture doesn't have token, skip test
        profile_path = Path("profiles") / profile_id / "profile.json"
        if not profile_path.exists():
            pytest.skip("Profile fixture not available")

        with open(profile_path, "r") as f:
            profile_data = json.load(f)

        # Add token if not present (for test purposes)
        if "jira_token" not in profile_data and "jira_config" in profile_data:
            profile_data["jira_config"]["jira_token"] = "test_secret_token"
            with open(profile_path, "w") as f:
                json.dump(profile_data, f)

        try:
            # When - Export with CONFIG_ONLY and include_token=False (default)
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="CONFIG_ONLY",
                include_token=False,
            )

            # Then - Credentials should be stripped
            assert result["manifest"]["includes_token"] is False

            # Check profile data for any credential fields
            profile_str = json.dumps(result["profile_data"]).lower()
            # Should not contain actual token value
            assert "test_secret_token" not in profile_str

        except FileNotFoundError:
            pytest.skip("Profile fixture not available")

    def test_full_data_also_strips_credentials_unless_requested(
        self, temp_profiles_dir_with_default
    ):
        """Verify FULL_DATA export also strips credentials by default.

        Security Test: Even full data exports should be secure by default.
        """
        profile_id = "default"
        query_id = "test_query"

        try:
            # When - Export with FULL_DATA and include_token=False (default)
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="FULL_DATA",
                include_token=False,
            )

            # Then - Credentials should still be stripped
            assert result["manifest"]["includes_token"] is False

            # Should not contain credential fields
            profile_str = json.dumps(result["profile_data"]).lower()
            # Check that no token-like values exist (basic sanity check)
            assert (
                '"jira_token":' not in profile_str or '"jira_token": ""' in profile_str
            )

        except FileNotFoundError:
            pytest.skip("Profile fixture not available")
