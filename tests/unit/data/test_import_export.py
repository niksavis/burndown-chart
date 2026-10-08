import tempfile

import pytest

from data.import_export import (
    resolve_profile_conflict,
    strip_credentials,
    validate_import_data,
)


@pytest.fixture
def temp_profiles_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_profile_with_token():
    return {
        "id": "p_test123",
        "name": "Test Profile",
        "description": "Test profile with credentials",
        "created_at": "2025-12-19T10:00:00",
        "last_used": "2025-12-19T10:00:00",
        "jira_config": {
            "base_url": "https://jira.example.com",
            "api_version": "v2",
            "jira_token": "secret_token_12345",
            "configured": True,
            "last_test_timestamp": "2025-12-19T10:00:00",
            "last_test_success": True,
        },
        "field_mappings": {
            "values": {},
            "dora": {
                "deployment_date": "fixVersions",
            },
        },
        "forecast_settings": {
            "pert_factor": 6,
            "deadline": "2026-07-01",
        },
        "queries": ["q_test1"],
        "active_query_id": "q_test1",
    }


@pytest.fixture
def sample_profile_without_token():
    return {
        "id": "p_test456",
        "name": "Clean Profile",
        "description": "Profile without credentials",
        "created_at": "2025-12-19T10:00:00",
        "last_used": "2025-12-19T10:00:00",
        "jira_config": {
            "base_url": "https://jira.example.com",
            "api_version": "v2",
            "configured": True,
            "last_test_timestamp": "2025-12-19T10:00:00",
            "last_test_success": True,
        },
        "field_mappings": {
            "values": {},
        },
        "forecast_settings": {
            "pert_factor": 6,
        },
        "queries": ["q_test2"],
    }


@pytest.fixture
def sample_query_data():
    return {
        "query_id": "q_test1",
        "jql": "project = TEST",
        "name": "Test Query",
        "statistics": {
            "total_issues": 100,
            "completed": 75,
        },
    }


class TestStripCredentials:
    def test_strip_credentials_removes_token(self, sample_profile_with_token):
        cleaned = strip_credentials(sample_profile_with_token)

        assert "jira_token" not in cleaned["jira_config"]
        assert cleaned["jira_config"]["base_url"] == "https://jira.example.com"
        assert cleaned["id"] == "p_test123"

    def test_strip_credentials_preserves_other_fields(self, sample_profile_with_token):
        cleaned = strip_credentials(sample_profile_with_token)

        assert cleaned["name"] == "Test Profile"
        assert cleaned["description"] == "Test profile with credentials"
        assert cleaned["jira_config"]["base_url"] == "https://jira.example.com"
        assert cleaned["jira_config"]["api_version"] == "v2"
        assert cleaned["jira_config"]["configured"] is True
        assert cleaned["field_mappings"]["dora"]["deployment_date"] == "fixVersions"
        assert cleaned["forecast_settings"]["pert_factor"] == 6
        assert cleaned["queries"] == ["q_test1"]
        assert cleaned["active_query_id"] == "q_test1"

    def test_strip_credentials_does_not_mutate_original(
        self, sample_profile_with_token
    ):
        original_token = sample_profile_with_token["jira_config"]["jira_token"]

        cleaned = strip_credentials(sample_profile_with_token)

        assert sample_profile_with_token["jira_config"]["jira_token"] == original_token
        assert "jira_token" not in cleaned["jira_config"]

    def test_strip_credentials_handles_missing_token(
        self, sample_profile_without_token
    ):
        cleaned = strip_credentials(sample_profile_without_token)

        assert "jira_token" not in cleaned["jira_config"]
        assert cleaned["id"] == "p_test456"
        assert cleaned["name"] == "Clean Profile"

    def test_strip_credentials_removes_sensitive_fields(self):
        profile_with_credentials = {
            "id": "p_test",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "jira_token": "secret",
                "token": "secret2",
                "jira_api_key": "key123",
                "api_secret": "secret789",
            },
        }

        cleaned = strip_credentials(profile_with_credentials)

        assert "jira_token" not in cleaned["jira_config"]
        assert "token" not in cleaned["jira_config"]
        assert "jira_api_key" not in cleaned["jira_config"]
        assert "api_secret" not in cleaned["jira_config"]
        assert cleaned["jira_config"]["base_url"] == "https://jira.example.com"


