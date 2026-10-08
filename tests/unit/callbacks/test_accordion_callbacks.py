from datetime import UTC
from unittest.mock import patch

import dash_bootstrap_components as dbc
from dash import html, no_update


class TestConfigurationStatusTracking:
    def test_status_all_locked_initially(self):
        from callbacks.accordion_settings import update_configuration_status

        status = update_configuration_status(None, None, 0, None)

        assert status["profile"]["enabled"] is True
        assert status["profile"]["complete"] is False
        assert status["profile"]["icon"] == "[Pending]"

        assert status["jira"]["enabled"] is False
        assert status["jira"]["complete"] is False
        assert status["jira"]["icon"] == "[Locked]"

        assert status["fields"]["enabled"] is False
        assert status["fields"]["complete"] is False
        assert status["fields"]["icon"] == "[Locked]"

        assert status["queries"]["enabled"] is False
        assert status["queries"]["complete"] is False
        assert status["queries"]["icon"] == "[Locked]"

        assert status["data_operations"]["enabled"] is False
        assert status["data_operations"]["complete"] is False
        assert status["data_operations"]["icon"] == "[Locked]"

    def test_status_profile_enabled_when_selected(self):
        from callbacks.accordion_settings import update_configuration_status

        status = update_configuration_status("default", None, 0, None)

        assert status["profile"]["enabled"] is True
        assert status["profile"]["complete"] is True
        assert status["profile"]["icon"] == "[OK]"

        assert status["jira"]["enabled"] is True
        assert status["jira"]["complete"] is False
        assert status["jira"]["icon"] == "[Pending]"

        assert status["fields"]["enabled"] is False
        assert status["queries"]["enabled"] is False
        assert status["data_operations"]["enabled"] is False

    def test_status_jira_complete_unlocks_fields_and_queries(self):
        from callbacks.accordion_settings import update_configuration_status

        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 0, None)

        assert status["profile"]["complete"] is True

        assert status["jira"]["enabled"] is True
        assert status["jira"]["complete"] is True
        assert status["jira"]["icon"] == "[OK]"

        assert status["fields"]["enabled"] is True
        assert status["fields"]["complete"] is False
        assert status["fields"]["icon"] == "[Pending]"

        assert status["queries"]["enabled"] is True
        assert status["queries"]["complete"] is False
        assert status["queries"]["icon"] == "[Pending]"

        assert status["data_operations"]["enabled"] is False
        assert status["data_operations"]["icon"] == "[Locked]"

    def test_status_query_saved_unlocks_data_ops(self):
        from callbacks.accordion_settings import update_configuration_status

        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 1, None)

        assert status["profile"]["complete"] is True
        assert status["jira"]["complete"] is True

        assert status["queries"]["enabled"] is True
        assert status["queries"]["complete"] is True
        assert status["queries"]["icon"] == "[OK]"

        assert status["data_operations"]["enabled"] is True
        assert status["data_operations"]["complete"] is False
        assert status["data_operations"]["icon"] == "[Pending]"


class TestSectionStateManagement:
    def test_section_states_all_disabled_when_locked(self):
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
        from callbacks.accordion_settings import update_section_states

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

        assert "accordion-item-disabled" not in jira_class
        assert "accordion-item-disabled" not in fields_class
        assert "accordion-item-disabled" not in queries_class

        assert "accordion-item-disabled" in data_ops_class


