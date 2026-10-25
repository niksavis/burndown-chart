import tempfile
from pathlib import Path
from typing import Literal

import pytest
from playwright.sync_api import ViewportSize, sync_playwright

from devtools.browser_observer import BrowserObservation
from devtools.journeys import capture_exported_report, capture_registered_tabs
from devtools.server import running_demo_server
from ui.tabs import TAB_CONFIG


@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile"])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_demo_tabs_and_budget_render_offline(
    generated_demo: Path, mobile: bool, theme: Literal["light", "dark"]
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        with running_demo_server(generated_demo, output / "server.log") as url:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    viewport: ViewportSize = (
                        {"width": 390, "height": 844}
                        if mobile
                        else {"width": 1440, "height": 1000}
                    )
                    context = browser.new_context(
                        viewport=viewport, color_scheme=theme, service_workers="block"
                    )
                    page = context.new_page()
                    observation = BrowserObservation()
                    observation.observe(context, page)
                    captured = capture_registered_tabs(page, url, output, mobile=mobile)
                    assert set(captured) == {tab["id"] for tab in TAB_CONFIG}
                    assert page.evaluate(
                        "matchMedia('(prefers-color-scheme: dark)').matches"
                    ) is (theme == "dark")
                    assert len(capture_exported_report(page, output)) == 8
                    observation.assert_clean()
                finally:
                    browser.close()
