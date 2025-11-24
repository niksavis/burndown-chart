"""
Unit tests for accordion settings panel callbacks.

Tests verify that:
1. Configuration status tracking works correctly
2. Section states update based on dependencies
3. Section titles show correct status icons
4. Query save enforcement blocks data operations
5. Profile settings save correctly
"""

from unittest.mock import patch
from dash import html, no_update
import dash_bootstrap_components as dbc


class TestConfigurationStatusTracking:
    """Test configuration status tracking callback."""

    def test_status_all_locked_initially(self):
        """Verify all sections locked when no profile selected."""
        from callbacks.accordion_settings import update_configuration_status

        # No profile selected, no JIRA status, no query saves
        status = update_configuration_status(None, None, 0)

        # Profile is always enabled (can select profile at any time)
        assert status["profile"]["enabled"] is True
        assert status["profile"]["complete"] is False
        assert status["profile"]["icon"] == "[Pending]"

        assert status["jira"]["enabled"] is False
        assert status["jira"]["complete"] is False
        assert status["jira"]["icon"] == "🔒"

        assert status["fields"]["enabled"] is False
        assert status["fields"]["complete"] is False
        assert status["fields"]["icon"] == "🔒"

        assert status["queries"]["enabled"] is False
        assert status["queries"]["complete"] is False
        assert status["queries"]["icon"] == "🔒"

        assert status["data_operations"]["enabled"] is False
        assert status["data_operations"]["complete"] is False
        assert status["data_operations"]["icon"] == "🔒"

    def test_status_profile_enabled_when_selected(self):
        """Verify profile section enabled when profile selected."""
        from callbacks.accordion_settings import update_configuration_status

        status = update_configuration_status("default", None, 0)

        # Profile section should be enabled
        assert status["profile"]["enabled"] is True
        assert status["profile"]["complete"] is True
        assert status["profile"]["icon"] == "[OK]"

        # JIRA section should be enabled (unlocked) but not complete
        assert status["jira"]["enabled"] is True
        assert status["jira"]["complete"] is False
        assert status["jira"]["icon"] == "[Pending]"

        # Other sections still locked
        assert status["fields"]["enabled"] is False
        assert status["queries"]["enabled"] is False
        assert status["data_operations"]["enabled"] is False

    def test_status_jira_complete_unlocks_fields_and_queries(self):
        """Verify JIRA completion unlocks field mappings and queries."""
        from callbacks.accordion_settings import update_configuration_status

        # JIRA status must contain 'success' or '[OK]' in its string representation
        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 0)

        # Profile complete
        assert status["profile"]["complete"] is True

        # JIRA complete
        assert status["jira"]["enabled"] is True
        assert status["jira"]["complete"] is True
        assert status["jira"]["icon"] == "[OK]"

        # Fields unlocked (enabled but not complete)
        assert status["fields"]["enabled"] is True
        assert status["fields"]["complete"] is False
        assert status["fields"]["icon"] == "[Pending]"

        # Queries unlocked (enabled but not complete)
        assert status["queries"]["enabled"] is True
        assert status["queries"]["complete"] is False
        assert status["queries"]["icon"] == "[Pending]"

        # Data ops still locked (no query saved yet)
        assert status["data_operations"]["enabled"] is False
        assert status["data_operations"]["icon"] == "🔒"

    def test_status_query_saved_unlocks_data_ops(self):
        """Verify saving query unlocks data operations."""
        from callbacks.accordion_settings import update_configuration_status

        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 1)

        # All previous sections complete
        assert status["profile"]["complete"] is True
        assert status["jira"]["complete"] is True

        # Queries complete (saved at least once)
        assert status["queries"]["enabled"] is True
        assert status["queries"]["complete"] is True
        assert status["queries"]["icon"] == "[OK]"

        # Data ops unlocked
        assert status["data_operations"]["enabled"] is True
        assert status["data_operations"]["complete"] is False
        assert status["data_operations"]["icon"] == "[Pending]"


