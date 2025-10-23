"""Visual validation tests for bug chart layout improvements.

Tests that verify the bug trend chart has proper spacing and no overlapping elements
between the forecast annotation and plotly modebar.
"""

from visualization.mobile_charts import create_bug_trend_chart


class TestBugChartLayout:
    """Test bug chart layout improvements."""

    def test_forecast_annotation_positioning(self):
        """Test forecast annotation is positioned to avoid toolbar overlap."""
        # Create sample data with proper ISO week format
        weekly_stats = [
            {
                "week": "2025-W01",
                "bugs_created": 5,
                "bugs_resolved": 3,
                "cumulative_open": 2,
            },
            {
                "week": "2025-W02",
                "bugs_created": 4,
                "bugs_resolved": 6,
                "cumulative_open": 0,
            },
            {
                "week": "2025-W03",
                "bugs_created": 3,
                "bugs_resolved": 2,
                "cumulative_open": 1,
            },
        ]

        # Create chart with forecast
        fig = create_bug_trend_chart(
            weekly_stats, viewport_size="desktop", include_forecast=True
        )

        # Verify figure created
        assert fig is not None

        # Check annotations exist
        annotations = fig.layout.annotations  # type: ignore[attr-defined]
        assert len(annotations) > 0, "Should have forecast annotation"

        # Find forecast annotation
        forecast_annotation = None
        for ann in annotations:
            if "Forecast" in ann.text:
                forecast_annotation = ann
                break

        assert forecast_annotation is not None, "Should have forecast annotation"

        # Verify annotation positioning
        # Should use yref="paper" and be positioned within plot area (< 1.0)
        assert forecast_annotation.yref == "paper"
        assert forecast_annotation.y <= 0.9, (
            "Annotation should be within plot area to avoid toolbar"
        )

        # Verify annotation has background styling to stand out
        assert forecast_annotation.bgcolor is not None
        assert forecast_annotation.bordercolor is not None

    def test_chart_top_margin_adequate(self):
        """Test chart has adequate top margin for plotly modebar."""
        weekly_stats = [
            {
                "week": "2025-W01",
                "bugs_created": 5,
                "bugs_resolved": 3,
                "cumulative_open": 2,
            },
            {
                "week": "2025-W02",
                "bugs_created": 4,
                "bugs_resolved": 6,
                "cumulative_open": 0,
            },
        ]

        for viewport in ["mobile", "tablet", "desktop"]:
            fig = create_bug_trend_chart(
                weekly_stats, viewport_size=viewport, include_forecast=True
            )

            # Check margin settings
            assert fig.layout.margin.t >= 30, f"Top margin too small for {viewport}"  # type: ignore[attr-defined]

    def test_vertical_line_styling(self):
        """Test vertical forecast line has proper styling."""
        weekly_stats = [
            {
                "week": "2025-W01",
                "bugs_created": 5,
                "bugs_resolved": 3,
                "cumulative_open": 2,
            },
            {
                "week": "2025-W02",
                "bugs_created": 4,
                "bugs_resolved": 6,
                "cumulative_open": 0,
            },
        ]

        fig = create_bug_trend_chart(
            weekly_stats, viewport_size="desktop", include_forecast=True
        )

        # Check for vertical line shape
        shapes = fig.layout.shapes  # type: ignore[attr-defined]
        vline = None
        for shape in shapes:
            if shape.type == "line" and shape.line.dash == "dash":
                vline = shape
                break

        # Vertical line should exist if forecast is enabled
        # (only added when we have 2+ weeks of data for forecast)
        if len(weekly_stats) >= 2:
            assert vline is not None, "Should have vertical forecast line"
            assert vline.line.width >= 1, "Line should have visible width"

    def test_chart_height_optimization(self):
        """Test chart height is optimized to minimize excessive white space."""
        weekly_stats = [
            {
                "week": "2025-W01",
                "bugs_created": 5,
                "bugs_resolved": 3,
                "cumulative_open": 2,
            },
            {
                "week": "2025-W02",
                "bugs_created": 4,
                "bugs_resolved": 6,
                "cumulative_open": 0,
            },
        ]

        # Desktop should have optimized height (not excessive)
        fig_desktop = create_bug_trend_chart(
            weekly_stats, viewport_size="desktop", include_forecast=True
        )
        # Use type: ignore to suppress linter false positives for Plotly attributes
        layout_height = fig_desktop.layout.height  # type: ignore[attr-defined]
        assert layout_height <= 600, (  # type: ignore[operator]
            "Desktop chart height should be optimized (≤600px)"
        )

        # Mobile should be compact
        fig_mobile = create_bug_trend_chart(
            weekly_stats, viewport_size="mobile", include_forecast=True
        )
        mobile_height = fig_mobile.layout.height  # type: ignore[attr-defined]
        assert mobile_height <= 450, (  # type: ignore[operator]
            "Mobile chart height should be compact (≤450px)"
        )

    def test_legend_positioning_desktop(self):
        """Test legend is well-positioned on desktop to avoid white space."""
        weekly_stats = [
            {
                "week": "2025-W01",
                "bugs_created": 5,
                "bugs_resolved": 3,
                "cumulative_open": 2,
            },
            {
                "week": "2025-W02",
                "bugs_created": 4,
                "bugs_resolved": 6,
                "cumulative_open": 0,
            },
        ]

        fig = create_bug_trend_chart(
            weekly_stats, viewport_size="desktop", include_forecast=True
        )

        # Check legend positioning
        legend = fig.layout.legend  # type: ignore[attr-defined]
        assert legend.orientation == "v", "Desktop should have vertical legend"
        assert legend.x >= 1.0, "Legend should be positioned outside plot area"
        # Legend should be centered vertically, not at top (to minimize white space)
        assert legend.y <= 0.8, (
            "Legend should be centered/lower to avoid excessive white space"
        )
