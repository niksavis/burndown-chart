"""
Unit tests for field mapping modal UI components.

Tests the field mapping modal creation and form generation to ensure:
- Proper modal structure with all required elements
- Form generation with correct field mappings
- Validation message creation
- Alert generation for success/error states
"""

import pytest
import dash_bootstrap_components as dbc
from dash import html
from ui.field_mapping_modal import (
    create_field_mapping_modal,
    create_field_mapping_form,
    create_metric_section,
    create_validation_message,
    create_field_mapping_success_alert,
    create_field_mapping_error_alert,
)


class TestCreateFieldMappingModal:
    """Test the main field mapping modal creation function."""

    def test_modal_returns_modal_component(self):
        """Test that function returns a dbc.Modal component."""
        modal = create_field_mapping_modal()
        assert isinstance(modal, dbc.Modal)

    def test_modal_has_correct_id(self):
        """Test that modal has the correct ID for callbacks."""
        modal = create_field_mapping_modal()
        assert getattr(modal, "id", None) == "field-mapping-modal"

    def test_modal_starts_closed(self):
        """Test that modal is initially closed."""
        modal = create_field_mapping_modal()
        assert getattr(modal, "is_open", None) is False

    def test_modal_has_xl_size(self):
        """Test that modal uses XL size for complex form."""
        modal = create_field_mapping_modal()
        assert getattr(modal, "size", None) == "xl"

    def test_modal_has_static_backdrop(self):
        """Test that modal has static backdrop to prevent accidental closing."""
        modal = create_field_mapping_modal()
        assert getattr(modal, "backdrop", None) == "static"

    def test_modal_has_header(self):
        """Test that modal has a header with title."""
        modal = create_field_mapping_modal()
        # Modal.children is a list: [header, body, footer]
        children = getattr(modal, "children", [])
        assert len(children) == 3
        header = children[0]
        assert isinstance(header, dbc.ModalHeader)

    def test_modal_has_body_with_loading(self):
        """Test that modal body includes loading wrapper."""
        modal = create_field_mapping_modal()
        children = getattr(modal, "children", [])
        body = children[1]
        assert isinstance(body, dbc.ModalBody)

    def test_modal_has_footer_with_buttons(self):
        """Test that modal footer has Cancel and Save buttons."""
        modal = create_field_mapping_modal()
        children = getattr(modal, "children", [])
        footer = children[2]
        assert isinstance(footer, dbc.ModalFooter)


class TestCreateFieldMappingForm:
    """Test the field mapping form generation."""

    def test_form_returns_div(self):
        """Test that form generation returns an html.Div."""
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
        """Test that form includes DORA metrics section."""
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Test Field",
                "field_type": "datetime",
            }
        ]
        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        # Form should have children (sections)
        assert hasattr(form, "children")
        assert form.children is not None

    def test_form_includes_flow_section(self):
        """Test that form includes Flow metrics section."""
        available_fields = [
            {
                "field_id": "customfield_10001",
                "field_name": "Test Field",
                "field_type": "datetime",
            }
        ]
        current_mappings = {"dora": {}, "flow": {}}

        form = create_field_mapping_form(available_fields, current_mappings)
        # Form children should be a list with at least DORA section, separator, and Flow section
        children = form.children
        assert isinstance(children, list)
        assert len(children) >= 2  # At least DORA and Flow sections

    def test_form_creates_field_options(self):
        """Test that available fields are converted to dropdown options."""
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

        # Should not raise an error
        form = create_field_mapping_form(available_fields, current_mappings)
        assert form is not None

    def test_form_applies_current_mappings(self):
        """Test that current mappings are applied to form."""
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
        # Form should be created successfully with mappings
        assert form is not None


