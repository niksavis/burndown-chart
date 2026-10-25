import pytest

from ui.demo_banner import create_demo_banner


def test_ordinary_application_has_no_demo_banner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BURNDOWN_DEMO_MODE", raising=False)
    assert create_demo_banner() is None


def test_demo_banner_identifies_synthetic_data_and_fixed_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BURNDOWN_DEMO_MODE", "1")
    monkeypatch.setenv("BURNDOWN_AS_OF", "2026-01-29T12:00:00+00:00")
    banner = create_demo_banner()
    assert banner is not None
    properties = banner.to_plotly_json()["props"]
    assert properties["id"] == "demo-mode-banner"
    assert (
        properties["children"]
        == "Offline demo - Synthetic data - Evaluation date: 2026-01-29"
    )
