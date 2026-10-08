from visualization.bug_charts import create_bug_trend_chart


class TestBugChartLayout:
    def test_forecast_annotation_positioning(self):
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

        fig = create_bug_trend_chart(
            weekly_stats, viewport_size="desktop", include_forecast=True
        )

        assert fig is not None

        annotations = fig.layout.annotations  # type: ignore[attr-defined]
        assert len(annotations) > 0, "Should have forecast annotation"

        forecast_annotation = None
        for ann in annotations:
            if "Forecast" in ann.text:
                forecast_annotation = ann
                break

        assert forecast_annotation is not None, "Should have forecast annotation"

        assert forecast_annotation.yref == "paper"
        assert forecast_annotation.y <= 0.9, (
            "Annotation should be within plot area to avoid toolbar"
        )

        assert forecast_annotation.bgcolor is not None
        assert forecast_annotation.bordercolor is not None

    def test_chart_top_margin_adequate(self):
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

            assert fig.layout.margin.t >= 30, f"Top margin too small for {viewport}"  # type: ignore[attr-defined]

    def test_vertical_line_styling(self):
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

        shapes = fig.layout.shapes  # type: ignore[attr-defined]
        vline = None
        for shape in shapes:
            if shape.type == "line" and shape.line.dash == "dash":
                vline = shape
                break

        if len(weekly_stats) >= 2:
            assert vline is not None, "Should have vertical forecast line"
            assert vline.line.width >= 1, "Line should have visible width"

    def test_chart_height_optimization(self):
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

        fig_desktop = create_bug_trend_chart(
            weekly_stats, viewport_size="desktop", include_forecast=True
        )
        layout_height = fig_desktop.layout.height  # type: ignore[attr-defined]
        assert layout_height <= 600, (  # type: ignore[operator]
            "Desktop chart height should be optimized (≤600px)"
        )

        fig_mobile = create_bug_trend_chart(
            weekly_stats, viewport_size="mobile", include_forecast=True
        )
        mobile_height = fig_mobile.layout.height  # type: ignore[attr-defined]
        assert mobile_height <= 450, (  # type: ignore[operator]
            "Mobile chart height should be compact (≤450px)"
        )

    def test_legend_positioning_desktop(self):
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

        legend = fig.layout.legend  # type: ignore[attr-defined]
        assert legend.orientation == "v", "Desktop should have vertical legend"
        assert legend.x >= 1.0, "Legend should be positioned outside plot area"
        assert legend.y <= 0.8, (
            "Legend should be centered/lower to avoid excessive white space"
        )
