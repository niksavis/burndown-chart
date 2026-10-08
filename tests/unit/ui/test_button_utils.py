import dash_bootstrap_components as dbc
import pytest
from dash import html

from ui.button_utils import create_action_button


class TestCreateActionButton:
    def test_create_button_basic(self):
        btn = create_action_button("Save")

        assert btn.id == "btn-save"  # type: ignore[attr-defined]
        assert btn.color == "primary"  # type: ignore[attr-defined]
        assert btn.size == "md"  # type: ignore[attr-defined]
        assert btn.title == "Save"  # type: ignore[attr-defined]

    def test_create_button_with_icon(self):
        btn = create_action_button("Delete", icon="trash")

        assert btn.id == "btn-delete"  # type: ignore[attr-defined]
        children = btn.children  # type: ignore[attr-defined]
        assert isinstance(children, list)
        assert len(children) == 2
        assert isinstance(children[0], html.I)
        assert "fa-trash" in children[0].className  # type: ignore[attr-defined]
        assert children[1] == "Delete"

    def test_create_button_with_icon_prefix(self):
        btn = create_action_button("Save", icon="fas fa-save")

        children = btn.children  # type: ignore[attr-defined]
        assert isinstance(children[0], html.I)  # type: ignore[index]
        assert "fas fa-save" in children[0].className  # type: ignore[index,attr-defined]

    def test_create_button_variants(self):
        variants = [
            "primary",
            "secondary",
            "success",
            "danger",
            "warning",
            "info",
            "light",
            "dark",
            "link",
        ]

        for variant in variants:
            btn = create_action_button("Test", variant=variant)
            assert btn.color == variant  # type: ignore[attr-defined]

    def test_create_button_sizes(self):
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            btn = create_action_button("Test", size=size)
            assert btn.size == size  # type: ignore[attr-defined]
            assert "minWidth" in btn.style  # type: ignore[attr-defined]
            assert "minHeight" in btn.style  # type: ignore[attr-defined]
            assert btn.style["minWidth"] == "44px"  # type: ignore[attr-defined]
            assert btn.style["minHeight"] == "44px"  # type: ignore[attr-defined]

    def test_create_button_with_id_suffix(self):
        btn = create_action_button("Submit", id_suffix="form-1")
        assert btn.id == "btn-submit-form-1"  # type: ignore[attr-defined]

        btn = create_action_button("Submit", id_suffix="modal")
        assert btn.id == "btn-submit-modal"  # type: ignore[attr-defined]

    def test_create_button_id_slugification(self):
        btn = create_action_button("Save Changes")
        assert btn.id == "btn-save-changes"  # type: ignore[attr-defined]

        btn = create_action_button("Delete All Items")
        assert btn.id == "btn-delete-all-items"  # type: ignore[attr-defined]

        btn = create_action_button("Log In")
        assert btn.id == "btn-log-in"  # type: ignore[attr-defined]

    def test_create_button_with_kwargs(self):
        btn = create_action_button(
            "Submit", disabled=True, className="custom-class", n_clicks=0
        )

        assert btn.disabled is True  # type: ignore[attr-defined]
        assert "custom-class" in btn.className  # type: ignore[attr-defined]
        assert btn.n_clicks == 0  # type: ignore[attr-defined]

    def test_create_button_with_custom_style(self):
        custom_style = {"backgroundColor": "red", "border": "2px solid black"}
        btn = create_action_button("Test", style=custom_style)

        assert "backgroundColor" in btn.style  # type: ignore[attr-defined]
        assert btn.style["backgroundColor"] == "red"  # type: ignore[attr-defined]
        assert "minWidth" in btn.style  # type: ignore[attr-defined]
        assert "minHeight" in btn.style  # type: ignore[attr-defined]

    def test_create_button_with_custom_aria_label(self):
        btn = create_action_button("X", aria_label="Close dialog")

        assert btn.title == "Close dialog"  # type: ignore[attr-defined]

    def test_create_button_empty_text_raises_error(self):
        with pytest.raises(ValueError, match="Button text is required"):
            create_action_button("")

        with pytest.raises(ValueError, match="Button text is required"):
            create_action_button("   ")

    def test_create_button_invalid_variant_raises_error(self):
        with pytest.raises(ValueError, match="Invalid variant"):
            create_action_button("Test", variant="invalid")

        with pytest.raises(ValueError, match="Invalid variant"):
            create_action_button("Test", variant="custom")

    def test_create_button_accessibility_features(self):
        btn = create_action_button("Submit Form")

        assert btn.title == "Submit Form"  # type: ignore[attr-defined]

        assert btn.style["minWidth"] == "44px"  # type: ignore[attr-defined]
        assert btn.style["minHeight"] == "44px"  # type: ignore[attr-defined]

        btn_disabled = create_action_button("Submit", disabled=True)
        assert btn_disabled.disabled is True  # type: ignore[attr-defined]


class TestButtonIntegration:
    def test_button_in_button_group(self):
        btn1 = create_action_button("Save", "save", variant="primary", size="sm")
        btn2 = create_action_button("Cancel", variant="secondary", size="sm")

        button_group = dbc.ButtonGroup([btn1, btn2])

        assert len(button_group.children) == 2  # type: ignore[arg-type]
        assert button_group.children[0].id == "btn-save"  # type: ignore[index,attr-defined]
        assert button_group.children[1].id == "btn-cancel"  # type: ignore[index,attr-defined]

    def test_button_consistency_across_sizes(self):
        btn_sm = create_action_button("Test", size="sm")
        btn_md = create_action_button("Test", size="md")
        btn_lg = create_action_button("Test", size="lg")

        for btn in [btn_sm, btn_md, btn_lg]:
            assert btn.style["minWidth"] == "44px"  # type: ignore[attr-defined]
            assert btn.style["minHeight"] == "44px"  # type: ignore[attr-defined]
            assert "borderRadius" in btn.style  # type: ignore[attr-defined]
            assert "fontSize" in btn.style  # type: ignore[attr-defined]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
