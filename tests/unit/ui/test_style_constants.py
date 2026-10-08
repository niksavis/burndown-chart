import pytest

from ui.style_constants import (
    DESIGN_TOKENS,
    get_button_style,
    get_card_style,
    get_color,
    get_responsive_cols,
    get_spacing,
)


class TestDesignTokens:
    def test_design_tokens_structure(self):
        assert "colors" in DESIGN_TOKENS
        assert "spacing" in DESIGN_TOKENS
        assert "typography" in DESIGN_TOKENS
        assert "layout" in DESIGN_TOKENS
        assert "animation" in DESIGN_TOKENS
        assert "breakpoints" in DESIGN_TOKENS
        assert "components" in DESIGN_TOKENS
        assert "mobile" in DESIGN_TOKENS

    def test_color_tokens(self):
        colors = DESIGN_TOKENS["colors"]
        assert colors["primary"] == "#0d6efd"
        assert colors["success"] == "#198754"
        assert colors["danger"] == "#dc3545"
        assert colors["white"] == "#ffffff"

    def test_spacing_tokens(self):
        spacing = DESIGN_TOKENS["spacing"]
        assert spacing["xs"] == "0.25rem"
        assert spacing["sm"] == "0.5rem"
        assert spacing["md"] == "1rem"
        assert spacing["lg"] == "1.5rem"

    def test_typography_tokens(self):
        typography = DESIGN_TOKENS["typography"]
        assert "fontFamily" in typography
        assert "size" in typography
        assert "weight" in typography
        assert typography["size"]["base"] == "1rem"
        assert typography["weight"]["bold"] == 700

    def test_layout_tokens(self):
        layout = DESIGN_TOKENS["layout"]
        assert "borderRadius" in layout
        assert "shadow" in layout
        assert "zIndex" in layout
        assert layout["borderRadius"]["md"] == "0.375rem"
        assert layout["zIndex"]["sticky"] == 1020

    def test_component_tokens(self):
        components = DESIGN_TOKENS["components"]
        assert "button" in components
        assert "card" in components
        assert "input" in components
        assert "tab" in components
        assert components["button"]["minWidth"] == "44px"
        assert components["button"]["minHeight"] == "44px"

    def test_mobile_tokens(self):
        mobile = DESIGN_TOKENS["mobile"]
        assert mobile["touchTargetMin"] == "44px"
        assert "bottomSheetMaxHeight" in mobile
        assert "navBarHeight" in mobile


class TestDesignTokenHelpers:
    def test_get_color_valid(self):
        assert get_color("primary") == "#0d6efd"
        assert get_color("success") == "#198754"
        assert get_color("white") == "#ffffff"

    def test_get_color_invalid(self):
        assert get_color("nonexistent") == "#0d6efd"

    def test_get_spacing_valid(self):
        assert get_spacing("xs") == "0.25rem"
        assert get_spacing("md") == "1rem"
        assert get_spacing("xl") == "2rem"

    def test_get_spacing_invalid(self):
        assert get_spacing("nonexistent") == "1rem"

    def test_get_card_style_default(self):
        style = get_card_style()
        assert "borderRadius" in style
        assert "padding" in style
        assert "boxShadow" in style
        assert style["borderRadius"] == "0.375rem"

    def test_get_card_style_elevated(self):
        style_default = get_card_style(elevated=False)
        style_elevated = get_card_style(elevated=True)
        assert style_default["boxShadow"] != style_elevated["boxShadow"]

    def test_get_card_style_variant(self):
        style = get_card_style(variant="primary")
        assert "backgroundColor" in style
        assert style["backgroundColor"] == "#0d6efd"

    def test_get_button_style_default(self):
        style = get_button_style()
        assert "padding" in style
        assert "fontSize" in style
        assert "borderRadius" in style
        assert "minWidth" in style
        assert "minHeight" in style
        assert style["minWidth"] == "44px"
        assert style["minHeight"] == "44px"

    def test_get_button_style_sizes(self):
        sm_style = get_button_style(size="sm")
        md_style = get_button_style(size="md")
        lg_style = get_button_style(size="lg")

        assert sm_style["minWidth"] == "44px"
        assert md_style["minWidth"] == "44px"
        assert lg_style["minWidth"] == "44px"

        assert sm_style["fontSize"] == "0.875rem"
        assert md_style["fontSize"] == "1rem"
        assert lg_style["fontSize"] == "1.125rem"

    def test_get_responsive_cols_default(self):
        cols = get_responsive_cols()
        assert cols["xs"] == 12
        assert cols["md"] == 6
        assert cols["lg"] == 4

    def test_get_responsive_cols_custom(self):
        cols = get_responsive_cols(mobile=12, tablet=4, desktop=3)
        assert cols["xs"] == 12
        assert cols["md"] == 4
        assert cols["lg"] == 3


class TestBackwardCompatibility:
    def test_existing_color_constants(self):
        from ui.style_constants import NEUTRAL_COLORS, PRIMARY_COLORS, SEMANTIC_COLORS

        assert "primary" in PRIMARY_COLORS
        assert "success" in SEMANTIC_COLORS
        assert "white" in NEUTRAL_COLORS

    def test_existing_typography_constants(self):
        from ui.style_constants import TYPOGRAPHY

        assert "font_family" in TYPOGRAPHY
        assert "scale" in TYPOGRAPHY
        assert "weights" in TYPOGRAPHY

    def test_existing_helper_functions(self):
        from ui.style_constants import (
            darken_color,
            hex_to_rgb,
            lighten_color,
            rgb_to_rgba,
        )

        assert hex_to_rgb("#ff0000") == "rgb(255, 0, 0)"

        assert rgb_to_rgba("rgb(255, 0, 0)", 0.5) == "rgba(255, 0, 0, 0.5)"

        lightened = lighten_color("#000000", 0.1)
        assert lightened.startswith("rgb(")

        darkened = darken_color("#ffffff", 0.1)
        assert darkened.startswith("rgb(")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
