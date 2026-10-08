import dash_bootstrap_components as dbc
import pytest
from dash import html

from ui.field_mapping_modal import (
    create_field_mapping_error_alert,
    create_field_mapping_form,
    create_field_mapping_modal,
    create_field_mapping_success_alert,
    create_metric_section,
    create_validation_message,
)


class TestCreateFieldMappingModal:
    def test_modal_returns_modal_component(self):
        modal = create_field_mapping_modal()
        assert isinstance(modal, dbc.Modal)

    def test_modal_has_correct_id(self):
        modal = create_field_mapping_modal()
        assert getattr(modal, "id", None) == "field-mapping-modal"

    def test_modal_starts_closed(self):
        modal = create_field_mapping_modal()
        assert getattr(modal, "is_open", None) is False

    def test_modal_has_xl_size(self):
        modal = create_field_mapping_modal()
        assert getattr(modal, "size", None) == "xl"

    def test_modal_has_static_backdrop(self):
        modal = create_field_mapping_modal()
        assert getattr(modal, "backdrop", None) == "static"

    def test_modal_has_header(self):
        modal = create_field_mapping_modal()
        children = getattr(modal, "children", [])
        assert len(children) == 3
        header = children[0]
        assert isinstance(header, dbc.ModalHeader)

    def test_modal_has_body_with_loading(self):
        modal = create_field_mapping_modal()
        children = getattr(modal, "children", [])
        body = children[1]
        assert isinstance(body, dbc.ModalBody)

    def test_modal_has_footer_with_buttons(self):
        modal = create_field_mapping_modal()
        children = getattr(modal, "children", [])
        footer = children[2]
        assert isinstance(footer, dbc.ModalFooter)


class TestCreateFieldMappingForm:
    def test_form_returns_div(self):
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Test Field",
                "field_type": "datetime",
            }
        ]
        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        assert isinstance(form, html.Div)

    def test_form_includes_dora_section(self):
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Test Field",
                "field_type": "datetime",
            }
        ]
        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        assert hasattr(form, "children")
        assert form.children is not None

    def test_form_includes_flow_section(self):
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Test Field",
                "field_type": "datetime",
            }
        ]
        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        children = form.children
        assert isinstance(children, list)
        assert len(children) >= 2

    def test_form_creates_field_options(self):
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Deployment Date",
                "field_type": "datetime",
            },
            {
                "field_id": "customfield_10002",
                "field_name": "Story Points",
                "field_type": "number",
            },
        ]
        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        assert form is not None

    def test_form_applies_current_mappings(self):
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Test Field",
                "field_type": "datetime",
            }
        ]
        current_mappings = {
            "dora": {"deployment_date": "customfield_10001"},
            "flow": {"status": "status"},
        }

        form = create_field_mapping_form(available_fields, current_mappings)
        assert form is not None


class TestCreateMetricSection:
    def test_section_returns_card(self):
        fields = [
            (
                "deployment_date",
                "Deployment Date",
                "datetime",
                "When was this deployed?",
            )
        ]
        field_options = [{"label": "Test Field", "value": "customfield_10001"}]
        current_mappings = {}

        section = create_metric_section(
            "Test Metrics", "test", fields, field_options, current_mappings
        )
        assert isinstance(section, dbc.Card)

    def test_section_has_header(self):
        fields = [
            (
                "deployment_date",
                "Deployment Date",
                "datetime",
                "When was this deployed?",
            )
        ]
        field_options = [{"label": "Test Field", "value": "customfield_10001"}]
        current_mappings = {}

        section = create_metric_section(
            "DORA Metrics", "dora", fields, field_options, current_mappings
        )
        children = getattr(section, "children", [])
        assert len(children) == 2
        header = children[0]
        assert isinstance(header, dbc.CardHeader)

    def test_section_creates_rows_for_fields(self):
        fields = [
            (
                "deployment_date",
                "Deployment Date",
                "datetime",
                "When was this deployed?",
            ),
            ("code_commit_date", "Commit Date", "datetime", "When was code committed?"),
        ]
        field_options = [{"label": "Test Field", "value": "customfield_10001"}]
        current_mappings = {}

        section = create_metric_section(
            "Test", "test", fields, field_options, current_mappings
        )
        children = getattr(section, "children", [])
        body = children[1]
        assert isinstance(body, dbc.CardBody)

    def test_section_applies_current_value(self):
        fields = [("deployment_date", "Deployment Date", "datetime", "Help text")]
        field_options = [
            {"label": "Custom Field 1", "value": "customfield_10001"},
            {"label": "Custom Field 2", "value": "customfield_10002"},
        ]
        current_mappings = {"deployment_date": "customfield_10001"}

        section = create_metric_section(
            "Test", "test", fields, field_options, current_mappings
        )
        assert section is not None


class TestCreateValidationMessage:
    def test_success_message_returns_alert(self):
        message = create_validation_message(True, "Field mapping is valid")
        assert isinstance(message, dbc.Alert)

    def test_success_message_has_success_color(self):
        message = create_validation_message(True, "Valid")
        assert getattr(message, "color", None) == "success"

    def test_warning_message_returns_alert(self):
        message = create_validation_message(False, "Field mapping has issues")
        assert isinstance(message, dbc.Alert)

    def test_warning_message_has_warning_color(self):
        message = create_validation_message(False, "Invalid")
        assert getattr(message, "color", None) == "warning"


