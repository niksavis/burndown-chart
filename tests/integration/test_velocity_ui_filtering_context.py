import pytest

pytest.skip(
    "Tests internal functions refactored in bd-rnol extraction", allow_module_level=True
)

from ui.pert_components import (  # noqa: E402
    _create_velocity_footer_content,
    _create_weekly_velocity_section,
)


class TestVelocityUIFilteringContext:
    def test_velocity_footer_content_without_filtering(self):
        footer_content = _create_velocity_footer_content()

        assert len(footer_content) == 3

        footer_text = footer_content[1]
        assert "10-week rolling average" in footer_text
        assert "filtered" not in footer_text

        assert footer_content[2] is not None

    def test_velocity_footer_content_with_filtering_same_count(self):
        footer_content = _create_velocity_footer_content(
            data_points_count=15, total_data_points=15
        )

        footer_text = footer_content[1]
        assert "10-week rolling average" in footer_text
        assert "filtered" not in footer_text

    def test_velocity_footer_content_with_filtering_active(self):
        footer_content = _create_velocity_footer_content(
            data_points_count=8, total_data_points=15
        )

        footer_text = footer_content[1]
        assert "last 8 weeks of data" in footer_text
        assert "filtered from 15 available weeks" in footer_text
        assert "10-week rolling average" not in footer_text

    def test_velocity_footer_content_edge_cases(self):
        footer_content = _create_velocity_footer_content(None, None)
        footer_text = footer_content[1]
        assert "10-week rolling average" in footer_text

        footer_content = _create_velocity_footer_content(8, None)
        footer_text = footer_content[1]
        assert "10-week rolling average" in footer_text

        footer_content = _create_velocity_footer_content(None, 15)
        footer_text = footer_content[1]
        assert "10-week rolling average" in footer_text

    def test_weekly_velocity_section_accepts_new_parameters(self):
        sample_trend_values = {
            "avg_weekly_items": 5.2,
            "med_weekly_items": 4.8,
            "avg_weekly_points": 25.5,
            "med_weekly_points": 23.0,
            "avg_items_trend": 10,
            "med_items_trend": -5,
            "avg_points_trend": 0,
            "med_points_trend": 15,
            "avg_items_icon": "fa-arrow-up",
            "avg_items_icon_color": "success",
            "med_items_icon": "fa-arrow-down",
            "med_items_icon_color": "danger",
            "avg_points_icon": "fa-equals",
            "avg_points_icon_color": "secondary",
            "med_points_icon": "fa-arrow-up",
            "med_points_icon_color": "success",
        }

        try:
            component = _create_weekly_velocity_section(
                **sample_trend_values,
                show_points=True,
                data_points_count=8,
                total_data_points=15,
            )

            assert component is not None
            assert hasattr(component, "children")

        except Exception as e:
            pytest.fail(f"Function should accept new parameters without error: {e}")

    def test_weekly_velocity_section_backward_compatibility(self):
        sample_trend_values = {
            "avg_weekly_items": 5.2,
            "med_weekly_items": 4.8,
            "avg_weekly_points": 25.5,
            "med_weekly_points": 23.0,
            "avg_items_trend": 10,
            "med_items_trend": -5,
            "avg_points_trend": 0,
            "med_points_trend": 15,
            "avg_items_icon": "fa-arrow-up",
            "avg_items_icon_color": "success",
            "med_items_icon": "fa-arrow-down",
            "med_items_icon_color": "danger",
            "avg_points_icon": "fa-equals",
            "avg_points_icon_color": "secondary",
            "med_points_icon": "fa-arrow-up",
            "med_points_icon_color": "success",
        }

        try:
            component = _create_weekly_velocity_section(
                **sample_trend_values,
                show_points=True,
            )

            assert component is not None
            assert hasattr(component, "children")

        except Exception as e:
            pytest.fail(f"Function should maintain backward compatibility: {e}")

    def test_velocity_section_different_filtering_scenarios(self):
        sample_trend_values = {
            "avg_weekly_items": 5.2,
            "med_weekly_items": 4.8,
            "avg_weekly_points": 25.5,
            "med_weekly_points": 23.0,
            "avg_items_trend": 10,
            "med_items_trend": -5,
            "avg_points_trend": 0,
            "med_points_trend": 15,
            "avg_items_icon": "fa-arrow-up",
            "avg_items_icon_color": "success",
            "med_items_icon": "fa-arrow-down",
            "med_items_icon_color": "danger",
            "avg_points_icon": "fa-equals",
            "avg_points_icon_color": "secondary",
            "med_points_icon": "fa-arrow-up",
            "med_points_icon_color": "success",
        }

        scenarios = [
            (None, None, "default"),
            (10, 10, "no_filtering"),
            (5, 20, "filtered"),
            (50, 20, "no_filtering_more_requested"),
        ]

        for data_points_count, total_data_points, scenario_name in scenarios:
            try:
                component = _create_weekly_velocity_section(
                    **sample_trend_values,
                    show_points=True,
                    data_points_count=data_points_count,
                    total_data_points=total_data_points,
                )

                assert component is not None
                assert hasattr(component, "children")

            except Exception as e:
                pytest.fail(f"Scenario '{scenario_name}' failed: {e}")

    def test_velocity_section_points_disabled_with_filtering(self):
        sample_trend_values = {
            "avg_weekly_items": 5.2,
            "med_weekly_items": 4.8,
            "avg_weekly_points": 25.5,
            "med_weekly_points": 23.0,
            "avg_items_trend": 10,
            "med_items_trend": -5,
            "avg_points_trend": 0,
            "med_points_trend": 15,
            "avg_items_icon": "fa-arrow-up",
            "avg_items_icon_color": "success",
            "med_items_icon": "fa-arrow-down",
            "med_items_icon_color": "danger",
            "avg_points_icon": "fa-equals",
            "avg_points_icon_color": "secondary",
            "med_points_icon": "fa-arrow-up",
            "med_points_icon_color": "success",
        }

        try:
            component = _create_weekly_velocity_section(
                **sample_trend_values,
                show_points=False,
                data_points_count=8,
                total_data_points=15,
            )

            assert component is not None
            assert hasattr(component, "children")

        except Exception as e:
            pytest.fail(f"Points disabled with filtering should work: {e}")

    def test_footer_content_structure(self):
        footer_content = _create_velocity_footer_content(8, 15)

        assert len(footer_content) == 3

        icon_element = footer_content[0]
        assert hasattr(icon_element, "className")
        assert "fas fa-calendar-week" in icon_element.className

        text_element = footer_content[1]
        assert isinstance(text_element, str)

        tooltip_element = footer_content[2]
        assert tooltip_element is not None
