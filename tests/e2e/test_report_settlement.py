import tempfile
from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch

import pytest
from playwright.sync_api import Page, expect, sync_playwright

from devtools.journeys import capture_exported_report
from devtools.report_observation import SCRIPT
from devtools.server import running_demo_server


def assert_report_bars_start_at_zero(page: Page, label: str) -> None:
    maximum_gap = page.evaluate("""() => {
        const chart = Chart.getChart('weeklyBreakdownChart');
        if (!chart) throw new Error('Weekly chart was not created');
        const series = chart.getDatasetMeta(0);
        const zero = chart.scales[series.yAxisID].getPixelForValue(0);
        const values = chart.data.datasets[0].data;
        return Math.max(...series.data.filter((element, index) => values[index] != null)
            .map(element => Math.abs(element.base - zero)));
    }""")
    assert maximum_gap <= 1, f"{label}: weekly bars {maximum_gap:.2f}px from zero"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_report_captures_wait_for_final_bar_positions(
    generated_demo: Path, theme: Literal["light", "dark"]
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        with running_demo_server(generated_demo, output / "server.log") as url:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    page = browser.new_page(color_scheme=theme)
                    page.goto(url, wait_until="domcontentloaded")
                    expect(page.locator("#tab-content")).to_contain_text(
                        "Project Health", timeout=30000
                    )
                    page.add_init_script(
                        "(() => {" + SCRIPT.read_text(encoding="utf-8") + "})()"
                    )
                    take_screenshot = Page.screenshot
                    captured = []

                    def checked_screenshot(target: Page, **kwargs: Any) -> bytes:
                        captured.append(kwargs["path"])
                        assert_report_bars_start_at_zero(page, "Before viewport")
                        result = take_screenshot(target, **kwargs)
                        assert_report_bars_start_at_zero(page, "After viewport")
                        return result

                    with patch.object(
                        Page,
                        "screenshot",
                        autospec=True,
                        side_effect=checked_screenshot,
                    ):
                        assert len(capture_exported_report(page, output)) == 8
                    assert len(captured) >= 8
                finally:
                    browser.close()
