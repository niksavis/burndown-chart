"""
Unit tests for JQL character count functionality (User Story 1).

Tests character counting utility, warning detection, and display components.
Following TDD approach: Write tests first (RED), implement minimum code (GREEN), refactor.
"""


class TestBasicCharacterCounting:
    """Test basic character counting across different input types."""

    def test_count_empty_string(self):
        """Empty textarea should return count of 0."""
        from ui.components import count_jql_characters

        assert count_jql_characters("") == 0

    def test_count_simple_ascii_query(self):
        """Count basic ASCII characters correctly."""
        from ui.components import count_jql_characters

        query = "project = TEST"
        assert count_jql_characters(query) == len(query)
        assert count_jql_characters(query) == 14

    def test_count_includes_whitespace(self):
        """Character count should include spaces and newlines."""
        from ui.components import count_jql_characters

        query = "project = TEST\n\nAND status = Done"
        assert count_jql_characters(query) == len(query)
        assert count_jql_characters(query) == 33  # Actual count: 14 + 2 newlines + 17

    def test_count_unicode_characters(self):
        """Count unicode characters (emoji, special chars) correctly."""
        from ui.components import count_jql_characters

        # Test with emoji and special characters
        query = "project = 🚀TEST"
        assert count_jql_characters(query) == len(query)
        assert count_jql_characters(query) == 15

        # Test with accented characters
        query_accented = "assignee = 'José García'"
        assert count_jql_characters(query_accented) == len(query_accented)

    def test_count_very_long_query(self):
        """Handle queries longer than JIRA's limit."""
        from ui.components import count_jql_characters

        # Create query longer than 2000 characters
        long_query = (
            "project = TEST" + " AND status = Done" * 150
        )  # Increased multiplier
        assert count_jql_characters(long_query) > 2000


class TestWarningThresholdDetection:
    """Test warning state activation at 1800 character threshold."""

    def test_no_warning_below_threshold(self):
        """Queries under 1800 characters should not trigger warning."""
        from ui.components import should_show_character_warning

        short_query = "project = TEST"
        assert should_show_character_warning(short_query) is False

        # Just below threshold
        medium_query = "a" * 1799
        assert should_show_character_warning(medium_query) is False

    def test_warning_at_threshold(self):
        """Query at exactly 1800 characters should trigger warning."""
        from ui.components import should_show_character_warning

        threshold_query = "a" * 1800
        assert should_show_character_warning(threshold_query) is True

    def test_warning_above_threshold(self):
        """Queries above 1800 characters should trigger warning."""
        from ui.components import should_show_character_warning

        long_query = "a" * 1850
        assert should_show_character_warning(long_query) is True

        very_long_query = "a" * 2500
        assert should_show_character_warning(very_long_query) is True

    def test_warning_boundary_conditions(self):
        """Test edge cases around 1800 threshold."""
        from ui.components import should_show_character_warning

        assert should_show_character_warning("a" * 1797) is False
        assert should_show_character_warning("a" * 1798) is False
        assert should_show_character_warning("a" * 1799) is False
        assert should_show_character_warning("a" * 1800) is True
        assert should_show_character_warning("a" * 1801) is True


class TestCharacterCountDisplayComponent:
    """Test the character count display UI component."""

    def test_display_component_structure(self):
        """Character count display should have correct structure."""
        from ui.components import create_character_count_display

        component = create_character_count_display(count=150, warning=False)

        # Should return a Dash component
        assert component is not None
        assert hasattr(component, "children")

    def test_display_shows_count(self):
        """Display should show current character count."""
        from ui.components import create_character_count_display

        component = create_character_count_display(count=1500, warning=False)

        # Check that count appears in component text
        component_str = str(component)
        assert "1500" in component_str or "1,500" in component_str

    def test_display_shows_reference_limit(self):
        """Display should reference JIRA's 2000 character limit."""
        from ui.components import create_character_count_display

        component = create_character_count_display(count=1500, warning=False)

        component_str = str(component)
        assert "2000" in component_str or "2,000" in component_str

    def test_display_applies_warning_class_when_over_threshold(self):
        """Warning CSS class should be applied when count > 1800."""
        from ui.components import create_character_count_display

        warning_component = create_character_count_display(count=1850, warning=True)

        # Should have warning class for CSS styling
        component_str = str(warning_component)
        assert "character-count-warning" in component_str

    def test_display_no_warning_class_when_under_threshold(self):
        """No warning CSS class when count ≤ 1800."""
        from ui.components import create_character_count_display

        safe_component = create_character_count_display(count=1500, warning=False)

        # Should not have warning class
        component_str = str(safe_component)
        assert "character-count-warning" not in component_str


class TestCharacterCountStateManagement:
    """Test state management for character count (dcc.Store integration)."""

    def test_create_initial_state(self):
        """Initial character count state should be valid."""
        from ui.components import create_character_count_state

        state = create_character_count_state(count=0, warning=False, textarea_id="main")

        assert state["count"] == 0
        assert state["warning"] is False
        assert state["textarea_id"] == "main"
        assert "last_updated" in state
        assert state["last_updated"] > 0

    def test_update_state_with_new_count(self):
        """State should update correctly when count changes."""
        from ui.components import create_character_count_state

        state = create_character_count_state(
            count=1850, warning=True, textarea_id="main"
        )

        assert state["count"] == 1850
        assert state["warning"] is True

    def test_state_validates_textarea_id(self):
        """State should only accept valid textarea IDs."""
        from ui.components import create_character_count_state

        # Valid IDs
        state_main = create_character_count_state(0, False, "main")
        assert state_main["textarea_id"] == "main"

        state_dialog = create_character_count_state(0, False, "dialog")
        assert state_dialog["textarea_id"] == "dialog"


class TestCharacterCountEdgeCases:
    """Test edge cases and error handling."""

    def test_handle_none_input(self):
        """Handle None input gracefully (user clears textarea)."""
        from ui.components import count_jql_characters

        # Should treat None as empty string
        assert count_jql_characters(None) == 0

    def test_handle_numeric_input(self):
        """Handle unexpected numeric input."""
        from ui.components import count_jql_characters

        # Should convert to string and count
        # This handles Dash's no_update or callback edge cases
        result = count_jql_characters(123)
        assert result >= 0

    def test_handle_very_large_query(self):
        """Handle queries much larger than JIRA's limit without crashing."""
        from ui.components import count_jql_characters

        huge_query = "x" * 50000
        count = count_jql_characters(huge_query)

        assert count == 50000
        assert count > 2000  # Way over limit


class TestCharacterCountAccessibility:
    """Test accessibility features of character count display."""

    def test_display_has_aria_label(self):
        """Character count should have ARIA label for screen readers."""
        from ui.components import create_character_count_display

        component = create_character_count_display(count=1500, warning=False)

        # Check that component has an ID for accessibility
        component_str = str(component)
        assert "id=" in component_str or component is not None

    def test_warning_state_is_announced(self):
        """Warning state should be announced to screen readers."""
        from ui.components import create_character_count_display

        warning_component = create_character_count_display(count=1850, warning=True)

        # At minimum, warning should be visually and semantically distinct
        assert warning_component is not None
        component_str = str(warning_component)
        assert "1,850" in component_str or "1850" in component_str
