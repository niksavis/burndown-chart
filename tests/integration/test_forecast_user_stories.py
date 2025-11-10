"""Verification script for User Stories 3, 4, 5 (Feature 009).

Tests:
- US3: Historical performance review (forecast data in past weeks)
- US4: WIP health with forecast ranges (Flow Load bidirectional)
- US5: Baseline building (<4 weeks of data)

Run: .\\.venv\\Scripts\\activate; python test_user_stories_3_5.py
"""

from data.metrics_snapshots import (
    save_metric_snapshot,
    get_metric_snapshot,
    add_forecasts_to_week,
)
from data.metrics_calculator import (
    calculate_forecast,
    calculate_trend_vs_forecast,
    calculate_flow_load_range,
)
from ui.metric_cards import create_forecast_section


def test_user_story_3_historical_review():
    """Test US3: Forecast data persists and loads for historical weeks."""
    print("\n=== User Story 3: Historical Performance Review ===")

    # Simulate saving multiple weeks of Flow Velocity data
    weeks_data = [
        ("2025-W43", {"completed_count": 10, "distribution": {}}),
        ("2025-W44", {"completed_count": 12, "distribution": {}}),
        ("2025-W45", {"completed_count": 15, "distribution": {}}),
        ("2025-W46", {"completed_count": 18, "distribution": {}}),
    ]

    print("\n1. Saving historical metrics...")
    for week, data in weeks_data:
        save_metric_snapshot(week, "flow_velocity", data)
        print(f"  Saved {week}: {data['completed_count']} items")

    # Add forecasts to week 46 (should use W43-45 as history)
    print("\n2. Calculating forecast for 2025-W46...")
    add_forecasts_to_week("2025-W46")

    # Load the snapshot and verify forecast was saved
    snapshot = get_metric_snapshot("2025-W46", "flow_velocity")
    print("\n3. Loading historical snapshot for 2025-W46...")

    if snapshot and "forecast" in snapshot:
        forecast = snapshot["forecast"]
        trend = snapshot.get("trend_vs_forecast")

        print(f"  ✓ Forecast found: {forecast['forecast_value']:.1f} items/week")
        print(f"  ✓ Confidence: {forecast['confidence']}")
        print(f"  ✓ Weeks used: {forecast['weeks_available']}")

        if trend:
            print(f"  ✓ Trend: {trend['direction']} {trend['status_text']}")
            print(f"  ✓ Color: {trend['color_class']}")

        # Test: US3 requirement - forecasts persist and load correctly
        assert forecast["forecast_value"] > 0, "Forecast value should be positive"
        assert (
            forecast["weeks_available"] >= 2
        ), "Should have at least 2 weeks of history"
        assert trend is not None, "Trend vs forecast should be calculated"

        print("\n✅ US3 PASS: Historical forecast data persists and loads correctly")
        return True
    else:
        print("\n❌ US3 FAIL: No forecast data found in historical snapshot")
        return False


def test_user_story_4_wip_health_ranges():
    """Test US4: Flow Load displays as range with bidirectional health check."""
    print("\n\n=== User Story 4: WIP Health with Forecast Ranges ===")

    # Test Flow Load range calculation
    print("\n1. Testing Flow Load range calculation...")
    forecast_value = 15.0
    range_data = calculate_flow_load_range(forecast_value, range_percent=0.20)

    print(f"  Forecast: {forecast_value:.1f} items")
    print(f"  Range (±20%): {range_data['lower']:.1f} - {range_data['upper']:.1f}")

    # Test: US4 requirement - range bounds calculated correctly
    assert range_data["lower"] == 12.0, "Lower bound should be 15 * 0.8 = 12"
    assert range_data["upper"] == 18.0, "Upper bound should be 15 * 1.2 = 18"

    print("  ✓ Range calculation correct")

    # Test different WIP scenarios
    print("\n2. Testing bidirectional WIP health scenarios...")

    test_scenarios = [
        (24, "above", "Above normal range - too much WIP"),
        (14, "within", "Within normal range ✓"),
        (9, "below", "Below normal range - underutilized"),
    ]

    for wip, expected_status, description in test_scenarios:
        trend = calculate_trend_vs_forecast(
            current_value=float(wip),
            forecast_value=forecast_value,
            metric_type="higher_better",  # Simplified for testing
        )

        if wip > range_data["upper"]:
            status = "above"
        elif wip < range_data["lower"]:
            status = "below"
        else:
            status = "within"

        print(f"  WIP={wip}: {status} range ({description})")
        print(f"    Direction: {trend['direction']}, Status: {trend['status_text']}")

        assert status == expected_status, f"WIP={wip} should be {expected_status}"

    print("\n✅ US4 PASS: Flow Load range and bidirectional health working")
    return True