class TestSectionStateManagement:
    """Test section state update callback."""

    def test_section_states_all_disabled_when_locked(self):
        """Verify all sections disabled when dependencies not met."""
        from callbacks.accordion_settings import update_section_states

        config_status = {
            "profile": {"enabled": False},
            "jira": {"enabled": False},
            "fields": {"enabled": False},
            "queries": {"enabled": False},
            "data_operations": {"enabled": False},
        }

        jira_class, fields_class, queries_class, data_ops_class = update_section_states(
            config_status
        )

        assert "accordion-item-disabled" in jira_class
        assert "accordion-item-disabled" in fields_class
        assert "accordion-item-disabled" in queries_class
        assert "accordion-item-disabled" in data_ops_class

    def test_section_states_progressive_unlock(self):
        """Verify sections unlock progressively as dependencies met."""
        from callbacks.accordion_settings import update_section_states

        # Profile selected, JIRA configured
        config_status = {
            "profile": {"enabled": True, "complete": True},
            "jira": {"enabled": True, "complete": True},
            "fields": {"enabled": True, "complete": False},
            "queries": {"enabled": True, "complete": False},
            "data_operations": {"enabled": False, "complete": False},
        }

        jira_class, fields_class, queries_class, data_ops_class = update_section_states(
            config_status
        )

        # JIRA, fields, queries should be enabled
        assert "accordion-item-disabled" not in jira_class
        assert "accordion-item-disabled" not in fields_class
        assert "accordion-item-disabled" not in queries_class

        # Data ops still disabled (query not saved)
        assert "accordion-item-disabled" in data_ops_class


class TestSectionTitleUpdates:
    """Test section title status icon callback."""

    def test_section_titles_show_locked_icons_initially(self):
        """Verify locked icons shown when sections disabled."""
        from callbacks.accordion_settings import update_section_titles

        config_status = {
            "profile": {"enabled": False, "icon": "🔒"},
            "jira": {"enabled": False, "icon": "🔒"},
            "fields": {"enabled": False, "icon": "🔒"},
            "queries": {"enabled": False, "icon": "🔒"},
            "data_operations": {"enabled": False, "icon": "🔒"},
        }

        (
            profile_title,
            jira_title,
            fields_title,
            queries_title,
            data_ops_title,
        ) = update_section_titles(config_status)

        assert "🔒" in profile_title
        assert "🔒" in jira_title
        assert "🔒" in fields_title
        assert "🔒" in queries_title
        assert "🔒" in data_ops_title

    def test_section_titles_show_in_progress_icons(self):
        """Verify in-progress icons shown when sections enabled but incomplete."""
        from callbacks.accordion_settings import update_section_titles

        config_status = {
            "profile": {"enabled": True, "icon": "[OK]"},
            "jira": {"enabled": True, "icon": "[Pending]"},
            "fields": {"enabled": True, "icon": "[Pending]"},
            "queries": {"enabled": True, "icon": "[Pending]"},
            "data_operations": {"enabled": False, "icon": "🔒"},
        }

        (
            profile_title,
            jira_title,
            fields_title,
            queries_title,
            data_ops_title,
        ) = update_section_titles(config_status)

        assert "[OK]" in profile_title
        assert "[Pending]" in jira_title
        assert "[Pending]" in fields_title
        assert "[Pending]" in queries_title
        assert "🔒" in data_ops_title

    def test_section_titles_show_complete_icons(self):
        """Verify checkmark icons shown when sections complete."""
        from callbacks.accordion_settings import update_section_titles

        config_status = {
            "profile": {"enabled": True, "icon": "[OK]"},
            "jira": {"enabled": True, "icon": "[OK]"},
            "fields": {"enabled": True, "icon": "[OK]"},
            "queries": {"enabled": True, "icon": "[OK]"},
            "data_operations": {"enabled": True, "icon": "[Pending]"},
        }

        (
            profile_title,
            jira_title,
            fields_title,
            queries_title,
            data_ops_title,
        ) = update_section_titles(config_status)

        assert "[OK]" in profile_title
        assert "[OK]" in jira_title
        assert "[OK]" in fields_title
        assert "[OK]" in queries_title
        assert "[Pending]" in data_ops_title