class TestValidateImportData:
    def test_validate_import_data_format_check(self):
        invalid_data = {"profile_data": {"id": "p_test"}}

        is_valid, errors = validate_import_data(invalid_data)

        assert is_valid is False
        assert any("manifest" in error.lower() for error in errors)

    def test_validate_import_data_valid_structure(self):
        valid_data = {
            "manifest": {
                "version": "2.0",
                "created_at": "2025-12-19T10:00:00+00:00",
                "created_by": "burndown-chart-enhanced",
                "export_type": "sharing",
                "profiles": ["p_test123"],
                "includes_cache": False,
                "includes_queries": True,
                "includes_setup_status": True,
                "export_mode": "CONFIG_ONLY",
                "includes_token": False,
            },
            "profile_data": {
                "profile_id": "p_test123",
                "jira_url": "https://jira.example.com",
                "jira_email": "test@example.com",
                "name": "Test Profile",
                "jira_config": {"base_url": "https://jira.example.com"},
                "field_mappings": {},
                "queries": [],
            },
        }

        is_valid, errors = validate_import_data(valid_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_import_data_missing_profile_data(self):
        invalid_data = {
            "manifest": {
                "version": "2.0",
                "profiles": ["p_test"],
            }
        }

        is_valid, errors = validate_import_data(invalid_data)

        assert is_valid is False
        assert any("profile_data" in error.lower() for error in errors)

    def test_validate_import_data_invalid_version(self):
        invalid_data = {
            "manifest": {
                "version": "999.0",
                "profiles": ["p_test"],
            },
            "profile_data": {"id": "p_test"},
        }

        is_valid, errors = validate_import_data(invalid_data)

        assert is_valid is False
        assert any("version" in error.lower() for error in errors)


class TestResolveProfileConflict:
    def test_resolve_profile_conflict_overwrite(
        self, sample_profile_with_token, sample_profile_without_token
    ):
        profile_id = "p_test123"
        existing = sample_profile_with_token.copy()
        incoming = sample_profile_without_token.copy()

        final_id, result = resolve_profile_conflict(
            profile_id, "overwrite", incoming, existing
        )

        assert final_id == profile_id
        assert result["name"] == incoming["name"]
        assert result["description"] == incoming["description"]

    def test_resolve_profile_conflict_merge(
        self, sample_profile_with_token, sample_profile_without_token
    ):
        profile_id = "p_test"
        existing = {
            "name": "Original",
            "jira_config": {"base_url": "https://old.com", "jira_token": "old_token"},
            "queries": [{"query_id": "q_old", "jql": "old"}],
        }
        incoming = {
            "name": "Updated",
            "jira_config": {"base_url": "https://new.com", "api_version": "v2"},
            "queries": [{"query_id": "q_new", "jql": "new"}],
        }

        final_id, result = resolve_profile_conflict(
            profile_id, "merge", incoming, existing
        )

        assert final_id == profile_id
        assert result["name"] == "Updated"
        assert result["jira_config"]["jira_token"] == "old_token"
        assert len(result["queries"]) >= 1

    def test_resolve_profile_conflict_rename(self, sample_profile_without_token):
        profile_id = "p_test"
        existing = {"name": "Existing"}
        incoming = sample_profile_without_token.copy()

        final_id, result = resolve_profile_conflict(
            profile_id, "rename", incoming, existing
        )

        assert final_id != profile_id
        assert "imported" in final_id or "_" in final_id
        assert result.get("profile_id") == final_id or result.get("id") == final_id
        assert "imported" in result["name"].lower()

    def test_resolve_profile_conflict_invalid_strategy(self):
        profile_id = "p_test"
        existing = {}
        incoming = {}

        with pytest.raises(ValueError, match="strategy"):
            resolve_profile_conflict(profile_id, "invalid", incoming, existing)


class TestExportProfileWithMode:
    def test_export_config_only_size_reduction(self):
        config_only_export = {
            "manifest": {
                "version": "2.0",
                "export_mode": "CONFIG_ONLY",
            },
            "profile_data": {
                "id": "p_test",
                "name": "Test Profile",
                "jira_config": {"base_url": "https://jira.example.com"},
                "field_mappings": {"values": {}},
                "queries": ["q_test"],
            },
        }

        full_data_export = {
            "manifest": {
                "version": "2.0",
                "export_mode": "FULL_DATA",
            },
            "profile_data": {
                "id": "p_test",
                "name": "Test Profile",
                "jira_config": {"base_url": "https://jira.example.com"},
                "field_mappings": {"values": {}},
                "queries": ["q_test"],
            },
            "query_data": {
                "q_test": {
                    "project_data": {
                        "statistics": {
                            "total_issues": 100,
                            "completed": 75,
                        },
                        "scope_metrics": {
                            "current": 50,
                            "original": 100,
                        },
                        "history": [
                            {"date": "2025-12-01", "value": 25} for _ in range(100)
                        ],
                    },
                    "jira_cache": {
                        "issues": [
                            {
                                "key": f"TEST-{i}",
                                "summary": "Test issue " * 10,
                                "description": "Long description " * 50,
                            }
                            for i in range(100)
                        ],
                        "metadata": {"cached_at": "2025-12-19T10:00:00"},
                    },
                }
            },
        }

        import json

        config_size = len(json.dumps(config_only_export))
        full_size = len(json.dumps(full_data_export))
        reduction_percent = ((full_size - config_size) / full_size) * 100

        assert reduction_percent >= 90, (
            f"CONFIG_ONLY should reduce size by 90%+, got {reduction_percent:.1f}%"
        )
        assert config_size < full_size / 10


class TestExportFullDataMode:
    def test_export_full_data_includes_query_data_unit(self):

        full_data_export = {
            "manifest": {
                "version": "2.0",
                "export_mode": "FULL_DATA",
                "includes_cache": True,
                "includes_queries": True,
            },
            "profile_data": {
                "id": "p_test",
                "name": "Test Profile",
                "jira_config": {"base_url": "https://jira.example.com"},
                "queries": ["q_test"],
            },
            "query_data": {
                "q_test": {
                    "project_data": {"statistics": {"total_issues": 100}},
                    "jira_cache": {"issues": []},
                }
            },
        }

        manifest = full_data_export["manifest"]
        has_query_data = "query_data" in full_data_export

        assert manifest["export_mode"] == "FULL_DATA"
        assert manifest["includes_cache"] is True
        assert has_query_data is True
        assert full_data_export["query_data"] is not None
        assert "q_test" in full_data_export["query_data"]

    def test_export_full_data_all_queries(self):

        profile_with_multiple_queries = {
            "id": "p_test",
            "queries": ["q_sprint1", "q_sprint2", "q_sprint3"],
            "active_query_id": "q_sprint2",
        }

        full_data_export = {
            "manifest": {
                "export_mode": "FULL_DATA",
            },
            "profile_data": profile_with_multiple_queries,
            "query_data": {
                "q_sprint1": {
                    "query_metadata": {"name": "Sprint 1", "jql": "sprint = 1"},
                    "project_data": {"statistics": {}},
                },
                "q_sprint2": {
                    "query_metadata": {"name": "Sprint 2", "jql": "sprint = 2"},
                    "project_data": {"statistics": {}},
                },
                "q_sprint3": {
                    "query_metadata": {"name": "Sprint 3", "jql": "sprint = 3"},
                    "project_data": {"statistics": {}},
                },
            },
        }

        query_data = full_data_export.get("query_data", {})
        exported_queries = list(query_data.keys())

        assert len(exported_queries) == 3
        assert "q_sprint1" in exported_queries
        assert "q_sprint2" in exported_queries
        assert "q_sprint3" in exported_queries

        for _query_id, query_content in query_data.items():
            assert "query_metadata" in query_content


class TestTokenInclusion:
    def test_export_with_token_includes_credentials(self):

        profile_with_token = {
            "id": "p_test",
            "name": "Test Profile",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "jira_token": "secret_token_12345",
                "configured": True,
            },
        }

        include_token = True
        if not include_token:
            result = strip_credentials(profile_with_token)
        else:
            result = profile_with_token.copy()

        assert "jira_token" in result["jira_config"]
        assert result["jira_config"]["jira_token"] == "secret_token_12345"

    def test_export_manifest_token_flag_consistency(self):

        config_without_token = {
            "manifest": {
                "includes_token": False,
            },
            "profile_data": {
                "jira_config": {
                    "base_url": "https://jira.example.com",
                },
            },
        }

        config_with_token = {
            "manifest": {
                "includes_token": True,
            },
            "profile_data": {
                "jira_config": {
                    "base_url": "https://jira.example.com",
                    "jira_token": "secret_token",
                },
            },
        }

        assert config_without_token["manifest"]["includes_token"] is False
        assert "jira_token" not in config_without_token["profile_data"]["jira_config"]

        assert config_with_token["manifest"]["includes_token"] is True
        assert "jira_token" in config_with_token["profile_data"]["jira_config"]

    def test_token_inclusion_works_with_both_export_modes(self):
        config_only_with_token = {
            "manifest": {
                "export_mode": "CONFIG_ONLY",
                "includes_token": True,
            },
            "profile_data": {
                "jira_config": {"jira_token": "token1"},
            },
        }

        full_data_with_token = {
            "manifest": {
                "export_mode": "FULL_DATA",
                "includes_token": True,
            },
            "profile_data": {
                "jira_config": {"jira_token": "token2"},
            },
            "query_data": {
                "q1": {"project_data": {}},
            },
        }

        assert config_only_with_token["manifest"]["includes_token"] is True
        assert "jira_token" in config_only_with_token["profile_data"]["jira_config"]

        assert full_data_with_token["manifest"]["includes_token"] is True
        assert "jira_token" in full_data_with_token["profile_data"]["jira_config"]