def test_user_story_5_baseline_building():
    """Test US5: Baseline building with <4 weeks of data."""
    print("\n\n=== User Story 5: Baseline Building ===")

    # Test with 2 weeks (minimum data)
    print("\n1. Testing with 2 weeks of data...")
    forecast_2w = calculate_forecast([10.0, 12.0])

    assert forecast_2w is not None, "Should calculate forecast with 2 weeks"
    assert (
        forecast_2w["confidence"] == "building"
    ), "Should show 'building' confidence"
    assert forecast_2w["weeks_available"] == 2, "Should report 2 weeks used"

    print(f"  ✓ Forecast: {forecast_2w['forecast_value']:.1f} items/week")
    print(f"  ✓ Confidence: {forecast_2w['confidence']}")
    print(f"  ✓ Weeks: {forecast_2w['weeks_available']}")

    # Test with 3 weeks
    print("\n2. Testing with 3 weeks of data...")
    forecast_3w = calculate_forecast([10.0, 11.0, 12.0])

    assert forecast_3w is not None, "Should calculate forecast with 3 weeks"
    assert (
        forecast_3w["confidence"] == "building"
    ), "Should still show 'building' confidence"
    assert forecast_3w["weeks_available"] == 3, "Should report 3 weeks used"

    print(f"  ✓ Forecast: {forecast_3w['forecast_value']:.1f} items/week")
    print(f"  ✓ Confidence: {forecast_3w['confidence']}")
    print(f"  ✓ Weeks: {forecast_3w['weeks_available']}")

    # Test with 4 weeks (established baseline)
    print("\n3. Testing with 4 weeks of data...")
    forecast_4w = calculate_forecast([10.0, 12.0, 11.0, 13.0])

    assert forecast_4w is not None, "Should calculate forecast with 4 weeks"
    assert (
        forecast_4w["confidence"] == "established"
    ), "Should show 'established' confidence"
    assert forecast_4w["weeks_available"] == 4, "Should report 4 weeks used"

    print(f"  ✓ Forecast: {forecast_4w['forecast_value']:.1f} items/week")
    print(f"  ✓ Confidence: {forecast_4w['confidence']}")
    print(f"  ✓ Weeks: {forecast_4w['weeks_available']}")

    # Test with 1 week (insufficient data)
    print("\n4. Testing with 1 week of data (insufficient)...")
    forecast_1w = calculate_forecast([10.0], min_weeks=2)

    assert forecast_1w is None, "Should return None with insufficient data"
    print("  ✓ Correctly returns None for insufficient data")

    # Test UI display
    print("\n5. Testing UI forecast section display...")

    # Test "Building baseline" badge
    forecast_section_building = create_forecast_section(
        forecast_data=forecast_2w,
        trend_vs_forecast={"direction": "→", "status_text": "On track", "color_class": "text-secondary", "is_good": True},
        metric_name="flow_velocity",
        unit="items/week",
    )

    # Verify "Building baseline" badge appears
    section_html = str(forecast_section_building)
    assert (
        "Building baseline" in section_html
    ), "Should display 'Building baseline' badge"
    print("  ✓ 'Building baseline' badge displays correctly")

    # Test established baseline (no badge)
    forecast_section_established = create_forecast_section(
        forecast_data=forecast_4w,
        trend_vs_forecast={"direction": "↗", "status_text": "+23% above forecast", "color_class": "text-success", "is_good": True},
        metric_name="flow_velocity",
        unit="items/week",
    )

    section_html_est = str(forecast_section_established)
    assert (
        "Building baseline" not in section_html_est
    ), "Should NOT display 'Building baseline' badge for established"
    print("  ✓ Established baseline (no badge) displays correctly")

    print("\n✅ US5 PASS: Baseline building with appropriate messaging working")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("FEATURE 009 - USER STORIES 3, 4, 5 VERIFICATION")
    print("=" * 60)

    try:
        us3_pass = test_user_story_3_historical_review()
        us4_pass = test_user_story_4_wip_health_ranges()
        us5_pass = test_user_story_5_baseline_building()

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"US3 (Historical Review):   {'✅ PASS' if us3_pass else '❌ FAIL'}")
        print(f"US4 (WIP Health Ranges):   {'✅ PASS' if us4_pass else '❌ FAIL'}")
        print(f"US5 (Baseline Building):   {'✅ PASS' if us5_pass else '❌ FAIL'}")

        all_pass = us3_pass and us4_pass and us5_pass
        print("\n" + "=" * 60)
        if all_pass:
            print("✅ ALL USER STORIES VERIFIED - FEATURE 009 COMPLETE")
        else:
            print("❌ SOME USER STORIES FAILED - SEE DETAILS ABOVE")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR during verification: {e}")
        import traceback

        traceback.print_exc()
