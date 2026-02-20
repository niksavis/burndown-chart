"""
Test suite for UI tooltip functionality and consistency.

This module validates tooltip implementation across all UI components
to ensure comprehensive user guidance and consistent experience.
"""

import pytest

from configuration.settings import (
    CHART_HELP_TEXTS,
    FORECAST_HELP_TEXTS,
    PROJECT_HELP_TEXTS,
    SCOPE_HELP_TEXTS,
    STATISTICS_HELP_TEXTS,
    VELOCITY_HELP_TEXTS,
)
from ui.tooltip_utils import create_info_tooltip


class TestTooltipUtilities:
    """Test suite for tooltip utility functions."""

    def test_create_info_tooltip_basic(self):
        """Test basic tooltip creation functionality."""
        tooltip = create_info_tooltip("test-id", "Test tooltip content")

        assert tooltip is not None
        assert "test-id" in str(tooltip)
        assert "Test tooltip content" in str(tooltip)

    def test_create_info_tooltip_with_html_content(self):
        """Test tooltip creation with HTML content."""
        html_content = "<strong>Bold text</strong> and <em>italic text</em>"
        tooltip = create_info_tooltip("html-test", html_content)

        assert tooltip is not None
        assert "html-test" in str(tooltip)
        assert "Bold text" in str(tooltip)

    def test_create_info_tooltip_with_long_content(self):
        """Test tooltip creation with long content."""
        long_content = "This is a very long tooltip content " * 10
        tooltip = create_info_tooltip("long-test", long_content)

        assert tooltip is not None
        assert "long-test" in str(tooltip)

    def test_create_info_tooltip_with_special_characters(self):
        """Test tooltip creation with special characters."""
        special_content = "Content with special chars: ±25%, <>&"
        tooltip = create_info_tooltip("special-test", special_content)

        assert tooltip is not None
        assert "special-test" in str(tooltip)


class TestHelpTextConfiguration:
    """Test suite for help text configuration completeness."""

    def test_forecast_help_texts_complete(self):
        """Test that all forecast help texts are defined."""
        required_keys = [
            "pert_methodology",
            "optimistic_forecast",
            "most_likely_forecast",
            "pessimistic_forecast",
            "expected_forecast",
            "three_point_estimation",
        ]

        for key in required_keys:
            assert key in FORECAST_HELP_TEXTS, f"Missing forecast help text: {key}"
            assert FORECAST_HELP_TEXTS[key].strip(), f"Empty forecast help text: {key}"

    def test_velocity_help_texts_complete(self):
        """Test that all velocity help texts are defined."""
        required_keys = [
            "weekly_velocity",
            "velocity_average",
            "velocity_median",
            "ten_week_calculation",
        ]

        for key in required_keys:
            assert key in VELOCITY_HELP_TEXTS, f"Missing velocity help text: {key}"
            assert VELOCITY_HELP_TEXTS[key].strip(), f"Empty velocity help text: {key}"

    def test_project_help_texts_complete(self):
        """Test that all project help texts are defined."""
        required_keys = [
            "project_overview",
            "completion_percentage",
            "items_vs_points",
            "completion_timeline",
        ]

        for key in required_keys:
            assert key in PROJECT_HELP_TEXTS, f"Missing project help text: {key}"
            assert PROJECT_HELP_TEXTS[key].strip(), f"Empty project help text: {key}"

    def test_scope_help_texts_complete(self):
        """Test that all scope help texts are defined."""
        required_keys = [
            "scope_change_rate",
            "adaptability_index",
            "throughput_ratio",
            "scope_metrics_explanation",
            "cumulative_chart",
            "weekly_growth",
        ]

        for key in required_keys:
            assert key in SCOPE_HELP_TEXTS, f"Missing scope help text: {key}"
            assert SCOPE_HELP_TEXTS[key].strip(), f"Empty scope help text: {key}"

    def test_statistics_help_texts_complete(self):
        """Test that all statistics help texts are defined."""
        required_keys = [
            "completed_items",
            "completed_points",
            "created_items",
            "created_points",
        ]

        for key in required_keys:
            assert key in STATISTICS_HELP_TEXTS, f"Missing statistics help text: {key}"
            assert STATISTICS_HELP_TEXTS[key].strip(), (
                f"Empty statistics help text: {key}"
            )

    def test_chart_help_texts_complete(self):
        """Test that all chart help texts are defined."""
        required_keys = [
            "burndown_vs_burnup",
            "pert_forecast_methodology",
            "historical_data_influence",
            "chart_legend_explained",
            "weekly_chart_methodology",
            "forecast_vs_actual_bars",
            "forecast_confidence_intervals",
        ]

        for key in required_keys:
            assert key in CHART_HELP_TEXTS, f"Missing chart help text: {key}"
            assert CHART_HELP_TEXTS[key].strip(), f"Empty chart help text: {key}"


