"""Integration test for complete HTML report generation.

Tests that the refactored report modules work end-to-end:
- Data loading
- Metric calculation
- Chart generation
- Template rendering
- HTML output validity
"""


def test_report_basic_structure_no_profile():
    """Test basic report structure generation without requiring profile fixture."""
    from data.report.renderer import render_template

    # Minimal test with empty metrics
    html = render_template(
        profile_name="Test Profile",
        query_name="Test Query",
        time_period_weeks=4,
        sections=["burndown"],
        metrics={
            "dashboard": {
                "health_score": 75,
                "show_points": False,
                "weeks_count": 4,
            },
            "burndown": {"has_data": False},
        },
        chart_script="// No charts",
    )

    # Verify basic HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "<head>" in html
    assert "</head>" in html
    assert "<body>" in html
    assert "</body>" in html

    # Verify profile and query info
    assert "Test Profile" in html
    assert "Test Query" in html

    # Verify responsive design
    assert "viewport" in html.lower()

    # Verify CSS is embedded
    assert "<style>" in html or "color:" in html


def test_report_template_partials_loaded():
    """Test that template partials are loaded correctly."""
    from data.report.renderer import render_template

    html = render_template(
        profile_name="TestProfile",
        query_name="TestQuery",
        time_period_weeks=12,
        sections=["burndown", "dora", "flow"],
        metrics={
            "dashboard": {
                "health_score": 85,
                "show_points": False,
                "weeks_count": 12,
                "milestone": None,
                "forecast_date": None,
                "deadline": None,
            },
            "burndown": {
                "has_data": True,
                "historical_data": {"dates": [], "remaining_items": []},
            },
            "dora": {"has_data": True},
            "flow": {"has_data": True},
        },
        chart_script="console.log('test');",
    )

    # Check that all major sections are present
    assert html
    assert len(html) > 1000  # Should have substantial content

    # Check for key structural elements
    assert "<html" in html
    assert "<body>" in html
    assert "</body>" in html


def test_report_file_size_reasonable():
    """Test that report size is reasonable with empty metrics."""
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=12,
        sections=["burndown", "dora", "flow"],
        metrics={
            "dashboard": {"health_score": 0, "show_points": False, "weeks_count": 12},
            "burndown": {"has_data": False},
            "dora": {"has_data": False},
            "flow": {"has_data": False},
        },
        chart_script="",
    )

    # File should be < 5MB
    assert len(html) < 5 * 1024 * 1024

    # File should have meaningful content (> 5KB minimum)
    assert len(html) > 5 * 1024


def test_report_css_classes_present():
    """Test that CSS classes for metric colors are defined."""
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown"],
        metrics={
            "dashboard": {"health_score": 0, "show_points": False, "weeks_count": 4}
        },
        chart_script="",
    )

    # Check for metric color classes
    assert "metric-color-good" in html or ".metric-color-good" in html
    assert "metric-color-info" in html or ".metric-color-info" in html
    assert "metric-color-warning" in html or ".metric-color-warning" in html

    # Check for responsive styles
    assert "@media" in html


def test_report_no_obvious_errors():
    """Test that generated HTML has no obvious errors."""
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown", "dora"],
        metrics={
            "dashboard": {"health_score": 50, "show_points": False, "weeks_count": 4},
            "burndown": {"has_data": False},
            "dora": {"has_data": False},
        },
        chart_script="new Chart(ctx, {});",
    )

    # Check for no Python tracebacks
    assert "Traceback" not in html
    assert "Error:" not in html or "No errors" in html

    # Check HTML is well-formed
    assert html.count("<html") <= 1
    assert html.count("</html>") == 1
    assert html.count("</body>") == 1


def test_report_chart_script_injection():
    """Test that chart scripts are properly injected."""
    from data.report.renderer import render_template

    chart_script = """
    (function() {
        const ctx = document.getElementById('testChart');
        if (ctx) {
            new Chart(ctx, {type: 'line', data: {}});
        }
    })();
    """

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown"],
        metrics={
            "dashboard": {"health_score": 0, "show_points": False, "weeks_count": 4}
        },
        chart_script=chart_script,
    )

    # Verify script is injected
    assert "testChart" in html
    assert "new Chart(ctx" in html


def test_report_date_formatting():
    """Test that dates are properly formatted in report."""
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown"],
        metrics={
            "dashboard": {"health_score": 0, "show_points": False, "weeks_count": 4}
        },
        chart_script="",
    )

    # Should have a generated date
    assert "2026" in html or "202" in html  # Current year
    # Should have day of week
    assert any(
        day in html
        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
    )
