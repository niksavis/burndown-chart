from unittest.mock import patch

from callbacks.field_mapping.tab_rendering import render_tab_content


class TestFieldMappingStateInitialization:
    @patch("callbacks.field_mapping.tab_rendering.fetch_available_jira_fields")
    @patch("callbacks.field_mapping.tab_rendering.load_app_settings")
    @patch("callbacks.field_mapping.tab_rendering.callback_context")
    @patch("callbacks.field_mapping.tab_rendering.ctx")
    def test_render_initializes_state_from_saved_settings(
        self, mock_dash_ctx, mock_callback_ctx, mock_load_settings, mock_fetch_fields
    ):
        mock_fetch_fields.return_value = []

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

        mock_callback_ctx.triggered = []
        mock_dash_ctx.triggered = []
        mock_dash_ctx.triggered_id = None

        empty_state = {}

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

        content, returned_state = render_tab_content(
            active_tab="tab-fields",
            metadata=metadata,
            is_open=True,
            refresh_trigger=0,
            fetched_field_values={},
            profile_switch_trigger=0,
            state_data=empty_state,
            collected_namespace_values={},
        )

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
        mock_fetch_fields.return_value = []

        mock_load_settings.return_value = {
            "field_mappings": {"dora": {}, "flow": {}},
        }

        mock_callback_ctx.triggered = [{"prop_id": "mappings-tabs.active_tab"}]
        mock_dash_ctx.triggered = [{"prop_id": "mappings-tabs.active_tab"}]
        mock_dash_ctx.triggered_id = "mappings-tabs"

        existing_state = {
            "_profile_id": "p_test123",
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_99999",
                },
                "flow": {
                    "completed_date": "customfield_88888",
                },
            },
            "development_projects": ["CHANGED"],
        }

        content, returned_state = render_tab_content(
            active_tab="tab-projects",
            metadata={},
            is_open=True,
            refresh_trigger=0,
            fetched_field_values={},
            profile_switch_trigger=0,
            state_data=existing_state,
            collected_namespace_values={},
        )

        assert returned_state == existing_state, (
            "State should not be reinitialized when switching tabs"
        )
        assert (
            returned_state["field_mappings"]["dora"]["deployment_date"]
            == "customfield_99999"
        )
        assert returned_state["development_projects"] == ["CHANGED"]

    @patch("callbacks.field_mapping.tab_rendering.fetch_available_jira_fields")
    @patch("callbacks.field_mapping.tab_rendering.load_app_settings")
    @patch("callbacks.field_mapping.tab_rendering.callback_context")
    @patch("callbacks.field_mapping.tab_rendering.ctx")
    def test_render_reinitializes_when_profile_tracking_only(
        self, mock_dash_ctx, mock_callback_ctx, mock_load_settings, mock_fetch_fields
    ):
        mock_fetch_fields.return_value = []

        mock_load_settings.return_value = {
            "field_mappings": {
                "dora": {"deployment_date": "customfield_10001"},
                "flow": {},
            },
        }

        mock_callback_ctx.triggered = []
        mock_dash_ctx.triggered = []
        mock_dash_ctx.triggered_id = None

        cleared_state = {"_profile_id": "p_new_profile"}

        metadata = {"fields": []}

        content, returned_state = render_tab_content(
            active_tab="tab-fields",
            metadata=metadata,
            is_open=True,
            refresh_trigger=0,
            fetched_field_values={},
            profile_switch_trigger=0,
            state_data=cleared_state,
            collected_namespace_values={},
        )

        assert returned_state["_profile_id"] == "p_new_profile", (
            "Profile ID should be preserved"
        )
        assert "field_mappings" in returned_state, "State should be reinitialized"
        assert (
            returned_state["field_mappings"]["dora"]["deployment_date"]
            == "customfield_10001"
        )
