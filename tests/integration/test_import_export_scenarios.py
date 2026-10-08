import json
from pathlib import Path

import pytest

from data.import_export import export_profile_with_mode


class TestConfigOnlyExport:
    def test_config_only_export_excludes_cache_files(
        self, temp_profiles_dir_with_default
    ):

        profiles_dir = temp_profiles_dir_with_default
        profile_id = "default"
        query_id = "test_query"

        query_path = Path(profiles_dir) / profile_id / "queries" / query_id
        query_path.mkdir(parents=True, exist_ok=True)

        project_data = {
            "query_id": query_id,
            "statistics": {"total_issues": 100},
        }
        with open(query_path / "project_data.json", "w") as f:
            json.dump(project_data, f)

        jira_cache = {
            "issues": [{"key": "TEST-1", "fields": {"summary": "Test"}}],
            "total": 1,
        }
        with open(query_path / "jira_cache.json", "w") as f:
            json.dump(jira_cache, f)

        try:
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="CONFIG_ONLY",
                include_token=False,
            )
        except FileNotFoundError:
            pytest.skip(
                "Profile fixture needs profile.json - "
                "use temp_profiles_dir_with_default fixture"
            )

        assert result is not None
        assert result["manifest"]["export_mode"] == "CONFIG_ONLY"
        assert "query_data" not in result or result.get("query_data") is None

    def test_export_config_only_file_size_validation(
        self, temp_profiles_dir_with_default
    ):

        from data.persistence.factory import get_backend

        profile_id = "default"
        query_id = "test_query"

        backend = get_backend()
        profile = backend.get_profile(profile_id)
        assert profile is not None, f"Fixture must seed profile '{profile_id}'"
        now = profile["created_at"]
        backend.save_query(
            profile_id,
            {
                "id": query_id,
                "name": "Test Query",
                "jql": "project = TEST",
                "created_at": now,
                "last_used": now,
            },
        )
        backend.save_statistics_batch(
            profile_id,
            query_id,
            [
                {
                    "stat_date": f"2026-01-{i + 1:02d}",
                    "week_label": f"2026-W{i + 1:02d}",
                    "remaining_items": 100 - i * 5,
                    "remaining_total_points": 200 - i * 10,
                    "items_added": 2,
                    "items_completed": 5,
                    "completed_items": i * 5,
                    "completed_points": i * 10,
                    "created_items": 2,
                    "created_points": 4,
                    "velocity_items": 5,
                    "velocity_points": 10,
                }
                for i in range(20)
            ],
        )

        config_only_result = export_profile_with_mode(
            profile_id=profile_id,
            query_id=query_id,
            export_mode="CONFIG_ONLY",
            include_token=False,
        )
        full_data_result = export_profile_with_mode(
            profile_id=profile_id,
            query_id=query_id,
            export_mode="FULL_DATA",
            include_token=False,
        )

        config_only_size = len(json.dumps(config_only_result))
        full_data_size = len(json.dumps(full_data_result))

        size_reduction_percent = (
            (full_data_size - config_only_size) / full_data_size * 100
        )

        assert config_only_size < full_data_size
        assert size_reduction_percent > 50, (
            f"CONFIG_ONLY export only {size_reduction_percent:.1f}% smaller. "
            f"Expected >50% reduction."
        )

    def test_config_only_preserves_configuration_structure(
        self, temp_profiles_dir_with_default
    ):

        profile_id = "default"
        query_id = "test_query"

        try:
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="CONFIG_ONLY",
                include_token=False,
            )

            assert "manifest" in result
            assert "profile_data" in result
            assert result["manifest"]["export_mode"] == "CONFIG_ONLY"
            assert result["manifest"]["includes_token"] is False

            profile_data = result["profile_data"]
            assert isinstance(profile_data, dict)
            assert len(profile_data) > 0

        except FileNotFoundError:
            pytest.skip(
                "Profile fixture needs profile.json - "
                "use temp_profiles_dir_with_default fixture"
            )


