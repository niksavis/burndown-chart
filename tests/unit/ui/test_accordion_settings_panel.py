import dash_bootstrap_components as dbc
from dash import html


class TestAccordionSettingsPanel:
    def test_accordion_panel_creates_successfully(self, temp_database):
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()

        assert panel is not None
        assert isinstance(panel, html.Div)

    def test_accordion_has_five_sections(self, temp_database):
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()

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

        assert hasattr(accordion, "children")
        sections = accordion.children
        assert isinstance(sections, list)
        assert len(sections) == 5

    def test_section_titles_correct(self, temp_database):
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()
        panel_str = str(panel)

        assert "1. Profile Settings" in panel_str or "Profile Settings" in panel_str
        assert "2. JIRA Configuration" in panel_str or "JIRA Configuration" in panel_str
        assert "3. Field Mappings" in panel_str or "Field Mappings" in panel_str
        assert "4. Query Management" in panel_str or "Query Management" in panel_str
        assert "5. Data Operations" in panel_str or "Data Operations" in panel_str

    def test_profile_settings_card_present(self, temp_database):
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()
        panel_str = str(panel)

        assert "profile-selector" in panel_str
        assert "create-profile-btn" in panel_str
        assert "Profile Management" in panel_str

    def test_configuration_status_store_present(self, temp_database):
        from ui.accordion_settings_panel import create_accordion_settings_panel

        panel = create_accordion_settings_panel()
        panel_str = str(panel)

        assert "configuration-status-store" in panel_str


class TestProfileSettingsCard:
    def test_profile_settings_card_creates(self, temp_database):
        from ui.profile_settings_card import create_profile_settings_card

        card = create_profile_settings_card()

        assert card is not None
        assert isinstance(card, html.Div)

    def test_profile_settings_has_all_inputs(self, temp_database):
        from ui.profile_settings_card import create_profile_settings_card

        card = create_profile_settings_card()
        card_str = str(card)

        assert "profile-selector" in card_str
        assert "create-profile-btn" in card_str
        assert "duplicate-profile-btn" in card_str
        assert "delete-profile-btn" in card_str

    def test_profile_settings_has_labels(self, temp_database):
        from ui.profile_settings_card import create_profile_settings_card

        card = create_profile_settings_card()
        card_str = str(card)

        assert "Profile Management" in card_str
        assert "Profile" in card_str
        assert "Duplicate" in card_str


class TestAccordionCardComponents:
    def test_jira_config_card_creates(self):
        from ui.accordion_settings_panel import create_jira_config_card

        card = create_jira_config_card()
        assert card is not None

    def test_field_mapping_card_creates(self):
        from ui.accordion_settings_panel import create_field_mapping_card

        card = create_field_mapping_card()
        assert card is not None

    def test_query_management_card_creates(self):
        from ui.accordion_settings_panel import create_query_management_card

        card = create_query_management_card()
        assert card is not None

    def test_data_operations_card_creates(self):
        from ui.accordion_settings_panel import create_data_operations_card

        card = create_data_operations_card()
        assert card is not None


class TestLayoutIntegration:
    def test_layout_uses_accordion_panel_when_enabled(self, temp_database):
        import ui.layout

        original_flag = ui.layout.USE_ACCORDION_SETTINGS
        ui.layout.USE_ACCORDION_SETTINGS = True

        try:
            from ui.layout import serve_layout

            layout = serve_layout()
            layout_str = str(layout)

            assert "profile-selector" in layout_str
            assert "Profile Management" in layout_str or "profile" in layout_str.lower()

        finally:
            ui.layout.USE_ACCORDION_SETTINGS = original_flag

    def test_layout_creates_with_both_panels(self, temp_database):
        import ui.layout
        from ui.layout import serve_layout

        ui.layout.USE_ACCORDION_SETTINGS = True
        layout_new = serve_layout()
        assert layout_new is not None

        ui.layout.USE_ACCORDION_SETTINGS = False
        layout_old = serve_layout()
        assert layout_old is not None