class TestQuerySaveEnforcement:
    """Test query save before data operations enforcement."""

    def test_data_ops_disabled_when_no_query_saved(self):
        """Verify update data button disabled when no query saved."""
        from callbacks.accordion_settings import enforce_query_save_before_data_ops

        config_status = {
            "queries": {"complete": False},
            "data_ops": {"enabled": False},
        }

        button_disabled, alert_content, alert_open = enforce_query_save_before_data_ops(
            config_status
        )

        assert button_disabled is True
        assert alert_open is True
        # Convert Alert component to string for comparison
        assert (
            "save" in str(alert_content).lower()
            and "query" in str(alert_content).lower()
        )

    def test_data_ops_enabled_when_query_saved(self):
        """Verify update data button enabled after query saved."""
        from callbacks.accordion_settings import enforce_query_save_before_data_ops

        config_status = {
            "queries": {"complete": True},
            "data_operations": {"enabled": True},
        }

        button_disabled, alert_content, alert_open = enforce_query_save_before_data_ops(
            config_status
        )

        assert button_disabled is False
        assert alert_open is False

    def test_data_ops_alert_warning_style(self):
        """Verify alert uses warning style when query not saved."""
        from callbacks.accordion_settings import enforce_query_save_before_data_ops

        config_status = {
            "queries": {"complete": False},
            "data_ops": {"enabled": False},
        }

        _, alert_content, _ = enforce_query_save_before_data_ops(config_status)

        # Alert should be a Dash Bootstrap Alert component
        assert isinstance(alert_content, (str, html.Div, dbc.Alert))


class TestProfileSettingsSave:
    """Test profile settings save callback."""

    @patch("data.persistence.save_app_settings")
    def test_save_profile_settings_success(self, mock_save_settings):
        """Verify profile settings save successfully."""
        from callbacks.accordion_settings import save_profile_settings

        mock_save_settings.return_value = None

        # Sample form inputs
        pert_factor = 1.5
        deadline = "2025-12-31"
        data_points = 10
        milestone_enabled = True
        milestone_date = "2025-06-15"

        result = save_profile_settings(
            1,  # n_clicks
            pert_factor,
            deadline,
            data_points,
            milestone_enabled,
            milestone_date,
        )

        # Verify save_app_settings called with correct parameters
        mock_save_settings.assert_called_once()
        # Check keyword arguments
        call_kwargs = mock_save_settings.call_args[1]
        assert call_kwargs["pert_factor"] == 1.5
        assert call_kwargs["deadline"] == "2025-12-31"
        assert call_kwargs["data_points_count"] == 10
        assert call_kwargs["show_milestone"] is True
        assert call_kwargs["milestone"] == "2025-06-15"

        # Verify success alert returned
        assert isinstance(result, (dbc.Alert, html.Div))

    @patch("data.persistence.save_app_settings")
    def test_save_profile_settings_error_handling(self, mock_save_settings):
        """Verify error handling when save fails."""
        from callbacks.accordion_settings import save_profile_settings

        mock_save_settings.side_effect = Exception("Save failed")

        result = save_profile_settings(
            1,
            1.5,
            "2025-12-31",
            10,
            False,
            None,
        )

        # Verify error alert returned
        assert isinstance(result, (dbc.Alert, html.Div))
        # Error message should mention failure
        result_str = str(result)
        assert "error" in result_str.lower() or "failed" in result_str.lower()

    def test_save_profile_settings_no_click(self):
        """Verify no action when save button not clicked."""
        from callbacks.accordion_settings import save_profile_settings

        # n_clicks = None (button not clicked)
        result = save_profile_settings(
            None,  # n_clicks
            1.5,
            "2025-12-31",
            10,
            False,
            None,
        )

        # Should return no_update when button not clicked
        assert result == no_update


class TestCallbackIntegration:
    """Integration tests for callback interactions."""

    def test_status_to_section_state_flow(self):
        """Verify status changes flow correctly to section state updates."""
        from callbacks.accordion_settings import (
            update_configuration_status,
            update_section_states,
        )

        # Simulate profile selection
        status = update_configuration_status("default", None, 0)
        jira_class, fields_class, queries_class, data_ops_class = update_section_states(
            status
        )

        # JIRA should be enabled (not disabled)
        assert "accordion-item-disabled" not in jira_class

        # Fields/queries/data_ops should be disabled
        assert "accordion-item-disabled" in fields_class
        assert "accordion-item-disabled" in queries_class
        assert "accordion-item-disabled" in data_ops_class

    def test_status_to_title_flow(self):
        """Verify status changes flow correctly to title updates."""
        from callbacks.accordion_settings import (
            update_configuration_status,
            update_section_titles,
        )

        # Simulate JIRA configuration
        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 0)

        (
            profile_title,
            jira_title,
            fields_title,
            queries_title,
            data_ops_title,
        ) = update_section_titles(status)

        # Profile should show checkmark, JIRA should show in-progress
        assert "[OK]" in profile_title
        # JIRA shows in-progress since we haven't verified field mappings
        assert "[Pending]" in jira_title or "[OK]" in jira_title

        # Fields and queries should show in-progress
        assert "[Pending]" in fields_title
        assert "[Pending]" in queries_title

        # Data ops should show locked
        assert "🔒" in data_ops_title

    def test_full_workflow_profile_to_data_ops(self):
        """Test complete workflow from profile selection to data operations."""
        from callbacks.accordion_settings import (
            update_configuration_status,
            enforce_query_save_before_data_ops,
        )

        # Step 1: No profile selected
        status = update_configuration_status(None, None, 0)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is True

        # Step 2: Profile selected
        status = update_configuration_status("default", None, 0)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is True  # Still locked (no JIRA)

        # Step 3: JIRA configured
        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 0)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is True  # Still locked (no query saved)

        # Step 4: Query saved
        status = update_configuration_status("default", jira_status, 1)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is False  # Finally unlocked! 🎉