class TestSectionTitleUpdates:
    def test_section_titles_show_locked_icons_initially(self):
        from callbacks.accordion_settings import update_section_titles

        config_status = {
            "profile": {"enabled": False, "icon": "[Locked]"},
            "jira": {"enabled": False, "icon": "[Locked]"},
            "fields": {"enabled": False, "icon": "[Locked]"},
            "queries": {"enabled": False, "icon": "[Locked]"},
            "data_operations": {"enabled": False, "icon": "[Locked]"},
        }

        (
            profile_title,
            jira_title,
            fields_title,
            queries_title,
            data_ops_title,
        ) = update_section_titles(config_status)

        assert "[Locked]" in profile_title
        assert "[Locked]" in jira_title
        assert "[Locked]" in fields_title
        assert "[Locked]" in queries_title
        assert "[Locked]" in data_ops_title

    def test_section_titles_show_in_progress_icons(self):
        from callbacks.accordion_settings import update_section_titles

        config_status = {
            "profile": {"enabled": True, "icon": "[OK]"},
            "jira": {"enabled": True, "icon": "[Pending]"},
            "fields": {"enabled": True, "icon": "[Pending]"},
            "queries": {"enabled": True, "icon": "[Pending]"},
            "data_operations": {"enabled": False, "icon": "[Locked]"},
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
        assert "[Locked]" in data_ops_title

    def test_section_titles_show_complete_icons(self):
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
    def test_data_ops_disabled_when_no_query_saved(self):
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
        assert (
            "save" in str(alert_content).lower()
            and "query" in str(alert_content).lower()
        )

    def test_data_ops_enabled_when_query_saved(self):
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
        from callbacks.accordion_settings import enforce_query_save_before_data_ops

        config_status = {
            "queries": {"complete": False},
            "data_ops": {"enabled": False},
        }

        _, alert_content, _ = enforce_query_save_before_data_ops(config_status)

        assert isinstance(alert_content, (str, html.Div, dbc.Alert))


class TestProfileSettingsSave:
    @patch("callbacks.accordion_settings.save_app_settings")
    def test_save_profile_settings_success(self, mock_save_settings):
        from callbacks.accordion_settings import save_profile_settings

        mock_save_settings.return_value = None

        pert_factor = 1.5
        deadline = "2025-12-31"
        data_points = 10
        milestone_enabled = True
        milestone_date = "2025-06-15"

        result = save_profile_settings(
            1,
            pert_factor,
            deadline,
            data_points,
            milestone_enabled,
            milestone_date,
        )

        mock_save_settings.assert_called_once()
        call_kwargs = mock_save_settings.call_args[1]
        assert call_kwargs["pert_factor"] == 1.5
        assert call_kwargs["deadline"] == "2025-12-31"
        assert call_kwargs["data_points_count"] == 10
        assert call_kwargs["show_milestone"] is True
        assert call_kwargs["milestone"] == "2025-06-15"

        assert isinstance(result, (dbc.Alert, html.Div))

    @patch("callbacks.accordion_settings.save_app_settings")
    def test_save_profile_settings_error_handling(self, mock_save_settings):
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

        assert isinstance(result, (dbc.Alert, html.Div))
        result_str = str(result)
        assert "error" in result_str.lower() or "failed" in result_str.lower()

    def test_save_profile_settings_no_click(self):
        from callbacks.accordion_settings import save_profile_settings

        result = save_profile_settings(
            None,
            1.5,
            "2025-12-31",
            10,
            False,
            None,
        )

        assert result == no_update


class TestCallbackIntegration:
    def test_status_to_section_state_flow(self):
        from callbacks.accordion_settings import (
            update_configuration_status,
            update_section_states,
        )

        status = update_configuration_status("default", None, 0, None)
        jira_class, fields_class, queries_class, data_ops_class = update_section_states(
            status
        )

        assert "accordion-item-disabled" not in jira_class

        assert "accordion-item-disabled" in fields_class
        assert "accordion-item-disabled" in queries_class
        assert "accordion-item-disabled" in data_ops_class

    def test_status_to_title_flow(self):
        from callbacks.accordion_settings import (
            update_configuration_status,
            update_section_titles,
        )

        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 0, None)

        (
            profile_title,
            jira_title,
            fields_title,
            queries_title,
            data_ops_title,
        ) = update_section_titles(status)

        assert "[OK]" in profile_title
        assert "[Pending]" in jira_title or "[OK]" in jira_title

        assert "[Pending]" in fields_title
        assert "[Pending]" in queries_title

        assert "[Locked]" in data_ops_title

    def test_full_workflow_profile_to_data_ops(self):
        from callbacks.accordion_settings import (
            enforce_query_save_before_data_ops,
            update_configuration_status,
        )

        status = update_configuration_status(None, None, 0, None)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is True

        status = update_configuration_status("default", None, 0, None)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is True

        jira_status = "[OK] JIRA Connected"
        status = update_configuration_status("default", jira_status, 0, None)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is True

        status = update_configuration_status("default", jira_status, 1, None)
        button_disabled, _, _ = enforce_query_save_before_data_ops(status)
        assert button_disabled is False


class TestLoadQueryJQL:
    def test_loads_query_jql(self, temp_database):
        from datetime import datetime

        from callbacks.accordion_settings import load_query_jql
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "kafka",
            "name": "Kafka Profile",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        query_data = {
            "id": "main",
            "profile_id": "kafka",
            "name": "Main Query",
            "jql": "project = KAFKA AND priority > Medium",
            "description": "High priority items",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("kafka", query_data)

        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        from unittest.mock import patch

        with patch("data.query_manager.get_active_profile_id", return_value="kafka"):
            result = load_query_jql("main")

        assert result == "project = KAFKA AND priority > Medium"

    def test_returns_empty_string_if_query_not_found(self, temp_database):
        from datetime import datetime

        from callbacks.accordion_settings import load_query_jql
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile_data = {
            "id": "default",
            "name": "Default Profile",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        result = load_query_jql("nonexistent")

        assert result == ""


class TestSaveQueryChanges:
    def test_saves_query_jql(self, temp_database):
        from datetime import datetime

        from callbacks.accordion_settings import save_query_changes
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "kafka",
            "name": "Kafka Profile",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        query_data = {
            "id": "main",
            "profile_id": "kafka",
            "name": "Main Query",
            "jql": "project = KAFKA",
            "description": "Original query",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("kafka", query_data)

        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        from unittest.mock import patch

        with patch("data.query_manager.get_active_profile_id", return_value="kafka"):
            result = save_query_changes(
                1, "main", "project = KAFKA AND priority = High"
            )

        assert "saved successfully" in str(result).lower()

        updated_query = backend.get_query("kafka", "main")
        assert updated_query is not None
        assert updated_query["jql"] == "project = KAFKA AND priority = High"

    def test_returns_warning_if_no_query_selected(self):
        from callbacks.accordion_settings import save_query_changes

        result = save_query_changes(1, None, "project = TEST")

        assert "No query selected" in str(result)

    def test_returns_warning_if_jql_empty(self):
        from callbacks.accordion_settings import save_query_changes

        result = save_query_changes(1, "main", "")

        assert "cannot be empty" in str(result).lower()


class TestCancelQueryEdit:
    def test_reloads_original_jql(self, temp_database):
        from datetime import datetime

        from callbacks.accordion_settings import cancel_query_edit
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "kafka",
            "name": "Kafka Profile",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        original_jql = "project = KAFKA AND created >= -12w"
        query_data = {
            "id": "main",
            "profile_id": "kafka",
            "name": "Main Query",
            "jql": original_jql,
            "description": "",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("kafka", query_data)

        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        from unittest.mock import patch

        with patch("data.query_manager.get_active_profile_id", return_value="kafka"):
            result = cancel_query_edit(1, "main")

        assert result == original_jql
