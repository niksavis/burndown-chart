import tempfile
from pathlib import Path
from typing import Literal

import pytest
from playwright.sync_api import sync_playwright

from data.demo.config import SCENARIOS
from devtools.capture import capture_view
from devtools.server import running_demo_server
from ui.tabs import TAB_CONFIG


@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile"])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_demo_tabs_scenarios_ranges_and_report_render_offline(
    generated_demo: Path, mobile: bool, theme: Literal["light", "dark"]
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        with running_demo_server(generated_demo, output / "server.log") as url:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    captured = capture_view(
                        browser, url, output, mobile=mobile, theme=theme
                    )
                    assert set(captured["tabs"]) == {tab["id"] for tab in TAB_CONFIG}
                    assert set(captured["scenarios"]) == set(SCENARIOS)
                    assert len(captured["report_sections"]) == 8
                    screenshots = captured["screenshots"]
                    assert "range-four-weeks.png" in screenshots
                    assert any(
                        name.startswith("sprint-charts-") for name in screenshots
                    )
                    for tab in TAB_CONFIG:
                        assert any(
                            name.startswith(tab["id"] + "-page-")
                            for name in screenshots
                        )
                finally:
                    browser.close()