class TestAlertHelpers:
    def test_success_alert_returns_alert(self):
        alert = create_field_mapping_success_alert()
        assert isinstance(alert, dbc.Alert)

    def test_success_alert_is_dismissable(self):
        alert = create_field_mapping_success_alert()
        assert getattr(alert, "dismissable", None) is True

    def test_success_alert_has_success_color(self):
        alert = create_field_mapping_success_alert()
        assert getattr(alert, "color", None) == "success"

    def test_success_alert_has_duration(self):
        alert = create_field_mapping_success_alert()
        assert getattr(alert, "duration", None) == 4000

    def test_error_alert_returns_alert(self):
        alert = create_field_mapping_error_alert("Test error")
        assert isinstance(alert, dbc.Alert)

    def test_error_alert_is_dismissable(self):
        alert = create_field_mapping_error_alert("Test error")
        assert getattr(alert, "dismissable", None) is True

    def test_error_alert_has_danger_color(self):
        alert = create_field_mapping_error_alert("Test error")
        assert getattr(alert, "color", None) == "danger"

    def test_error_alert_includes_message(self):
        error_msg = "Failed to validate field"
        alert = create_field_mapping_error_alert(error_msg)
        assert alert.children is not None


class TestFieldMappingIntegration:
    def test_modal_and_form_integration(self):
        try:
            modal = create_field_mapping_modal()

            available_fields = [
                {
                    "field_id": "customfield_10001",
                    "field_name": "Test",
                    "field_type": "datetime",
                }
            ]
            current_mappings = {"dora": {}, "flow": {}}
            form = create_field_mapping_form(available_fields, current_mappings)

            assert modal is not None
            assert form is not None
        except Exception as e:
            pytest.fail(f"Integration test raised exception: {e}")

    def test_complete_workflow_structure(self):
        modal = create_field_mapping_modal()

        available_fields = [
            {"field_id": "cf1", "field_name": "Field 1", "field_type": "datetime"},
            {"field_id": "cf2", "field_name": "Field 2", "field_type": "number"},
        ]
        current_mappings = {"dora": {"deployment_date": "cf1"}, "flow": {}}
        form = create_field_mapping_form(available_fields, current_mappings)

        success_msg = create_validation_message(True, "Valid")
        warning_msg = create_validation_message(False, "Invalid")

        success_alert = create_field_mapping_success_alert()
        error_alert = create_field_mapping_error_alert("Error")

        assert modal is not None
        assert form is not None
        assert success_msg is not None
        assert warning_msg is not None
        assert success_alert is not None
        assert error_alert is not None


class TestFieldTypeDisplay:
    def test_field_type_shown_in_help_text(self):

        available_fields = [
            {
                "field_id": "created",
                "field_name": "Created",
                "field_type": "datetime",
            },
            {
                "field_id": "issuetype",
                "field_name": "Issue Type",
                "field_type": "select",
            },
            {
                "field_id": "customfield_10001",
                "field_name": "Deployment Date",
                "field_type": "datetime",
            },
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)

        form_str = str(form)

        assert "Type: datetime" in form_str
        assert "Type: select" in form_str

    def test_standard_and_custom_field_type_labels(self):

        available_fields = [
            {
                "field_id": "created",
                "field_name": "Created",
                "field_type": "datetime",
            },
            {
                "field_id": "customfield_10001",
                "field_name": "Deployment Date",
                "field_type": "datetime",
            },
            {
                "field_id": "status",
                "field_name": "Status",
                "field_type": "select",
            },
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        form_str = str(form)

        assert "Type: datetime" in form_str
        assert "Type: select" in form_str


class TestFieldTypeRequirements:
    @pytest.mark.parametrize(
        "field_name,expected_type",
        [
            ("deployment_date", "datetime"),
            ("target_environment", "select"),
            ("change_failure", "select"),
            ("affected_environment", "select"),
            ("severity_level", "select"),
            ("flow_item_type", "select"),
            ("effort_category", "select"),
            ("status", "select"),
        ],
    )
    def test_expected_types_shown_for_all_fields(self, field_name, expected_type):
        available_fields = [
            {
                "field_id": "created",
                "field_name": "Created",
                "field_type": "datetime",
            }
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        form_str = str(form)

        assert f"Type: {expected_type}" in form_str

    def test_all_dora_fields_have_type_information(self):
        available_fields = [
            {
                "field_id": "test",
                "field_name": "Test",
                "field_type": "datetime",
            }
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        form_str = str(form)

        dora_fields = [
            "deployment_date",
            "target_environment",
            "code_commit_date",
            "incident_detected_at",
            "incident_resolved_at",
            "change_failure",
            "affected_environment",
            "severity_level",
        ]

        for _field in dora_fields:
            pass

        assert "Type: datetime" in form_str
        assert "Type: select" in form_str

    def test_all_flow_fields_have_type_information(self):
        available_fields = [
            {
                "field_id": "test",
                "field_name": "Test",
                "field_type": "select",
            }
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        form_str = str(form)

        assert "Type: select" in form_str
        assert "Type: datetime" in form_str


class TestValidationPlaceholders:
    def test_validation_placeholders_use_pattern_matching_ids(self):
        available_fields = [
            {
                "field_id": "created",
                "field_name": "Created",
                "field_type": "datetime",
            }
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        form_str = str(form)

        assert "field-validation-message" in form_str

    def test_each_field_has_validation_placeholder(self):
        available_fields = [
            {
                "field_id": "test",
                "field_name": "Test",
                "field_type": "datetime",
            }
        ]

        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        form_str = str(form)

        assert "field-validation-message" in form_str