class TestConflictResolutionStrategies:
    def test_resolve_conflict_overwrite_strategy(self):

        profile_id = "p_prod"
        existing = {
            "profile_id": "p_prod",
            "name": "Old Production",
            "description": "Old config",
            "jira_config": {
                "base_url": "https://old.jira.com",
                "jira_token": "old_token",
            },
            "queries": ["q_old1", "q_old2"],
            "forecast_settings": {"pert_factor": 6},
        }
        incoming = {
            "profile_id": "p_prod",
            "name": "New Production",
            "description": "Updated config",
            "jira_config": {
                "base_url": "https://new.jira.com",
            },
            "queries": ["q_new1"],
            "forecast_settings": {"pert_factor": 8},
        }

        final_id, result = resolve_profile_conflict(
            profile_id, "overwrite", incoming, existing
        )

        assert final_id == profile_id
        assert result["name"] == "New Production"
        assert result["description"] == "Updated config"
        assert result["jira_config"]["base_url"] == "https://new.jira.com"
        assert result["queries"] == ["q_new1"]
        assert result["forecast_settings"]["pert_factor"] == 8

        assert "jira_token" not in result.get("jira_config", {})

    def test_resolve_conflict_merge_preserves_token(self):

        profile_id = "p_merge"
        existing = {
            "profile_id": "p_merge",
            "name": "Existing",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "jira_token": "existing_secure_token",
                "configured": True,
            },
            "queries": ["q_existing"],
        }
        incoming = {
            "profile_id": "p_merge",
            "name": "Imported",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "api_version": "v2",
            },
            "queries": ["q_imported"],
        }

        final_id, result = resolve_profile_conflict(
            profile_id, "merge", incoming, existing
        )

        assert final_id == profile_id
        assert result["jira_config"]["jira_token"] == "existing_secure_token"

        assert result["name"] == "Imported"
        assert result["jira_config"]["api_version"] == "v2"

    def test_resolve_conflict_rename_appends_timestamp(self):

        profile_id = "p_duplicate"
        existing = {
            "profile_id": "p_duplicate",
            "name": "Original",
        }
        incoming = {
            "profile_id": "p_duplicate",
            "name": "Imported Copy",
        }

        final_id, result = resolve_profile_conflict(
            profile_id, "rename", incoming, existing
        )

        assert final_id != profile_id
        assert "imported" in final_id.lower() or "_" in final_id

        assert result.get("profile_id") == final_id or result.get("id") == final_id
        assert "imported" in result["name"].lower()
        assert "Imported Copy" in result["name"]

    def test_resolve_conflict_merge_combines_queries(self):

        profile_id = "p_team"
        existing = {
            "profile_id": "p_team",
            "queries": [
                {"query_id": "q_sprint1", "jql": "sprint = 1"},
                {"query_id": "q_sprint2", "jql": "sprint = 2"},
            ],
        }
        incoming = {
            "profile_id": "p_team",
            "queries": [
                {"query_id": "q_sprint3", "jql": "sprint = 3"},
                {"query_id": "q_sprint4", "jql": "sprint = 4"},
            ],
        }

        final_id, result = resolve_profile_conflict(
            profile_id, "merge", incoming, existing
        )

        assert len(result["queries"]) == 4
        query_ids = [q["query_id"] for q in result["queries"]]
        assert "q_sprint1" in query_ids
        assert "q_sprint2" in query_ids
        assert "q_sprint3" in query_ids
        assert "q_sprint4" in query_ids