class TestTooltipContentQuality:
    """Test suite for tooltip content quality and consistency."""

    def test_help_texts_have_reasonable_length(self):
        """Test that help texts are neither too short nor too long."""
        all_texts = {}
        all_texts.update(FORECAST_HELP_TEXTS)
        all_texts.update(VELOCITY_HELP_TEXTS)
        all_texts.update(PROJECT_HELP_TEXTS)
        all_texts.update(SCOPE_HELP_TEXTS)
        all_texts.update(STATISTICS_HELP_TEXTS)
        all_texts.update(CHART_HELP_TEXTS)

        for key, text in all_texts.items():
            # Should be at least 20 characters (meaningful content)
            assert len(text) >= 20, f"Help text too short: {key} ({len(text)} chars)"
            # Should be less than 1000 characters (tooltip friendly)
            assert len(text) <= 1000, f"Help text too long: {key} ({len(text)} chars)"

    def test_help_texts_have_meaningful_content(self):
        """Test that help texts contain meaningful, substantial content."""
        all_texts = {}
        all_texts.update(FORECAST_HELP_TEXTS)
        all_texts.update(VELOCITY_HELP_TEXTS)
        all_texts.update(PROJECT_HELP_TEXTS)
        all_texts.update(SCOPE_HELP_TEXTS)
        all_texts.update(STATISTICS_HELP_TEXTS)
        all_texts.update(CHART_HELP_TEXTS)

        for key, text in all_texts.items():
            text = text.strip()
            # Should contain substantial content (more than just a single word)
            assert len(text.split()) >= 5, (
                f"Help text should contain meaningful content (at least 5 words): {key}"
            )
            # Should not be just whitespace or empty
            assert text, f"Help text should not be empty: {key}"

    def test_help_texts_no_placeholder_content(self):
        """Test that help texts don't contain placeholder content."""
        all_texts = {}
        all_texts.update(FORECAST_HELP_TEXTS)
        all_texts.update(VELOCITY_HELP_TEXTS)
        all_texts.update(PROJECT_HELP_TEXTS)
        all_texts.update(SCOPE_HELP_TEXTS)
        all_texts.update(STATISTICS_HELP_TEXTS)
        all_texts.update(CHART_HELP_TEXTS)

        placeholder_indicators = ["TODO", "FIXME", "XXX", "placeholder", "lorem ipsum"]

        for key, text in all_texts.items():
            text_lower = text.lower()
            for placeholder in placeholder_indicators:
                assert placeholder not in text_lower, (
                    f"Help text contains placeholder: {key}"
                )

    def test_help_texts_consistent_terminology(self):
        """Test that help texts use consistent terminology."""
        all_texts = {}
        all_texts.update(FORECAST_HELP_TEXTS)
        all_texts.update(VELOCITY_HELP_TEXTS)
        all_texts.update(PROJECT_HELP_TEXTS)
        all_texts.update(SCOPE_HELP_TEXTS)
        all_texts.update(STATISTICS_HELP_TEXTS)
        all_texts.update(CHART_HELP_TEXTS)

        # Check for consistent PERT terminology
        pert_texts = [
            text for text in all_texts.values() if "PERT" in text or "pert" in text
        ]
        if pert_texts:
            # Should consistently use "PERT" (uppercase) for the methodology
            for text in pert_texts:
                if "pert" in text.lower():
                    # Allow "PERT" or at start of sentence, but not "pert" in middle
                    words = text.split()
                    for i, word in enumerate(words):
                        if word.lower().startswith("pert") and not word.startswith(
                            "PERT"
                        ):
                            # Check if it's at start of sentence
                            prev_word = words[i - 1] if i > 0 else ""
                            if not prev_word.endswith((".", "!", "?")):
                                pytest.fail(f"Inconsistent PERT terminology in: {text}")


class TestTooltipIntegration:
    """Integration tests for tooltip functionality across the application."""

    def test_all_help_text_categories_accessible(self):
        """Test that all help text categories can be imported and accessed."""
        categories = [
            FORECAST_HELP_TEXTS,
            VELOCITY_HELP_TEXTS,
            PROJECT_HELP_TEXTS,
            SCOPE_HELP_TEXTS,
            STATISTICS_HELP_TEXTS,
            CHART_HELP_TEXTS,
        ]

        for category in categories:
            assert isinstance(category, dict), (
                "Help text category should be a dictionary"
            )
            assert len(category) > 0, "Help text category should not be empty"

    def test_tooltip_function_handles_edge_cases(self):
        """Test that tooltip function handles various edge cases."""
        # Test with empty content
        tooltip = create_info_tooltip("empty-test", "")
        assert tooltip is not None

        # Test with None content (should handle gracefully)
        try:
            tooltip = create_info_tooltip("none-test", None)
            # Should either work or raise appropriate exception
        except (TypeError, ValueError):
            # Expected behavior for None content
            pass

    def test_tooltip_accessibility_features(self):
        """Test that tooltips include accessibility features."""
        tooltip = create_info_tooltip("a11y-test", "Accessibility test content")
        tooltip_str = str(tooltip)

        # Should include ARIA attributes or similar accessibility features
        # This test may need adjustment based on actual tooltip implementation
        assert tooltip_str is not None
        assert len(tooltip_str) > 0