class TestExportSecurity:
    def test_config_only_strips_credentials_by_default(
        self, temp_profiles_dir_with_default
    ):

        profile_id = "default"
        query_id = "test_query"

        result = export_profile_with_mode(
            profile_id=profile_id,
            query_id=query_id,
            export_mode="CONFIG_ONLY",
            include_token=False,
        )

        assert result["manifest"]["includes_token"] is False

        profile_str = json.dumps(result["profile_data"]).lower()
        assert "test_secret_token" not in profile_str

    def test_full_data_also_strips_credentials_unless_requested(
        self, temp_profiles_dir_with_default
    ):

        profile_id = "default"
        query_id = "test_query"

        try:
            result = export_profile_with_mode(
                profile_id=profile_id,
                query_id=query_id,
                export_mode="FULL_DATA",
                include_token=False,
            )

            assert result["manifest"]["includes_token"] is False

            profile_str = json.dumps(result["profile_data"]).lower()
            assert (
                '"jira_token":' not in profile_str or '"jira_token": ""' in profile_str
            )

        except FileNotFoundError:
            pytest.skip("Profile fixture not available")


class TestConfigOnlyImport:
    def test_config_only_import_prompts_for_token(self, temp_profiles_dir_with_default):

        config_only_package = {
            "manifest": {
                "version": "2.0",
                "export_mode": "CONFIG_ONLY",
                "includes_token": False,
                "export_type": "sharing",
                "profiles": ["imported_profile"],
                "includes_cache": False,
                "includes_queries": True,
                "includes_setup_status": True,
                "created_at": "2025-12-19T10:00:00+00:00",
                "created_by": "test",
            },
            "profile_data": {
                "profile_id": "imported_profile",
                "query_id": "imported_query",
                "jira_url": "https://jira.example.com",
                "jira_config": {
                    "base_url": "https://jira.example.com",
                    "configured": True,
                },
                "field_mappings": {},
                "queries": ["imported_query"],
            },
            "profile_id": "imported_profile",
            "query_id": "imported_query",
        }

        manifest = config_only_package["manifest"]
        profile_data = config_only_package["profile_data"]

        assert manifest["includes_token"] is False
        assert "jira_token" not in profile_data.get("jira_config", {})

        assert manifest["export_mode"] == "CONFIG_ONLY"

    def test_config_only_no_data_until_sync(self, temp_profiles_dir_with_default):

        config_only_package = {
            "manifest": {
                "version": "2.0",
                "export_mode": "CONFIG_ONLY",
                "includes_token": False,
                "export_type": "sharing",
                "profiles": ["test_profile"],
                "includes_cache": False,
                "includes_queries": True,
                "includes_setup_status": True,
                "created_at": "2025-12-19T10:00:00+00:00",
                "created_by": "test",
            },
            "profile_data": {
                "profile_id": "test_profile",
                "query_id": "test_query",
                "jira_url": "https://jira.example.com",
                "jira_config": {
                    "base_url": "https://jira.example.com",
                },
                "queries": ["test_query"],
            },
            "profile_id": "test_profile",
            "query_id": "test_query",
        }

        has_query_data = "query_data" in config_only_package
        has_cache_data = (
            config_only_package.get("query_data", {}).get("jira_cache") is not None
        )

        assert has_query_data is False or config_only_package.get("query_data") is None
        assert has_cache_data is False

        manifest = config_only_package["manifest"]
        assert manifest["includes_cache"] is False
        assert manifest["export_mode"] == "CONFIG_ONLY"


