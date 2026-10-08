from unittest.mock import patch


def test_normalize_show_points():
    from callbacks.settings.helpers import normalize_show_points

    assert normalize_show_points(1) is True
    assert normalize_show_points(0) is False

    assert normalize_show_points(["show"]) is True
    assert normalize_show_points([]) is False

    assert normalize_show_points(True) is True
    assert normalize_show_points(False) is False


@patch("data.persistence.load_app_settings")
def test_settings_reload_workflow(mock_load_settings):
    mock_load_settings.return_value = {
        "show_points": 1,
        "pert_factor": 1.5,
        "data_points_count": 15,
        "deadline": "2026-12-31",
        "milestone": "2026-06-30",
    }

    from callbacks.settings.helpers import normalize_show_points
    from data.persistence import load_app_settings

    settings = load_app_settings()
    settings["show_points"] = normalize_show_points(settings.get("show_points", True))

    assert settings["show_points"] is True
    assert settings["pert_factor"] == 1.5
    assert settings["data_points_count"] == 15
    assert settings["deadline"] == "2026-12-31"
    mock_load_settings.assert_called_once()


def test_ui_sync_logic():
    settings = {
        "show_points": True,
        "pert_factor": 1.8,
        "data_points_count": 25,
        "deadline": "2027-01-01",
        "milestone": "2026-09-15",
    }

    result = (
        settings.get("pert_factor", 1.2),
        settings.get("deadline") or None,
        settings.get("show_points", True),
        settings.get("data_points_count", 20),
        settings.get("milestone") or None,
    )

    assert result == (1.8, "2027-01-01", True, 25, "2026-09-15")

    settings = {}
    result = (
        settings.get("pert_factor", 1.2),
        settings.get("deadline") or None,
        settings.get("show_points", True),
        settings.get("data_points_count", 20),
        settings.get("milestone") or None,
    )

    assert result == (
        1.2,
        None,
        True,
        20,
        None,
    )


def test_checklist_conversion_logic():
    show_points = True
    points_toggle_value = ["show"] if show_points else []
    assert points_toggle_value == ["show"]

    show_points = False
    points_toggle_value = ["show"] if show_points else []
    assert points_toggle_value == []
