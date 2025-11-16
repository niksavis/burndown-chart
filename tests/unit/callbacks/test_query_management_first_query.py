"""Unit tests for first query creation (no query selected scenario).

Bug Report: "I cannot create the 1st query because the save button
(save as and discard too) are disabled."

Update: "now the Create New Query item is back to Query dropdown. I can write
the query and Query Name gets generated, so that is a plus. But save is not
working, only save as in this case. why is it so?"

Root Cause: When no query is selected OR "Create New Query" is selected, the
button state callback was treating them differently. "Create New Query" had
Save button hardcoded as disabled.

Fix: Updated manage_button_states() to enable Save/Save As when JQL is present
in both "no selection" and "Create New Query" modes. Updated save_query_overwrite()
to handle both modes with auto-generated name support.
"""

import pytest
from unittest.mock import patch
from callbacks.query_management import manage_button_states, save_query_overwrite


class TestFirstQueryCreation:
    """Test button states and save logic for first query in profile."""

    def test_button_states_no_selection_with_jql(self):
        """Verify Save button is enabled when JQL is entered and no query selected.

        Scenario: User enters JQL in empty profile (first query)
        Expected: Save and Save As buttons enabled
        """
        # Arrange: No query selected, JQL entered, no name
        current_name = ""
        current_jql = "project = KAFKA AND created >= -4w"
        selected_query_id = None  # No selection
        dropdown_options = []

        # Act
        save_disabled, save_as_disabled, discard_disabled, show_alert = (
            manage_button_states(
                current_name, current_jql, selected_query_id, dropdown_options
            )
        )

        # Assert
        assert save_disabled is False, "Save button should be ENABLED when JQL present"
        assert save_as_disabled is False, (
            "Save As button should be ENABLED when JQL present"
        )
        assert discard_disabled is False, (
            "Discard button should be ENABLED when content present"
        )
        assert show_alert is True, "Alert should show when content present"

    def test_button_states_no_selection_with_jql_and_name(self):
        """Verify buttons enabled when both JQL and name are entered."""
        # Arrange
        current_name = "My First Query"
        current_jql = "project = KAFKA"
        selected_query_id = None
        dropdown_options = []

        # Act
        save_disabled, save_as_disabled, discard_disabled, show_alert = (
            manage_button_states(
                current_name, current_jql, selected_query_id, dropdown_options
            )
        )

        # Assert
        assert save_disabled is False, "Save button should be ENABLED"
        assert save_as_disabled is False, "Save As button should be ENABLED"
        assert discard_disabled is False, "Discard button should be ENABLED"

    def test_button_states_no_selection_empty_jql(self):
        """Verify buttons disabled when JQL is empty."""
        # Arrange
        current_name = ""
        current_jql = ""
        selected_query_id = None
        dropdown_options = []

        # Act
        save_disabled, save_as_disabled, discard_disabled, show_alert = (
            manage_button_states(
                current_name, current_jql, selected_query_id, dropdown_options
            )
        )

        # Assert
        assert save_disabled is True, "Save button should be DISABLED when no JQL"
        assert save_as_disabled is True, "Save As button should be DISABLED when no JQL"
        assert discard_disabled is True, (
            "Discard button should be DISABLED when no content"
        )
        assert show_alert is False, "Alert should NOT show when no content"

    @patch("data.query_manager.create_query")
    @patch("data.query_manager.set_active_query")
    @patch("data.query_manager.get_active_profile_id")
    @patch("data.query_manager.list_queries_for_profile")
    @patch("data.jql_parser.generate_query_name_from_jql")
    def test_save_first_query_auto_generated_name(
        self,
        mock_generate_name,
        mock_list_queries,
        mock_get_profile_id,
        mock_set_active,
        mock_create_query,
    ):
        """Test saving first query with auto-generated name."""
        # Arrange
        mock_get_profile_id.return_value = "p_test123"
        mock_generate_name.return_value = "KAFKA Last 4 Weeks"
        mock_create_query.return_value = "q_new123"
        mock_list_queries.return_value = [
            {"id": "q_new123", "name": "KAFKA Last 4 Weeks", "is_active": True}
        ]

        # Act: Save query with empty name (should auto-generate)
        n_clicks = 1
        query_name = ""  # Empty - should be auto-generated
        query_jql = "project = KAFKA AND created >= -4w"
        selected_query_id = None  # No selection (first query)

        feedback, options, value = save_query_overwrite(
            n_clicks, query_name, query_jql, selected_query_id
        )

        # Assert
        mock_generate_name.assert_called_once_with("project = KAFKA AND created >= -4w")
        mock_create_query.assert_called_once_with(
            "p_test123", "KAFKA Last 4 Weeks", "project = KAFKA AND created >= -4w"
        )
        mock_set_active.assert_called_once_with("p_test123", "q_new123")
        assert value == "q_new123", "Should select newly created query"
        assert len(options) == 2, "Should have Create New + 1 query in dropdown"

    @patch("data.query_manager.create_query")
    @patch("data.query_manager.set_active_query")
    @patch("data.query_manager.get_active_profile_id")
    @patch("data.query_manager.list_queries_for_profile")
    def test_save_first_query_custom_name(
        self,
        mock_list_queries,
        mock_get_profile_id,
        mock_set_active,
        mock_create_query,
    ):
        """Test saving first query with custom name provided by user."""
        # Arrange
        mock_get_profile_id.return_value = "p_test123"
        mock_create_query.return_value = "q_new123"
        mock_list_queries.return_value = [
            {"id": "q_new123", "name": "My Custom Query", "is_active": True}
        ]

        # Act: Save query with custom name
        n_clicks = 1
        query_name = "My Custom Query"  # User provided name
        query_jql = "project = KAFKA"
        selected_query_id = None  # No selection (first query)

        feedback, options, value = save_query_overwrite(
            n_clicks, query_name, query_jql, selected_query_id
        )

        # Assert: Should use provided name, NOT auto-generate
        mock_create_query.assert_called_once_with(
            "p_test123", "My Custom Query", "project = KAFKA"
        )
        mock_set_active.assert_called_once_with("p_test123", "q_new123")
        assert value == "q_new123"

    def test_button_states_create_new_with_jql(self):
        """Verify Save button is enabled when JQL is entered in Create New Query mode.

        Scenario: User selects "Create New Query" from dropdown and types JQL
        Expected: Save and Save As buttons both enabled (updated behavior)
        """
        # Arrange: Create New Query selected, JQL entered, name auto-generated
        current_name = "KAFKA Last 4 Weeks"  # Auto-generated
        current_jql = "project = KAFKA AND created >= -4w"
        selected_query_id = "__create_new__"
        dropdown_options = []

        # Act
        save_disabled, save_as_disabled, discard_disabled, show_alert = (
            manage_button_states(
                current_name, current_jql, selected_query_id, dropdown_options
            )
        )

        # Assert
        assert save_disabled is False, (
            "Save button should be ENABLED in Create New mode (updated behavior)"
        )
        assert save_as_disabled is False, "Save As button should be ENABLED"
        assert discard_disabled is False, "Discard button should be ENABLED"
        assert show_alert is True, "Alert should show when content present"

    def test_button_states_create_new_empty_jql(self):
        """Verify buttons disabled when JQL is empty in Create New Query mode."""
        # Arrange
        current_name = ""
        current_jql = ""
        selected_query_id = "__create_new__"
        dropdown_options = []

        # Act
        save_disabled, save_as_disabled, discard_disabled, show_alert = (
            manage_button_states(
                current_name, current_jql, selected_query_id, dropdown_options
            )
        )

        # Assert
        assert save_disabled is True, "Save button should be DISABLED when no JQL"
        assert save_as_disabled is True, "Save As button should be DISABLED when no JQL"
        assert discard_disabled is True, (
            "Discard button should be DISABLED when no content"
        )
        assert show_alert is False, "Alert should NOT show when no content"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