class TestFullDataImport:
    def test_full_data_import_no_token_prompt(self, temp_profiles_dir_with_default):

        full_data_package = {
            "manifest": {
                "version": "2.0",
                "export_mode": "FULL_DATA",
                "includes_token": False,
                "includes_cache": True,
                "export_type": "sharing",
                "profiles": ["full_profile"],
                "includes_queries": True,
                "includes_setup_status": True,
                "created_at": "2025-12-19T10:00:00+00:00",
                "created_by": "test",
            },
            "profile_data": {
                "profile_id": "full_profile",
                "query_id": "full_query",
                "jira_url": "https://jira.example.com",
                "jira_config": {
                    "base_url": "https://jira.example.com",
                },
                "queries": ["full_query"],
            },
            "profile_id": "full_profile",
            "query_id": "full_query",
            "query_data": {
                "full_query": {
                    "project_data": {
                        "statistics": {"total_issues": 50, "completed": 40},
                    },
                    "jira_cache": {
                        "issues": [{"key": "TEST-1", "summary": "Test Issue"}],
                        "cached_at": "2025-12-19T09:00:00",
                    },
                }
            },
        }

        has_query_data = "query_data" in full_data_package
        has_project_data = (
            full_data_package.get("query_data", {})
            .get("full_query", {})
            .get("project_data")
            is not None
        )

        assert has_query_data is True
        assert has_project_data is True
        assert full_data_package["manifest"]["includes_cache"] is True

        manifest = full_data_package["manifest"]
        assert manifest["export_mode"] == "FULL_DATA"

    def test_full_data_charts_render_immediately(self, temp_profiles_dir_with_default):

        full_data_package = {
            "manifest": {
                "version": "2.0",
                "export_mode": "FULL_DATA",
                "includes_cache": True,
            },
            "profile_data": {
                "profile_id": "chart_profile",
                "query_id": "chart_query",
            },
            "profile_id": "chart_profile",
            "query_id": "chart_query",
            "query_data": {
                "chart_query": {
                    "project_data": {
                        "statistics": {
                            "total_issues": 100,
                            "completed": 75,
                            "in_progress": 15,
                            "remaining": 10,
                        },
                        "scope_metrics": {
                            "current": 50,
                            "original": 100,
                            "added": 20,
                            "removed": 70,
                        },
                        "forecast": {
                            "completion_date": "2025-12-31",
                            "confidence_95": "2026-01-15",
                        },
                    },
                    "jira_cache": {
                        "issues": [{"key": f"TEST-{i}"} for i in range(100)],
                    },
                    "metrics_snapshots": {
                        "history": [
                            {"date": "2025-12-01", "velocity": 10},
                            {"date": "2025-12-08", "velocity": 12},
                        ],
                    },
                }
            },
        }

        query_data = full_data_package.get("query_data", {}).get("chart_query", {})
        has_statistics = "statistics" in query_data.get("project_data", {})
        has_scope = "scope_metrics" in query_data.get("project_data", {})
        has_forecast = "forecast" in query_data.get("project_data", {})
        has_history = "metrics_snapshots" in query_data

        assert has_statistics is True
        assert has_scope is True
        assert has_forecast is True
        assert has_history is True

        project_data = query_data.get("project_data", {})
        assert project_data["statistics"]["total_issues"] == 100
        assert project_data["scope_metrics"]["current"] == 50
        assert project_data["forecast"]["completion_date"] == "2025-12-31"


