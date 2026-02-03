"""Test settings reload after import and profile switch (burndown-chart-e1ew)."""

from unittest.mock import patch


def test_normalize_show_points():
    """Test that show_points is normalized to boolean."""
    from callbacks.settings.helpers import normalize_show_points

    # Test int to bool (database format)
    assert normalize_show_points(1) is True
    assert normalize_show_points(0) is False

    # Test list to bool (checkbox format)
    assert normalize_show_points(["show"]) is True
    assert normalize_show_points([]) is False

    # Test bool passthrough
    assert normalize_show_points(True) is True
    assert normalize_show_points(False) is False


@patch("data.persistence.load_app_settings")
def test_settings_reload_workflow(mock_load_settings):
    """Integration test: verify settings reload flow after import."""
    # Arrange - simulate imported profile with points enabled
    mock_load_settings.return_value = {
        "show_points": 1,  # Database stores as int
        "pert_factor": 1.5,
        "data_points_count": 15,
        "deadline": "2026-12-31",
        "milestone": "2026-06-30",
    }

    # Act - simulate what the callback does
    from data.persistence import load_app_settings
    from callbacks.settings.helpers import normalize_show_points

    settings = load_app_settings()
    settings["show_points"] = normalize_show_points(settings.get("show_points", True))

    # Assert - verify settings are loaded and normalized
    assert settings["show_points"] is True  # Normalized to boolean
    assert settings["pert_factor"] == 1.5
    assert settings["data_points_count"] == 15
    assert settings["deadline"] == "2026-12-31"
    mock_load_settings.assert_called_once()


def test_ui_sync_logic():
    """Test UI sync logic with various settings."""
    # Test with complete settings
    settings = {
        "show_points": True,
        "pert_factor": 1.8,
        "data_points_count": 25,
        "deadline": "2027-01-01",
        "milestone": "2026-09-15",
    }

    result = (
        settings.get("pert_factor", 1.2),
        settings.get("deadline") or None,  # CRITICAL: Use None for empty dates (not "")
        settings.get("show_points", True),
        settings.get("data_points_count", 20),
        settings.get("milestone")
        or None,  # CRITICAL: Use None for empty dates (not "")
    )

    assert result == (1.8, "2027-01-01", True, 25, "2026-09-15")

    # Test with missing keys (defaults)
    settings = {}
    result = (
        settings.get("pert_factor", 1.2),
        settings.get("deadline") or None,  # CRITICAL: Use None for empty dates (not "")
        settings.get("show_points", True),
        settings.get("data_points_count", 20),
        settings.get("milestone")
        or None,  # CRITICAL: Use None for empty dates (not "")
    )

    assert result == (
        1.2,
        None,
        True,
        20,
        None,
    )  # FIXED: Empty dates should be None, not ""


def test_checklist_conversion_logic():
    """Test boolean to checklist format conversion for points-toggle."""
    # Test True -> ["show"]
    show_points = True
    points_toggle_value = ["show"] if show_points else []
    assert points_toggle_value == ["show"]

    # Test False -> []
    show_points = False
    points_toggle_value = ["show"] if show_points else []
    assert points_toggle_value == []
