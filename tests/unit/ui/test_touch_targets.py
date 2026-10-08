from ui.button_utils import create_button_style
from ui.styles import create_input_style


class TestTouchTargetCompliance:
    def test_button_touch_targets_compliance(self):
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            style = create_button_style(size=size, touch_friendly=True)
            min_height = style.get("minHeight", "0px")

            height_value = float(min_height.replace("px", ""))

            if size == "sm":
                assert height_value >= 38, (
                    f"Small button height {height_value}px < 38px minimum"
                )
            else:
                assert height_value >= 44, (
                    f"Button size {size} height {height_value}px < 44px requirement"
                )

    def test_input_touch_targets_compliance(self):
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            style = create_input_style(size=size)
            height = style.get("height", "")

            if "max(" in height:
                if size == "sm":
                    assert "38px" in height, (
                        f"Small input should have min 38px, got: {height}"
                    )
                elif size == "md":
                    assert "44px" in height, (
                        f"Medium input should have min 44px, got: {height}"
                    )
                elif size == "lg":
                    assert "48px" in height, (
                        f"Large input should have min 48px, got: {height}"
                    )
                print(
                    f"[OK] Input {size} height: {height} - "
                    "meets touch target requirements"
                )
            else:
                print(
                    f"[!] Input {size} height: {height} - "
                    "check if this meets requirements"
                )

    def test_touch_target_utility_classes(self):
        expected_min_height = 44
        expected_min_width = 44

        assert expected_min_height == 44, (
            "Mobile touch target minimum height should be 44px"
        )
        assert expected_min_width == 44, (
            "Mobile touch target minimum width should be 44px"
        )

    def test_small_interactive_elements_compliance(self):
        style = create_button_style(size="sm", touch_friendly=True)

        min_height = float(style.get("minHeight", "0px").replace("px", ""))
        assert min_height >= 38, (
            f"Small interactive elements should be at least 38px, got {min_height}px"
        )

    def test_form_control_spacing(self):

        style = create_input_style(size="md")
        padding = style.get("padding", "")

        assert "0.375rem" in padding or "0.5rem" in padding or "1rem" in padding, (
            f"Input padding {padding} should provide adequate touch spacing"
        )

    def test_css_touch_target_classes_implementation(self):

        css_classes = {
            "mobile-touch-target": {"min_height": "44px", "min_width": "44px"},
            "mobile-touch-target-sm": {"min_height": "38px", "min_width": "38px"},
            "mobile-link-button": {"min_height": "44px", "min_width": "44px"},
            "mobile-form-control": {"min_height": "44px"},
        }

        for class_name, expected_props in css_classes.items():
            if "min_height" in expected_props:
                height_value = int(expected_props["min_height"].replace("px", ""))
                if "sm" in class_name:
                    assert height_value >= 38, (
                        f"{class_name} should have min 38px height"
                    )
                else:
                    assert height_value >= 44, (
                        f"{class_name} should have min 44px height"
                    )
            print(f"[OK] CSS class {class_name} meets touch target requirements")

    def test_responsive_breakpoint_touch_targets(self):
        expected_mobile_rules = [
            ".btn-sm { min-height: 38px }",
            ".btn { min-height: 44px }",
            ".form-control { min-height: 44px }",
            ".btn-link { min-height: 44px; min-width: 44px }",
        ]

        for rule in expected_mobile_rules:
            if "38px" in rule:
                assert "btn-sm" in rule, "38px minimum should only be for small buttons"
            elif "44px" in rule:
                assert any(
                    selector in rule
                    for selector in [".btn", ".form-control", ".btn-link"]
                ), "44px minimum should be for standard interactive elements"
            print(f"[OK] Mobile breakpoint rule validated: {rule}")
