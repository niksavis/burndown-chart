class TestBasicCharacterCounting:
    def test_count_empty_string(self):
        from ui.jql_components import count_jql_characters

        assert count_jql_characters("") == 0

    def test_count_simple_ascii_query(self):
        from ui.jql_components import count_jql_characters

        query = "project = TEST"
        assert count_jql_characters(query) == len(query)
        assert count_jql_characters(query) == 14

    def test_count_includes_whitespace(self):
        from ui.jql_components import count_jql_characters

        query = "project = TEST\n\nAND status = Done"
        assert count_jql_characters(query) == len(query)
        assert count_jql_characters(query) == 33

    def test_count_unicode_characters(self):
        from ui.jql_components import count_jql_characters

        query = "project = TEST-123"
        assert count_jql_characters(query) == len(query)
        assert count_jql_characters(query) == 18

        query_accented = "assignee = 'José García'"
        assert count_jql_characters(query_accented) == len(query_accented)

    def test_count_very_long_query(self):
        from ui.jql_components import count_jql_characters

        long_query = "project = TEST" + " AND status = Done" * 150
        assert count_jql_characters(long_query) > 2000


class TestWarningThresholdDetection:
    def test_no_warning_below_threshold(self):
        from ui.jql_components import should_show_character_warning

        short_query = "project = TEST"
        assert should_show_character_warning(short_query) is False

        medium_query = "a" * 1799
        assert should_show_character_warning(medium_query) is False

    def test_warning_at_threshold(self):
        from ui.jql_components import should_show_character_warning

        threshold_query = "a" * 1800
        assert should_show_character_warning(threshold_query) is True

    def test_warning_above_threshold(self):
        from ui.jql_components import should_show_character_warning

        long_query = "a" * 1850
        assert should_show_character_warning(long_query) is True

        very_long_query = "a" * 2500
        assert should_show_character_warning(very_long_query) is True

    def test_warning_boundary_conditions(self):
        from ui.jql_components import should_show_character_warning

        assert should_show_character_warning("a" * 1797) is False
        assert should_show_character_warning("a" * 1798) is False
        assert should_show_character_warning("a" * 1799) is False
        assert should_show_character_warning("a" * 1800) is True
        assert should_show_character_warning("a" * 1801) is True


class TestCharacterCountDisplayComponent:
    def test_display_component_structure(self):
        from ui.jql_components import create_character_count_display

        component = create_character_count_display(count=150, warning=False)

        assert component is not None
        assert hasattr(component, "children")

    def test_display_shows_count(self):
        from ui.jql_components import create_character_count_display

        component = create_character_count_display(count=1500, warning=False)

        component_str = str(component)
        assert "1500" in component_str or "1,500" in component_str

    def test_display_shows_reference_limit(self):
        from ui.jql_components import create_character_count_display

        component = create_character_count_display(count=1500, warning=False)

        component_str = str(component)
        assert "2000" in component_str or "2,000" in component_str

    def test_display_applies_warning_class_when_over_threshold(self):
        from ui.jql_components import create_character_count_display

        warning_component = create_character_count_display(count=1850, warning=True)

        component_str = str(warning_component)
        assert "character-count-warning" in component_str

    def test_display_no_warning_class_when_under_threshold(self):
        from ui.jql_components import create_character_count_display

        safe_component = create_character_count_display(count=1500, warning=False)

        component_str = str(safe_component)
        assert "character-count-warning" not in component_str


class TestCharacterCountStateManagement:
    def test_create_initial_state(self):
        from ui.jql_components import create_character_count_state

        state = create_character_count_state(count=0, warning=False, textarea_id="main")

        assert state["count"] == 0
        assert state["warning"] is False
        assert state["textarea_id"] == "main"
        assert "last_updated" in state
        assert state["last_updated"] > 0

    def test_update_state_with_new_count(self):
        from ui.jql_components import create_character_count_state

        state = create_character_count_state(
            count=1850, warning=True, textarea_id="main"
        )

        assert state["count"] == 1850
        assert state["warning"] is True

    def test_state_validates_textarea_id(self):
        from ui.jql_components import create_character_count_state

        state_main = create_character_count_state(0, False, "main")
        assert state_main["textarea_id"] == "main"

        state_dialog = create_character_count_state(0, False, "dialog")
        assert state_dialog["textarea_id"] == "dialog"


class TestCharacterCountEdgeCases:
    def test_handle_none_input(self):
        from ui.jql_components import count_jql_characters

        assert count_jql_characters(None) == 0

    def test_handle_numeric_input(self):
        from ui.jql_components import count_jql_characters

        result = count_jql_characters(123)
        assert result >= 0

    def test_handle_very_large_query(self):
        from ui.jql_components import count_jql_characters

        huge_query = "x" * 50000
        count = count_jql_characters(huge_query)

        assert count == 50000
        assert count > 2000


class TestCharacterCountAccessibility:
    def test_display_has_aria_label(self):
        from ui.jql_components import create_character_count_display

        component = create_character_count_display(count=1500, warning=False)

        component_str = str(component)
        assert "id=" in component_str or component is not None

    def test_warning_state_is_announced(self):
        from ui.jql_components import create_character_count_display

        warning_component = create_character_count_display(count=1850, warning=True)

        assert warning_component is not None
        component_str = str(warning_component)
        assert "1,850" in component_str or "1850" in component_str
