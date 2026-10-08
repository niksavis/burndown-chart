def _get_empty_metrics():
    return {
        "dashboard": {
            "health_score": 0,
            "health_status": "UNKNOWN",
            "show_points": False,
            "weeks_count": 4,
            "has_data": False,
            "items_completion_pct": 0.0,
            "points_completion_pct": 0.0,
            "completed_items": 0,
            "remaining_items": 0,
            "total_items": 0,
            "completed_points": 0.0,
            "remaining_points": 0.0,
            "total_points": 0.0,
            "velocity_items": 0.0,
            "velocity_points": 0.0,
            "velocity_cv": 0.0,
            "trend_direction": "stable",
            "forecast_date": None,
            "forecast_date_items": None,
            "forecast_date_points": None,
            "deadline": None,
            "completion_confidence": 50.0,
            "scope_change_rate": 0.0,
        },
        "scope": {"has_data": False},
        "burndown": {"has_data": False},
        "bug_analysis": {"has_data": False},
        "dora": {"has_data": False},
        "flow": {"has_data": False},
        "budget": {"has_data": False},
    }


def test_report_basic_structure_no_profile():
    from data.report.renderer import render_template

    metrics = _get_empty_metrics()
    metrics["dashboard"]["health_score"] = 75

    html = render_template(
        profile_name="Test Profile",
        query_name="Test Query",
        time_period_weeks=4,
        sections=["burndown"],
        metrics=metrics,
        chart_script="// No charts",
    )

    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "<head>" in html
    assert "</head>" in html
    assert "<body>" in html
    assert "</body>" in html

    assert "Test Profile" in html
    assert "Test Query" in html

    assert "viewport" in html.lower()

    assert "<style>" in html or "color:" in html


def test_report_template_partials_loaded():
    from data.report.renderer import render_template

    metrics = _get_empty_metrics()
    metrics["dashboard"].update(
        {
            "health_score": 85,
            "health_status": "GOOD",
            "weeks_count": 12,
            "items_completion_pct": 65.0,
            "points_completion_pct": 70.0,
            "has_data": True,
        }
    )
    metrics["burndown"] = {
        "has_data": True,
        "historical_data": {"dates": [], "remaining_items": []},
    }

    html = render_template(
        profile_name="TestProfile",
        query_name="TestQuery",
        time_period_weeks=12,
        sections=["burndown"],
        metrics=metrics,
        chart_script="console.log('test');",
    )

    assert html
    assert len(html) > 1000

    assert "<html" in html
    assert "<body>" in html
    assert "</body>" in html


def test_report_file_size_reasonable():
    from data.report.renderer import render_template

    metrics = _get_empty_metrics()
    metrics["dashboard"]["weeks_count"] = 12

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=12,
        sections=["burndown", "dora", "flow"],
        metrics=metrics,
        chart_script="",
    )

    assert len(html) < 5 * 1024 * 1024

    assert len(html) > 5 * 1024


def test_report_css_classes_present():
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown"],
        metrics=_get_empty_metrics(),
        chart_script="",
    )

    assert "metric-color-good" in html or ".metric-color-good" in html
    assert "metric-color-info" in html or ".metric-color-info" in html
    assert "metric-color-warning" in html or ".metric-color-warning" in html

    assert "@media" in html


def test_report_no_obvious_errors():
    from data.report.renderer import render_template

    metrics = _get_empty_metrics()
    metrics["dashboard"]["health_score"] = 50

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown", "dora"],
        metrics=metrics,
        chart_script="new Chart(ctx, {});",
    )

    assert "Traceback" not in html
    assert "Error:" not in html or "No errors" in html

    assert html.count("<html") <= 1
    assert html.count("</html>") == 1
    assert html.count("</body>") == 1


def test_report_chart_script_injection():
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
        metrics=_get_empty_metrics(),
        chart_script=chart_script,
    )

    assert "testChart" in html
    assert "new Chart(ctx" in html


def test_report_embedded_dependencies_not_escaped() -> None:
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown"],
        metrics=_get_empty_metrics(),
        chart_script="",
    )

    assert '@charset "UTF-8"' in html
    assert "@charset &#34;UTF-8&#34;" not in html
    assert "[data-bs-theme='light']" in html
    assert "[data-bs-theme=&#39;light&#39;]" not in html
    assert "a > code" in html
    assert "a &gt; code" not in html


def test_report_date_formatting():
    from data.report.renderer import render_template

    html = render_template(
        profile_name="Test",
        query_name="Test",
        time_period_weeks=4,
        sections=["burndown"],
        metrics=_get_empty_metrics(),
        chart_script="",
    )

    assert "2026" in html or "202" in html
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