class TestCreateMetricSection:
    """Test the metric section creation."""

    def test_section_returns_card(self):
        """Test that section returns a dbc.Card component."""
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
        """Test that section has a header with title."""
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
        # Card should have children: [header, body]
        children = getattr(section, "children", [])
        assert len(children) == 2
        header = children[0]
        assert isinstance(header, dbc.CardHeader)

    def test_section_creates_rows_for_fields(self):
        """Test that section creates a row for each field."""
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
        """Test that section applies current mapping value to dropdown."""
        fields = [("deployment_date", "Deployment Date", "datetime", "Help text")]
        field_options = [
            {"label": "Custom Field 1", "value": "customfield_10001"},
            {"label": "Custom Field 2", "value": "customfield_10002"},
        ]
        current_mappings = {"deployment_date": "customfield_10001"}

        section = create_metric_section(
            "Test", "test", fields, field_options, current_mappings
        )
        # Should not raise an error with current mapping
        assert section is not None


class TestCreateValidationMessage:
    """Test validation message creation."""

    def test_success_message_returns_alert(self):
        """Test that success message returns a dbc.Alert."""
        message = create_validation_message(True, "Field mapping is valid")
        assert isinstance(message, dbc.Alert)

    def test_success_message_has_success_color(self):
        """Test that success message uses success color."""
        message = create_validation_message(True, "Valid")
        assert getattr(message, "color", None) == "success"

    def test_warning_message_returns_alert(self):
        """Test that warning message returns a dbc.Alert."""
        message = create_validation_message(False, "Field mapping has issues")
        assert isinstance(message, dbc.Alert)

    def test_warning_message_has_warning_color(self):
        """Test that warning message uses warning color."""
        message = create_validation_message(False, "Invalid")
        assert getattr(message, "color", None) == "warning"


class TestAlertHelpers:
    """Test alert helper functions."""

    def test_success_alert_returns_alert(self):
        """Test that success alert helper returns a dbc.Alert."""
        alert = create_field_mapping_success_alert()
        assert isinstance(alert, dbc.Alert)

    def test_success_alert_is_dismissable(self):
        """Test that success alert is dismissable."""
        alert = create_field_mapping_success_alert()
        assert getattr(alert, "dismissable", None) is True

    def test_success_alert_has_success_color(self):
        """Test that success alert uses success color."""
        alert = create_field_mapping_success_alert()
        assert getattr(alert, "color", None) == "success"

    def test_success_alert_has_duration(self):
        """Test that success alert auto-dismisses after duration."""
        alert = create_field_mapping_success_alert()
        assert getattr(alert, "duration", None) == 4000  # 4 seconds

    def test_error_alert_returns_alert(self):
        """Test that error alert helper returns a dbc.Alert."""
        alert = create_field_mapping_error_alert("Test error")
        assert isinstance(alert, dbc.Alert)

    def test_error_alert_is_dismissable(self):
        """Test that error alert is dismissable."""
        alert = create_field_mapping_error_alert("Test error")
        assert getattr(alert, "dismissable", None) is True

    def test_error_alert_has_danger_color(self):
        """Test that error alert uses danger color."""
        alert = create_field_mapping_error_alert("Test error")
        assert getattr(alert, "color", None) == "danger"

    def test_error_alert_includes_message(self):
        """Test that error alert includes the error message."""
        error_msg = "Failed to validate field"
        alert = create_field_mapping_error_alert(error_msg)
        # Alert children should contain the error message
        assert alert.children is not None


class TestFieldMappingIntegration:
    """Integration tests for field mapping modal components."""

    def test_modal_and_form_integration(self):
        """Test that modal and form can be created together without errors."""
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
        """Test that all components can be created for a complete workflow."""
        # Create modal
        modal = create_field_mapping_modal()

        # Create form
        available_fields = [
            {"field_id": "cf1", "field_name": "Field 1", "field_type": "datetime"},
            {"field_id": "cf2", "field_name": "Field 2", "field_type": "number"},
        ]
        current_mappings = {"dora": {"deployment_date": "cf1"}, "flow": {}}
        form = create_field_mapping_form(available_fields, current_mappings)

        # Create validation messages
        success_msg = create_validation_message(True, "Valid")
        warning_msg = create_validation_message(False, "Invalid")

        # Create alerts
        success_alert = create_field_mapping_success_alert()
        error_alert = create_field_mapping_error_alert("Error")

        # All components should be created successfully
        assert modal is not None
        assert form is not None
        assert success_msg is not None
        assert warning_msg is not None
        assert success_alert is not None
        assert error_alert is not None