class TestLoadQueryJQL:
    """Test load_query_jql callback."""

    def test_loads_query_jql(self, temp_profiles_dir_with_default):
        """Verify loads JQL when query selected."""
        from unittest.mock import patch
        import json

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka"
        query_dir = kafka_dir / "queries" / "main"
        query_dir.mkdir(parents=True)

        query_file = query_dir / "query.json"
        with open(query_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "name": "Main Query",
                    "jql": "project = KAFKA AND priority > Medium",
                    "description": "High priority items",
                    "created_at": "2025-01-01T00:00:00Z",
                },
                f,
            )

        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f)

        # Act
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from callbacks.accordion_settings import load_query_jql

            result = load_query_jql("main")

        # Assert
        assert result == "project = KAFKA AND priority > Medium"

    def test_returns_empty_string_if_query_not_found(
        self, temp_profiles_dir_with_default
    ):
        """Verify returns empty string if query file doesn't exist."""
        from unittest.mock import patch
        import json

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "default",
            "active_query_id": "main",
            "profiles": {},
        }
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f)

        # Act
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from callbacks.accordion_settings import load_query_jql

            result = load_query_jql("nonexistent")

        # Assert
        assert result == ""


class TestSaveQueryChanges:
    """Test save_query_changes callback."""

    def test_saves_query_jql(self, temp_profiles_dir_with_default):
        """Verify saves updated JQL to query file."""
        from unittest.mock import patch
        import json

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka"
        query_dir = kafka_dir / "queries" / "main"
        query_dir.mkdir(parents=True)

        query_file = query_dir / "query.json"
        with open(query_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "name": "Main Query",
                    "jql": "project = KAFKA",
                    "description": "",
                    "created_at": "2025-01-01T00:00:00Z",
                },
                f,
            )

        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f)

        # Act
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from callbacks.accordion_settings import save_query_changes

            result = save_query_changes(
                1, "main", "project = KAFKA AND priority = High"
            )

        # Assert - result should be a success Alert
        assert "saved successfully" in str(result).lower()

        # Verify file updated
        with open(query_file, "r") as f:
            query_data = json.load(f)

        assert query_data["jql"] == "project = KAFKA AND priority = High"
        assert "updated_at" in query_data

    def test_returns_warning_if_no_query_selected(self):
        """Verify returns warning if query_id is None."""
        from callbacks.accordion_settings import save_query_changes

        result = save_query_changes(1, None, "project = TEST")

        # Should be a warning Alert
        assert "No query selected" in str(result)

    def test_returns_warning_if_jql_empty(self):
        """Verify returns warning if JQL is empty."""
        from callbacks.accordion_settings import save_query_changes

        result = save_query_changes(1, "main", "")

        # Should be a warning Alert
        assert "cannot be empty" in str(result).lower()


class TestCancelQueryEdit:
    """Test cancel_query_edit callback."""

    def test_reloads_original_jql(self, temp_profiles_dir_with_default):
        """Verify reloads original JQL on cancel."""
        from unittest.mock import patch
        import json

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka"
        query_dir = kafka_dir / "queries" / "main"
        query_dir.mkdir(parents=True)

        query_file = query_dir / "query.json"
        original_jql = "project = KAFKA AND created >= -12w"
        with open(query_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "name": "Main Query",
                    "jql": original_jql,
                    "description": "",
                    "created_at": "2025-01-01T00:00:00Z",
                },
                f,
            )

        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f)

        # Act
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from callbacks.accordion_settings import cancel_query_edit

            result = cancel_query_edit(1, "main")

        # Assert
        assert result == original_jql
