"""Test field mapping state initialization in render callback."""

from unittest.mock import patch
from callbacks.field_mapping import render_tab_content


class TestFieldMappingStateInitialization:
    """Test that render_tab_content properly initializes state from saved settings."""

    @patch("data.persistence.load_app_settings")
    @patch("callbacks.field_mapping.callback_context")
    def test_render_initializes_state_from_saved_settings(
        self, mock_ctx, mock_load_settings
    ):
        """Test that opening modal initializes state store from profile.json."""
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
            "completion_statuses": ["Done", "Closed"],
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

        mock_ctx.triggered = []  # Simulate initial render

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
        assert returned_state["completion_statuses"] == ["Done", "Closed"]

    @patch("data.persistence.load_app_settings")
    @patch("callbacks.field_mapping.callback_context")
    def test_render_preserves_state_when_already_initialized(
        self, mock_ctx, mock_load_settings
    ):
        """Test that switching tabs preserves state (doesn't reinitialize)."""
        # Arrange: Mock saved settings (won't be used because state already exists)
        mock_load_settings.return_value = {
            "field_mappings": {"dora": {}, "flow": {}},
        }

        mock_ctx.triggered = [{"prop_id": "mappings-tabs.active_tab"}]

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

    @patch("data.persistence.load_app_settings")
    @patch("callbacks.field_mapping.callback_context")
    def test_render_reinitializes_when_profile_tracking_only(
        self, mock_ctx, mock_load_settings
    ):
        """Test that state with only _profile_id is considered empty and gets reinitialized."""
        # Arrange: This happens after profile switch cleared state
        mock_load_settings.return_value = {
            "field_mappings": {
                "dora": {"deployment_date": "customfield_10001"},
                "flow": {},
            },
        }

        mock_ctx.triggered = []

        # State cleared by profile switch (only profile tracking remains)
        cleared_state = {"_profile_id": "p_new_profile"}

        metadata = {"fields": []}

        # Act: Render tab
        content, returned_state = render_tab_content(
            active_tab="tab-fields",
            metadata=metadata,
            is_open=True,
            refresh_trigger=0,
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