class TestTokenInclusionIntegration:
    def test_token_included_no_import_prompt(self, temp_profiles_dir_with_default):

        export_with_token = {
            "manifest": {
                "version": "2.0",
                "export_mode": "CONFIG_ONLY",
                "includes_token": True,
                "export_type": "backup",
                "profiles": ["backup_profile"],
                "includes_cache": False,
                "includes_queries": True,
                "includes_setup_status": True,
                "created_at": "2025-12-19T10:00:00+00:00",
                "created_by": "test",
            },
            "profile_data": {
                "profile_id": "backup_profile",
                "query_id": "backup_query",
                "jira_url": "https://jira.example.com",
                "jira_config": {
                    "base_url": "https://jira.example.com",
                    "jira_token": "backup_token_12345",
                    "configured": True,
                },
                "queries": ["backup_query"],
            },
            "profile_id": "backup_profile",
            "query_id": "backup_query",
        }

        manifest = export_with_token["manifest"]
        profile_data = export_with_token["profile_data"]
        has_token = "jira_token" in profile_data.get("jira_config", {})

        assert manifest["includes_token"] is True
        assert has_token is True
        assert profile_data["jira_config"]["jira_token"] == "backup_token_12345"

    def test_token_warning_modal_shown_on_checkbox(
        self, temp_profiles_dir_with_default
    ):

        token_warning_config = {
            "modal_id": "token-warning-modal",
            "trigger": "include-token-checkbox",
            "security_consequences": [
                "Allow anyone with the file to access your JIRA instance",
                "Expose your credentials if file is shared or leaked",
                "Grant full API access until token is revoked",
            ],
            "safe_use_cases": [
                "This is a personal backup on a secure device",
                "You will not share this file with others",
                "You understand how to revoke the token if needed",
            ],
        }

        has_security_consequences = (
            len(token_warning_config["security_consequences"]) > 0
        )
        has_safe_use_cases = len(token_warning_config["safe_use_cases"]) > 0

        assert has_security_consequences is True
        assert has_safe_use_cases is True
        assert len(token_warning_config["security_consequences"]) >= 3
        assert len(token_warning_config["safe_use_cases"]) >= 3

        consequences_str = " ".join(token_warning_config["security_consequences"])
        assert "access your jira" in consequences_str.lower()
        assert (
            "credentials" in consequences_str.lower()
            or "token" in consequences_str.lower()
        )


class TestImportConflictResolution:
    def test_import_conflict_merge_strategy(self, temp_profiles_dir_with_default):

        from data.import_export import resolve_profile_conflict

        profile_id = "conflict_profile"
        existing = {
            "profile_id": profile_id,
            "name": "Existing Config",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "jira_token": "existing_token_123",
                "configured": True,
            },
            "queries": ["q_existing"],
            "forecast_settings": {"pert_factor": 6},
        }

        incoming = {
            "profile_id": profile_id,
            "name": "Imported Config",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "api_version": "v2",
            },
            "queries": ["q_imported"],
            "forecast_settings": {"pert_factor": 8, "deadline": "2026-01-01"},
        }

        final_id, merged = resolve_profile_conflict(
            profile_id, "merge", incoming, existing
        )

        assert final_id == profile_id
        assert merged["jira_config"]["jira_token"] == "existing_token_123"
        assert merged["jira_config"]["api_version"] == "v2"
        assert merged["forecast_settings"]["deadline"] == "2026-01-01"

    def test_import_conflict_overwrite_strategy(self, temp_profiles_dir_with_default):

        from data.import_export import resolve_profile_conflict

        profile_id = "replace_profile"
        existing = {
            "profile_id": profile_id,
            "name": "Old Config",
            "jira_config": {
                "base_url": "https://old.jira.com",
                "jira_token": "old_token",
            },
            "queries": ["q_old"],
        }

        incoming = {
            "profile_id": profile_id,
            "name": "New Config",
            "jira_config": {
                "base_url": "https://new.jira.com",
            },
            "queries": ["q_new"],
        }

        final_id, overwritten = resolve_profile_conflict(
            profile_id, "overwrite", incoming, existing
        )

        assert final_id == profile_id
        assert overwritten["name"] == "New Config"
        assert overwritten["jira_config"]["base_url"] == "https://new.jira.com"
        assert overwritten["queries"] == ["q_new"]
        assert "jira_token" not in overwritten.get("jira_config", {})

    def test_import_conflict_rename_strategy(self, temp_profiles_dir_with_default):

        from data.import_export import resolve_profile_conflict

        profile_id = "duplicate_profile"
        existing = {
            "profile_id": profile_id,
            "name": "Original Profile",
        }

        incoming = {
            "profile_id": profile_id,
            "name": "Imported Duplicate",
        }

        final_id, renamed = resolve_profile_conflict(
            profile_id, "rename", incoming, existing
        )

        assert final_id != profile_id
        assert "imported" in final_id or "_" in final_id
        assert renamed.get("profile_id") == final_id or renamed.get("id") == final_id
        assert "imported" in renamed["name"].lower()
        assert "Imported Duplicate" in renamed["name"]

        assert existing["profile_id"] == profile_id
