"""Test field mapping state initialization in render callback.

CRITICAL: All tests MUST mock functions that read/write to profile files:
- data.persistence.load_app_settings
- data.persistence.load_jira_configuration
- data.field_mapper.fetch_available_jira_fields (calls load_jira_configuration)

Without proper mocks, tests will modify real user data in profiles/ directory!
"""

from unittest.mock import patch
from callbacks.field_mapping.tab_rendering import render_tab_content


class TestFieldMappingStateInitialization:
    """Test that render_tab_content properly initializes state from saved settings."""

    @patch("data.field_mapper.fetch_available_jira_fields")
    @patch("data.persistence.load_app_settings")
    @patch("callbacks.field_mapping.tab_rendering.callback_context")
    @patch("dash.ctx")
    def test_render_initializes_state_from_saved_settings(
        self, mock_dash_ctx, mock_callback_ctx, mock_load_settings, mock_fetch_fields
    ):
        """Test that opening modal initializes state store from profile.json."""
        # Arrange: Mock fetch_available_jira_fields to prevent real API calls
        mock_fetch_fields.return_value = []

        # Arrange: Mock saved settings with field mappings
        mock_load_settings.return_value = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10001",
                    "deployment_successful": "customfield_10002",
                },
                "flow": {
                    "completed_date": "resolutiondate",
                    "work_item_size": "customfield_10003",
                },
            },
            "development_projects": ["PROJ1", "PROJ2"],
            "devops_projects": ["DEVOPS"],
            "flow_end_statuses": ["Done", "Closed"],
            "active_statuses": ["In Progress"],
            "flow_start_statuses": ["To Do"],
            "wip_statuses": ["In Progress", "Review"],
            "production_environment_values": ["prod", "production"],
            "flow_type_mappings": {
                "Feature": {"issue_types": ["Story"], "effort_categories": []},
                "Defect": {"issue_types": ["Bug"], "effort_categories": []},
                "Technical Debt": {
                    "issue_types": ["Tech Debt"],
                    "effort_categories": [],
                },
                "Risk": {"issue_types": ["Risk"], "effort_categories": []},
            },
        }

        mock_callback_ctx.triggered = []  # Simulate initial render
        mock_dash_ctx.triggered = []
        mock_dash_ctx.triggered_id = None

        # Empty state (modal opening for first time)
        empty_state = {}

        # Mock metadata
        metadata = {
            "fields": [
                {
                    "id": "customfield_10001",
                    "name": "Deployment Date",
                    "type": "datetime",
                    "custom": True,
                },
                {
                    "id": "customfield_10002",
                    "name": "Deployment Successful",
                    "type": "option",
                    "custom": True,
                },
                {
                    "id": "customfield_10003",
                    "name": "Story Points",
                    "type": "number",
                    "custom": True,
                },
                {
                    "id": "resolutiondate",
                    "name": "Resolution Date",
                    "type": "datetime",
                    "custom": False,
                },
            ]
        }

        # Act: Render tab content (Fields tab)
        content, returned_state = render_tab_content(
            active_tab="tab-fields",
            metadata=metadata,
            is_open=True,
            refresh_trigger=0,
            fetched_field_values={},  # No fetched values in test
            profile_switch_trigger=0,  # NEW: Profile switch trigger
            state_data=empty_state,
            collected_namespace_values={},  # No collected DOM values in test
        )

        # Assert: State should be initialized from saved settings
        assert returned_state is not None, "render_tab_content should return state"
        assert "field_mappings" in returned_state, "State should contain field_mappings"
        assert (
            returned_state["field_mappings"]["dora"]["deployment_date"]
            == "customfield_10001"
        )
        assert (
            returned_state["field_mappings"]["dora"]["deployment_successful"]
            == "customfield_10002"
        )
        assert (
            returned_state["field_mappings"]["flow"]["completed_date"]
            == "resolutiondate"
        )
        assert (
            returned_state["field_mappings"]["flow"]["work_item_size"]
            == "customfield_10003"
        )

        # Verify other settings also initialized
        assert returned_state["development_projects"] == ["PROJ1", "PROJ2"]
        assert returned_state["devops_projects"] == ["DEVOPS"]
        assert returned_state["flow_end_statuses"] == ["Done", "Closed"]

    @patch("data.field_mapper.fetch_available_jira_fields")
    @patch("data.persistence.load_app_settings")
    @patch("callbacks.field_mapping.tab_rendering.callback_context")
    @patch("dash.ctx")
    def test_render_preserves_state_when_already_initialized(
        self, mock_dash_ctx, mock_callback_ctx, mock_load_settings, mock_fetch_fields
    ):
        """Test that switching tabs preserves state (doesn't reinitialize)."""
        # Arrange: Mock fetch_available_jira_fields to prevent real API calls
        mock_fetch_fields.return_value = []

        # Arrange: Mock saved settings (won't be used because state already exists)
        mock_load_settings.return_value = {
            "field_mappings": {"dora": {}, "flow": {}},
        }

        mock_callback_ctx.triggered = [{"prop_id": "mappings-tabs.active_tab"}]
        mock_dash_ctx.triggered = [{"prop_id": "mappings-tabs.active_tab"}]
        mock_dash_ctx.triggered_id = "mappings-tabs"

        # State already initialized with user changes
        existing_state = {
            "_profile_id": "p_test123",
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_99999",  # User changed this
                },
                "flow": {
                    "completed_date": "customfield_88888",  # User changed this
                },
            },
            "development_projects": ["CHANGED"],
        }

        # Act: Render different tab
        content, returned_state = render_tab_content(
            active_tab="tab-projects",
            metadata={},
            is_open=True,
            refresh_trigger=0,
            fetched_field_values={},  # No fetched values in test
            profile_switch_trigger=0,  # NEW: Profile switch trigger
            state_data=existing_state,
            collected_namespace_values={},  # No collected DOM values in test
        )

        # Assert: State should be preserved (not reinitialized)
        assert returned_state == existing_state, (
            "State should not be reinitialized when switching tabs"
        )
        assert (
            returned_state["field_mappings"]["dora"]["deployment_date"]
            == "customfield_99999"
        )
        assert returned_state["development_projects"] == ["CHANGED"]

    @patch("data.field_mapper.fetch_available_jira_fields")
    @patch("data.persistence.load_app_settings")
    @patch("callbacks.field_mapping.tab_rendering.callback_context")
    @patch("dash.ctx")
    def test_render_reinitializes_when_profile_tracking_only(
        self, mock_dash_ctx, mock_callback_ctx, mock_load_settings, mock_fetch_fields
    ):
        """Test that state with only _profile_id is considered empty and gets reinitialized."""
        # Arrange: Mock fetch_available_jira_fields to prevent real JIRA API calls
        # CRITICAL: Without this mock, fetch_available_jira_fields() calls load_jira_configuration()
        # which triggers migration code that WRITES to the real profile.json!
        mock_fetch_fields.return_value = []

        # Arrange: This happens after profile switch cleared state
        mock_load_settings.return_value = {
            "field_mappings": {
                "dora": {"deployment_date": "customfield_10001"},
                "flow": {},
            },
        }

        mock_callback_ctx.triggered = []
        mock_dash_ctx.triggered = []
        mock_dash_ctx.triggered_id = None

        # State cleared by profile switch (only profile tracking remains)
        cleared_state = {"_profile_id": "p_new_profile"}

        metadata = {"fields": []}

        # Act: Render tab
        content, returned_state = render_tab_content(
            active_tab="tab-fields",
            metadata=metadata,
            is_open=True,
            refresh_trigger=0,
            fetched_field_values={},  # No fetched values in test
            profile_switch_trigger=0,  # NEW: Profile switch trigger
            state_data=cleared_state,
            collected_namespace_values={},  # No collected DOM values in test
        )

        # Assert: State should be reinitialized from settings
        assert returned_state["_profile_id"] == "p_new_profile", (
            "Profile ID should be preserved"
        )
        assert "field_mappings" in returned_state, "State should be reinitialized"
        assert (
            returned_state["field_mappings"]["dora"]["deployment_date"]
            == "customfield_10001"
        )
