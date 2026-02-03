"""
Unit tests for UI components - specifically input field builders.

Tests the contract-compliant input field builders added in Phase 2.
"""

import pytest
from dash import html
import dash_bootstrap_components as dbc
from ui.form_components import create_input_field, create_labeled_input


class TestCreateInputField:
    """Test create_input_field function following component contracts."""

    def test_create_input_basic(self):
        """Test input field creation with minimal parameters."""
        field = create_input_field("Username")

        # Should return a Div
        assert isinstance(field, html.Div)
        # Should have 2 children: label and input
        assert len(field.children) == 2  # type: ignore[attr-defined]

        label = field.children[0]  # type: ignore[index]
        input_elem = field.children[1]  # type: ignore[index]

        assert isinstance(label, dbc.Label)
        assert isinstance(input_elem, dbc.Input)
        assert input_elem.id == "input-username"  # type: ignore[attr-defined]
        assert input_elem.type == "text"  # type: ignore[attr-defined]

    def test_create_input_with_type(self):
        """Test input field with different input types."""
        types_to_test = ["text", "number", "date", "email", "password"]

        for input_type in types_to_test:
            field = create_input_field("Test Field", input_type=input_type)
            input_elem = field.children[1]  # type: ignore[index]
            assert input_elem.type == input_type  # type: ignore[attr-defined]

    def test_create_input_with_custom_id(self):
        """Test input field with custom ID."""
        field = create_input_field("Test", input_id="custom-id")
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.id == "custom-id"  # type: ignore[attr-defined]

    def test_create_input_id_slugification(self):
        """Test that label is properly slugified for ID."""
        field = create_input_field("PERT Factor")
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.id == "input-pert-factor"  # type: ignore[attr-defined]

        field = create_input_field("Start Date (Optional)")
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.id == "input-start-date-optional"  # type: ignore[attr-defined]

    def test_create_input_with_placeholder(self):
        """Test input field with placeholder."""
        field = create_input_field("Email", placeholder="user@example.com")
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.placeholder == "user@example.com"  # type: ignore[attr-defined]

    def test_create_input_with_value(self):
        """Test input field with initial value."""
        field = create_input_field("PERT Factor", value=1.5)
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.value == 1.5  # type: ignore[attr-defined]

    def test_create_input_required(self):
        """Test required input field."""
        field = create_input_field("Username", required=True)

        label = field.children[0]  # type: ignore[index]
        input_elem = field.children[1]  # type: ignore[index]

        # Label should include required indicator (*)
        assert isinstance(label.children, list)  # type: ignore[attr-defined]

        # Input should have required=True (dbc.Input handles aria-required internally)
        assert input_elem.required is True  # type: ignore[attr-defined]

    def test_create_input_sizes(self):
        """Test input field sizes."""
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            field = create_input_field("Test", size=size)
            input_elem = field.children[1]  # type: ignore[index]
            assert input_elem.size == size  # type: ignore[attr-defined]

    def test_create_input_with_kwargs(self):
        """Test input field with additional kwargs."""
        field = create_input_field(
            "Amount", input_type="number", min=0, max=100, step=0.1, disabled=True
        )
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.min == 0  # type: ignore[attr-defined]
        assert input_elem.max == 100  # type: ignore[attr-defined]
        assert input_elem.step == 0.1  # type: ignore[attr-defined]
        assert input_elem.disabled is True  # type: ignore[attr-defined]

    def test_create_input_empty_label_raises_error(self):
        """Test that empty label raises ValueError."""
        with pytest.raises(ValueError, match="Label is required"):
            create_input_field("")

        with pytest.raises(ValueError, match="Label is required"):
            create_input_field("   ")

    def test_create_input_invalid_type_raises_error(self):
        """Test that invalid input type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid input_type"):
            create_input_field("Test", input_type="invalid")

    def test_create_input_label_association(self):
        """Test that label is properly associated with input."""
        field = create_input_field("Username")

        label = field.children[0]  # type: ignore[index]
        input_elem = field.children[1]  # type: ignore[index]

        # Label htmlFor should match input id
        assert label.html_for == input_elem.id  # type: ignore[attr-defined]


class TestCreateLabeledInput:
    """Test create_labeled_input function following component contracts."""

    def test_create_labeled_input_basic(self):
        """Test labeled input creation with minimal parameters."""
        field = create_labeled_input("Username", "username-input")

        assert isinstance(field, html.Div)
        # Should have at least 2 children: label and input
        assert len(field.children) >= 2  # type: ignore[attr-defined]

    def test_create_labeled_input_with_help_text(self):
        """Test labeled input with help text."""
        field = create_labeled_input(
            "PERT Factor", "pert-input", help_text="Typically 1.5-2.0"
        )

        # Should have 3 children: label, input, help text
        assert len(field.children) == 3  # type: ignore[attr-defined]

        help_text_elem = field.children[2]  # type: ignore[index]
        assert isinstance(help_text_elem, dbc.FormText)

    def test_create_labeled_input_with_error(self):
        """Test labeled input with error message."""
        field = create_labeled_input(
            "Email", "email-input", error_message="Invalid email format", invalid=True
        )

        # Should have 3 children: label, input, error feedback
        assert len(field.children) == 3  # type: ignore[attr-defined]

        error_elem = field.children[2]  # type: ignore[index]
        assert isinstance(error_elem, dbc.FormFeedback)

    def test_create_labeled_input_with_help_and_error(self):
        """Test labeled input with both help text and error message."""
        field = create_labeled_input(
            "Email",
            "email-input",
            help_text="Enter your email address",
            error_message="Invalid email format",
            invalid=True,
        )

        # Should have 4 children: label, input, help text, error feedback
        assert len(field.children) == 4  # type: ignore[attr-defined]

    def test_create_labeled_input_empty_label_raises_error(self):
        """Test that empty label raises ValueError."""
        with pytest.raises(ValueError, match="Label is required"):
            create_labeled_input("", "test-input")

    def test_create_labeled_input_empty_id_raises_error(self):
        """Test that empty input_id raises ValueError."""
        with pytest.raises(ValueError, match="input_id is required"):
            create_labeled_input("Test", "")

    def test_create_labeled_input_invalid_type_raises_error(self):
        """Test that invalid input type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid input_type"):
            create_labeled_input("Test", "test-input", input_type="invalid")

    def test_create_labeled_input_accessibility(self):
        """Test accessibility features."""
        field = create_labeled_input(
            "Email",
            "email-input",
            help_text="Enter your email",
            error_message="Invalid email",
            invalid=True,
        )

        # Input should have invalid=True (dbc.Input handles aria-invalid internally)
        input_elem = field.children[1]  # type: ignore[index]
        assert input_elem.invalid is True  # type: ignore[attr-defined]

        # Help text and error should be present in the field
        assert len(field.children) == 4  # type: ignore[attr-defined] (label, input, help, error)


class TestInputFieldIntegration:
    """Integration tests for input fields."""

    def test_input_field_in_form(self):
        """Test input fields work in a form."""
        username = create_input_field("Username", required=True)
        email = create_labeled_input("Email", "email-input", input_type="email")

        form = html.Form([username, email])

        assert len(form.children) == 2  # type: ignore[attr-defined]

    def test_input_field_validation_states(self):
        """Test input fields with validation states."""
        valid_field = create_input_field("Username", valid=True)
        invalid_field = create_input_field("Email", invalid=True)

        # Both should create without errors
        assert isinstance(valid_field, html.Div)
        assert isinstance(invalid_field, html.Div)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
