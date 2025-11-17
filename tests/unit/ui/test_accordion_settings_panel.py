"""
Unit tests for accordion-based settings panel.

Tests verify that:
1. Accordion panel renders with all 5 sections
2. Profile section is enabled by default
3. Sections have correct titles and structure
4. All required components are present
"""

from dash import html
import dash_bootstrap_components as dbc


class TestAccordionSettingsPanel:
    """Test accordion settings panel structure."""

    def test_accordion_panel_creates_successfully(self):
        """Verify accordion panel renders without errors."""
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()

        assert panel is not None
        assert isinstance(panel, html.Div)

    def test_accordion_has_five_sections(self):
        """Verify accordion contains all 5 required sections."""
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()

        # Find accordion component in panel
        def find_accordion(component):
            if isinstance(component, dbc.Accordion):
                return component
            if hasattr(component, "children"):
                if isinstance(component.children, list):
                    for child in component.children:
                        result = find_accordion(child)
                        if result:
                            return result
                else:
                    return find_accordion(component.children)
            return None

        accordion = find_accordion(panel)
        assert accordion is not None

        # Verify accordion has children (sections)
        assert hasattr(accordion, "children")
        sections = accordion.children
        assert isinstance(sections, list)
        assert len(sections) == 5  # 5 sections

    def test_section_titles_correct(self):
        """Verify each section has correct title."""
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()
        panel_str = str(panel)

        # Check for section titles (emoji + text)
        assert "1️⃣ Profile Settings" in panel_str or "Profile Settings" in panel_str
        assert "2️⃣ JIRA Configuration" in panel_str or "JIRA Configuration" in panel_str
        assert "3️⃣ Field Mappings" in panel_str or "Field Mappings" in panel_str
        assert "4️⃣ Query Management" in panel_str or "Query Management" in panel_str
        assert "5️⃣ Data Operations" in panel_str or "Data Operations" in panel_str

    def test_profile_settings_card_present(self):
        """Verify profile settings card is included."""
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()
        panel_str = str(panel)

        # Check for profile settings components (profile management only)
        assert "profile-selector" in panel_str
        assert "create-profile-btn" in panel_str
        assert "Profile Management" in panel_str
        # Note: PERT factor/deadline are in Parameters panel, not Profile Settings

    def test_configuration_status_store_present(self):
        """Verify configuration status store exists for dependency tracking."""
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()
        panel_str = str(panel)

        assert "configuration-status-store" in panel_str


class TestProfileSettingsCard:
    """Test profile settings card component."""

    def test_profile_settings_card_creates(self):
        """Verify profile settings card renders."""
        from ui.profile_settings_card import create_profile_settings_card

        card = create_profile_settings_card()

        assert card is not None
        # Returns Div wrapper, not Card directly
        assert isinstance(card, html.Div)

    def test_profile_settings_has_all_inputs(self):
        """Verify all required inputs are present."""
        from ui.profile_settings_card import create_profile_settings_card

        card = create_profile_settings_card()
        card_str = str(card)

        # Profile management inputs (PERT/deadline are in Parameters panel)
        assert "profile-selector" in card_str
        assert "create-profile-btn" in card_str
        assert "duplicate-profile-btn" in card_str
        assert "delete-profile-btn" in card_str

    def test_profile_settings_has_labels(self):
        """Verify all labels are present."""
        from ui.profile_settings_card import create_profile_settings_card

        card = create_profile_settings_card()
        card_str = str(card)

        # Profile management labels
        assert "Profile Management" in card_str
        assert "Profile" in card_str  # Profile selector label
        assert "New" in card_str  # Create new profile button
        assert "Duplicate" in card_str  # Duplicate profile button


class TestAccordionCardComponents:
    """Test individual card components."""

    def test_jira_config_card_creates(self):
        """Verify JIRA config card renders."""
        from ui.accordion_settings_panel import create_jira_config_card

        card = create_jira_config_card()
        assert card is not None

    def test_field_mapping_card_creates(self):
        """Verify field mapping card renders."""
        from ui.accordion_settings_panel import create_field_mapping_card

        card = create_field_mapping_card()
        assert card is not None

    def test_query_management_card_creates(self):
        """Verify query management card renders."""
        from ui.accordion_settings_panel import create_query_management_card

        card = create_query_management_card()
        assert card is not None

    def test_data_operations_card_creates(self):
        """Verify data operations card renders."""
        from ui.accordion_settings_panel import create_data_operations_card

        card = create_data_operations_card()
        assert card is not None


class TestLayoutIntegration:
    """Test accordion panel integration with main layout."""

    def test_layout_uses_accordion_panel_when_enabled(self):
        """Verify layout uses accordion panel when feature flag enabled."""
        import ui.layout

        # Temporarily enable accordion panel
        original_flag = ui.layout.USE_ACCORDION_SETTINGS
        ui.layout.USE_ACCORDION_SETTINGS = True

        try:
            from ui.layout import serve_layout

            layout = serve_layout()
            layout_str = str(layout)

            # Check for profile management components
            assert "profile-selector" in layout_str  # Profile dropdown present
            assert (
                "Profile Management" in layout_str or "profile" in layout_str.lower()
            )  # Profile section exists

        finally:
            # Restore original flag
            ui.layout.USE_ACCORDION_SETTINGS = original_flag

    def test_layout_creates_with_both_panels(self):
        """Verify layout works with both old and new panel."""
        import ui.layout
        from ui.layout import serve_layout

        # Test with accordion panel
        ui.layout.USE_ACCORDION_SETTINGS = True
        layout_new = serve_layout()
        assert layout_new is not None

        # Test with improved panel (original)
        ui.layout.USE_ACCORDION_SETTINGS = False
        layout_old = serve_layout()
        assert layout_old is not None
